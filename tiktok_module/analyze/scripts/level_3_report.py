"""
Generate a Level 3 Audience & Growth Analysis report.

Usage:
    python analyze/scripts/level_3_report.py

Reads:  store/data/analytics/analytics.db
Writes: analyze/outputs/level-3-audience-growth-YYYY-MM-DD.json
        analyze/outputs/level-3-audience-growth-YYYY-MM-DD.md
"""

import json
import os
import sys
from datetime import datetime, timezone
from statistics import median

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import (
    connect, load_master_dataset, compare_dimension,
    build_missing_data, render_dimension_table, render_missing_data_section,
    fmt, fmt_pct, safe_mean, safe_median, OUTPUT_DIR,
)


FOLLOWER_DIMENSIONS = [
    {"name": "framework", "buckets": None},
    {"name": "slide_layout", "buckets": None},
    {"name": "content_type", "buckets": None},
    {"name": "city", "buckets": None},
    {"name": "slide_count", "buckets": {
        "1-5": (1, 5), "6-8": (6, 8), "9+": (9, 999),
    }},
]


def build_follower_acquisition(posts):
    results = []
    for dim in FOLLOWER_DIMENSIONS:
        comp = compare_dimension(posts, dim["name"], dim["buckets"])
        # Re-sort by follower conversion
        comp["groups"].sort(key=lambda g: g["mean_follower_conversion"] or 0, reverse=True)
        results.append(comp)
    return results


def build_engagement_grid(posts):
    views_list = [p["views"] for p in posts if p["views"]]
    eng_list = [p["engagement_rate"] for p in posts if p["engagement_rate"] is not None]

    if not views_list or not eng_list:
        return {"quadrant_counts": {}, "quadrant_posts": {}, "profile_skew": None, "recommendation_signal": "Insufficient data."}

    med_views = median(views_list)
    med_eng = median(eng_list)

    quadrants = {"star": [], "niche_hit": [], "viral_shallow": [], "underperformer": []}
    for p in posts:
        if p["views"] is None or p["engagement_rate"] is None:
            continue
        if p["views"] >= med_views and p["engagement_rate"] >= med_eng:
            q = "star"
        elif p["views"] < med_views and p["engagement_rate"] >= med_eng:
            q = "niche_hit"
        elif p["views"] >= med_views and p["engagement_rate"] < med_eng:
            q = "viral_shallow"
        else:
            q = "underperformer"
        quadrants[q].append({
            "slug": p["slug"] or p["post_id"][:16],
            "views": p["views"],
            "engagement_rate": p["engagement_rate"],
            "follower_conversion": p["follower_conversion"],
        })

    counts = {k: len(v) for k, v in quadrants.items()}
    dominant = max(counts, key=counts.get)

    signals = {
        "star": "Account has a healthy mix of reach and resonance.",
        "niche_hit": "Content resonates deeply but reaches narrow audiences. Consider broader hooks to expand reach without losing engagement.",
        "viral_shallow": "Content reaches people but doesn't convert. Prioritize niche hit patterns for audience growth.",
        "underperformer": "Most content underperforms on both reach and engagement. Strategic review needed.",
    }

    return {
        "median_views_threshold": med_views,
        "median_engagement_threshold": med_eng,
        "quadrant_counts": counts,
        "quadrant_posts": quadrants,
        "profile_skew": dominant,
        "recommendation_signal": f"Account skews {dominant.replace('_', ' ').title()}. {signals[dominant]}",
    }


