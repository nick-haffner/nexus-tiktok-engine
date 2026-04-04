"""
Shared query infrastructure for Levels 2-5.

Provides:
    - Database connection
    - Master dataset loader
    - Per-post derived field computation
    - Generic dimension comparison function
    - Confidence tagging
    - Trajectory detection
    - Missing data assessment
"""

import os
import sqlite3
import sys
from datetime import datetime, timezone
from statistics import median, stdev

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
# Master dataset
# ---------------------------------------------------------------------------

MASTER_QUERY = """
SELECT
    p.post_id, p.posted_date, p.content_type, p.slide_count,
    p.description, p.hashtags, p.sound_name, p.sound_type, p.posted_time,
    n.slug, n.city, n.framework, n.slide_layout,
    r.captured_at, r.hours_since_post, r.type as reading_type,
    r.views, r.likes, r.comments, r.shares, r.bookmarks,
    r.new_followers, r.avg_watch_time_seconds,
    r.watched_full_percent, r.fyp_percent, r.profile_visits
FROM readings r
JOIN posts p ON r.post_id = p.post_id
LEFT JOIN nexus_post_metadata n ON r.post_id = n.post_id
"""


def load_master_dataset(conn):
    rows = conn.execute(MASTER_QUERY).fetchall()
    posts = [dict(r) for r in rows]

    # Sort by posted_date for gap computation
    posts.sort(key=lambda p: p["posted_date"])

    # Compute derived fields
    for i, post in enumerate(posts):
        views = post["views"] or 0
        likes = post["likes"] or 0
        comments = post["comments"] or 0
        shares = post["shares"] or 0
        bookmarks = post["bookmarks"] or 0
        new_followers = post["new_followers"]

        post["engagement_rate"] = round((likes + comments + shares) / views * 100, 2) if views else None
        post["save_rate"] = round(bookmarks / views * 100, 2) if views else None
        post["comment_rate"] = round(comments / views * 100, 2) if views else None
        post["follower_conversion"] = round(new_followers / views * 1000, 2) if views and new_followers is not None else None

        fyp = post["fyp_percent"]
        post["non_fyp_percent"] = round(100 - fyp, 2) if fyp is not None else None

        # Day of week
        try:
            d = datetime.fromisoformat(post["posted_date"]).date()
            post["posted_day_of_week"] = d.strftime("%A")
        except (ValueError, TypeError):
            post["posted_day_of_week"] = None

        # Caption length
        desc = post["description"]
        post["caption_length_words"] = len(desc.split()) if desc else None

        # Hashtag count
        ht = post["hashtags"]
        if ht and ht.strip():
            post["hashtag_count"] = len([h for h in ht.split(",") if h.strip()])
        else:
            post["hashtag_count"] = 0

        # Days since previous post
        if i == 0:
            post["days_since_previous_post"] = None
        else:
            try:
                cur_date = datetime.fromisoformat(post["posted_date"]).date()
                prev_date = datetime.fromisoformat(posts[i - 1]["posted_date"]).date()
                post["days_since_previous_post"] = (cur_date - prev_date).days
            except (ValueError, TypeError):
                post["days_since_previous_post"] = None

        # Age in days
        try:
            posted_date = datetime.fromisoformat(post["posted_date"]).date()
            post["age_days"] = (datetime.now(timezone.utc).date() - posted_date).days
        except (ValueError, TypeError):
            post["age_days"] = None

    return posts


# ---------------------------------------------------------------------------
# Dimension comparison
# ---------------------------------------------------------------------------

def confidence_label(n):
    if n >= 10:
        return "high"
    elif n >= 5:
        return "moderate"
    else:
        return "low"


def compute_trajectory(group_posts):
    """Assess whether views are improving, declining, or stable across the last 3+ posts."""
    if len(group_posts) < 3:
        return None

    sorted_posts = sorted(group_posts, key=lambda p: p["posted_date"])
    views = [p["views"] for p in sorted_posts if p["views"]]
    if len(views) < 3:
        return None

    group_mean = sum(views) / len(views)
    recent = views[-3:]
    recent_mean = sum(recent) / len(recent)

    if recent_mean > group_mean * 1.2:
        return "improving"
    elif recent_mean < group_mean * 0.8:
        return "declining"
    else:
        return "stable"


def safe_median(values):
    return median(values) if values else None


def safe_mean(values):
    return round(sum(values) / len(values), 2) if values else None


