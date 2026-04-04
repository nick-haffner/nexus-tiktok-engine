"""
Ingest collected metrics from pending-capture.csv into the analytics database.

Reads the manifest to determine which batches to ingest. Processes only rows
in the CSV whose batch has status "collected" in the manifest (or all rows
with filled metrics if run with --all). Updates manifest status per batch.

Usage:
    python store/scripts/ingest.py                  # ingest next collected batch
    python store/scripts/ingest.py --batch N         # ingest specific batch
    python store/scripts/ingest.py --all             # ingest all rows with metrics

Reads:  store/procedures/capture-reading/manifest.json
        store/procedures/capture-reading/pending-capture.csv
Writes: store/data/analytics/analytics.db
Updates: manifest.json (batch status -> ingested)
Cleanup: removes manifest.json and pending-capture.csv when all batches are ingested

Exit codes:
    0 -- Success
    1 -- Fatal error
"""

import csv
import json
import sqlite3
import sys
import os
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
DB_PATH = os.path.join(MODULE_ROOT, "store", "data", "analytics", "analytics.db")
MANIFEST_PATH = os.path.join(MODULE_ROOT, "store", "procedures", "capture-reading", "manifest.json")
CSV_PATH = os.path.join(MODULE_ROOT, "store", "procedures", "capture-reading", "pending-capture.csv")


