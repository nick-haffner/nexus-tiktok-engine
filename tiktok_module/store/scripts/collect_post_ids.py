"""
Unit process: collect all post IDs and dates from TikTok.

Uses TikTok's /api/post/item_list/ endpoint, called from browser context
on any tiktok.com page. Paginates automatically to collect all posts.

This script is designed to be:
    - Run independently for testing
    - Called by the discover procedure

Usage:
    python store/scripts/collect_post_ids.py                    # print JS to execute
    python store/scripts/collect_post_ids.py --parse '<json>'   # parse collected data

Input format (from browser JS execution):
    {"posts": [{"post_id": "762139...", "createTime": 1775092930, ...}, ...], "count": N}

Output: CSV to stdout (post_id,posted_date,sound_name) suitable for piping to discover.py input.

Exit codes:
    0 -- Success
    1 -- Fatal error
"""

import csv
import json
import re
import sys
import os
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")

# JavaScript for collecting all post IDs via the item_list API.
# Must be executed in a browser context on any tiktok.com page.
# The browser's session cookies authenticate the request.
#
# Step 1: Gets secUid from /tiktokstudio/api/web/user
# Step 2: Paginates /api/post/item_list/ to collect all posts
# Step 3: Deduplicates (pinned posts appear twice) and returns JSON
COLLECT_IDS_JS = """
(async () => {
    // Step 1 — get secUid from TikTok Studio user API
    const userResp = await fetch("/tiktokstudio/api/web/user?needIsVerified=true", {
        credentials: "include"
    });
    const userData = await userResp.json();
    const secUid = userData?.userBaseInfo?.UserProfile?.UserBase?.SecUid;

    if (!secUid) {
        return JSON.stringify({
            error: "Could not get secUid from user API. Are you logged into TikTok Studio?"
        });
    }

    // Step 2 — paginate /api/post/item_list/
    const allPosts = [];
    let cursor = "0";
    let hasMore = true;
    let pages = 0;

    while (hasMore && pages < 20) {
        const params = new URLSearchParams({
            aid: "1988",
            count: "30",
            cursor: cursor,
            secUid: secUid,
            needPinnedItemIds: "true"
        });

        const resp = await fetch(
            "/api/post/item_list/?" + params.toString(),
            { credentials: "include" }
        );
        const data = await resp.json();

        if ((data.statusCode || data.status_code) !== 0) {
            return JSON.stringify({
                error: "item_list API error",
                status_code: data.statusCode || data.status_code,
                msg: data.statusMsg || data.status_msg
            });
        }

        const items = data.itemList || [];
        for (const item of items) {
            allPosts.push({
                post_id: item.id,
                createTime: item.createTime,
                desc: (item.desc || "").substring(0, 100),
                type: item.imagePost ? "carousel" : "video",
                sound_name: item.music?.title || null,
                slide_count: item.imagePost ? (item.imagePost.images || []).length : 1,
                aweme_type: item.imagePost ? 150 : 0
            });
        }

        hasMore = data.hasMore;
        cursor = data.cursor || "0";
        pages++;
    }

    // Step 3 — deduplicate by post_id (pinned posts appear in both positions)
    const seen = new Set();
    const unique = allPosts.filter(p => {
        if (seen.has(p.post_id)) return false;
        seen.add(p.post_id);
        return true;
    });

    return JSON.stringify({ posts: unique, count: unique.length, pages: pages });
})();
"""


def build_collect_ids_js():
    """Return the JavaScript for collecting post IDs from TikTok."""
    return COLLECT_IDS_JS


def parse_hashtags(description):
    """Extract hashtags from a description string. Returns comma-separated, # stripped."""
    if not description:
        return ""
    tags = re.findall(r"#(\w+)", description)
    return ",".join(tags) if tags else ""