def build_save_rate_analysis(posts):
    save_rates = [p["save_rate"] for p in posts if p["save_rate"] is not None]
    if not save_rates:
        return {"high_save_posts": [], "high_save_dimensions": {}, "save_rate_follower_correlation": "insufficient_data"}

    med_save = median(save_rates)
    threshold = med_save * 2

    high_save = [p for p in posts if p["save_rate"] is not None and p["save_rate"] > threshold]

    # Which dimensions cluster in high-save posts
    dim_counts = {}
    for dim in ["framework", "city", "content_type"]:
        vals = {}
        for p in high_save:
            v = p.get(dim)
            if v:
                vals[v] = vals.get(v, 0) + 1
        if vals:
            dim_counts[dim] = sorted(vals.items(), key=lambda x: -x[1])

    # Correlation: save_rate vs follower_conversion
    pairs = [(p["save_rate"], p["follower_conversion"])
             for p in posts if p["save_rate"] is not None and p["follower_conversion"] is not None]
    if len(pairs) >= 5:
        high_save_fc = [fc for sr, fc in pairs if sr > med_save]
        low_save_fc = [fc for sr, fc in pairs if sr <= med_save]
        if high_save_fc and low_save_fc:
            high_mean = sum(high_save_fc) / len(high_save_fc)
            low_mean = sum(low_save_fc) / len(low_save_fc)
            if high_mean > low_mean * 1.3:
                corr = "positive"
            elif low_mean > high_mean * 1.3:
                corr = "negative"
            else:
                corr = "none"
        else:
            corr = "insufficient_data"
    else:
        corr = "insufficient_data"

    return {
        "save_rate_median": med_save,
        "threshold": threshold,
        "high_save_posts": [{
            "slug": p["slug"] or p["post_id"][:16],
            "save_rate": p["save_rate"],
            "views": p["views"],
            "follower_conversion": p["follower_conversion"],
        } for p in high_save],
        "high_save_dimensions": dim_counts,
        "save_rate_follower_correlation": corr,
        "data_citation": f"{len(pairs)} posts with both save_rate and follower_conversion",
    }


