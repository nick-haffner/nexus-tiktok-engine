"""
Generate a Level 5 Conversion Funnel Analysis report.

Usage:
    python analyze/scripts/level_5_report.py

Reads:  store/data/analytics/analytics.db
Writes: analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.json
        analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.md
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import (
    connect, load_master_dataset, compare_dimension,
    build_missing_data, render_dimension_table, render_missing_data_section,
    fmt, fmt_pct, safe_mean, OUTPUT_DIR,
)


CTA_PATTERNS = {
    "waitlist": ["waitlist", "wait list", "sign up", "join the"],
    "website": ["nexus-concierge.com", "nexusconcierge.com"],
    "follow": ["follow us", "follow for", "give us a follow"],
    "engage": ["save this", "share this", "comment below", "bookmark"],
}
PRODUCT_KEYWORDS = ["nexus", "concierge", "local friend", "local recs"]


def classify_cta(description):
    if not description:
        return {"has_cta": False, "cta_type": "none", "has_product_mention": False}

    desc_lower = description.lower()

    cta_type = "none"
    for ctype, patterns in CTA_PATTERNS.items():
        for pattern in patterns:
            if pattern in desc_lower:
                cta_type = ctype
                break
        if cta_type != "none":
            break

    has_product = any(kw in desc_lower for kw in PRODUCT_KEYWORDS)

    return {
        "has_cta": cta_type != "none",
        "cta_type": cta_type,
        "has_product_mention": has_product,
    }


def enrich_with_cta(posts):
    for post in posts:
        cta = classify_cta(post["description"])
        post.update(cta)
    return posts


def build_caption_length(posts):
    buckets = {
        "short (<50)": (0, 49),
        "medium (50-150)": (50, 150),
        "long (150+)": (151, 99999),
    }
    comp = compare_dimension(posts, "caption_length_words", buckets)

    # Add comment_rate as a supplementary metric per group
    for group in comp["groups"]:
        matching = [p for p in posts
                    if p.get("caption_length_words") is not None
                    and p.get("comment_rate") is not None]
        bucket_posts = []
        for p in matching:
            for name, (lo, hi) in buckets.items():
                if lo <= p["caption_length_words"] <= hi and name == group["value"]:
                    bucket_posts.append(p)
        group["mean_comment_rate"] = safe_mean([p["comment_rate"] for p in bucket_posts]) if bucket_posts else None

    # Optimal length signal
    viable = [g for g in comp["groups"] if g["post_count"] >= 3]
    if viable:
        best = max(viable, key=lambda g: g.get("mean_comment_rate") or 0)
        comp["optimal_length_signal"] = {
            "bucket": best["value"],
            "mean_comment_rate": best.get("mean_comment_rate"),
            "confidence": best["confidence"],
        }
    else:
        comp["optimal_length_signal"] = None

    return comp


def build_hashtag_strategy(posts):
    buckets = {
        "minimal (0-2)": (0, 2),
        "standard (3-5)": (3, 5),
        "heavy (6+)": (6, 99999),
    }
    comp = compare_dimension(posts, "hashtag_count", buckets)

    viable = [g for g in comp["groups"] if g["post_count"] >= 3]
    if viable:
        best = max(viable, key=lambda g: g["mean_views"] or 0)
        comp["optimal_hashtag_signal"] = {
            "range": best["value"],
            "mean_views": best["mean_views"],
            "confidence": best["confidence"],
        }
    else:
        comp["optimal_hashtag_signal"] = None

    return comp


def build_cta_analysis(posts):
    # CTA presence
    with_cta = [p for p in posts if p["has_cta"]]
    without_cta = [p for p in posts if not p["has_cta"]]

    def group_metrics(group):
        if not group:
            return {"count": 0, "mean_engagement_rate": None, "mean_save_rate": None, "mean_follower_conversion": None}
        return {
            "count": len(group),
            "mean_engagement_rate": safe_mean([p["engagement_rate"] for p in group if p["engagement_rate"] is not None]),
            "mean_save_rate": safe_mean([p["save_rate"] for p in group if p["save_rate"] is not None]),
            "mean_follower_conversion": safe_mean([p["follower_conversion"] for p in group if p["follower_conversion"] is not None]),
        }

    cta_presence = {
        "with_cta": group_metrics(with_cta),
        "without_cta": group_metrics(without_cta),
    }

    # CTA type comparison
    by_type = {}
    for p in posts:
        t = p["cta_type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(p)

    cta_type_comparison = [
        {"cta_type": t, **group_metrics(group)}
        for t, group in sorted(by_type.items())
    ]

    # Product mention impact
    with_mention = [p for p in posts if p["has_product_mention"]]
    without_mention = [p for p in posts if not p["has_product_mention"]]
    product_mention_impact = {
        "with_mention": group_metrics(with_mention),
        "without_mention": group_metrics(without_mention),
    }

    # Finding
    w = cta_presence["with_cta"]
    wo = cta_presence["without_cta"]
    if w["mean_save_rate"] and wo["mean_save_rate"] and wo["mean_save_rate"] > 0:
        ratio = w["mean_save_rate"] / wo["mean_save_rate"]
        if ratio > 1.15:
            finding = f"Posts with CTAs have {ratio:.1f}x higher save rate than posts without."
        elif ratio < 0.85:
            finding = f"Posts with CTAs have {ratio:.1f}x lower save rate than posts without."
        else:
            finding = "No measurable difference in save rate between posts with and without CTAs."
    else:
        finding = "Insufficient data to compare CTA impact."

    return {
        "cta_presence": cta_presence,
        "cta_type_comparison": cta_type_comparison,
        "product_mention_impact": product_mention_impact,
        "finding": finding,
    }


def build_content_funnel(posts):
    total_views = sum(p["views"] for p in posts if p["views"])
    total_likes = sum(p["likes"] for p in posts if p["likes"])
    total_comments = sum(p["comments"] for p in posts if p["comments"])
    total_shares = sum(p["shares"] for p in posts if p["shares"])
    total_bookmarks = sum(p["bookmarks"] for p in posts if p["bookmarks"])
    total_new_followers = sum(p["new_followers"] for p in posts if p["new_followers"] is not None)

    if not total_views:
        return {"funnel_stages": [], "stage_dropoffs": [], "funnel_bottleneck": None, "funnel_by_content_type": {}}

    engagement_rate = round((total_likes + total_comments + total_shares) / total_views * 100, 2)
    save_rate = round(total_bookmarks / total_views * 100, 2)
    follower_conversion = round(total_new_followers / total_views * 1000, 2) if total_new_followers else None

    stages = [
        {"stage": "View", "value": total_views, "unit": "count"},
        {"stage": "Engage", "value": engagement_rate, "unit": "percent"},
        {"stage": "Save", "value": save_rate, "unit": "percent"},
        {"stage": "Follow", "value": follower_conversion, "unit": "per_1k_views"},
        {"stage": "Profile Visit", "value": None, "unit": "per_1k_views"},  # Stub
    ]

    # Stage dropoffs
    dropoffs = []
    if engagement_rate and save_rate:
        dropoffs.append({"from": "Engage", "to": "Save", "ratio": round(save_rate / engagement_rate, 3)})
    if save_rate and follower_conversion:
        # Convert follower_conversion from per-1K to percent for comparable ratio
        fc_pct = follower_conversion / 10
        dropoffs.append({"from": "Save", "to": "Follow", "ratio": round(fc_pct / save_rate, 3) if save_rate else None})

    bottleneck = None
    if dropoffs:
        worst = min(dropoffs, key=lambda d: d["ratio"] if d["ratio"] is not None else 999)
        bottleneck = f"Largest dropoff: {worst['from']} -> {worst['to']} (ratio: {worst['ratio']})"

    # By content type
    by_type = {}
    for ct in ["carousel", "video"]:
        ct_posts = [p for p in posts if p["content_type"] == ct]
        if not ct_posts:
            continue
        ct_views = sum(p["views"] for p in ct_posts if p["views"])
        if not ct_views:
            continue
        ct_likes = sum(p["likes"] for p in ct_posts if p["likes"])
        ct_comments = sum(p["comments"] for p in ct_posts if p["comments"])
        ct_shares = sum(p["shares"] for p in ct_posts if p["shares"])
        ct_bookmarks = sum(p["bookmarks"] for p in ct_posts if p["bookmarks"])
        ct_followers = sum(p["new_followers"] for p in ct_posts if p["new_followers"] is not None)
        by_type[ct] = {
            "posts": len(ct_posts),
            "engagement_rate": round((ct_likes + ct_comments + ct_shares) / ct_views * 100, 2),
            "save_rate": round(ct_bookmarks / ct_views * 100, 2),
            "follower_conversion": round(ct_followers / ct_views * 1000, 2) if ct_followers else None,
        }

    return {
        "funnel_stages": stages,
        "stage_dropoffs": dropoffs,
        "funnel_bottleneck": bottleneck,
        "funnel_by_content_type": by_type,
    }


def build_cta_timeline(posts):
    sorted_posts = sorted(posts, key=lambda p: p["posted_date"])
    timeline = [{
        "posted_date": p["posted_date"],
        "slug": p["slug"] or p["post_id"][:16],
        "cta_type": p["cta_type"],
        "save_rate": p["save_rate"],
        "follower_conversion": p["follower_conversion"],
    } for p in sorted_posts]

    # Detect shift: split at midpoint, compare CTA prevalence
    phase_comparison = None
    if len(sorted_posts) >= 10:
        mid = len(sorted_posts) // 2
        first_half = sorted_posts[:mid]
        second_half = sorted_posts[mid:]
        first_cta_pct = sum(1 for p in first_half if p["has_cta"]) / len(first_half) * 100
        second_cta_pct = sum(1 for p in second_half if p["has_cta"]) / len(second_half) * 100
        if abs(first_cta_pct - second_cta_pct) > 20:
            first_save = safe_mean([p["save_rate"] for p in first_half if p["save_rate"] is not None])
            second_save = safe_mean([p["save_rate"] for p in second_half if p["save_rate"] is not None])
            phase_comparison = {
                "first_half_cta_pct": round(first_cta_pct, 1),
                "second_half_cta_pct": round(second_cta_pct, 1),
                "first_half_save_rate": first_save,
                "second_half_save_rate": second_save,
                "shift_detected": True,
            }

    return {"timeline": timeline, "phase_comparison": phase_comparison}


def render_markdown(report):
    lines = []
    lines.append("# Level 5 Conversion Funnel Analysis")
    lines.append("")
    lines.append(f"**Analysis period:** {report['analysis_period']}  ")
    lines.append(f"**Generated:** {report['generated_at']}")
    lines.append("")

    # Caption length
    lines.append("## Caption Length")
    lines.append("")
    cl = report["caption_length"]
    lines.append(render_dimension_table(cl))
    if cl.get("optimal_length_signal"):
        sig = cl["optimal_length_signal"]
        lines.append(f"**Optimal for comments:** {sig['bucket']} (mean comment rate: {fmt_pct(sig['mean_comment_rate'])}, confidence: {sig['confidence']})")
    lines.append("")

    # Hashtag strategy
    lines.append("## Hashtag Strategy")
    lines.append("")
    hs = report["hashtag_strategy"]
    lines.append(render_dimension_table(hs))
    if hs.get("optimal_hashtag_signal"):
        sig = hs["optimal_hashtag_signal"]
        lines.append(f"**Optimal range:** {sig['range']} (mean views: {fmt(sig['mean_views'])}, confidence: {sig['confidence']})")
    lines.append("")

    # CTA analysis
    cta = report["cta_analysis"]
    lines.append("## CTA & Product Mention Impact")
    lines.append("")
    lines.append(f"**Finding:** {cta['finding']}")
    lines.append("")
    lines.append("| Group | Posts | Eng% | Save% | Follower/1K |")
    lines.append("|---|---|---|---|---|")
    for label, data in [("With CTA", cta["cta_presence"]["with_cta"]),
                         ("Without CTA", cta["cta_presence"]["without_cta"])]:
        lines.append(f"| {label} | {data['count']} | {fmt_pct(data['mean_engagement_rate'])} | "
                     f"{fmt_pct(data['mean_save_rate'])} | {fmt(data['mean_follower_conversion'])} |")
    lines.append("")

    lines.append("**By CTA type:**")
    lines.append("")
    lines.append("| Type | Posts | Eng% | Save% | Follower/1K |")
    lines.append("|---|---|---|---|---|")
    for t in cta["cta_type_comparison"]:
        lines.append(f"| {t['cta_type']} | {t['count']} | {fmt_pct(t['mean_engagement_rate'])} | "
                     f"{fmt_pct(t['mean_save_rate'])} | {fmt(t['mean_follower_conversion'])} |")
    lines.append("")

    pm = cta["product_mention_impact"]
    lines.append("**Product mention:**")
    lines.append(f"- With mention: {pm['with_mention']['count']} posts, "
                 f"eng {fmt_pct(pm['with_mention']['mean_engagement_rate'])}, "
                 f"save {fmt_pct(pm['with_mention']['mean_save_rate'])}")
    lines.append(f"- Without mention: {pm['without_mention']['count']} posts, "
                 f"eng {fmt_pct(pm['without_mention']['mean_engagement_rate'])}, "
                 f"save {fmt_pct(pm['without_mention']['mean_save_rate'])}")
    lines.append("")

    # Content funnel
    funnel = report["content_funnel"]
    lines.append("## Content Funnel")
    lines.append("")
    if funnel["funnel_stages"]:
        lines.append("| Stage | Value |")
        lines.append("|---|---|")
        for s in funnel["funnel_stages"]:
            if s["value"] is None:
                val = "-- (stub)"
            elif s["unit"] == "percent":
                val = f"{s['value']}%"
            elif s["unit"] == "per_1k_views":
                val = f"{s['value']} per 1K views"
            else:
                val = fmt(s["value"])
            lines.append(f"| {s['stage']} | {val} |")
        lines.append("")
        if funnel["funnel_bottleneck"]:
            lines.append(f"**{funnel['funnel_bottleneck']}**")
            lines.append("")

        if funnel["funnel_by_content_type"]:
            lines.append("**By content type:**")
            lines.append("")
            lines.append("| Type | Posts | Eng% | Save% | Follower/1K |")
            lines.append("|---|---|---|---|---|")
            for ct, data in funnel["funnel_by_content_type"].items():
                lines.append(f"| {ct} | {data['posts']} | {data['engagement_rate']}% | "
                             f"{data['save_rate']}% | {fmt(data['follower_conversion'])} |")
            lines.append("")

    # CTA timeline
    tl = report["cta_timeline"]
    lines.append("## CTA Evolution Timeline")
    lines.append("")
    if tl["phase_comparison"]:
        pc = tl["phase_comparison"]
        lines.append(f"**Shift detected:** CTA usage went from {pc['first_half_cta_pct']}% to {pc['second_half_cta_pct']}%.")
        lines.append(f"Save rate: {fmt_pct(pc['first_half_save_rate'])} -> {fmt_pct(pc['second_half_save_rate'])}")
    else:
        lines.append("No significant CTA strategy shift detected.")
    lines.append("")

    # Missing data
    lines.append(render_missing_data_section(report["missing_data"]))

    return "\n".join(lines)


def main():
    conn = connect()
    posts = load_master_dataset(conn)
    posts = enrich_with_cta(posts)

    report = {
        "report_type": "level_5_conversion_funnel",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_period": "all-time",
        "caption_length": build_caption_length(posts),
        "hashtag_strategy": build_hashtag_strategy(posts),
        "cta_analysis": build_cta_analysis(posts),
        "content_funnel": build_content_funnel(posts),
        "cta_timeline": build_cta_timeline(posts),
        "missing_data": build_missing_data(conn),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = os.path.join(OUTPUT_DIR, f"level-5-conversion-funnel-{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    md_path = os.path.join(OUTPUT_DIR, f"level-5-conversion-funnel-{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(report))

    print(f"Level 5 report generated: {md_path}")
    conn.close()


if __name__ == "__main__":
    main()
