"""
Generate content artifacts (caption.md, README.md) from existing database fields.

Does not require Chrome or external access — works entirely from the database.

Usage:
    python store/scripts/generate_artifacts.py                 # generate all missing artifacts
    python store/scripts/generate_artifacts.py --dry-run        # report what would be generated

Reads:  store/data/analytics/analytics.db
Writes: store/data/posts/{slug}/caption.md (from description field)
        store/data/posts/{slug}/README.md (from DB metadata, only if not already present)

Exit codes:
    0 -- Success
    1 -- Fatal error
"""

import os
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
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def generate_caption_md(slug, description, posts_dir):
    """Write caption.md from the description field if it doesn't exist."""
    if not description or not description.strip():
        return False

    post_dir = os.path.join(posts_dir, slug)
    if not os.path.isdir(post_dir):
        os.makedirs(post_dir, exist_ok=True)

    caption_path = os.path.join(post_dir, "caption.md")
    if os.path.exists(caption_path):
        return False

    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(f"# Caption\n\n{description}\n")

    return True


def generate_readme_md(slug, post_data, meta_data, posts_dir):
    """
    Write README.md from DB metadata if it doesn't exist.
    Only generates if at least framework or city is known.
    """
    post_dir = os.path.join(posts_dir, slug)
    if not os.path.isdir(post_dir):
        os.makedirs(post_dir, exist_ok=True)

    readme_path = os.path.join(post_dir, "README.md")
    if os.path.exists(readme_path):
        return False

    city = meta_data.get("city") or "Unknown"
    framework = meta_data.get("framework") or ""
    slide_layout = meta_data.get("slide_layout") or ""
    slide_count = post_data.get("slide_count") or ""
    posted_date = post_data.get("posted_date") or ""

    # Only generate if we have at least city or framework
    if city == "Unknown" and not framework:
        return False

    title = city
    if framework:
        title += f" -- {framework.replace('_', ' ').title()}"

    lines = [
        f"# {title}",
        "",
        f"- **Date posted:** {posted_date}",
        f"- **Slides:** {slide_count}",
    ]
    if framework:
        lines.append(f"- **Framework:** {framework.replace('_', ' ').title()}")
    if slide_layout:
        lines.append(f"- **Slide layout:** {slide_layout.replace('_', ' ').title()}")
    lines.extend([
        "- **Views:**",
        "- **Notes:**",
        "",
    ])

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return True


def main():
    dry_run = "--dry-run" in sys.argv

    conn = connect()

    rows = conn.execute("""
        SELECT p.post_id, p.posted_date, p.description, p.content_type, p.slide_count,
               n.slug, n.city, n.framework, n.slide_layout
        FROM posts p
        LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
        WHERE n.slug IS NOT NULL
    """).fetchall()

    captions_generated = 0
    readmes_generated = 0
    captions_skipped = 0
    readmes_skipped = 0

    for row in rows:
        slug = row["slug"]
        description = row["description"]
        post_data = {"posted_date": row["posted_date"], "slide_count": row["slide_count"]}
        meta_data = {"city": row["city"], "framework": row["framework"],
                     "slide_layout": row["slide_layout"]}

        # Caption
        if description and description.strip():
            caption_path = os.path.join(POSTS_DIR, slug, "caption.md")
            if not os.path.exists(caption_path):
                if dry_run:
                    print(f"  [caption] Would generate: {slug}/caption.md")
                else:
                    if generate_caption_md(slug, description, POSTS_DIR):
                        captions_generated += 1
                    else:
                        captions_skipped += 1
            else:
                captions_skipped += 1
        else:
            captions_skipped += 1

        # README
        readme_path = os.path.join(POSTS_DIR, slug, "README.md")
        if not os.path.exists(readme_path):
            if meta_data["city"] or meta_data["framework"]:
                if dry_run:
                    print(f"  [readme]  Would generate: {slug}/README.md")
                else:
                    if generate_readme_md(slug, post_data, meta_data, POSTS_DIR):
                        readmes_generated += 1
                    else:
                        readmes_skipped += 1
            else:
                readmes_skipped += 1
        else:
            readmes_skipped += 1

    conn.close()

    if dry_run:
        print(f"\nDry run complete. No files written.")
    else:
        print(f"\n--- Artifact Generation Report ---")
        print(f"caption.md generated: {captions_generated}")
        print(f"caption.md skipped (exists or no description): {captions_skipped}")
        print(f"README.md generated: {readmes_generated}")
        print(f"README.md skipped (exists or insufficient metadata): {readmes_skipped}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