def parse_collected_data(raw_json):
    """
    Parse collected post data into a list of post dicts with full metadata.

    Accepts:
    1. Object with posts array: {"posts": [...], "count": N}
    2. Array of objects: [{"post_id": "...", "createTime": ...}, ...]
    3. Legacy format: {"post_ids": ["..."], "dates": {"id": "date", ...}}
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        return None, f"Failed to parse JSON: {e}"

    if isinstance(data, dict) and "error" in data:
        return None, data["error"]

    posts = []

    # Format 1: object with posts array (primary — from COLLECT_IDS_JS)
    if isinstance(data, dict) and "posts" in data:
        for item in data["posts"]:
            post_id = str(item.get("post_id") or item.get("id", ""))
            create_time = item.get("createTime")
            posted_date = ""
            if create_time:
                posted_date = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d")
            desc = item.get("desc") or ""
            posts.append({
                "post_id": post_id,
                "posted_date": posted_date,
                "description": desc,
                "hashtags": parse_hashtags(desc),
                "sound_name": item.get("sound_name") or "",
                "content_type": item.get("type") or "",
                "slide_count": item.get("slide_count"),
                "aweme_type": item.get("aweme_type"),
            })
        return posts, None

    # Format 2: array of objects
    if isinstance(data, list):
        for item in data:
            post_id = str(item.get("post_id") or item.get("id", ""))
            create_time = item.get("createTime")
            posted_date = item.get("posted_date", "")
            if not posted_date and create_time:
                posted_date = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d")
            desc = item.get("desc") or item.get("description") or ""
            posts.append({
                "post_id": post_id,
                "posted_date": posted_date,
                "description": desc,
                "hashtags": parse_hashtags(desc),
                "sound_name": item.get("sound_name") or "",
                "content_type": item.get("type") or item.get("content_type") or "",
                "slide_count": item.get("slide_count"),
                "aweme_type": item.get("aweme_type"),
            })
        return posts, None

    # Format 3: legacy {post_ids: [...], dates: {...}}
    if isinstance(data, dict) and "post_ids" in data:
        dates = data.get("dates", {})
        for pid in data["post_ids"]:
            pid = str(pid)
            posts.append({"post_id": pid, "posted_date": dates.get(pid, ""), "sound_name": ""})
        return posts, None

    return None, "Unrecognized format. Expected object with 'posts' key, array, or object with 'post_ids' key."


def validate_posts(posts):
    """Validate parsed posts. Return warnings list."""
    warnings = []
    for p in posts:
        if not p["post_id"] or not p["post_id"].isdigit():
            warnings.append(f"Invalid post_id: '{p['post_id']}'")
        if not p["posted_date"]:
            warnings.append(f"Missing posted_date for {p['post_id']}")
    return warnings


def output_csv(posts, stream=None):
    """Write posts as CSV (no header) to a stream or stdout."""
    out = stream or sys.stdout
    writer = csv.writer(out)
    for p in posts:
        writer.writerow([p["post_id"], p["posted_date"], p.get("sound_name", "")])


def output_json(posts, path):
    """Write posts as JSON file with full metadata."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    print(f"Written {len(posts)} posts to {path}", file=sys.stderr)


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    # Parse mode — from file, argument, or stdin
    if "--parse-file" in args:
        idx = args.index("--parse-file")
        if idx + 1 < len(args):
            with open(args[idx + 1], "r", encoding="utf-8") as f:
                raw = f.read()
        else:
            print("ERROR: --parse-file requires a file path", file=sys.stderr)
            sys.exit(1)
    elif "--parse" in args:
        idx = args.index("--parse")
        if idx + 1 < len(args):
            raw = args[idx + 1]
        else:
            raw = sys.stdin.read()
    else:
        raw = None

    if raw is not None:
        posts, error = parse_collected_data(raw)
        if error:
            print(f"ERROR: {error}", file=sys.stderr)
            sys.exit(1)

        warnings = validate_posts(posts)
        if warnings:
            for w in warnings:
                print(f"WARNING: {w}", file=sys.stderr)

        # Filter out invalid entries
        valid = [p for p in posts if p["post_id"] and p["post_id"].isdigit()]

        print(f"Parsed {len(valid)} valid post(s) ({len(posts) - len(valid)} invalid)", file=sys.stderr)

        # Output as CSV to stdout
        output_csv(valid)

        # If --output flag, write CSV to file
        if "--output" in args:
            out_idx = args.index("--output")
            if out_idx + 1 < len(args):
                out_path = args[out_idx + 1]
                with open(out_path, "w", newline="", encoding="utf-8") as f:
                    output_csv(valid, f)
                print(f"CSV written to {out_path}", file=sys.stderr)

        # If --output-json flag, write JSON with full metadata
        if "--output-json" in args:
            out_idx = args.index("--output-json")
            if out_idx + 1 < len(args):
                output_json(valid, args[out_idx + 1])

        sys.exit(0)

    # Default: print the JS and instructions
    print("--- Post ID Collection ---", file=sys.stderr)
    print("", file=sys.stderr)
    print("Execute the following JavaScript on any tiktok.com page", file=sys.stderr)
    print("(TikTok Studio or public profile — session cookies required):", file=sys.stderr)
    print("", file=sys.stderr)
    print(COLLECT_IDS_JS, file=sys.stderr)
    print("", file=sys.stderr)
    print("The JS automatically:", file=sys.stderr)
    print("  1. Gets your secUid from the TikTok Studio user API", file=sys.stderr)
    print("  2. Paginates /api/post/item_list/ to collect all posts", file=sys.stderr)
    print("  3. Returns JSON with post IDs, dates, descriptions, and types", file=sys.stderr)
    print("", file=sys.stderr)
    print("Then parse:", file=sys.stderr)
    print("  python collect_post_ids.py --parse '<json_result>' --output input.csv", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