def connect():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        print("ERROR: manifest.json not found. Run triage first.", file=sys.stderr)
        sys.exit(1)
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_csv():
    if not os.path.exists(CSV_PATH):
        print("ERROR: pending-capture.csv not found.", file=sys.stderr)
        sys.exit(1)
    rows = []
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def to_int(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return int(float(val))  # float() first to handle "3.0" strings
    except (ValueError, TypeError):
        return None


def to_float(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def row_has_metrics(row):
    """Check if a CSV row has been filled with metrics (at minimum, views)."""
    return row.get("views", "").strip() != ""


def validate_row(row, conn):
    warnings = []
    errors = []
    post_id = row["post_id"]

    cur = conn.execute("SELECT post_id FROM posts WHERE post_id = ?", (post_id,))
    if cur.fetchone() is None:
        errors.append(f"Post {post_id} not found in posts table")
        return False, warnings, errors

    views_raw = row.get("views", "").strip()
    if not views_raw:
        errors.append(f"Views is required for {post_id}")
        return False, warnings, errors
    views = to_int(views_raw)
    if views is None:
        errors.append(f"Views has non-numeric value '{views_raw}' for {post_id}")
        return False, warnings, errors

    # Check views non-decreasing
    cur = conn.execute(
        "SELECT views FROM readings WHERE post_id = ? ORDER BY captured_at DESC LIMIT 1",
        (post_id,),
    )
    prev = cur.fetchone()
    if prev and views < prev["views"]:
        warnings.append(f"Views decreased for {post_id}: {prev['views']} -> {views}")

    # Check metric completeness (all readings now capture all metrics)
    expected_fields = [
        "new_followers", "avg_watch_time_seconds",
        "watched_full_percent", "fyp_percent",
    ]
    missing = [f for f in expected_fields if not row.get(f, "").strip()]
    if missing:
        warnings.append(f"Reading for {post_id} missing: {', '.join(missing)}")

    return True, warnings, errors


def insert_row(row, conn):
    now = datetime.now(timezone.utc)
    captured_at = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    posted_date = datetime.strptime(row["posted_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    hours_since_post = int((now - posted_date).total_seconds() / 3600)

    conn.execute(
        """INSERT INTO readings (post_id, captured_at, hours_since_post, type,
                                 views, likes, comments, shares, bookmarks,
                                 new_followers, avg_watch_time_seconds,
                                 watched_full_percent, fyp_percent,
                                 profile_visits, search_percent, profile_percent,
                                 following_percent, other_percent)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            row["post_id"],
            captured_at,
            hours_since_post,
            row["type"],
            to_int(row["views"]),
            to_int(row["likes"]),
            to_int(row["comments"]),
            to_int(row["shares"]),
            to_int(row["bookmarks"]),
            to_int(row.get("new_followers")),
            to_float(row.get("avg_watch_time_seconds")),
            to_float(row.get("watched_full_percent")),
            to_float(row.get("fyp_percent")),
            to_int(row.get("profile_visits")),
            to_float(row.get("search_percent")),
            to_float(row.get("profile_percent")),
            to_float(row.get("following_percent")),
            to_float(row.get("other_percent")),
        ),
    )


def ingest_account(manifest, conn):
    acct = manifest["account_checkpoint"]
    if not acct["due"] or acct["captured"]:
        return

    if acct["followers"] is not None and acct["total_likes"] is not None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            conn.execute("INSERT INTO account VALUES (?, ?, ?)",
                         (today, acct["followers"], acct["total_likes"]))
            conn.commit()
            acct["captured"] = True
            print(f"Account checkpoint saved: {acct['followers']} followers, {acct['total_likes']} likes.")
        except sqlite3.IntegrityError:
            print(f"Account checkpoint for {today} already exists. Skipped.")
    elif acct["due"]:
        print("Account checkpoint due but not yet collected. Skipped.")


def ingest_batch(batch_num, csv_rows, manifest, conn):
    """Ingest all rows for a specific batch number."""
    batch_rows = [r for r in csv_rows if int(r["batch"]) == batch_num and row_has_metrics(r)]

    if not batch_rows:
        print(f"Batch {batch_num}: no filled rows to ingest.")
        return 0, 0, [], []

    ingested = 0
    skipped = 0
    all_warnings = []
    all_errors = []

    for row in batch_rows:
        ok, warnings, errors = validate_row(row, conn)
        all_warnings.extend(warnings)

        if not ok:
            all_errors.extend(errors)
            skipped += 1
            continue

        try:
            insert_row(row, conn)
            ingested += 1

            # Update manifest post status
            for p in manifest["posts"]:
                if p["post_id"] == row["post_id"]:
                    p["status"] = "ingested"
                    break

        except sqlite3.Error as e:
            all_errors.append(f"DB error for {row['post_id']}: {e}")
            skipped += 1

    conn.commit()

    # Update batch status in manifest
    for b in manifest["batches"]:
        if b["batch"] == batch_num:
            batch_posts = [p for p in manifest["posts"] if p["batch"] == batch_num]
            if all(p["status"] == "ingested" for p in batch_posts):
                b["status"] = "ingested"
            elif any(p["status"] == "ingested" for p in batch_posts):
                b["status"] = "partial"
            break

    save_manifest(manifest)

    return ingested, skipped, all_warnings, all_errors


def cleanup_if_complete(manifest):
    """Remove manifest and CSV if all batches are ingested."""
    all_ingested = all(b["status"] == "ingested" for b in manifest["batches"])
    acct_done = not manifest["account_checkpoint"]["due"] or manifest["account_checkpoint"]["captured"]

    if all_ingested and acct_done:
        if os.path.exists(CSV_PATH):
            os.remove(CSV_PATH)
        if os.path.exists(MANIFEST_PATH):
            os.remove(MANIFEST_PATH)
        print("\nAll batches ingested. Cleaned up manifest and CSV.")
        return True
    return False


def main():
    args = sys.argv[1:]
    manifest = load_manifest()
    csv_rows = load_csv()
    conn = connect()

    # Determine which batch(es) to ingest
    if "--all" in args:
        batches_to_ingest = [b["batch"] for b in manifest["batches"]]
    elif "--batch" in args:
        idx = args.index("--batch")
        if idx + 1 < len(args):
            batches_to_ingest = [int(args[idx + 1])]
        else:
            print("ERROR: --batch requires a batch number.", file=sys.stderr)
            sys.exit(1)
    else:
        # Default: ingest the next collected batch (or first batch with filled metrics)
        batches_to_ingest = []
        for b in manifest["batches"]:
            if b["status"] in ("pending", "collected"):
                # Check if this batch has any filled rows in the CSV
                batch_rows = [r for r in csv_rows if int(r["batch"]) == b["batch"] and row_has_metrics(r)]
                if batch_rows:
                    batches_to_ingest.append(b["batch"])
                    break

        if not batches_to_ingest:
            print("No batches ready for ingestion (no filled metrics found).")
            conn.close()
            sys.exit(0)

    total_ingested = 0
    total_skipped = 0
    total_warnings = []
    total_errors = []

    for batch_num in batches_to_ingest:
        print(f"\n--- Ingesting Batch {batch_num} ---")
        ingested, skipped, warnings, errors = ingest_batch(batch_num, csv_rows, manifest, conn)
        total_ingested += ingested
        total_skipped += skipped
        total_warnings.extend(warnings)
        total_errors.extend(errors)

        batch_posts = [r for r in csv_rows if int(r["batch"]) == batch_num and row_has_metrics(r)]
        for r in batch_posts:
            slug = r.get("slug") or r["post_id"][:16]
            views = r.get("views", "")
            print(f"  {slug:30s} {r['type']:8s} views={views}")

    # Account checkpoint
    ingest_account(manifest, conn)

    conn.close()

    # Report
    print(f"\n--- Ingestion Report ---")
    print(f"Readings ingested: {total_ingested}")
    if total_skipped:
        print(f"Skipped: {total_skipped}")
    if total_warnings:
        print(f"Warnings ({len(total_warnings)}):")
        for w in total_warnings:
            print(f"  {w}")
    if total_errors:
        print(f"Errors ({len(total_errors)}):")
        for e in total_errors:
            print(f"  {e}")
    if not total_warnings and not total_errors:
        print("No warnings or errors.")

    # Check if everything is done
    cleanup_if_complete(manifest)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        print("The manifest has been preserved. Diagnose the error and retry.", file=sys.stderr)
        sys.exit(1)
