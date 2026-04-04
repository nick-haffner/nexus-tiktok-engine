"""
Discover and register TikTok posts, enrich with API metadata.

Idempotent: safe to run repeatedly. New posts are registered. Existing posts
have null fields updated. Non-null fields are never overwritten.

Scope: registration + API enrichment only. Content download (capture content)
and derived classification (derive) are separate procedures.

Usage:
    python store/scripts/discover.py --check                    # print cutoff date
    python store/scripts/discover.py <input_csv>                # register + enrich
    python store/scripts/discover.py <input_csv> --enrich       # also run API enrichment

Input CSV format (two or three columns, no header):
    post_id,posted_date[,sound_name]
    7621390157509365023,2026-03-25,original sound - nexusconcierge

Exit codes:
    0 -- Success
    1 -- Fatal error
    2 -- Partial completion (some posts failed enrichment)
"""

import csv
import json
import math
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
DB_PATH = os.path.join(MODULE_ROOT, "store", "data", "analytics", "analytics.db")
POSTS_DIR = os.path.join(MODULE_ROOT, "store", "data", "posts")
LAST_RUN_PATH = os.path.join(MODULE_ROOT, "store", "procedures", "discover-posts", "last-run.txt")

BATCH_SIZE = 5


def connect():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def read_last_run():
    if not os.path.exists(LAST_RUN_PATH):
        return None
    with open(LAST_RUN_PATH, "r") as f:
        return f.read().strip()


