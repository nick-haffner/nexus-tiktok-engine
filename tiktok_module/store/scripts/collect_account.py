"""
Unit process: collect account-level metrics from TikTok Studio.

Collects follower count and total likes from the TikTok Studio overview page.

This script is designed to be:
    - Run independently for testing: python store/scripts/collect_account.py
    - Imported by the batch collection orchestrator

Requires: Chrome with active TikTok Studio session.

Two collection methods:
    1. API: JavaScript fetch against TikTok Studio's account data endpoint
    2. Page: Navigate to TikTok Studio overview and read metrics

Usage:
    python store/scripts/collect_account.py
    python store/scripts/collect_account.py --parse '<json_result>'

Output: JSON to stdout with collected metrics. Errors to stderr.

Exit codes:
    0 — Success
    1 — Fatal error
"""

import json
import sys
import os
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")


# ---------------------------------------------------------------------------
# Page-based collection
# ---------------------------------------------------------------------------

OVERVIEW_URL = "https://www.tiktok.com/tiktokstudio"

# The overview page shows follower count and total likes prominently.
# These are read via read_page (accessibility tree) after navigation.
# No API method documented for account-level data — page navigation is the primary method.


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------

def format_result(followers, total_likes):
    """Format account checkpoint data."""
    return {
        "type": "account_checkpoint",
        "captured_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "followers": followers,
        "total_likes": total_likes,
    }


def validate_result(result):
    """Check that required fields are present and reasonable."""
    errors = []
    if result.get("followers") is None:
        errors.append("followers is null")
    elif not isinstance(result["followers"], int) or result["followers"] < 0:
        errors.append(f"followers has unexpected value: {result['followers']}")

    if result.get("total_likes") is None:
        errors.append("total_likes is null")
    elif not isinstance(result["total_likes"], int) or result["total_likes"] < 0:
        errors.append(f"total_likes has unexpected value: {result['total_likes']}")

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    # Parse mode: takes a JSON string with followers and total_likes
    if "--parse" in args:
        idx = args.index("--parse")
        if idx + 1 < len(args):
            try:
                raw = json.loads(args[idx + 1])
                followers = raw.get("followers")
                total_likes = raw.get("total_likes")

                if isinstance(followers, str):
                    followers = int(followers.replace(",", ""))
                if isinstance(total_likes, str):
                    total_likes = int(total_likes.replace(",", "").replace("K", "000").replace("M", "000000"))

                result = format_result(followers, total_likes)
                errors = validate_result(result)
                if errors:
                    print(f"VALIDATION WARNINGS: {', '.join(errors)}", file=sys.stderr)

                print(json.dumps(result, indent=2))
                sys.exit(0)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"ERROR: Failed to parse input: {e}", file=sys.stderr)
                sys.exit(1)

    # Default: print instructions for manual collection
    print("--- Account Checkpoint Collection ---", file=sys.stderr)
    print(f"Navigate to: {OVERVIEW_URL}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Read the following from the overview page:", file=sys.stderr)
    print("  1. Follower count (displayed prominently)", file=sys.stderr)
    print("  2. Total likes (displayed prominently)", file=sys.stderr)
    print("", file=sys.stderr)
    print("Then run:", file=sys.stderr)
    print('  python collect_account.py --parse \'{"followers": 443, "total_likes": 13000}\'', file=sys.stderr)


if __name__ == "__main__":
    main()
