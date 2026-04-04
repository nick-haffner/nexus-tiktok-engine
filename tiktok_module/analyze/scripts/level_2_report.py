"""
Generate a Level 2 Content Strategy Analysis report.

Usage:
    python analyze/scripts/level_2_report.py

Reads:  store/data/analytics/analytics.db
Writes: analyze/outputs/level-2-content-strategy-YYYY-MM-DD.json
        analyze/outputs/level-2-content-strategy-YYYY-MM-DD.md
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import (
    connect, load_master_dataset, compare_dimension,
    build_missing_data, render_dimension_table, render_missing_data_section,
    fmt, fmt_pct, OUTPUT_DIR,
)

DIMENSIONS = [
    {"name": "framework", "buckets": None},
    {"name": "slide_layout", "buckets": None},
    {"name": "content_type", "buckets": None},
    {"name": "slide_count", "buckets": {
        "1-5": (1, 5), "6-8": (6, 8), "9+": (9, 999),
    }},
    {"name": "city", "buckets": None},
    {"name": "content_topics", "buckets": None},
    {"name": "sound_type", "buckets": None},
]


def build_dimension_comparisons(posts):
    comparisons = []
    for dim in DIMENSIONS:
        comp = compare_dimension(posts, dim["name"], dim["buckets"])
        comparisons.append(comp)
    return comparisons


def build_content_mix(conn):
    rows = conn.execute("""
        SELECT p.post_id, p.posted_date, p.content_type, p.slide_count,
               n.framework, n.slide_layout, n.city
        FROM posts p
        LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
        ORDER BY p.posted_date DESC
        LIMIT 10
    """).fetchall()

    mix = {}
    fields = ["content_type", "framework", "slide_layout", "city"]
    total = len(rows)
    for field in fields:
        counts = {}
        for r in rows:
            val = r[field] if r[field] else "(unclassified)"
            counts[val] = counts.get(val, 0) + 1
        mix[field] = [
            {"value": v, "count": c, "percentage": round(c / total * 100)}
            for v, c in sorted(counts.items(), key=lambda x: -x[1])
        ]

    return {"period": "last 10 posts", "dimensions": mix}


def build_correlation_highlights(posts):
    highlights = []

    def cross_cut(dim_a, dim_b, metric, posts):
        filtered = [p for p in posts if p.get(dim_a) and p.get(dim_b) and p.get(metric) is not None]
        if len(filtered) < 6:
            return None

        groups = {}
        for p in filtered:
            key = f"{p[dim_a]} x {p[dim_b]}"
            if key not in groups:
                groups[key] = []
            groups[key].append(p[metric])

        if len(groups) < 2:
            return None

        group_means = {k: sum(v) / len(v) for k, v in groups.items() if len(v) >= 3}
        if len(group_means) < 2:
            return None

        best = max(group_means, key=group_means.get)
        worst = min(group_means, key=group_means.get)
        if group_means[worst] == 0:
            return None
        ratio = group_means[best] / group_means[worst]

        if ratio > 1.5:
            n_total = sum(len(v) for k, v in groups.items() if k in (best, worst))
            return {
                "finding": f"{best} has {ratio:.1f}x higher {metric} than {worst}",
                "dimensions": [dim_a, dim_b],
                "metric": metric,
                "data_citation": f"{best}: {group_means[best]:.1f}, {worst}: {group_means[worst]:.1f}",
                "confidence": "high" if n_total >= 10 else "moderate" if n_total >= 5 else "low",
            }
        return None

    pairs = [
        ("framework", "city", "mean_views"),
        ("content_type", "slide_count", "save_rate"),
        ("framework", "content_type", "engagement_rate"),
    ]
    for dim_a, dim_b, metric in pairs:
        # Use individual post metric, not mean_ prefix
        result = cross_cut(dim_a, dim_b, metric.replace("mean_", ""), posts)
        if result:
            highlights.append(result)

    return highlights


def build_classification_gap(conn):
    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    fields = ["framework", "slide_layout", "city"]

    field_coverage = {}
    for field in fields:
        filled = conn.execute(
            f"SELECT COUNT(*) FROM nexus_post_metadata WHERE {field} IS NOT NULL AND {field} != ''"
        ).fetchone()[0]
        field_coverage[field] = {"filled": filled, "total": total, "pct": round(filled / total * 100) if total else 0}

    unclassified = conn.execute("""
        SELECT n.slug, n.framework, n.slide_layout, n.city
        FROM nexus_post_metadata n
        WHERE n.framework IS NULL
        ORDER BY n.slug
    """).fetchall()

    blocking = [f for f, info in field_coverage.items() if info["pct"] < 70 and f in ("framework", "city")]

    return {
        "total_posts": total,
        "classified_posts": field_coverage.get("framework", {}).get("filled", 0),
        "unclassified_posts": total - field_coverage.get("framework", {}).get("filled", 0),
        "field_coverage": field_coverage,
        "unclassified_list": [dict(r) for r in unclassified],
        "impact": f"framework at {field_coverage['framework']['pct']}% coverage — comparisons have low confidence"
            if field_coverage["framework"]["pct"] < 30
            else f"framework at {field_coverage['framework']['pct']}% coverage",
        "blocking_fields": blocking,
    }


def render_markdown(report):
    lines = []
    lines.append("# Level 2 Content Strategy Analysis")
    lines.append("")
    lines.append(f"**Analysis period:** {report['analysis_period']}  ")
    lines.append(f"**Generated:** {report['generated_at']}")
    lines.append("")

    # Dimension comparisons
    lines.append("## Dimension Comparisons")
    lines.append("")
    for comp in report["dimension_comparisons"]:
        lines.append(render_dimension_table(comp))

    # Content mix
    mix = report["content_mix"]
    lines.append("## Content Mix (Last 10 Posts)")
    lines.append("")
    for field, values in mix["dimensions"].items():
        lines.append(f"**{field}:**")
        for v in values:
            lines.append(f"- {v['value']}: {v['count']} ({v['percentage']}%)")
        lines.append("")

    # Correlation highlights
    highlights = report["correlation_highlights"]
    lines.append("## Correlation Highlights")
    lines.append("")
    if highlights:
        for h in highlights:
            lines.append(f"- [{h['confidence']}] {h['finding']} ({h['data_citation']})")
    else:
        lines.append("No significant cross-dimensional patterns found at current sample sizes.")
    lines.append("")

    # Classification gap
    gap = report["classification_gap"]
    lines.append("## Classification Gap")
    lines.append("")
    lines.append(f"**{gap['classified_posts']}/{gap['total_posts']}** posts classified. {gap['impact']}.")
    lines.append("")
    if gap["blocking_fields"]:
        lines.append(f"**Blocking:** {', '.join(gap['blocking_fields'])} below 70% coverage — backfill recommended.")
        lines.append("")

    # Missing data
    lines.append(render_missing_data_section(report["missing_data"]))

    return "\n".join(lines)


def main():
    conn = connect()
    posts = load_master_dataset(conn)

    comparisons = build_dimension_comparisons(posts)
    content_mix = build_content_mix(conn)
    highlights = build_correlation_highlights(posts)
    gap = build_classification_gap(conn)
    missing = build_missing_data(conn)

    report = {
        "report_type": "level_2_content_strategy",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_period": "all-time",
        "dimension_comparisons": comparisons,
        "content_mix": content_mix,
        "correlation_highlights": highlights,
        "classification_gap": gap,
        "missing_data": missing,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = os.path.join(OUTPUT_DIR, f"level-2-content-strategy-{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    md_path = os.path.join(OUTPUT_DIR, f"level-2-content-strategy-{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(report))

    print(f"Level 2 report generated: {md_path}")
    conn.close()


if __name__ == "__main__":
    main()
