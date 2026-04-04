"""
Run capture triage against the analytics database.

Produces a manifest (JSON) and a pending-capture CSV with batch assignments.
The manifest tracks the state of the capture cycle. The CSV is human-readable
and human-fillable — if automated collection fails, a human can fill it manually.

Usage:
    python store/scripts/triage.py

Reads:  store/data/analytics/analytics.db
Writes: store/procedures/capture-reading/manifest.json
        store/procedures/capture-reading/pending-capture.csv

Exit codes:
    0 — Success (manifest and CSV written; may have zero posts if nothing is due)
    1 — Fatal error (DB not found, query error)
    2 — Existing manifest found (must complete or clear before re-triaging)
"""

import csv
import json
import math
import sqlite3
import sys
import os
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
DB_PATH = os.path.join(MODULE_ROOT, "store", "data", "analytics", "analytics.db")
MANIFEST_PATH = os.path.join(MODULE_ROOT, "store", "procedures", "capture-reading", "manifest.json")
CSV_PATH = os.path.join(MODULE_ROOT, "store", "procedures", "capture-reading", "pending-capture.csv")

BATCH_SIZE = 5

CSV_HEADERS = [
    "batch", "post_id", "slug", "posted_date", "hours_old", "type",
    "views", "likes", "comments", "shares", "bookmarks",
    "new_followers", "avg_watch_time_seconds", "watched_full_percent",
    "fyp_percent", "profile_visits",
    "search_percent", "profile_percent", "following_percent", "other_percent",
]


def connect():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def run_triage(conn):
    """
    Reading cadence (2026-04-04):
      - 0-3 days (0-72h):    daily, every 6h   (algorithm actively testing)
      - 3-7 days (72-168h):  daily, every 12h  (distribution settling)
      - 7-30 days (168-720h): weekly, every 7d  (second-wave monitoring)
      - 30 days (720h):      mature, once       (lifetime baseline capstone)
      - 30+ days:            on-demand only     (via /store-update for)
      - Any age <=30d, no readings: backfill
    """
    return conn.execute("""
        SELECT
            p.post_id, n.slug, p.posted_date,
            CAST((julianday('now') - julianday(p.posted_date)) * 24 AS INTEGER) AS hours_old,
            CASE
                -- Backfill: any post <=30 days with zero readings
                WHEN NOT EXISTS (
                        SELECT 1 FROM readings r4
                        WHERE r4.post_id = p.post_id
                    )
                    AND CAST((julianday('now') - julianday(p.posted_date)) * 24 AS INTEGER) <= 720
                    THEN 'backfill'
                -- Hyper-early: post is 0-3 days old, last reading was 6+ hours ago
                WHEN CAST((julianday('now') - julianday(p.posted_date)) * 24 AS INTEGER) <= 72
                    AND CAST((julianday('now') - julianday(MAX(r.captured_at))) * 24 AS INTEGER) >= 6
                    THEN 'daily'
                -- Daily: post is 3-7 days old, last reading was 12+ hours ago
                WHEN CAST((julianday('now') - julianday(p.posted_date)) * 24 AS INTEGER) BETWEEN 73 AND 168
                    AND CAST((julianday('now') - julianday(MAX(r.captured_at))) * 24 AS INTEGER) >= 12
                    THEN 'daily'
                -- Weekly: post is 7-30 days old, last reading was 7+ days ago
                WHEN CAST((julianday('now') - julianday(p.posted_date)) * 24 AS INTEGER) BETWEEN 169 AND 720
                    AND CAST((julianday('now') - julianday(MAX(r.captured_at))) * 24 AS INTEGER) >= 168
                    THEN 'weekly'
                -- Mature: post is 30+ days old, has no reading at or after 720h
                WHEN CAST((julianday('now') - julianday(p.posted_date)) * 24 AS INTEGER) > 720
                    AND NOT EXISTS (
                        SELECT 1 FROM readings r5
                        WHERE r5.post_id = p.post_id AND r5.hours_since_post >= 720
                    )
                    THEN 'mature'
                ELSE NULL
            END AS action_needed
        FROM posts p
        LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
        LEFT JOIN readings r ON p.post_id = r.post_id
        GROUP BY p.post_id
        HAVING action_needed IS NOT NULL
    """).fetchall()