def write_last_run():
    os.makedirs(os.path.dirname(LAST_RUN_PATH), exist_ok=True)
    with open(LAST_RUN_PATH, "w") as f:
        f.write(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"))


def check_mode():
    last_run = read_last_run()
    if last_run:
        print(f"Last discovery run: {last_run}")
        print(f"Only include posts published after {last_run}.")
    else:
        print("No previous discovery run. Include all posts from TikTok Studio.")
    sys.exit(0)


def parse_input(path):
    """
    Parse input file — accepts JSON (full metadata) or CSV (legacy, minimal).

    JSON format: array of objects with post_id, posted_date, description, hashtags, etc.
    CSV format: two or three columns (post_id, posted_date[, sound_name]), no header.
    """
    if not os.path.exists(path):
        print(f"ERROR: Input file not found: {path}", file=sys.stderr)
        sys.exit(1)

    # Try JSON first
    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            print(f"Loaded {len(data)} posts from JSON input.", file=sys.stderr)
            return data
        else:
            print(f"ERROR: JSON input must be an array of post objects.", file=sys.stderr)
            sys.exit(1)

    # Fall back to CSV
    posts = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                post = {
                    "post_id": row[0].strip(),
                    "posted_date": row[1].strip(),
                }
                if len(row) >= 3 and row[2].strip():
                    post["sound_name"] = row[2].strip()
                posts.append(post)
    return posts


# ---------------------------------------------------------------------------
# Directory and metadata extraction
# ---------------------------------------------------------------------------

def find_matching_directory(posted_date):
    for base in [os.path.join("store", "data", "posts")]:
        base_path = os.path.join(MODULE_ROOT, base)
        if not os.path.isdir(base_path):
            continue
        for entry in os.listdir(base_path):
            entry_path = os.path.join(base_path, entry)
            if not os.path.isdir(entry_path):
                continue
            if posted_date in entry:
                return entry_path, entry
    return None, None


def extract_metadata(dir_path, dir_name):
    metadata = {
        "city": None,
        "framework": None,
        "slide_layout": None,
        "content_type": None,
        "slide_count": None,
        "sound_name": None,
    }

    city_match = re.match(r"^([A-Za-z\-\s]+?)(?:_\d|$)", dir_name)
    if city_match:
        metadata["city"] = city_match.group(1).replace("-", " ").strip()

    readme_path = os.path.join(dir_path, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()

        for line in readme.split("\n"):
            line_lower = line.lower().strip()
            if "framework:" in line_lower:
                val = line.split(":", 1)[1].strip().strip("*").strip()
                if val:
                    metadata["framework"] = val.lower().replace(" ", "_").replace("vs.", "vs").replace("vs ", "vs_")
            elif "format:" in line_lower or "slide layout:" in line_lower:
                val = line.split(":", 1)[1].strip().strip("*").strip()
                if val:
                    layout_match = re.match(r"^([\w\-]+)", val)
                    if layout_match:
                        metadata["slide_layout"] = layout_match.group(1).lower().replace("-", "_")
                metadata["content_type"] = "carousel"
            elif "slides:" in line_lower:
                val = line.split(":", 1)[1].strip()
                try:
                    metadata["slide_count"] = int(val)
                except ValueError:
                    pass

    copy_path = os.path.join(dir_path, "copy.md")
    if os.path.exists(copy_path):
        with open(copy_path, "r", encoding="utf-8") as f:
            copy = f.read()

        slides = re.findall(r"^## Slide \d+", copy, re.MULTILINE)
        if slides and metadata["slide_count"] is None:
            metadata["slide_count"] = len(slides)

    if metadata["slide_count"] is None:
        final_path = os.path.join(dir_path, "slides")
        if os.path.isdir(final_path):
            slide_files = [f for f in os.listdir(final_path) if f.lower().startswith("slide")]
            if slide_files:
                metadata["slide_count"] = len(slide_files)

    return metadata


# ---------------------------------------------------------------------------
# Enrichment from API
# ---------------------------------------------------------------------------

def enrich_from_api(post_id, api_data, conn):
    """
    Update permanent post fields from collect_post API enrichment data.
    Only updates fields that are currently NULL in the DB.
    Returns count of fields actually updated.
    """
    updated = 0

    cur_posts = conn.execute(
        "SELECT sound_name, posted_time, description, hashtags FROM posts WHERE post_id = ?",
        (post_id,),
    ).fetchone()
    if not cur_posts:
        return 0

    cur_posts = dict(cur_posts)

    updates = []
    params = []
    # Description: overwrite if current is NULL or truncated (shorter than incoming)
    incoming_desc = api_data.get("description")
    if incoming_desc:
        cur_desc = cur_posts["description"]
        if cur_desc is None or (len(incoming_desc) > len(cur_desc)):
            updates.append("description = ?")
            params.append(incoming_desc)
            updated += 1
    # Hashtags: overwrite if NULL or if incoming has more (truncated desc = truncated hashtags)
    incoming_hashtags = api_data.get("hashtags")
    if incoming_hashtags:
        cur_hashtags = cur_posts["hashtags"]
        if cur_hashtags is None or (len(incoming_hashtags) > len(cur_hashtags)):
            updates.append("hashtags = ?")
            params.append(incoming_hashtags)
            updated += 1
    if api_data.get("sound_name") and cur_posts["sound_name"] is None:
        updates.append("sound_name = ?")
        params.append(api_data["sound_name"])
        updated += 1
    if api_data.get("posted_time") and cur_posts["posted_time"] is None:
        updates.append("posted_time = ?")
        params.append(api_data["posted_time"])
        updated += 1

    if updates:
        params.append(post_id)
        conn.execute(f"UPDATE posts SET {', '.join(updates)} WHERE post_id = ?", params)

    # Regenerate slug if it's a fallback and description is now available
    if api_data.get("description"):
        cur_meta = conn.execute(
            "SELECT slug FROM nexus_post_metadata WHERE post_id = ?", (post_id,)
        ).fetchone()
        if cur_meta and is_fallback_slug(cur_meta["slug"]):
            posted_date = conn.execute(
                "SELECT posted_date FROM posts WHERE post_id = ?", (post_id,)
            ).fetchone()["posted_date"]
            new_slug = derive_slug(posted_date, api_data["description"], post_id)
            if new_slug and new_slug != cur_meta["slug"]:
                conflict = conn.execute(
                    "SELECT post_id FROM nexus_post_metadata WHERE slug = ? AND post_id != ?",
                    (new_slug, post_id),
                ).fetchone()
                if not conflict:
                    new_path = f"store/data/posts/{new_slug}"
                    conn.execute(
                        "UPDATE nexus_post_metadata SET slug = ? WHERE post_id = ?",
                        (new_slug, post_id),
                    )
                    conn.execute(
                        "UPDATE posts SET content_path = ? WHERE post_id = ?",
                        (new_path, post_id),
                    )
                    ensure_post_directory(new_slug)
                    updated += 1

    # Video details: duration_seconds
    if api_data.get("duration_seconds"):
        vid = conn.execute("SELECT duration_seconds FROM video_details WHERE post_id = ?", (post_id,)).fetchone()
        if vid and vid["duration_seconds"] is None:
            conn.execute("UPDATE video_details SET duration_seconds = ? WHERE post_id = ?",
                         (api_data["duration_seconds"], post_id))
            updated += 1

    return updated


# ---------------------------------------------------------------------------
# Registration (idempotent)
# ---------------------------------------------------------------------------

def derive_slug(posted_date, description=None, post_id=None):
    """
    Generate a standardized slug: YYYY-MM-DD-descriptor.

    Descriptor priority:
    1. First meaningful phrase from description (2-5 words, lowercased, hyphenated)
    2. Last 6 digits of post_id as fallback

    Fallback slugs (ending in numeric-only descriptor) can be regenerated
    on a later run when description becomes available.
    """
    descriptor = None

    if description and description.strip():
        # Extract first sentence or clause, clean to a short descriptor
        text = description.strip()
        # Take first ~60 chars, split on sentence boundaries
        first_chunk = text[:80].split(".")[0].split("!")[0].split("?")[0].split("\n")[0]
        # Remove emoji and special chars, keep letters/numbers/spaces
        cleaned = re.sub(r"[^\w\s]", "", first_chunk).strip()
        # Take first 3-5 meaningful words (skip very short words)
        words = [w.lower() for w in cleaned.split() if len(w) > 1][:5]
        if words:
            descriptor = "-".join(words)
            # Cap length
            if len(descriptor) > 40:
                descriptor = descriptor[:40].rsplit("-", 1)[0]

    if not descriptor and post_id:
        descriptor = post_id[-6:]

    if not descriptor:
        return None

    return f"{posted_date}-{descriptor}"


def is_fallback_slug(slug):
    """Check if a slug uses the numeric fallback format (ends in 6 digits)."""
    if not slug:
        return True
    parts = slug.split("-")
    # Date is first 3 parts (YYYY-MM-DD), descriptor is the rest
    if len(parts) <= 3:
        return True
    descriptor = "-".join(parts[3:])
    return descriptor.isdigit()


def ensure_post_directory(slug):
    """Create the post directory and slides subdirectory if they don't exist."""
    if not slug:
        return None
    post_dir = os.path.join(POSTS_DIR, slug)
    slides_dir = os.path.join(post_dir, "slides")
    os.makedirs(slides_dir, exist_ok=True)
    return post_dir


def register_post(post_id, posted_date, metadata, conn):
    """
    Insert a new post or update null fields on an existing post.
    Idempotent: safe to call multiple times for the same post_id.

    Creates the post directory on registration.
    If a fallback slug exists and description is now available, regenerates the slug.
    """
    description = metadata.get("description")
    slug = derive_slug(posted_date, description, post_id)
    # Disambiguate if slug already taken by a different post
    if slug and conn.execute("SELECT 1 FROM nexus_post_metadata WHERE slug = ?", (slug,)).fetchone():
        slug = f"{slug}-{post_id[-4:]}"
    content_path = f"store/data/posts/{slug}" if slug else None

    existing = conn.execute("SELECT post_id FROM posts WHERE post_id = ?", (post_id,)).fetchone()

    if existing is None:
        # New post — INSERT
        conn.execute(
            """INSERT INTO posts (post_id, posted_date, description, hashtags,
                                  content_type, aweme_type, sound_name, slide_count, content_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                post_id, posted_date,
                metadata.get("description") or None,
                metadata.get("hashtags") or None,
                metadata.get("content_type"),
                metadata.get("aweme_type"),
                metadata.get("sound_name"),
                metadata.get("slide_count"),
                content_path,
            ),
        )

        conn.execute(
            """INSERT INTO nexus_post_metadata (post_id, slug, city, framework, slide_layout)
               VALUES (?, ?, ?, ?, ?)""",
            (
                post_id, slug, metadata["city"],
                metadata["framework"], metadata["slide_layout"],
            ),
        )

        ct = metadata.get("content_type")
        if ct == "carousel":
            conn.execute("INSERT INTO carousel_details (post_id) VALUES (?)", (post_id,))
        elif ct == "video":
            conn.execute("INSERT INTO video_details (post_id, duration_seconds) VALUES (?, ?)",
                         (post_id, None))

        # Create post directory
        if slug:
            ensure_post_directory(slug)

        return "registered"

    else:
        # Existing post — UPDATE null fields only
        cur_posts = dict(conn.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,)).fetchone())
        cur_meta = dict(conn.execute("SELECT * FROM nexus_post_metadata WHERE post_id = ?", (post_id,)).fetchone())

        actually_updated = False

        # Check if slug should be regenerated (fallback → description-based)
        current_slug = cur_meta.get("slug")
        if is_fallback_slug(current_slug) and description:
            new_slug = derive_slug(posted_date, description, post_id)
            if new_slug and new_slug != current_slug:
                # Check the new slug isn't already taken
                conflict = conn.execute(
                    "SELECT post_id FROM nexus_post_metadata WHERE slug = ? AND post_id != ?",
                    (new_slug, post_id),
                ).fetchone()
                if not conflict:
                    slug = new_slug
                    content_path = f"store/data/posts/{slug}"
                    conn.execute(
                        "UPDATE nexus_post_metadata SET slug = ? WHERE post_id = ?",
                        (slug, post_id),
                    )
                    conn.execute(
                        "UPDATE posts SET content_path = ? WHERE post_id = ?",
                        (content_path, post_id),
                    )
                    actually_updated = True
        else:
            slug = current_slug

        updates_posts = []
        params_posts = []
        for col, val in [
            ("description", metadata.get("description")),
            ("hashtags", metadata.get("hashtags")),
            ("content_type", metadata.get("content_type")),
            ("aweme_type", metadata.get("aweme_type")),
            ("sound_name", metadata.get("sound_name")),
            ("slide_count", metadata.get("slide_count")),
            ("content_path", content_path),
        ]:
            if val is not None and cur_posts.get(col) is None:
                updates_posts.append(f"{col} = ?")
                params_posts.append(val)
                actually_updated = True

        if updates_posts:
            params_posts.append(post_id)
            conn.execute(
                f"UPDATE posts SET {', '.join(updates_posts)} WHERE post_id = ?",
                params_posts,
            )

        updates_meta = []
        params_meta = []
        for col, val in [
            ("city", metadata.get("city")),
            ("framework", metadata.get("framework")),
            ("slide_layout", metadata.get("slide_layout")),
        ]:
            if val is not None and cur_meta.get(col) is None:
                updates_meta.append(f"{col} = ?")
                params_meta.append(val)
                actually_updated = True

        if updates_meta:
            params_meta.append(post_id)
            conn.execute(
                f"UPDATE nexus_post_metadata SET {', '.join(updates_meta)} WHERE post_id = ?",
                params_meta,
            )

        # Ensure subtype table row exists
        ct = metadata.get("content_type")
        if ct == "carousel":
            conn.execute("INSERT OR IGNORE INTO carousel_details (post_id) VALUES (?)", (post_id,))
        elif ct == "video":
            conn.execute("INSERT OR IGNORE INTO video_details (post_id, duration_seconds) VALUES (?, ?)",
                         (post_id, None))

        # Ensure post directory exists
        if slug:
            ensure_post_directory(slug)

        return "updated" if actually_updated else "unchanged"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--check":
        check_mode()

    if len(sys.argv) < 2:
        print("Usage: python store/scripts/discover.py [--check | <input_csv>] [--enrich]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    do_enrich = "--enrich" in sys.argv

    input_posts = parse_input(input_path)
    if not input_posts:
        print("No posts in input file.")
        sys.exit(0)

    conn = connect()

    # Batch posts
    num_batches = math.ceil(len(input_posts) / BATCH_SIZE)
    results = {"registered": [], "updated": [], "unchanged": [], "enriched": [], "errors": []}

    for batch_num in range(1, num_batches + 1):
        start = (batch_num - 1) * BATCH_SIZE
        end = start + BATCH_SIZE
        batch = input_posts[start:end]

        print(f"\n--- Batch {batch_num}/{num_batches} ({len(batch)} posts) ---")

        for post in batch:
            dir_path, dir_name = find_matching_directory(post["posted_date"])

            if dir_path:
                metadata = extract_metadata(dir_path, dir_name)
                source = f"matched: {dir_name}/"
            else:
                metadata = {
                    "city": None, "framework": None, "slide_layout": None,
                    "content_type": None, "slide_count": None,
                    "sound_name": None,
                }
                source = "no repo match"

            # Merge in fields from input (JSON input carries description, hashtags, etc.)
            # Input fields fill gaps — they don't overwrite metadata extracted from the repo.
            # Use 'is not None' instead of truthiness to handle 0 values (e.g., aweme_type=0 for videos).
            for field in ["description", "hashtags", "sound_name", "content_type",
                          "slide_count", "aweme_type"]:
                if post.get(field) is not None and metadata.get(field) is None:
                    metadata[field] = post[field]

            try:
                action = register_post(post["post_id"], post["posted_date"], metadata, conn)
                filled = [k for k, v in metadata.items() if v is not None]
                empty = [k for k, v in metadata.items() if v is None]
                entry = {
                    "post_id": post["post_id"],
                    "posted_date": post["posted_date"],
                    "source": source,
                    "filled": filled,
                    "empty": empty,
                }

                label = (metadata.get("city") or post["post_id"][:16])
                if action == "registered":
                    results["registered"].append(entry)
                    print(f"  [REG] {label} ({post['posted_date']}) -- {source}")
                elif action == "updated":
                    results["updated"].append(entry)
                    print(f"  [UPD] {label} ({post['posted_date']}) -- filled: {', '.join(filled)}")
                else:
                    results["unchanged"].append(entry)
                    print(f"  [ - ] {label} ({post['posted_date']}) -- unchanged")

            except sqlite3.Error as e:
                error_msg = f"{post['post_id']}: {e}"
                results["errors"].append(error_msg)
                print(f"  [ERR] {post['post_id']}: {e}", file=sys.stderr)
                print("ERROR: Database error during registration. Stopping.", file=sys.stderr)
                print(f"Diagnosis: post_id={post['post_id']}, error={e}", file=sys.stderr)
                conn.rollback()
                sys.exit(1)

        conn.commit()
        print(f"  Batch {batch_num} committed.")

    # Enrichment (if requested) would be called here by the orchestrating procedure.
    # The --enrich flag is a placeholder for the procedure to call collect_post
    # for each registered post and then enrich_from_api.
    if do_enrich:
        print("\n--- Enrichment ---")
        print("Enrichment requires Chrome access to call the TikTok API.")
        print("For each post, run collect_post.py and pass the result to enrich_from_api.")
        print("The orchestrating procedure (Claude) handles this step.")

    write_last_run()

    # Report
    print(f"\n--- Discovery Report ---")
    print(f"Input posts: {len(input_posts)}")
    print(f"Newly registered: {len(results['registered'])}")
    print(f"Updated (null fields filled): {len(results['updated'])}")
    print(f"Unchanged: {len(results['unchanged'])}")
    if results["errors"]:
        print(f"Errors: {len(results['errors'])}")
        for e in results["errors"]:
            print(f"  {e}")

    incomplete = [r for r in results["registered"] + results["updated"] if r["empty"]]
    if incomplete:
        print(f"\n{len(incomplete)} post(s) have incomplete metadata.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