def compare_dimension(posts, dimension, buckets=None):
    """
    Group posts by a dimension value, compute aggregate metrics per group.

    Args:
        posts: list of post dicts from load_master_dataset
        dimension: field name to group by
        buckets: optional dict mapping bucket_name -> (min_val, max_val) for numeric bucketing

    Returns:
        dict with 'dimension', 'groups', 'excluded_count'
    """
    groups = {}
    excluded = 0

    for post in posts:
        val = post.get(dimension)

        if val is None:
            excluded += 1
            continue

        # Apply bucketing if provided
        if buckets:
            bucket_name = None
            for name, (lo, hi) in buckets.items():
                if lo <= val <= hi:
                    bucket_name = name
                    break
            if bucket_name is None:
                excluded += 1
                continue
            val = bucket_name

        # Handle exploded multi-value fields (comma-separated)
        if isinstance(val, str) and "," in val and dimension in ("content_topics", "content_topics"):
            values = [v.strip() for v in val.split(",") if v.strip()]
        else:
            values = [val]

        for v in values:
            key = str(v)
            if key not in groups:
                groups[key] = []
            groups[key].append(post)

    result_groups = []
    for value, group_posts in groups.items():
        views_list = [p["views"] for p in group_posts if p["views"]]
        eng_list = [p["engagement_rate"] for p in group_posts if p["engagement_rate"] is not None]
        save_list = [p["save_rate"] for p in group_posts if p["save_rate"] is not None]
        fc_list = [p["follower_conversion"] for p in group_posts if p["follower_conversion"] is not None]
        wfp_list = [p["watched_full_percent"] for p in group_posts if p["watched_full_percent"] is not None]
        dates = [p["posted_date"] for p in group_posts if p["posted_date"]]

        result_groups.append({
            "value": value,
            "post_count": len(group_posts),
            "confidence": confidence_label(len(group_posts)),
            "mean_views": safe_mean(views_list),
            "median_views": safe_median(views_list),
            "mean_engagement_rate": safe_mean(eng_list),
            "mean_save_rate": safe_mean(save_list),
            "mean_follower_conversion": safe_mean(fc_list),
            "mean_watched_full_percent": safe_mean(wfp_list),
            "mean_profile_visits": None,  # Stub — Tier 3
            "total_views": sum(views_list),
            "trajectory": compute_trajectory(group_posts),
            "last_used": max(dates) if dates else None,
            "notable": None,  # Set below
        })

    # Flag notable groups
    if result_groups:
        by_views = sorted(result_groups, key=lambda g: g["mean_views"] or 0, reverse=True)
        if len(by_views) >= 2:
            by_views[0]["notable"] = "highest mean views"
            by_views[-1]["notable"] = "lowest mean views"

        by_save = sorted(result_groups, key=lambda g: g["mean_save_rate"] or 0, reverse=True)
        if len(by_save) >= 2 and by_save[0]["notable"] is None:
            by_save[0]["notable"] = "highest save rate"

        for g in result_groups:
            if g["trajectory"] == "declining" and g["notable"] is None:
                g["notable"] = "declining trajectory"

    # Sort by mean_views descending
    result_groups.sort(key=lambda g: g["mean_views"] or 0, reverse=True)

    return {
        "dimension": dimension,
        "groups": result_groups,
        "excluded_count": excluded,
    }


# ---------------------------------------------------------------------------
# Missing data assessment
# ---------------------------------------------------------------------------