def check_account(conn):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return conn.execute("""
        SELECT CASE
            WHEN MAX(captured_date) IS NULL THEN 'due'
            WHEN MAX(captured_date) < ? THEN 'due'
            ELSE 'not_due'
        END AS status,
        MAX(captured_date) AS last_captured
        FROM account
    """, (today,)).fetchone()


def build_manifest(rows, acct):
    now = datetime.now(timezone.utc).isoformat()
    num_batches = math.ceil(len(rows) / BATCH_SIZE) if rows else 0

    posts = []
    for i, row in enumerate(rows):
        batch_num = (i // BATCH_SIZE) + 1
        posts.append({
            "post_id": row["post_id"],
            "slug": row["slug"],
            "posted_date": row["posted_date"],
            "hours_old": row["hours_old"],
            "reading_type": row["action_needed"],
            "batch": batch_num,
            "status": "pending",
        })

    batches = []
    for b in range(1, num_batches + 1):
        batch_posts = [p for p in posts if p["batch"] == b]
        batches.append({
            "batch": b,
            "status": "pending",
            "posts_count": len(batch_posts),
        })

    return {
        "created_at": now,
        "total_posts": len(rows),
        "batch_size": BATCH_SIZE,
        "num_batches": num_batches,
        "csv_path": "store/procedures/capture-reading/pending-capture.csv",
        "account_checkpoint": {
            "due": acct["status"] == "due",
            "captured": False,
            "last_captured": acct["last_captured"],
            "followers": None,
            "total_likes": None,
        },
        "batches": batches,
        "posts": posts,
    }


def write_manifest(manifest):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def write_csv(manifest):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for post in manifest["posts"]:
            writer.writerow([
                post["batch"],
                post["post_id"],
                post["slug"],
                post["posted_date"],
                post["hours_old"],
                post["reading_type"],
                # Metric columns — blank for manual or automated fill
                "", "", "", "", "",   # views, likes, comments, shares, bookmarks
                "", "", "",           # new_followers, avg_watch_time, watched_full_pct
                "", "",               # fyp_percent, profile_visits
                "", "", "", "",       # search_pct, profile_pct, following_pct, other_pct
            ])


def print_summary(manifest):
    total = manifest["total_posts"]
    batches = manifest["num_batches"]
    acct = manifest["account_checkpoint"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"Capture Triage -- {today}")
    print()

    if total == 0:
        print("Posts due: 0")
        print("Nothing to capture.")
    else:
        print(f"Posts due: {total} ({batches} batch(es) of {BATCH_SIZE})")
        print()

        for batch_info in manifest["batches"]:
            b = batch_info["batch"]
            batch_posts = [p for p in manifest["posts"] if p["batch"] == b]
            print(f"  Batch {b} ({len(batch_posts)} posts):")
            for p in batch_posts:
                label = p["slug"] or p["post_id"][:16]
                cols = f"all metrics ({p['reading_type']})"
                print(f"    {label} (posted {p['hours_old']}h ago) -- {p['reading_type']} ({cols})")

    print()
    if acct["due"]:
        if acct["last_captured"]:
            print(f"Account checkpoint: DUE (last captured {acct['last_captured']})")
        else:
            print("Account checkpoint: DUE (never captured)")
    else:
        print(f"Account checkpoint: not due (last captured {acct['last_captured']})")

    print()
    if total > 0:
        print(f"Manifest: store/procedures/capture-reading/manifest.json")
        print(f"CSV:      store/procedures/capture-reading/pending-capture.csv")


def main():
    # Check for existing manifest
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
            pending = sum(1 for p in existing["posts"] if p["status"] in ("pending", "collected"))
            if pending > 0:
                print(f"ERROR: Existing manifest found with {pending} unfinished post(s).", file=sys.stderr)
                print(f"Complete the current capture cycle or delete the manifest before re-triaging.", file=sys.stderr)
                sys.exit(2)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"ERROR: Existing manifest is corrupted: {e}", file=sys.stderr)
            print(f"Delete the manifest to start fresh: rm {MANIFEST_PATH}", file=sys.stderr)
            sys.exit(1)

    try:
        conn = connect()
        rows = run_triage(conn)
        acct = check_account(conn)
        conn.close()
    except sqlite3.Error as e:
        print(f"ERROR: Database query failed: {e}", file=sys.stderr)
        sys.exit(1)

    manifest = build_manifest(rows, acct)
    write_manifest(manifest)
    write_csv(manifest)
    print_summary(manifest)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
