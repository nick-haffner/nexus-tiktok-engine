"""
Migrate analytics.db from v2 to v3 schema.

Changes:
    1. carousel_details: add slide_texts, visual_summary, has_cta, cta_type, cta_text
    2. nexus_post_metadata: remove hook_text, hook_style, angle, cta_text, content_topics;
       rename format -> slide_layout
    3. posts: add content_topics (universal stub)

Usage:
    python store/scripts/migrate_v3_schema.py

Exit codes:
    0 -- Success
    1 -- Fatal error
"""

import json
import os
import shutil
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
DB_PATH = os.path.join(MODULE_ROOT, "store", "data", "analytics", "analytics.db")


def connect():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=OFF")  # Off during migration
    conn.row_factory = sqlite3.Row
    return conn


def backup():
    backup_path = DB_PATH + ".v2.bak"
    shutil.copy2(DB_PATH, backup_path)
    print(f"Backup created: {backup_path}")


def migrate(conn):
    # --- 1. Recreate carousel_details with new columns ---
    print("Migrating carousel_details...")

    old_carousel = conn.execute("SELECT post_id FROM carousel_details").fetchall()
    old_ids = [r["post_id"] for r in old_carousel]

    conn.execute("DROP TABLE carousel_details")
    conn.execute("""
        CREATE TABLE carousel_details (
            post_id        TEXT PRIMARY KEY REFERENCES posts(post_id),
            slide_texts    TEXT,        -- JSON array of per-slide text content
            visual_summary TEXT,        -- AI description of visual style, layout, progression
            has_cta        INTEGER,     -- 0 or 1
            cta_type       TEXT,        -- "waitlist", "website", "follow", "engage", or other
            cta_text       TEXT         -- the actual CTA string from the CTA slide
        )
    """)

    for pid in old_ids:
        conn.execute("INSERT INTO carousel_details (post_id) VALUES (?)", (pid,))

    print(f"  Recreated with new columns. {len(old_ids)} rows preserved.")

    # --- 2. Recreate nexus_post_metadata ---
    print("Migrating nexus_post_metadata...")

    old_meta = [dict(r) for r in conn.execute("SELECT * FROM nexus_post_metadata").fetchall()]

    conn.execute("DROP TABLE nexus_post_metadata")
    conn.execute("""
        CREATE TABLE nexus_post_metadata (
            post_id      TEXT PRIMARY KEY REFERENCES posts(post_id),
            slug         TEXT UNIQUE,
            city         TEXT,
            framework    TEXT,
            slide_layout TEXT
        )
    """)

    for row in old_meta:
        conn.execute(
            "INSERT INTO nexus_post_metadata (post_id, slug, city, framework, slide_layout) VALUES (?, ?, ?, ?, ?)",
            (row["post_id"], row["slug"], row["city"], row["framework"], row.get("format")),
        )

    print(f"  Recreated. {len(old_meta)} rows migrated. Removed: hook_text, hook_style, angle, cta_text, content_topics. Renamed: format -> slide_layout.")

    # --- 3. Add content_topics to posts ---
    print("Adding content_topics to posts...")

    # Check if column already exists
    cols = [d[0] for d in conn.execute("SELECT * FROM posts LIMIT 0").description]
    if "content_topics" not in cols:
        conn.execute("ALTER TABLE posts ADD COLUMN content_topics TEXT")
        print("  Added content_topics column (stub, all NULL).")
    else:
        print("  content_topics column already exists.")

    conn.commit()


def verify(conn):
    conn.execute("PRAGMA foreign_keys=ON")

    print("\n--- Verification ---")

    # carousel_details
    cols = [d[0] for d in conn.execute("SELECT * FROM carousel_details LIMIT 0").description]
    count = conn.execute("SELECT COUNT(*) FROM carousel_details").fetchone()[0]
    print(f"carousel_details: {count} rows, columns: {', '.join(cols)}")

    # nexus_post_metadata
    cols = [d[0] for d in conn.execute("SELECT * FROM nexus_post_metadata LIMIT 0").description]
    count = conn.execute("SELECT COUNT(*) FROM nexus_post_metadata").fetchone()[0]
    fw_count = conn.execute("SELECT COUNT(*) FROM nexus_post_metadata WHERE framework IS NOT NULL").fetchone()[0]
    sl_count = conn.execute("SELECT COUNT(*) FROM nexus_post_metadata WHERE slide_layout IS NOT NULL").fetchone()[0]
    print(f"nexus_post_metadata: {count} rows, columns: {', '.join(cols)}")
    print(f"  framework: {fw_count}/{count}, slide_layout: {sl_count}/{count}")

    # posts
    cols = [d[0] for d in conn.execute("SELECT * FROM posts LIMIT 0").description]
    print(f"posts columns: {', '.join(cols)}")

    # FK check
    fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        print(f"FOREIGN KEY ERRORS: {len(fk_errors)}")
    else:
        print("Foreign key integrity: OK")


def main():
    backup()
    conn = connect()
    migrate(conn)
    verify(conn)
    conn.close()
    print("\nv3 migration complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        print("Restore from backup: analytics.db.v2.bak", file=sys.stderr)
        sys.exit(1)