def build_missing_data(conn):
    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]

    addressable_gaps = [
        {"gap": "Competitive context", "affects": "L1, L2, Synthesis",
         "resolution": "Add competitor tracking via manual research or third-party tools"},
        {"gap": "Classification metadata", "affects": "L2, L3",
         "resolution": "Backfill existing posts or capture during generate procedure (38/45 lack framework)"},
        {"gap": "Content artifacts", "affects": "L2, L3, L5",
         "resolution": "Automate capture during generate and discover procedures (~37/45 lack copy.md)"},
        {"gap": "posted_time", "affects": "L4",
         "resolution": "Add to Phase 2 collect or discover enrichment"},
        {"gap": "Follower attribution", "affects": "L3",
         "resolution": "Capture fresh readings going forward to determine if backfill data is artifactual"},
        {"gap": "Profile visits", "affects": "L5",
         "resolution": "Expand Phase 2 collect to capture profile_visits per post"},
        {"gap": "Traffic source breakdown", "affects": "L3",
         "resolution": "Expand Phase 2 collect (only fyp_percent currently captured)"},
        {"gap": "CTA heuristic accuracy", "affects": "L5",
         "resolution": "Populate carousel_details.cta_type and cta_text during generate procedure (currently keyword-matched from description)"},
        {"gap": "sound_name / sound_type", "affects": "L2",
         "resolution": "Collect sound_name during enrichment, tag sound_type during production"},
    ]

    structural_gaps = [
        {"gap": "Creative judgment", "affects": "L2, L3, L5, Synthesis",
         "description": "Assessing hook appeal, caption authenticity, visual energy. Engine performs structured analysis and surfaces questions for human judgment."},
    ]

    stubbed_columns = [
        {"table": "posts", "column": "posted_time", "tier": 2,
         "description": "Posting time of day"},
        {"table": "posts", "column": "sound_type", "tier": 2,
         "description": "Sound classification (trending/original/licensed)"},
        {"table": "readings", "column": "profile_visits", "tier": 3,
         "description": "Profile visits per post"},
        {"table": "readings", "column": "search_percent", "tier": 3,
         "description": "Traffic source: search"},
        {"table": "readings", "column": "profile_percent", "tier": 3,
         "description": "Traffic source: profile"},
        {"table": "readings", "column": "following_percent", "tier": 3,
         "description": "Traffic source: following"},
        {"table": "readings", "column": "other_percent", "tier": 3,
         "description": "Traffic source: other"},
    ]

    nexus_fields = ["framework", "slide_layout", "city"]
    nexus_coverage = {}
    for field in nexus_fields:
        filled = conn.execute(
            f"SELECT COUNT(*) FROM nexus_post_metadata WHERE {field} IS NOT NULL AND {field} != ''"
        ).fetchone()[0]
        nexus_coverage[field] = {
            "filled": filled, "total": total,
            "pct": round(filled / total * 100) if total else 0,
        }

    account_count = conn.execute("SELECT COUNT(*) FROM account").fetchone()[0]
    readings_count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]

    return {
        "addressable_gaps": addressable_gaps,
        "structural_gaps": structural_gaps,
        "stubbed_columns": stubbed_columns,
        "nexus_metadata_coverage": nexus_coverage,
        "account_checkpoints": account_count,
        "total_readings": readings_count,
        "total_posts": total,
    }


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def fmt(v):
    if v is None:
        return "--"
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)


def fmt_pct(v):
    if v is None:
        return "--"
    return f"{v:.1f}%"


def render_dimension_table(comparison, primary_metric="mean_views"):
    """Render a dimension comparison as a Markdown table."""
    lines = []
    dim = comparison["dimension"]
    groups = comparison["groups"]
    excluded = comparison["excluded_count"]

    lines.append(f"### {dim}")
    lines.append("")

    if not groups:
        lines.append(f"No data available for this dimension ({excluded} posts excluded).")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"| Value | Posts | Mean Views | Median Views | Eng% | Save% | Follower/1K | Trajectory | Notable |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    for g in groups:
        notable = g["notable"] or ""
        lines.append(
            f"| {g['value']} | {g['post_count']} ({g['confidence']}) | "
            f"{fmt(g['mean_views'])} | {fmt(g['median_views'])} | "
            f"{fmt_pct(g['mean_engagement_rate'])} | {fmt_pct(g['mean_save_rate'])} | "
            f"{fmt(g['mean_follower_conversion'])} | {g['trajectory'] or '--'} | "
            f"{notable} |"
        )

    if excluded:
        lines.append(f"\n*{excluded} post(s) excluded (null value for this dimension).*")
    lines.append("")
    return "\n".join(lines)


def render_missing_data_section(missing):
    lines = []
    lines.append("## Data Coverage")
    lines.append("")

    nexus = missing.get("nexus_metadata_coverage", {})
    if nexus:
        lines.append("**Classification coverage:**")
        lines.append("")
        lines.append("| Field | Populated | Coverage |")
        lines.append("|---|---|---|")
        for field, info in nexus.items():
            lines.append(f"| {field} | {info['filled']}/{info['total']} | {info['pct']}% |")
        lines.append("")

    stubs = missing.get("stubbed_columns", [])
    if stubs:
        lines.append("**Stubbed columns (not yet collected):**")
        lines.append("")
        for s in stubs:
            lines.append(f"- `{s['table']}.{s['column']}` (Tier {s['tier']}) -- {s['description']}")
        lines.append("")

    addr = missing.get("addressable_gaps", [])
    if addr:
        lines.append("**Addressable gaps:**")
        lines.append("")
        for g in addr:
            lines.append(f"- **{g['gap']}** ({g['affects']}): {g['resolution']}")
        lines.append("")

    struct = missing.get("structural_gaps", [])
    if struct:
        lines.append("**Structural gaps (accepted by procedure):**")
        lines.append("")
        for g in struct:
            lines.append(f"- **{g['gap']}** ({g['affects']}): {g['description']}")
        lines.append("")

    lines.append(f"Account checkpoints: {missing.get('account_checkpoints', 0)}")
    lines.append("")
    return "\n".join(lines)
