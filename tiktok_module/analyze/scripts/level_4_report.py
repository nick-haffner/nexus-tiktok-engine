"""
Generate a Level 4 Cadence & Timing Optimization report.

Usage:
    python analyze/scripts/level_4_report.py

Reads:  store/data/analytics/analytics.db
Writes: analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.json
        analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.md
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from statistics import stdev

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import (
    connect, load_master_dataset, compare_dimension,
    build_missing_data, render_dimension_table, render_missing_data_section,
    fmt, fmt_pct, safe_mean, OUTPUT_DIR,
)


def build_posting_frequency(posts):
    if not posts:
        return {"frequency_periods": [], "overall_posts_per_week": None,
                "frequency_performance_correlation": "insufficient_data"}

    sorted_posts = sorted(posts, key=lambda p: p["posted_date"])
    min_date = datetime.fromisoformat(sorted_posts[0]["posted_date"]).date()
    max_date = datetime.fromisoformat(sorted_posts[-1]["posted_date"]).date()
    total_weeks = max((max_date - min_date).days / 7, 1)

    # Rolling 7-day windows
    periods = []
    window_start = min_date
    while window_start <= max_date:
        window_end = window_start + timedelta(days=7)
        window_posts = [
            p for p in sorted_posts
            if window_start <= datetime.fromisoformat(p["posted_date"]).date() < window_end
        ]
        if window_posts:
            views = [p["views"] for p in window_posts if p["views"]]
            eng = [p["engagement_rate"] for p in window_posts if p["engagement_rate"] is not None]
            save = [p["save_rate"] for p in window_posts if p["save_rate"] is not None]
            periods.append({
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "posts_count": len(window_posts),
                "mean_views": safe_mean(views),
                "mean_engagement_rate": safe_mean(eng),
                "mean_save_rate": safe_mean(save),
            })
        window_start = window_end

    overall_ppw = round(len(sorted_posts) / total_weeks, 1)

    # Correlation: do higher-frequency weeks perform better?
    if len(periods) >= 4:
        high_freq = [p for p in periods if p["posts_count"] >= 2]
        low_freq = [p for p in periods if p["posts_count"] == 1]
        if high_freq and low_freq:
            high_mean = safe_mean([p["mean_views"] for p in high_freq if p["mean_views"]])
            low_mean = safe_mean([p["mean_views"] for p in low_freq if p["mean_views"]])
            if high_mean and low_mean:
                if high_mean > low_mean * 1.2:
                    corr = "positive"
                elif low_mean > high_mean * 1.2:
                    corr = "negative"
                else:
                    corr = "none"
            else:
                corr = "insufficient_data"
        else:
            corr = "insufficient_data"
    else:
        corr = "insufficient_data"

    return {
        "frequency_periods": periods,
        "overall_posts_per_week": overall_ppw,
        "frequency_performance_correlation": corr,
        "data_citation": f"{len(periods)} weekly periods analyzed, {len(posts)} total posts",
    }


def build_day_of_week(posts):
    return compare_dimension(posts, "posted_day_of_week")


def build_time_of_day(posts):
    # Fully stubbed — posted_time is NULL for all posts
    has_time = [p for p in posts if p.get("posted_time")]
    if not has_time:
        return {
            "dimension": "time_of_day",
            "groups": [],
            "excluded_count": len(posts),
            "stubbed": True,
        }

    buckets = {
        "morning (06-12)": (6, 11),
        "midday (12-17)": (12, 16),
        "evening (17-21)": (17, 20),
        "night (21-06)": (21, 5),
    }
    # Would bucket by hour extracted from posted_time
    # For now, return empty
    return {
        "dimension": "time_of_day",
        "groups": [],
        "excluded_count": len(posts),
        "stubbed": True,
    }


def build_gap_analysis(posts):
    buckets = {
        "0-1 days": (0, 1),
        "2-3 days": (2, 3),
        "4-7 days": (4, 7),
        "8+ days": (8, 9999),
    }
    comp = compare_dimension(posts, "days_since_previous_post", buckets)

    # Determine optimal gap signal
    best = None
    if comp["groups"]:
        # Filter to groups with reasonable confidence
        viable = [g for g in comp["groups"] if g["post_count"] >= 3]
        if viable:
            best_group = max(viable, key=lambda g: g["mean_views"] or 0)
            best = {
                "bucket": best_group["value"],
                "mean_views": best_group["mean_views"],
                "confidence": best_group["confidence"],
            }

    comp["optimal_gap_signal"] = best
    return comp


def build_consistency(posts):
    gaps = [p["days_since_previous_post"] for p in posts if p["days_since_previous_post"] is not None]

    if len(gaps) < 3:
        return {"gap_stddev": None, "posting_pattern": "insufficient_data",
                "consistency_performance_signal": None}

    sd = round(stdev(gaps), 1)

    if sd < 2:
        pattern = "consistent"
    elif sd > 5:
        pattern = "bursty"
    else:
        pattern = "irregular"

    # Compare performance in consistent vs bursty stretches
    # Simple: split posts into those preceded by a gap near the mean vs far from it
    mean_gap = sum(gaps) / len(gaps)
    signal = None
    near = [p for p in posts if p["days_since_previous_post"] is not None
            and abs(p["days_since_previous_post"] - mean_gap) <= sd]
    far = [p for p in posts if p["days_since_previous_post"] is not None
           and abs(p["days_since_previous_post"] - mean_gap) > sd]
    if len(near) >= 3 and len(far) >= 3:
        near_views = safe_mean([p["views"] for p in near if p["views"]])
        far_views = safe_mean([p["views"] for p in far if p["views"]])
        if near_views and far_views:
            if near_views > far_views * 1.3:
                signal = "Consistent posting cadence correlates with higher views."
            elif far_views > near_views * 1.3:
                signal = "Irregular posting gaps correlate with higher views."
            else:
                signal = "No significant difference between consistent and irregular stretches."

    return {
        "gap_stddev": sd,
        "posting_pattern": pattern,
        "consistency_performance_signal": signal,
    }


def render_markdown(report):
    lines = []
    lines.append("# Level 4 Cadence & Timing Optimization")
    lines.append("")
    lines.append(f"**Analysis period:** {report['analysis_period']}  ")
    lines.append(f"**Generated:** {report['generated_at']}")
    lines.append("")

    # Frequency
    freq = report["posting_frequency"]
    lines.append("## Posting Frequency")
    lines.append("")
    lines.append(f"Overall: **{fmt(freq['overall_posts_per_week'])} posts/week** | "
                 f"Frequency-performance correlation: **{freq['frequency_performance_correlation']}**")
    lines.append(f"*{freq.get('data_citation', '')}*")
    lines.append("")

    # Day of week
    lines.append("## Day-of-Week Performance")
    lines.append("")
    lines.append(render_dimension_table(report["day_of_week"]))

    # Time of day
    tod = report["time_of_day"]
    lines.append("## Time-of-Day Performance")
    lines.append("")
    if tod.get("stubbed"):
        lines.append("*Fully stubbed. `posted_time` is not captured (Tier 2).*")
    else:
        lines.append(render_dimension_table(tod))
    lines.append("")

    # Gap analysis
    gap = report["gap_analysis"]
    lines.append("## Gap Analysis")
    lines.append("")
    lines.append(render_dimension_table(gap))
    if gap.get("optimal_gap_signal"):
        sig = gap["optimal_gap_signal"]
        lines.append(f"**Optimal gap:** {sig['bucket']} (mean views: {fmt(sig['mean_views'])}, confidence: {sig['confidence']})")
    else:
        lines.append("*No optimal gap signal — insufficient data per bucket.*")
    lines.append("")

    # Consistency
    con = report["consistency"]
    lines.append("## Posting Consistency")
    lines.append("")
    lines.append(f"Gap standard deviation: **{fmt(con['gap_stddev'])}** days | Pattern: **{con['posting_pattern']}**")
    if con["consistency_performance_signal"]:
        lines.append(f"Signal: {con['consistency_performance_signal']}")
    lines.append("")

    # Missing data
    lines.append(render_missing_data_section(report["missing_data"]))

    return "\n".join(lines)


def main():
    conn = connect()
    posts = load_master_dataset(conn)

    report = {
        "report_type": "level_4_cadence_timing",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_period": "all-time",
        "posting_frequency": build_posting_frequency(posts),
        "day_of_week": build_day_of_week(posts),
        "time_of_day": build_time_of_day(posts),
        "gap_analysis": build_gap_analysis(posts),
        "consistency": build_consistency(posts),
        "missing_data": build_missing_data(conn),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = os.path.join(OUTPUT_DIR, f"level-4-cadence-timing-{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    md_path = os.path.join(OUTPUT_DIR, f"level-4-cadence-timing-{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(report))

    print(f"Level 4 report generated: {md_path}")
    conn.close()


if __name__ == "__main__":
    main()
