"""
Unit process: collect metrics for a single TikTok post.

Two collection methods:
    1. API fetch via /aweme/v2/data/insight/ (preferred — no page navigation)
    2. Direct URL navigation to tiktokstudio/analytics/{post_id}/overview (fallback)

This script is designed to be:
    - Run independently for testing: python store/scripts/collect_post.py <post_id> [--method api|page]
    - Imported by the batch collection orchestrator

Requires: Chrome with active TikTok Studio session (Claude-in-Chrome or manual).

Usage:
    python store/scripts/collect_post.py <post_id>
    python store/scripts/collect_post.py <post_id> --method page
    python store/scripts/collect_post.py <post_id> --reading-type snapshot
    python store/scripts/collect_post.py <post_id> --reading-type velocity

Output: JSON to stdout with collected metrics. Errors to stderr.

Exit codes:
    0 — Success (metrics printed as JSON to stdout)
    1 — Fatal error
"""

import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")


# ---------------------------------------------------------------------------
# API collection method
# ---------------------------------------------------------------------------

# JavaScript template for fetching metrics via TikTok's internal API.
# This must be executed in a browser context on any TikTok Studio page.
# The browser's session cookies authenticate the request.

API_JS_TEMPLATE = """
(async () => {{
    const postId = "{post_id}";
    const insightTypes = [
        "video_info",
        "realtime_new_followers",
        "video_per_duration_realtime",
        "video_finish_rate_realtime",
        "video_traffic_source_percent_realtime"
    ];

    const typeRequests = insightTypes.map(t => ({{
        insigh_type: t,
        aweme_id: postId
    }}));

    const params = new URLSearchParams({{
        locale: "en",
        aid: "1988",
        tz_offset: String(new Date().getTimezoneOffset() * -60),
        type_requests: JSON.stringify(typeRequests)
    }});

    const resp = await fetch(
        "https://www.tiktok.com/aweme/v2/data/insight/?" + params.toString(),
        {{ credentials: "include" }}
    );
    const data = await resp.json();

    // API returns insight types as flat top-level keys (not nested under data.type_responses)
    if (!data.video_info) {{
        return JSON.stringify({{ error: "No video_info in API response", raw_status: data.status_code }});
    }}

    const result = {{
        post_id: postId,
        method: "api",
        views: null,
        likes: null,
        comments: null,
        shares: null,
        bookmarks: null,
        new_followers: null,
        avg_watch_time_seconds: null,
        watched_full_percent: null,
        fyp_percent: null,
        profile_visits: null,
        search_percent: null,
        profile_percent: null,
        following_percent: null,
        other_percent: null,
        sound_name: null,
        duration_seconds: null,
        create_time: null,
        description: null
    }};

    // video_info — core 5 metrics + enrichment data (top-level key)
    if (data.video_info.statistics) {{
        const stats = data.video_info.statistics;
        result.views = stats.play_count || 0;
        result.likes = stats.digg_count || 0;
        result.comments = stats.comment_count || 0;
        result.shares = stats.share_count || 0;
        result.bookmarks = stats.collect_count || 0;
    }}

    // enrichment: description (full caption text)
    if (data.video_info.desc) {{
        result.description = data.video_info.desc;
    }}

    // enrichment: sound name — not available from this endpoint (music object is empty).
    // Sound data must be sourced from /api/post/item_list/ (collect_post_ids).

    // enrichment: video duration (API returns milliseconds, convert to seconds)
    if (data.video_info.video && data.video_info.video.duration) {{
        result.duration_seconds = Math.round(data.video_info.video.duration / 1000);
    }}

    // enrichment: create time (unix timestamp — can derive posted_time)
    if (data.video_info.create_time) {{
        result.create_time = data.video_info.create_time;
    }}

    // new followers — not returned by this endpoint; leave null

    // avg watch time (top-level key)
    if (data.video_per_duration_realtime && data.video_per_duration_realtime.value) {{
        result.avg_watch_time_seconds = Math.round((data.video_per_duration_realtime.value.value || 0) * 100) / 100;
    }}

    // watched full percent (top-level key)
    if (data.video_finish_rate_realtime && data.video_finish_rate_realtime.value) {{
        result.watched_full_percent = Math.round((data.video_finish_rate_realtime.value.value || 0) * 10000) / 100;
    }}

    // traffic sources (top-level key)
    if (data.video_traffic_source_percent_realtime && data.video_traffic_source_percent_realtime.value) {{
        const sources = data.video_traffic_source_percent_realtime.value.value;
        if (Array.isArray(sources)) {{
            for (const src of sources) {{
                const pct = Math.round((src.value || 0) * 10000) / 100;
                const key = (src.key || "").toLowerCase();
                if (key === "for you") result.fyp_percent = pct;
                else if (key === "search") result.search_percent = pct;
                else if (key === "personal profile") result.profile_percent = pct;
                else if (key === "follow") result.following_percent = pct;
                else result.other_percent = (result.other_percent || 0) + pct;
            }}
        }}
    }}

    return JSON.stringify(result);
}})();
"""


def build_api_js(post_id):
    """Return the JavaScript string for collecting one post's metrics via API."""
    return API_JS_TEMPLATE.format(post_id=post_id)


