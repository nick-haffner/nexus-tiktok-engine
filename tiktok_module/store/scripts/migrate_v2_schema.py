"""
Migrate analytics.db from v1 (flat posts table) to v2 (normalized schema).

Changes:
    1. Recreate `posts` table with only universal TikTok fields + Tier 2/3 stubs
    2. Create `nexus_post_metadata` table (company-specific data, joined on post_id)
    3. Create `carousel_details` table (subtype stub)
    4. Create `video_details` table (subtype stub)
    5. Add Tier 3 stub columns to `readings` table
    6. Migrate data from old posts → new posts + nexus_post_metadata
    7. Backfill Tier A posts (README.md data not yet in DB)

Usage:
    python store/scripts/migrate_v2_schema.py

Reads:  store/data/analytics/analytics.db
        store/data/posts/*/README.md (for Tier A backfill)
Writes: store/data/analytics/analytics.db (in-place migration)
        store/data/analytics/analytics.db.v1.bak (backup)

Exit codes:
    0 — Success
    1 — Fatal error
"""

import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
DB_PATH = os.path.join(MODULE_ROOT, "store", "data", "analytics", "analytics.db")
POSTS_DIR = os.path.join(MODULE_ROOT, "store", "data", "posts")


def connect():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=OFF")  # Off during migration
    conn.row_factory = sqlite3.Row
    return conn


def backup(conn):
    backup_path = DB_PATH + ".v1.bak"
    conn.close()
    shutil.copy2(DB_PATH, backup_path)
    print(f"Backup created: {backup_path}")
    return sqlite3.connect(DB_PATH)


