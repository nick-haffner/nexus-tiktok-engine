"""
Generate a Level 1 Performance Report.

Usage:
    python analyze/scripts/level_1_report.py [--days N]

Options:
    --days N    Reporting period length in days (default: 7)

Reads:  store/data/analytics/analytics.db
Writes: analyze/outputs/level-1-performance-YYYY-MM-DD.json
        analyze/outputs/level-1-performance-YYYY-MM-DD.md

Exit codes:
    0 — Success
    1 — Fatal error (DB not found, query error)
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from statistics import median

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import build_missing_data, render_missing_data_section


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
DB_PATH = os.path.join(MODULE_ROOT, "store", "data", "analytics", "analytics.db")
OUTPUT_DIR = os.path.join(MODULE_ROOT, "analyze", "outputs")


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def connect():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Step 1 — Reporting period
# ---------------------------------------------------------------------------

def compute_periods(days):
    period_end = datetime.now(timezone.utc).date()
    period_start = period_end - timedelta(days=days)
    comparison_end = period_start
    comparison_start = comparison_end - timedelta(days=days)
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "comparison_start": comparison_start.isoformat(),
        "comparison_end": comparison_end.isoformat(),
    }


# ---------------------------------------------------------------------------
# Step 2 — Aggregate metrics
# ---------------------------------------------------------------------------

def query_post_count(conn, start, end):
    row = conn.execute(
        "SELECT COUNT(*) as n FROM posts WHERE posted_date >= ? AND posted_date < ?",
        (start, end),
    ).fetchone()
    return row["n"]


def query_post_count_all(conn):
    return conn.execute("SELECT COUNT(*) as n FROM posts").fetchone()["n"]


def query_aggregate_metrics(conn, start, end):
    row = conn.execute("""
        SELECT
            SUM(r.views) as total_views,
            AVG(r.views) as mean_views,
            SUM(r.likes) as total_likes,
            SUM(r.comments) as total_comments,
            SUM(r.shares) as total_shares,
            SUM(r.bookmarks) as total_bookmarks,
            SUM(r.new_followers) as total_new_followers
        FROM readings r
        JOIN posts p ON r.post_id = p.post_id
        WHERE p.posted_date >= ? AND p.posted_date < ?
    """, (start, end)).fetchone()
    return dict(row) if row["total_views"] is not None else None


def query_aggregate_metrics_all(conn):
    row = conn.execute("""
        SELECT
            SUM(r.views) as total_views,
            AVG(r.views) as mean_views,
            SUM(r.likes) as total_likes,
            SUM(r.comments) as total_comments,
            SUM(r.shares) as total_shares,
            SUM(r.bookmarks) as total_bookmarks,
            SUM(r.new_followers) as total_new_followers
        FROM readings r
    """).fetchone()
    return dict(row) if row["total_views"] is not None else None


def query_views_for_median(conn, start, end):
    rows = conn.execute("""
        SELECT r.views
        FROM readings r
        JOIN posts p ON r.post_id = p.post_id
        WHERE p.posted_date >= ? AND p.posted_date < ?
        ORDER BY r.views
    """, (start, end)).fetchall()
    return [r["views"] for r in rows]


def query_views_for_median_all(conn):
    rows = conn.execute("SELECT views FROM readings ORDER BY views").fetchall()
    return [r["views"] for r in rows]


def safe_rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator * 100, 2)


def safe_delta(current, previous):
    if current is None or previous is None:
        return None
    return current - previous


def safe_delta_pct(current, previous):
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def build_aggregate_section(conn, periods):
    cur = periods
    cur_start, cur_end = cur["period_start"], cur["period_end"]
    cmp_start, cmp_end = cur["comparison_start"], cur["comparison_end"]

    cur_count = query_post_count(conn, cur_start, cur_end)
    cmp_count = query_post_count(conn, cmp_start, cmp_end)
    all_count = query_post_count_all(conn)

    cur_agg = query_aggregate_metrics(conn, cur_start, cur_end)
    cmp_agg = query_aggregate_metrics(conn, cmp_start, cmp_end)
    all_agg = query_aggregate_metrics_all(conn)

    cur_views_list = query_views_for_median(conn, cur_start, cur_end)
    cmp_views_list = query_views_for_median(conn, cmp_start, cmp_end)
    all_views_list = query_views_for_median_all(conn)

    cur_median = median(cur_views_list) if cur_views_list else None
    cmp_median = median(cmp_views_list) if cmp_views_list else None
    all_median = median(all_views_list) if all_views_list else None

    def rates(agg):
        if not agg or not agg["total_views"]:
            return None, None
        eng = safe_rate(
            (agg["total_likes"] or 0) + (agg["total_comments"] or 0) + (agg["total_shares"] or 0),
            agg["total_views"],
        )
        save = safe_rate(agg["total_bookmarks"] or 0, agg["total_views"])
        return eng, save

    cur_eng, cur_save = rates(cur_agg)
    cmp_eng, cmp_save = rates(cmp_agg)
    all_eng, all_save = rates(all_agg)

    return {
        "posts_published": {
            "current": cur_count,
            "previous": cmp_count,
            "delta": safe_delta(cur_count, cmp_count),
        },
        "total_views": {
            "current": cur_agg["total_views"] if cur_agg else None,
            "previous": cmp_agg["total_views"] if cmp_agg else None,
            "delta_pct": safe_delta_pct(
                cur_agg["total_views"] if cur_agg else None,
                cmp_agg["total_views"] if cmp_agg else None,
            ),
        },
        "median_views": {
            "current": cur_median,
            "previous": cmp_median,
            "delta_pct": safe_delta_pct(cur_median, cmp_median),
        },
        "mean_engagement_rate": {
            "current": cur_eng,
            "previous": cmp_eng,
            "delta_pp": safe_delta(cur_eng, cmp_eng),
        },
        "mean_save_rate": {
            "current": cur_save,
            "previous": cmp_save,
            "delta_pp": safe_delta(cur_save, cmp_save),
        },
        "total_new_followers": {
            "current": cur_agg["total_new_followers"] if cur_agg else None,
            "previous": cmp_agg["total_new_followers"] if cmp_agg else None,
            "delta": safe_delta(
                cur_agg["total_new_followers"] if cur_agg else None,
                cmp_agg["total_new_followers"] if cmp_agg else None,
            ),
        },
        # Stubbed — Tier 3
        "mean_profile_visits": {"current": None, "previous": None, "delta": None},
        "mean_non_fyp_rate": {"current": None, "previous": None, "delta_pp": None},
        "all_time": {
            "posts_published": all_count,
            "total_views": all_agg["total_views"] if all_agg else None,
            "median_views": all_median,
            "mean_engagement_rate": all_eng,
            "mean_save_rate": all_save,
            "total_new_followers": all_agg["total_new_followers"] if all_agg else None,
        },
    }


# ---------------------------------------------------------------------------
# Step 3 — Account growth
# ---------------------------------------------------------------------------

def build_account_growth(conn, periods, aggregate):
    rows = conn.execute("""
        SELECT captured_date, followers, total_likes
        FROM account
        WHERE captured_date <= ?
        ORDER BY captured_date DESC
        LIMIT 2
    """, (periods["period_end"],)).fetchall()

    if not rows:
        return None

    current = dict(rows[0])
    previous = dict(rows[1]) if len(rows) > 1 else None

    cur_followers = current["followers"]
    prev_followers = previous["followers"] if previous else None
    cur_likes = current["total_likes"]
    prev_likes = previous["total_likes"] if previous else None

    posts_pub = aggregate["posts_published"]["current"]
    total_views = aggregate["total_views"]["current"]
    total_new = aggregate["total_new_followers"]["current"]

    return {
        "followers": {
            "current": cur_followers,
            "previous": prev_followers,
            "delta": safe_delta(cur_followers, prev_followers),
            "growth_rate_pct": safe_delta_pct(cur_followers, prev_followers),
        },
        "total_likes": {
            "current": cur_likes,
            "previous": prev_likes,
            "delta": safe_delta(cur_likes, prev_likes),
            "growth_rate_pct": safe_delta_pct(cur_likes, prev_likes),
        },
        "followers_per_post": round(safe_delta(cur_followers, prev_followers) / posts_pub, 2)
            if prev_followers is not None and posts_pub
            else None,
        "followers_per_1k_views": round(total_new / total_views * 1000, 2)
            if total_new and total_views
            else None,
        # Stubbed — requires daily checkpoints
        "growth_curve": [],
        # Stubbed — Tier 3
        "profile_visit_total": {"current": None, "previous": None, "delta": None},
    }


# ---------------------------------------------------------------------------
# Step 4 — Per-post table
# ---------------------------------------------------------------------------

def build_per_post_table(conn, periods):
    cur_start = periods["period_start"]
    cur_end = periods["period_end"]

    rows = conn.execute("""
        SELECT
            r.post_id, n.slug, p.posted_date,
            r.captured_at, r.hours_since_post, r.type,
            r.views, r.likes, r.comments, r.shares, r.bookmarks,
            r.new_followers, r.avg_watch_time_seconds,
            r.watched_full_percent, r.fyp_percent,
            n.city, n.framework, p.content_type, p.slide_count
        FROM readings r
        JOIN posts p ON r.post_id = p.post_id
        LEFT JOIN nexus_post_metadata n ON r.post_id = n.post_id
        WHERE r.captured_at >= ? AND r.captured_at < ?
        ORDER BY r.views DESC
    """, (cur_start, cur_end)).fetchall()

    # Trailing all-time median for outlier detection
    all_views = conn.execute("SELECT views FROM readings ORDER BY views").fetchall()
    all_views_list = [r["views"] for r in all_views]
    trailing_median = median(all_views_list) if all_views_list else None

    table = []
    for r in rows:
        views = r["views"]
        likes = r["likes"]
        comments = r["comments"]
        shares = r["shares"]
        bookmarks = r["bookmarks"]
        fyp = r["fyp_percent"]

        posted = r["posted_date"]
        period_end_date = datetime.fromisoformat(cur_end).date()
        posted_date = datetime.fromisoformat(posted).date()
        age_days = (period_end_date - posted_date).days
        day_of_week = posted_date.strftime("%A")

        outlier = None
        if trailing_median and trailing_median > 0:
            if views > 2 * trailing_median:
                outlier = "high"
            elif views < 0.5 * trailing_median:
                outlier = "low"

        table.append({
            "post_id": r["post_id"],
            "slug": r["slug"],
            "published": posted,
            "posted_time": None,  # Stub — Tier 2
            "posted_day_of_week": day_of_week,
            "age_days": age_days,
            "views": views,
            "engagement_rate": safe_rate(likes + comments + shares, views),
            "save_rate": safe_rate(bookmarks, views),
            "new_followers": r["new_followers"],
            "profile_visits": None,  # Stub — Tier 3
            "fyp_percent": fyp,
            "non_fyp_percent": round(100 - fyp, 2) if fyp is not None else None,
            "reading_type": r["type"],
            "is_new": posted >= cur_start,
            "outlier": outlier,
            "city": r["city"],
            "framework": r["framework"],
            "content_type": r["content_type"],
            "slide_count": r["slide_count"],
        })

    return table


# ---------------------------------------------------------------------------
# Step 5 — Anomaly detection
# ---------------------------------------------------------------------------

def detect_anomalies(conn, periods, per_post_table):
    flags = []
    cur_end = periods["period_end"]

    # 5a. Posts overdue for readings
    overdue = conn.execute("""
        SELECT p.post_id, n.slug, p.posted_date,
               CAST((julianday('now') - julianday(p.posted_date)) * 24 AS INTEGER) as hours_old
        FROM posts p
        LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
        WHERE NOT EXISTS (
            SELECT 1 FROM readings r WHERE r.post_id = p.post_id
        )
        AND julianday('now') - julianday(p.posted_date) > 2.0
    """).fetchall()
    for r in overdue:
        flags.append({
            "type": "overdue_reading",
            "severity": "warning",
            "message": f"Post {r['slug'] or r['post_id']} is {r['hours_old']}h old with no readings.",
            "post_id": r["post_id"],
        })

    # 5b. Account checkpoint overdue
    last_cp = conn.execute("SELECT MAX(captured_date) as d FROM account").fetchone()
    if last_cp["d"]:
        last_date = datetime.fromisoformat(last_cp["d"]).date()
        end_date = datetime.fromisoformat(cur_end).date()
        if (end_date - last_date).days > 7:
            flags.append({
                "type": "overdue_checkpoint",
                "severity": "warning",
                "message": f"Account checkpoint overdue. Last: {last_cp['d']} ({(end_date - last_date).days} days ago).",
                "post_id": None,
            })

    # 5c. Metric divergence
    if per_post_table:
        views_list = [p["views"] for p in per_post_table if p["views"]]
        eng_list = [p["engagement_rate"] for p in per_post_table if p["engagement_rate"] is not None]
        if views_list and eng_list:
            med_views = median(views_list)
            mean_eng = sum(eng_list) / len(eng_list)
            for p in per_post_table:
                if (p["views"] and p["views"] > med_views
                        and p["engagement_rate"] is not None
                        and mean_eng > 0
                        and p["engagement_rate"] < 0.5 * mean_eng):
                    flags.append({
                        "type": "metric_divergence",
                        "severity": "info",
                        "message": f"Post {p['slug'] or p['post_id']}: high views ({p['views']}) but low engagement ({p['engagement_rate']}%).",
                        "post_id": p["post_id"],
                    })

    # 5d. Views decrease between readings
    integrity = conn.execute("""
        SELECT r1.post_id, n.slug, r1.views as earlier_views, r2.views as later_views
        FROM readings r1
        JOIN readings r2 ON r1.post_id = r2.post_id AND r1.captured_at < r2.captured_at
        LEFT JOIN nexus_post_metadata n ON r1.post_id = n.post_id
        WHERE r2.views < r1.views
    """).fetchall()
    for r in integrity:
        flags.append({
            "type": "data_integrity",
            "severity": "critical",
            "message": f"Post {r['slug'] or r['post_id']}: views decreased ({r['earlier_views']} -> {r['later_views']}).",
            "post_id": r["post_id"],
        })

    # 5e. Cadence gaps
    gaps = conn.execute("""
        SELECT posted_date,
               CAST(julianday(posted_date) - julianday(
                   LAG(posted_date) OVER (ORDER BY posted_date)
               ) AS INTEGER) as gap_days
        FROM posts
        ORDER BY posted_date DESC
        LIMIT 10
    """).fetchall()
    for r in gaps:
        if r["gap_days"] is not None and r["gap_days"] > 7:
            flags.append({
                "type": "cadence_gap",
                "severity": "info",
                "message": f"{r['gap_days']}-day gap before post on {r['posted_date']}.",
                "post_id": None,
            })

    # Stub: audience_shift — not evaluated until traffic source data available

    return flags


# ---------------------------------------------------------------------------
# Step 6 — Executive summary
# ---------------------------------------------------------------------------

def build_executive_summary(aggregate, account_growth, anomalies, periods):
    cur_median = aggregate["median_views"]["current"]
    prev_median = aggregate["median_views"]["previous"]
    delta_pct = aggregate["median_views"]["delta_pct"]
    posts_pub = aggregate["posts_published"]["current"]
    has_critical = any(f["severity"] == "critical" for f in anomalies)

    if posts_pub is not None and posts_pub < 2 and cur_median is None:
        health = "insufficient_data"
        text = (
            f"Insufficient data for the reporting period "
            f"({periods['period_start']} to {periods['period_end']}). "
            f"{posts_pub} post(s) published with readings available."
        )
    elif delta_pct is not None and delta_pct > 10 and not has_critical:
        health = "strong"
        parts = [f"Median views up {delta_pct}% WoW"]
        if prev_median is not None:
            parts[0] += f" ({int(prev_median)} → {int(cur_median)})"
        parts.append(f"{posts_pub} post(s) published")
        if account_growth and account_growth["followers"]["delta"] is not None:
            parts.append(f"follower growth: +{account_growth['followers']['delta']}")
        text = ". ".join(parts) + "."
    elif delta_pct is not None and delta_pct < -10 or has_critical:
        health = "declining"
        parts = []
        if delta_pct is not None:
            parts.append(f"Median views {'down' if delta_pct < 0 else 'up'} {abs(delta_pct)}% WoW")
        if has_critical:
            crit_count = sum(1 for f in anomalies if f["severity"] == "critical")
            parts.append(f"{crit_count} critical flag(s)")
        parts.append(f"{posts_pub} post(s) published")
        text = ". ".join(parts) + ". Investigate in Level 2."
    else:
        health = "steady"
        parts = [f"Median views stable"]
        if delta_pct is not None:
            parts[0] += f" ({delta_pct:+.1f}% WoW)"
        parts.append(f"{posts_pub} post(s) published")
        if account_growth and account_growth["followers"]["delta"] is not None:
            parts.append(f"follower growth: +{account_growth['followers']['delta']}")
        text = ". ".join(parts) + "."

    return {
        "health_status": health,
        "summary_text": text,
    }


# ---------------------------------------------------------------------------
# Step 7 — Assemble structured output
# ---------------------------------------------------------------------------

def assemble(periods, summary, aggregate, account_growth, per_post, anomalies, missing_data):
    return {
        "report_type": "level_1_performance",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": periods,
        "executive_summary": summary,
        "aggregate_metrics": aggregate,
        "account_growth": account_growth,
        "per_post_table": per_post,
        "anomalies": anomalies,
        "missing_data": missing_data,
    }


# ---------------------------------------------------------------------------
# Step 8 — Render to Markdown
# ---------------------------------------------------------------------------

def render_markdown(report):
    lines = []
    p = report["period"]
    summary = report["executive_summary"]
    agg = report["aggregate_metrics"]
    growth = report["account_growth"]
    posts = report["per_post_table"]
    flags = report["anomalies"]

    lines.append(f"# Level 1 Performance Report")
    lines.append(f"")
    lines.append(f"**Period:** {p['period_start']} to {p['period_end']}  ")
    lines.append(f"**Comparison:** {p['comparison_start']} to {p['comparison_end']}  ")
    lines.append(f"**Generated:** {report['generated_at']}")
    lines.append("")

    # Executive summary
    status_label = summary["health_status"].upper()
    lines.append(f"## Status: {status_label}")
    lines.append("")
    lines.append(summary["summary_text"])
    lines.append("")

    # Aggregate metrics
    lines.append("## Aggregate Metrics")
    lines.append("")
    lines.append("| Metric | Current | Previous | Delta | All-Time |")
    lines.append("|---|---|---|---|---|")

    def fmt(v):
        if v is None:
            return "—"
        if isinstance(v, float):
            return f"{v:.1f}"
        return str(v)

    def fmt_delta(v, suffix=""):
        if v is None:
            return "—"
        sign = "+" if v > 0 else ""
        if isinstance(v, float):
            return f"{sign}{v:.1f}{suffix}"
        return f"{sign}{v}{suffix}"

    at = agg["all_time"]
    lines.append(f"| Posts published | {fmt(agg['posts_published']['current'])} | {fmt(agg['posts_published']['previous'])} | {fmt_delta(agg['posts_published']['delta'])} | {fmt(at['posts_published'])} |")
    lines.append(f"| Total views | {fmt(agg['total_views']['current'])} | {fmt(agg['total_views']['previous'])} | {fmt_delta(agg['total_views']['delta_pct'], '%')} | {fmt(at['total_views'])} |")
    lines.append(f"| Median views | {fmt(agg['median_views']['current'])} | {fmt(agg['median_views']['previous'])} | {fmt_delta(agg['median_views']['delta_pct'], '%')} | {fmt(at['median_views'])} |")
    lines.append(f"| Engagement rate | {fmt(agg['mean_engagement_rate']['current'])}% | {fmt(agg['mean_engagement_rate']['previous'])}% | {fmt_delta(agg['mean_engagement_rate']['delta_pp'], 'pp')} | {fmt(at['mean_engagement_rate'])}% |")
    lines.append(f"| Save rate | {fmt(agg['mean_save_rate']['current'])}% | {fmt(agg['mean_save_rate']['previous'])}% | {fmt_delta(agg['mean_save_rate']['delta_pp'], 'pp')} | {fmt(at['mean_save_rate'])}% |")
    lines.append(f"| New followers | {fmt(agg['total_new_followers']['current'])} | {fmt(agg['total_new_followers']['previous'])} | {fmt_delta(agg['total_new_followers']['delta'])} | {fmt(at['total_new_followers'])} |")
    lines.append("")

    # Account growth
    lines.append("## Account Growth")
    lines.append("")
    if growth:
        lines.append("| Metric | Current | Previous | Delta | Growth Rate |")
        lines.append("|---|---|---|---|---|")
        lines.append(f"| Followers | {fmt(growth['followers']['current'])} | {fmt(growth['followers']['previous'])} | {fmt_delta(growth['followers']['delta'])} | {fmt_delta(growth['followers']['growth_rate_pct'], '%')} |")
        lines.append(f"| Total likes | {fmt(growth['total_likes']['current'])} | {fmt(growth['total_likes']['previous'])} | {fmt_delta(growth['total_likes']['delta'])} | {fmt_delta(growth['total_likes']['growth_rate_pct'], '%')} |")
        lines.append("")
        lines.append(f"- Followers per post: {fmt(growth['followers_per_post'])}")
        lines.append(f"- Followers per 1K views: {fmt(growth['followers_per_1k_views'])}")
    else:
        lines.append("No account checkpoints available.")
    lines.append("")

    # Per-post table
    lines.append("## Per-Post Performance")
    lines.append("")
    if posts:
        lines.append("| Post | Published | Age | Views | Eng% | Save% | Followers | Type | Outlier |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for p in posts:
            slug = p["slug"] or p["post_id"][:12] + "…"
            outlier_mark = ""
            if p["outlier"] == "high":
                outlier_mark = "HIGH"
            elif p["outlier"] == "low":
                outlier_mark = "LOW"
            lines.append(
                f"| {slug} | {p['published']} | {p['age_days']}d | "
                f"{fmt(p['views'])} | {fmt(p['engagement_rate'])}% | "
                f"{fmt(p['save_rate'])}% | {fmt(p['new_followers'])} | "
                f"{p['reading_type']} | {outlier_mark} |"
            )
    else:
        lines.append("No readings captured in this period.")
    lines.append("")

    # Anomalies
    lines.append("## Anomalies & Flags")
    lines.append("")
    if flags:
        for severity in ["critical", "warning", "info"]:
            sev_flags = [f for f in flags if f["severity"] == severity]
            if sev_flags:
                lines.append(f"**{severity.upper()}:**")
                for f in sev_flags:
                    lines.append(f"- [{f['type']}] {f['message']}")
                lines.append("")
    else:
        lines.append("No anomalies detected.")
    lines.append("")

    # Missing data
    missing = report.get("missing_data")
    if missing:
        lines.append(render_missing_data_section(missing))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    days = 7
    args = sys.argv[1:]
    if "--days" in args:
        idx = args.index("--days")
        if idx + 1 < len(args):
            days = int(args[idx + 1])

    conn = connect()
    periods = compute_periods(days)

    print(f"Reporting period: {periods['period_start']} to {periods['period_end']}")
    print(f"Comparison period: {periods['comparison_start']} to {periods['comparison_end']}")

    aggregate = build_aggregate_section(conn, periods)
    account_growth = build_account_growth(conn, periods, aggregate)
    per_post = build_per_post_table(conn, periods)
    anomalies = detect_anomalies(conn, periods, per_post)
    missing_data = build_missing_data(conn)
    summary = build_executive_summary(aggregate, account_growth, anomalies, periods)
    report = assemble(periods, summary, aggregate, account_growth, per_post, anomalies, missing_data)

    # Write outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = os.path.join(OUTPUT_DIR, f"level-1-performance-{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    md_path = os.path.join(OUTPUT_DIR, f"level-1-performance-{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(report))

    print(f"Level 1 report generated: {md_path}")
    conn.close()


if __name__ == "__main__":
    main()
