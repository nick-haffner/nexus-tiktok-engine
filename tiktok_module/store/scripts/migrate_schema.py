"""
Schema migration: reorganize posts table.

Changes:
  - Reorder columns: universal first, nexus-specific last
  - Rename 'format' -> 'content_type' (values: carousel, video, photo)
  - Add columns: hashtags, aweme_type, content_path
  - Set content_path for engine-produced posts with known directories

Run once. Creates a backup before migrating.

Usage:
    python scripts/migrate_schema.py
"""

import os
import shutil
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(SCRIPT_DIR, "..")
DB_PATH = os.path.join(REPO_ROOT, "analytics", "analytics.db")
BACKUP_PATH = DB_PATH + ".pre_migration_bak"


# Mapping of old format values to generalized content_type
FORMAT_MAP = {
    "combined": "carousel",
    "split": "carousel",
    "single_point": "carousel",
}

# Engine-produced posts with known directories (slug -> content_path)
KNOWN_PATHS = {
    "los-angeles-2026-03-27": "posts/los-angeles-2026-03-27",
    "los-angeles-2026-03-31": "posts/los-angeles-2026-03-31",
    "nashville-2026-03-30": "posts/nashville-2026-03-30",
}


def main():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)

    # Backup
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup created at {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Disable FK checks during table recreation
    conn.execute("PRAGMA foreign_keys=OFF")

    # Verify current schema
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(posts)").fetchall()]
    print(f"Current columns: {cols}")

    if "content_type" in cols:
        print("Migration already applied (content_type column exists). Exiting.")
        conn.close()
        return

    if "format" not in cols:
        print("ERROR: Expected 'format' column not found.", file=sys.stderr)
        sys.exit(1)

    conn.execute("BEGIN TRANSACTION")

    try:
        # Create new table with target column order
        conn.execute("""
            CREATE TABLE posts_new (
                -- Universal: any TikTok post has these
                post_id      TEXT PRIMARY KEY,
                posted_date  TEXT NOT NULL,
                description  TEXT,
                hashtags     TEXT,
                content_type TEXT,
                aweme_type   INTEGER,
                sound_name   TEXT,
                slide_count  INTEGER,
                content_path TEXT,
                -- Nexus-specific: our content formula
                slug         TEXT UNIQUE,
                city         TEXT,
                hook_text    TEXT,
                framework    TEXT,
                angle        TEXT
            )
        """)

        # Migrate data with format -> content_type mapping
        rows = conn.execute("SELECT * FROM posts").fetchall()
        for row in rows:
            old_format = row["format"]
            content_type = FORMAT_MAP.get(old_format, old_format)

            # Determine content_path for known engine posts
            slug = row["slug"]
            content_path = KNOWN_PATHS.get(slug)

            conn.execute("""
                INSERT INTO posts_new (
                    post_id, posted_date, description, hashtags,
                    content_type, aweme_type, sound_name, slide_count,
                    content_path, slug, city, hook_text, framework, angle
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["post_id"], row["posted_date"], row["description"], None,
                content_type, None, row["sound_name"], row["slide_count"],
                content_path, slug, row["city"], row["hook_text"],
                row["framework"], row["angle"],
            ))

        migrated = len(rows)

        # Drop old table, rename new
        conn.execute("DROP TABLE posts")
        conn.execute("ALTER TABLE posts_new RENAME TO posts")

        # Verify FK integrity
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            print(f"WARNING: FK check found {len(fk_errors)} issues: {fk_errors}")
        else:
            print("FK integrity check passed.")

        conn.execute("COMMIT")
        conn.execute("PRAGMA foreign_keys=ON")

        # Verify
        new_cols = [r["name"] for r in conn.execute("PRAGMA table_info(posts)").fetchall()]
        print(f"New columns: {new_cols}")
        print(f"Migrated {migrated} rows.")

    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"ERROR: Migration failed, rolled back. {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
