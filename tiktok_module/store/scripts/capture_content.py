"""
Capture content: triage and orchestrate carousel slide downloads.

Scans the database for carousel posts missing slide images on the filesystem.
Downloads slides in batches using the content retrieval unit process.

Usage:
    python store/scripts/capture_content.py                # triage + download
    python store/scripts/capture_content.py --triage-only  # triage only, no download

Reads:  store/data/analytics/analytics.db
        store/data/posts/{slug}/slides/ (filesystem check)
Writes: store/data/posts/{slug}/slides/Slide N.{ext} (via unit process)

Exit codes:
    0 -- Success
    1 -- Fatal error
"""

import json
import math
import os
import sqlite3
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
DB_PATH = os.path.join(MODULE_ROOT, "store", "data", "analytics", "analytics.db")
POSTS_DIR = os.path.join(MODULE_ROOT, "store", "data", "posts")

sys.path.insert(0, SCRIPT_DIR)
from collect_content import build_collect_urls_js, parse_urls_result, download_all_slides

BATCH_SIZE = 5


def connect():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------

def triage(conn):
    """
    Scan all posts. For carousels, check if slides exist on filesystem.
    Returns dict with 'needs_content', 'has_content', 'videos'.
    """
    rows = conn.execute("""
        SELECT p.post_id, p.content_type, p.slide_count, p.content_path,
               n.slug
        FROM posts p
        LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
        ORDER BY p.posted_date DESC
    """).fetchall()

    needs_content = []
    has_content = []
    videos = []
    no_slug = []

    for row in rows:
        post = dict(row)
        content_type = post["content_type"]
        slug = post["slug"]

        if content_type == "video":
            videos.append(post)
            continue

        if content_type != "carousel":
            continue

        if not slug:
            no_slug.append(post)
            continue

        slides_dir = os.path.join(POSTS_DIR, slug, "slides")
        if os.path.isdir(slides_dir):
            files = [f for f in os.listdir(slides_dir) if not f.startswith(".")]
            if files:
                post["existing_slides"] = len(files)
                has_content.append(post)
                continue

        post["existing_slides"] = 0
        needs_content.append(post)

    return {
        "needs_content": needs_content,
        "has_content": has_content,
        "videos": videos,
        "no_slug": no_slug,
    }


def print_triage(result):
    needs = result["needs_content"]
    has = result["has_content"]
    videos = result["videos"]
    no_slug = result["no_slug"]
    num_batches = math.ceil(len(needs) / BATCH_SIZE) if needs else 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Capture Content Triage -- {today}")
    print()
    print(f"Carousels needing content: {len(needs)}")
    print(f"Carousels with content: {len(has)}")
    print(f"Videos (skipped): {len(videos)}")
    if no_slug:
        print(f"Carousels without slug (cannot download): {len(no_slug)}")
    print()

    if not needs:
        print("Nothing to capture.")
        return

    for batch_num in range(1, num_batches + 1):
        start = (batch_num - 1) * BATCH_SIZE
        end = start + BATCH_SIZE
        batch = needs[start:end]
        print(f"  Batch {batch_num} ({len(batch)} carousels):")
        for p in batch:
            label = p["slug"] or p["post_id"][:16]
            expected = p["slide_count"] or "?"
            print(f"    {label:40s} expected slides: {expected}")


# ---------------------------------------------------------------------------
# Download orchestration
# ---------------------------------------------------------------------------

def ensure_slides_dir(slug):
    """Create the slides directory if it doesn't exist. Returns the path."""
    slides_dir = os.path.join(POSTS_DIR, slug, "slides")
    os.makedirs(slides_dir, exist_ok=True)
    return slides_dir


def download_batch(batch, batch_num, urls_cache):
    """
    Download slides for a batch of posts.

    Phase 1 (URL collection) must have already been run for this batch — the
    URLs are passed in via urls_cache[post_id]. This separation allows the
    orchestrating procedure to collect URLs via browser JS, then pass them
    to this function for Python-side download.

    Args:
        batch: list of post dicts from triage
        batch_num: batch number for display
        urls_cache: dict mapping post_id -> parsed URLs data from collect_content.parse_urls_result

    Returns (successes, failures) lists.
    """
    successes = []
    failures = []

    for post in batch:
        slug = post["slug"]
        post_id = post["post_id"]
        slides_dir = ensure_slides_dir(slug)

        urls_data = urls_cache.get(post_id)
        if not urls_data:
            failures.append({
                "post_id": post_id,
                "slug": slug,
                "error": "No URL data collected for this post. Run Phase 1 (JS URL collection) first.",
            })
            print(f"    {slug}: SKIPPED — no URL data", file=sys.stderr)
            continue

        print(f"    {slug}: downloading {urls_data['slide_count']} slides...")
        result = download_all_slides(urls_data, slides_dir)

        if result["failed"] == 0:
            successes.append({
                "post_id": post_id,
                "slug": slug,
                "slides_downloaded": result["downloaded"],
            })
        else:
            failures.append({
                "post_id": post_id,
                "slug": slug,
                "error": f"{result['failed']} slide(s) failed: {'; '.join(result['errors'])}",
                "partial_downloaded": result["downloaded"],
            })

    return successes, failures