def parse_api_result(js_result_str):
    """Parse the JSON string returned by the API JS execution."""
    try:
        result = json.loads(js_result_str)
        if "error" in result:
            return None, result["error"]
        return result, None
    except (json.JSONDecodeError, TypeError) as e:
        return None, f"Failed to parse API result: {e}"


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------

VELOCITY_FIELDS = ["views", "likes", "comments", "shares", "bookmarks"]

SNAPSHOT_FIELDS = VELOCITY_FIELDS + [
    "new_followers", "avg_watch_time_seconds", "watched_full_percent",
    "fyp_percent", "profile_visits", "search_percent", "profile_percent",
    "following_percent", "other_percent",
]

# Enrichment fields — permanent post data extracted alongside metrics
ENRICHMENT_FIELDS = ["sound_name", "duration_seconds", "create_time", "description"]


def format_result(raw_result, reading_type="reading"):
    """
    Format a raw collection result into the standard output structure.

    All metrics are captured on every reading regardless of type.
    The reading_type field is retained for triage window tracking
    but no longer gates which metrics are collected.

    Enrichment fields (sound_name, duration_seconds, create_time, description)
    are always included.
    """
    formatted = {
        "post_id": raw_result["post_id"],
        "method": raw_result.get("method", "unknown"),
        "reading_type": reading_type,
    }

    for field in SNAPSHOT_FIELDS:
        formatted[field] = raw_result.get(field)

    # Always include enrichment fields
    for field in ENRICHMENT_FIELDS:
        formatted[field] = raw_result.get(field)

    # Derive posted_time from create_time if available
    if formatted.get("create_time"):
        from datetime import datetime, timezone
        try:
            dt = datetime.fromtimestamp(int(formatted["create_time"]), tz=timezone.utc)
            formatted["posted_time"] = dt.strftime("%H:%M+00:00")
        except (ValueError, TypeError, OSError):
            formatted["posted_time"] = None
    else:
        formatted["posted_time"] = None

    return formatted


def parse_hashtags(description):
    """Extract hashtags from a description string. Returns comma-separated, # stripped."""
    if not description:
        return None
    import re
    tags = re.findall(r"#(\w+)", description)
    return ",".join(tags) if tags else None


def extract_enrichment(formatted_result):
    """
    Extract permanent data fields from a collect_post result.

    These fields can be written to the posts/video_details tables
    by discover's enrich_from_api function. The collect_post API call
    returns both transient metrics and permanent metadata — this function
    separates the permanent fields for consumption by discover.

    Returns a dict suitable for passing to discover.enrich_from_api().
    """
    description = formatted_result.get("description")
    enrichment = {
        "sound_name": formatted_result.get("sound_name"),
        "duration_seconds": formatted_result.get("duration_seconds"),
        "posted_time": formatted_result.get("posted_time"),
        "description": description,
        "hashtags": parse_hashtags(description),
    }
    return {k: v for k, v in enrichment.items() if v is not None}


def validate_result(result):
    """Check that required fields are present and non-null."""
    errors = []
    if result.get("views") is None:
        errors.append("views is null")
    if result.get("likes") is None:
        errors.append("likes is null")
    if result.get("comments") is None:
        errors.append("comments is null")
    if result.get("shares") is None:
        errors.append("shares is null")
    if result.get("bookmarks") is None:
        errors.append("bookmarks is null")

    # All readings now capture all metrics
    if result.get("fyp_percent") is None:
        errors.append("fyp_percent is null")

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    post_id = args[0]
    method = "api"
    reading_type = "reading"

    if "--method" in args:
        idx = args.index("--method")
        if idx + 1 < len(args):
            method = args[idx + 1]

    if "--reading-type" in args:
        idx = args.index("--reading-type")
        if idx + 1 < len(args):
            reading_type = args[idx + 1]

    if method == "api":
        js = build_api_js(post_id)
        print("--- API JavaScript for post collection ---", file=sys.stderr)
        print(f"Post ID: {post_id}", file=sys.stderr)
        print(f"Reading type: {reading_type}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Execute the following JavaScript on any TikTok Studio page:", file=sys.stderr)
        print("", file=sys.stderr)
        print(js, file=sys.stderr)
        print("", file=sys.stderr)
        print("Paste the JSON result as the first argument to --parse:", file=sys.stderr)
        print(f"  python collect_post.py {post_id} --parse '<json_result>'", file=sys.stderr)

    elif method == "page":
        url = f"https://www.tiktok.com/tiktokstudio/analytics/{post_id}/overview"
        print(f"Navigate to: {url}", file=sys.stderr)
        print(f"Read all metrics from the page. Reading type: {reading_type}", file=sys.stderr)

    # Parse mode: takes a JSON result string and formats + validates it
    if "--parse" in args:
        idx = args.index("--parse")
        if idx + 1 < len(args):
            raw_json = args[idx + 1]
            result, error = parse_api_result(raw_json)
            if error:
                print(f"ERROR: {error}", file=sys.stderr)
                sys.exit(1)

            formatted = format_result(result, reading_type)
            errors = validate_result(formatted)
            if errors:
                print(f"VALIDATION WARNINGS: {', '.join(errors)}", file=sys.stderr)

            print(json.dumps(formatted, indent=2))
            sys.exit(0)


if __name__ == "__main__":
    main()