def migrate_posts_table(conn):
    """Recreate posts table with universal fields only, add Tier 2 stubs."""

    # Read all existing data
    rows = conn.execute("SELECT * FROM posts").fetchall()
    old_data = [dict(r) for r in rows]

    # Read existing readings and account data to preserve
    readings_data = [dict(r) for r in conn.execute("SELECT * FROM readings").fetchall()]
    account_data = [dict(r) for r in conn.execute("SELECT * FROM account").fetchall()]

    # Drop old tables (order matters for foreign keys)
    conn.execute("DROP TABLE IF EXISTS readings")
    conn.execute("DROP TABLE IF EXISTS carousel_details")
    conn.execute("DROP TABLE IF EXISTS video_details")
    conn.execute("DROP TABLE IF EXISTS nexus_post_metadata")
    conn.execute("DROP TABLE IF EXISTS posts")
    conn.execute("DROP TABLE IF EXISTS account")

    # Create new posts table — universal TikTok data only
    conn.execute("""
        CREATE TABLE posts (
            post_id       TEXT PRIMARY KEY,
            posted_date   TEXT NOT NULL,
            posted_time   TEXT,
            description   TEXT,
            hashtags      TEXT,
            content_type  TEXT,
            aweme_type    INTEGER,
            sound_name    TEXT,
            sound_type    TEXT,
            slide_count   INTEGER,
            content_path  TEXT
        )
    """)

    # Create nexus_post_metadata — company-specific
    conn.execute("""
        CREATE TABLE nexus_post_metadata (
            post_id        TEXT PRIMARY KEY REFERENCES posts(post_id),
            slug           TEXT UNIQUE,
            city           TEXT,
            hook_text      TEXT,
            hook_style     TEXT,
            framework      TEXT,
            angle          TEXT,
            format         TEXT,
            cta_text       TEXT,
            content_topics TEXT
        )
    """)

    # Create carousel_details — subtype stub
    conn.execute("""
        CREATE TABLE carousel_details (
            post_id TEXT PRIMARY KEY REFERENCES posts(post_id)
        )
    """)

    # Create video_details — subtype stub
    conn.execute("""
        CREATE TABLE video_details (
            post_id          TEXT PRIMARY KEY REFERENCES posts(post_id),
            duration_seconds REAL
        )
    """)

    # Recreate readings with Tier 3 stubs
    conn.execute("""
        CREATE TABLE readings (
            post_id                TEXT NOT NULL REFERENCES posts(post_id),
            captured_at            TEXT NOT NULL,
            hours_since_post       INTEGER NOT NULL,
            type                   TEXT NOT NULL CHECK(type IN ('velocity', 'snapshot')),
            views                  INTEGER NOT NULL,
            likes                  INTEGER NOT NULL,
            comments               INTEGER NOT NULL,
            shares                 INTEGER NOT NULL,
            bookmarks              INTEGER NOT NULL,
            new_followers          INTEGER,
            avg_watch_time_seconds REAL,
            watched_full_percent   REAL,
            fyp_percent            REAL,
            profile_visits         INTEGER,
            search_percent         REAL,
            profile_percent        REAL,
            following_percent      REAL,
            other_percent          REAL,
            PRIMARY KEY (post_id, captured_at)
        )
    """)

    # Recreate account
    conn.execute("""
        CREATE TABLE account (
            captured_date TEXT PRIMARY KEY,
            followers     INTEGER NOT NULL,
            total_likes   INTEGER NOT NULL
        )
    """)

    # Migrate post data
    for row in old_data:
        # Insert into universal posts table
        conn.execute("""
            INSERT INTO posts (post_id, posted_date, posted_time, description, hashtags,
                               content_type, aweme_type, sound_name, sound_type,
                               slide_count, content_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["post_id"], row["posted_date"], None, row["description"],
            row["hashtags"], row["content_type"], row["aweme_type"],
            row["sound_name"], None, row["slide_count"], row["content_path"],
        ))

        # Insert into nexus_post_metadata
        conn.execute("""
            INSERT INTO nexus_post_metadata (post_id, slug, city, hook_text, hook_style,
                                             framework, angle, format, cta_text, content_topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["post_id"], row.get("slug"), row.get("city"),
            row.get("hook_text"), None, row.get("framework"),
            row.get("angle"), None, None, None,
        ))

        # Insert into subtype table
        ct = row.get("content_type")
        if ct == "carousel":
            conn.execute("INSERT INTO carousel_details (post_id) VALUES (?)", (row["post_id"],))
        elif ct == "video":
            conn.execute("INSERT INTO video_details (post_id, duration_seconds) VALUES (?, ?)",
                         (row["post_id"], None))

    # Restore readings data (with new Tier 3 stub columns as NULL)
    for row in readings_data:
        conn.execute("""
            INSERT INTO readings (post_id, captured_at, hours_since_post, type,
                                  views, likes, comments, shares, bookmarks,
                                  new_followers, avg_watch_time_seconds,
                                  watched_full_percent, fyp_percent,
                                  profile_visits, search_percent, profile_percent,
                                  following_percent, other_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["post_id"], row["captured_at"], row["hours_since_post"],
            row["type"], row["views"], row["likes"], row["comments"],
            row["shares"], row["bookmarks"], row["new_followers"],
            row["avg_watch_time_seconds"], row["watched_full_percent"],
            row["fyp_percent"], None, None, None, None, None,
        ))

    # Restore account data
    for row in account_data:
        conn.execute("INSERT INTO account VALUES (?, ?, ?)",
                     (row["captured_date"], row["followers"], row["total_likes"]))

    conn.commit()
    print(f"Migrated {len(old_data)} posts to new schema.")
    print(f"Restored {len(readings_data)} readings with Tier 3 stubs.")
    print(f"Restored {len(account_data)} account checkpoint(s).")


def parse_readme_metadata(readme_path):
    """Extract framework, angle, format from a README.md file."""
    metadata = {"framework": None, "angle": None, "format": None}
    if not os.path.exists(readme_path):
        return metadata

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    for line in content.split("\n"):
        line_stripped = line.strip().lower()
        if "framework:" in line_stripped:
            val = line.split(":", 1)[1].strip().strip("*").strip()
            if val:
                metadata["framework"] = val.lower().replace(" ", "_").replace("vs.", "vs").replace("vs ", "vs_")
        elif "angle:" in line_stripped:
            val = line.split(":", 1)[1].strip().strip("*").strip()
            if val:
                metadata["angle"] = val.lower().replace(" ", "_")
        elif "format:" in line_stripped:
            val = line.split(":", 1)[1].strip().strip("*").strip()
            if val:
                # Extract just the format name before any parenthetical
                format_match = re.match(r"^([\w\-]+)", val)
                if format_match:
                    metadata["format"] = format_match.group(1).lower().replace("-", "_")

    return metadata


def backfill_tier_a(conn):
    """Backfill nexus_post_metadata from README.md for posts missing framework."""
    updated = 0
    rows = conn.execute("""
        SELECT n.post_id, n.slug
        FROM nexus_post_metadata n
        WHERE n.framework IS NULL AND n.slug IS NOT NULL
    """).fetchall()

    for row in rows:
        slug = row["slug"]
        readme_path = os.path.join(POSTS_DIR, slug, "README.md")
        if not os.path.exists(readme_path):
            continue

        metadata = parse_readme_metadata(readme_path)
        if not metadata["framework"]:
            continue

        conn.execute("""
            UPDATE nexus_post_metadata
            SET framework = COALESCE(framework, ?),
                angle = COALESCE(angle, ?),
                format = COALESCE(format, ?)
            WHERE post_id = ?
        """, (
            metadata["framework"], metadata["angle"],
            metadata["format"], row["post_id"],
        ))
        updated += 1
        print(f"  Backfilled: {slug} -> framework={metadata['framework']}, "
              f"angle={metadata['angle']}, format={metadata['format']}")

    conn.commit()
    print(f"Tier A backfill: updated {updated} post(s).")


def verify(conn):
    """Print verification summary."""
    conn.execute("PRAGMA foreign_keys=ON")

    posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    meta = conn.execute("SELECT COUNT(*) FROM nexus_post_metadata").fetchone()[0]
    carousel = conn.execute("SELECT COUNT(*) FROM carousel_details").fetchone()[0]
    video = conn.execute("SELECT COUNT(*) FROM video_details").fetchone()[0]
    readings = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    account = conn.execute("SELECT COUNT(*) FROM account").fetchone()[0]

    fw_filled = conn.execute("SELECT COUNT(*) FROM nexus_post_metadata WHERE framework IS NOT NULL").fetchone()[0]
    fmt_filled = conn.execute("SELECT COUNT(*) FROM nexus_post_metadata WHERE format IS NOT NULL").fetchone()[0]

    print(f"\n--- Verification ---")
    print(f"posts:               {posts}")
    print(f"nexus_post_metadata: {meta} ({fw_filled} with framework, {fmt_filled} with format)")
    print(f"carousel_details:    {carousel}")
    print(f"video_details:       {video}")
    print(f"readings:            {readings}")
    print(f"account:             {account}")

    # Check foreign key integrity
    fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        print(f"FOREIGN KEY ERRORS: {len(fk_errors)}")
        for e in fk_errors:
            print(f"  {e}")
    else:
        print("Foreign key integrity: OK")

    # Spot-check readings columns
    r = conn.execute("SELECT * FROM readings LIMIT 1").fetchone()
    cols = [d[0] for d in conn.execute("SELECT * FROM readings LIMIT 0").description]
    print(f"readings columns ({len(cols)}): {', '.join(cols)}")

    p = conn.execute("SELECT * FROM posts LIMIT 0")
    pcols = [d[0] for d in p.description]
    print(f"posts columns ({len(pcols)}): {', '.join(pcols)}")


def main():
    conn = connect()

    # Backup
    conn = backup(connect())
    conn.row_factory = sqlite3.Row

    print("Migrating to v2 schema...")
    migrate_posts_table(conn)

    print("\nBackfilling Tier A (README.md data)...")
    backfill_tier_a(conn)

    verify(conn)
    conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