def collect_urls_for_batch(batch):
    """
    Generate JS for collecting image URLs for all posts in a batch.

    Returns a dict of {post_id: js_string} for the orchestrator to execute
    in the browser. After execution, parse results with parse_urls_result()
    and pass to download_batch() via urls_cache.
    """
    js_scripts = {}
    for post in batch:
        js_scripts[post["post_id"]] = build_collect_urls_js(post["post_id"])
    return js_scripts


def print_batch_summary(batch_num, successes, failures):
    total = len(successes) + len(failures)
    print(f"\n--- Batch {batch_num} Complete ({len(successes)}/{total} carousels) ---")
    for s in successes:
        print(f"  {s['slug']:40s} {s['slides_downloaded']} slides downloaded")
    for f in failures:
        print(f"  {f['slug']:40s} FAILED: {f['error']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    triage_only = "--triage-only" in args

    conn = connect()
    result = triage(conn)
    print_triage(result)

    if triage_only or not result["needs_content"]:
        conn.close()
        sys.exit(0)

    needs = result["needs_content"]
    num_batches = math.ceil(len(needs) / BATCH_SIZE)

    # Check for --urls-file flag (pre-collected URLs from browser JS)
    urls_cache = {}
    if "--urls-file" in args:
        idx = args.index("--urls-file")
        if idx + 1 < len(args):
            urls_path = args[idx + 1]
            with open(urls_path, "r", encoding="utf-8") as f:
                all_urls = json.load(f)
            # all_urls is a dict of {post_id: urls_data}
            if isinstance(all_urls, dict):
                urls_cache = all_urls
            elif isinstance(all_urls, list):
                for item in all_urls:
                    if "post_id" in item:
                        urls_cache[item["post_id"]] = item
            print(f"Loaded URLs for {len(urls_cache)} post(s) from {urls_path}")

    if not urls_cache:
        # No pre-collected URLs. Print JS for the orchestrator to execute.
        print("\n--- Phase 1: URL Collection Required ---")
        print("The following JS must be executed in the browser for each batch.")
        print("The orchestrating procedure (Claude) handles this step.")
        print()
        for batch_num in range(1, num_batches + 1):
            start = (batch_num - 1) * BATCH_SIZE
            end = start + BATCH_SIZE
            batch = needs[start:end]
            js_scripts = collect_urls_for_batch(batch)
            print(f"Batch {batch_num}: {len(js_scripts)} post(s) need URL collection")
            for pid in js_scripts:
                slug = next((p["slug"] for p in batch if p["post_id"] == pid), pid[:16])
                print(f"  {slug}: python collect_content.py {pid}")
        print()
        print("After collecting URLs, save as JSON and re-run:")
        print("  python capture_content.py --urls-file urls.json")
        conn.close()
        sys.exit(0)

    # Phase 2: Download using cached URLs
    total_successes = 0
    total_failures = 0
    total_slides = 0

    for batch_num in range(1, num_batches + 1):
        start = (batch_num - 1) * BATCH_SIZE
        end = start + BATCH_SIZE
        batch = needs[start:end]

        print(f"\n--- Downloading Batch {batch_num}/{num_batches} ---")
        successes, failures = download_batch(batch, batch_num, urls_cache)
        print_batch_summary(batch_num, successes, failures)

        total_successes += len(successes)
        total_failures += len(failures)
        for s in successes:
            total_slides += s.get("slides_downloaded", 0)

        if failures:
            print(f"\n{len(failures)} failure(s) in batch {batch_num}.", file=sys.stderr)
            # Stop on failure for diagnosis
            print("Stopping. Diagnose failures before continuing.", file=sys.stderr)
            break

    conn.close()

    # Report
    print(f"\n--- Capture Content Report ---")
    print(f"Carousels downloaded: {total_successes} ({total_slides} total slides)")
    if total_failures:
        print(f"Carousels failed: {total_failures}")
    print(f"Carousels already had content: {len(result['has_content'])}")
    print(f"Videos skipped: {len(result['videos'])}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