def build_return_audience_trend(conn):
    rows = conn.execute("""
        SELECT p.posted_date, r.fyp_percent
        FROM readings r
        JOIN posts p ON r.post_id = p.post_id
        WHERE r.fyp_percent IS NOT NULL
        ORDER BY p.posted_date
    """).fetchall()

    if not rows:
        return {"fyp_percent_trend": [], "trend_direction": "insufficient_data", "current_mean_fyp": None, "traffic_source_breakdown": None}

    trend = [{"posted_date": r["posted_date"], "fyp_percent": r["fyp_percent"]} for r in rows]
    fyp_values = [r["fyp_percent"] for r in rows]

    if len(fyp_values) >= 4:
        first_half = fyp_values[:len(fyp_values) // 2]
        second_half = fyp_values[len(fyp_values) // 2:]
        first_mean = sum(first_half) / len(first_half)
        second_mean = sum(second_half) / len(second_half)
        if second_mean < first_mean - 2:
            direction = "declining"
        elif second_mean > first_mean + 2:
            direction = "increasing"
        else:
            direction = "stable"
    else:
        direction = "insufficient_data"

    recent = fyp_values[-5:] if len(fyp_values) >= 5 else fyp_values
    current_mean = round(sum(recent) / len(recent), 1)

    return {
        "fyp_percent_trend": trend,
        "trend_direction": direction,
        "current_mean_fyp": current_mean,
        "traffic_source_breakdown": None,  # Stub — Tier 3
    }


def build_account_growth(conn):
    rows = conn.execute("SELECT captured_date, followers, total_likes FROM account ORDER BY captured_date").fetchall()
    checkpoints = [dict(r) for r in rows]

    if len(checkpoints) < 2:
        return {
            "checkpoints": checkpoints,
            "growth_rate_trend": "insufficient_data",
            "followers_per_post_trend": [],
            "projected_milestones": None,
        }

    rates = []
    for i in range(1, len(checkpoints)):
        prev = checkpoints[i - 1]["followers"]
        cur = checkpoints[i]["followers"]
        if prev and prev > 0:
            rates.append(round((cur - prev) / prev * 100, 1))

    if len(rates) >= 3:
        first_half = rates[:len(rates) // 2]
        second_half = rates[len(rates) // 2:]
        if sum(second_half) / len(second_half) > sum(first_half) / len(first_half) * 1.2:
            trend = "accelerating"
        elif sum(second_half) / len(second_half) < sum(first_half) / len(first_half) * 0.8:
            trend = "decelerating"
        else:
            trend = "steady"
    else:
        trend = "insufficient_data"

    return {
        "checkpoints": checkpoints,
        "growth_rate_trend": trend,
        "followers_per_post_trend": [],
        "projected_milestones": None,
    }


def render_markdown(report):
    lines = []
    lines.append("# Level 3 Audience & Growth Analysis")
    lines.append("")
    lines.append(f"**Analysis period:** {report['analysis_period']}  ")
    lines.append(f"**Generated:** {report['generated_at']}")
    lines.append("")

    # Follower acquisition
    lines.append("## Follower Acquisition by Dimension")
    lines.append("")
    for comp in report["follower_acquisition"]:
        lines.append(render_dimension_table(comp, primary_metric="mean_follower_conversion"))

    # Engagement grid
    grid = report["engagement_quality_grid"]
    lines.append("## Engagement Quality Grid")
    lines.append("")
    if grid["quadrant_counts"]:
        lines.append(f"Thresholds: median views = {fmt(grid.get('median_views_threshold'))}, "
                     f"median engagement = {fmt_pct(grid.get('median_engagement_threshold'))}")
        lines.append("")
        lines.append("| Quadrant | Count | Description |")
        lines.append("|---|---|---|")
        labels = {
            "star": "High views + high engagement",
            "niche_hit": "Low views + high engagement",
            "viral_shallow": "High views + low engagement",
            "underperformer": "Low views + low engagement",
        }
        for q, label in labels.items():
            count = grid["quadrant_counts"].get(q, 0)
            lines.append(f"| {q.replace('_', ' ').title()} | {count} | {label} |")
        lines.append("")
        lines.append(f"**Profile:** {grid['recommendation_signal']}")
    else:
        lines.append("Insufficient data for engagement grid.")
    lines.append("")

    # Save rate
    save = report["save_rate_analysis"]
    lines.append("## Save Rate as Growth Indicator")
    lines.append("")
    lines.append(f"Save rate/follower correlation: **{save['save_rate_follower_correlation']}** ({save.get('data_citation', '')})")
    lines.append("")
    if save["high_save_posts"]:
        lines.append(f"High-save posts (>{fmt(save.get('threshold'))}% save rate):")
        for p in save["high_save_posts"]:
            lines.append(f"- {p['slug']}: {fmt_pct(p['save_rate'])} save, {fmt(p['views'])} views, {fmt(p['follower_conversion'])} followers/1K")
    lines.append("")

    # Return audience
    rat = report["return_audience_trend"]
    lines.append("## Return Audience Trend (FYP%)")
    lines.append("")
    lines.append(f"Trend: **{rat['trend_direction']}** | Current mean FYP: {fmt_pct(rat['current_mean_fyp'])}")
    if rat["traffic_source_breakdown"] is None:
        lines.append("*Traffic source breakdown not available (Tier 3 stub).*")
    lines.append("")

    # Account growth
    ag = report["account_growth_trajectory"]
    lines.append("## Account Growth Trajectory")
    lines.append("")
    lines.append(f"Growth trend: **{ag['growth_rate_trend']}** | Checkpoints: {len(ag['checkpoints'])}")
    if ag["checkpoints"]:
        latest = ag["checkpoints"][-1]
        lines.append(f"Latest: {latest['followers']} followers, {latest['total_likes']} likes ({latest['captured_date']})")
    lines.append("")

    # Missing data
    lines.append(render_missing_data_section(report["missing_data"]))

    return "\n".join(lines)


def main():
    conn = connect()
    posts = load_master_dataset(conn)

    report = {
        "report_type": "level_3_audience_growth",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_period": "all-time",
        "follower_acquisition": build_follower_acquisition(posts),
        "engagement_quality_grid": build_engagement_grid(posts),
        "save_rate_analysis": build_save_rate_analysis(posts),
        "return_audience_trend": build_return_audience_trend(conn),
        "account_growth_trajectory": build_account_growth(conn),
        "missing_data": build_missing_data(conn),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = os.path.join(OUTPUT_DIR, f"level-3-audience-growth-{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    md_path = os.path.join(OUTPUT_DIR, f"level-3-audience-growth-{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(report))

    print(f"Level 3 report generated: {md_path}")
    conn.close()


if __name__ == "__main__":
    main()
