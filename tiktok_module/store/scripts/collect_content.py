"""
Unit process: download carousel slide images for a single TikTok post.

Two-phase workflow:
    Phase 1 (browser): Execute JS to collect signed image URLs from /api/post/item_list/
    Phase 2 (Python):  Download images directly from CDN URLs and save to disk

The signed CDN URLs are self-authenticating (signature in query params, not cookies),
so Phase 2 uses Python urllib — no browser needed for the download step.

This script is designed to be:
    - Run independently for testing: python store/scripts/collect_content.py <post_id>
    - Imported by the capture content procedure

Requires: Chrome with active TikTok session for Phase 1 (URL collection only).

Usage:
    python store/scripts/collect_content.py <post_id>
    python store/scripts/collect_content.py <post_id> --parse '<json>' --output-dir <path>

Output: JSON to stdout with post_id, slide_count, file_paths, and errors.

Exit codes:
    0 — Success (all slides downloaded)
    1 — Fatal error
    2 — Partial (some slides failed)
"""

import json
import os
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")


# ---------------------------------------------------------------------------
# Phase 1: JavaScript for URL collection (executed in browser)
# ---------------------------------------------------------------------------

# Gets image URLs for a single carousel post from /api/post/item_list/.
# Must be executed in browser context on any tiktok.com page.
# Returns JSON with post_id, slide_count, and slides[] with URLs + dimensions.

COLLECT_URLS_JS = """
(async () => {{
    // Get secUid
    const userResp = await fetch("/tiktokstudio/api/web/user?needIsVerified=true", {{
        credentials: "include"
    }});
    const userData = await userResp.json();
    const secUid = userData?.userBaseInfo?.UserProfile?.UserBase?.SecUid;

    if (!secUid) {{
        return JSON.stringify({{
            error: "Could not get secUid. Are you logged into TikTok Studio?"
        }});
    }}

    // Paginate item_list until we find the target post
    const postId = "{post_id}";
    let cursor = "0";
    let hasMore = true;
    let pages = 0;
    let target = null;

    while (hasMore && pages < 20 && !target) {{
        const params = new URLSearchParams({{
            aid: "1988",
            count: "30",
            cursor: cursor,
            secUid: secUid,
            needPinnedItemIds: "true"
        }});

        const resp = await fetch(
            "/api/post/item_list/?" + params.toString(),
            {{ credentials: "include" }}
        );
        const data = await resp.json();

        if ((data.statusCode || data.status_code) !== 0) {{
            return JSON.stringify({{
                error: "item_list API error",
                status_code: data.statusCode || data.status_code
            }});
        }}

        for (const item of (data.itemList || [])) {{
            if (item.id === postId) {{
                target = item;
                break;
            }}
        }}

        hasMore = data.hasMore;
        cursor = data.cursor || "0";
        pages++;
    }}

    if (!target) {{
        return JSON.stringify({{ error: "Post not found in item_list", post_id: postId }});
    }}

    if (!target.imagePost) {{
        return JSON.stringify({{ error: "Post is not a carousel", post_id: postId }});
    }}

    const images = target.imagePost.images || [];
    const slides = images.map((img, i) => ({{
        index: i,
        url: img.imageURL?.urlList?.[0] || null,
        width: img.imageWidth || null,
        height: img.imageHeight || null
    }}));

    return JSON.stringify({{
        post_id: postId,
        slide_count: slides.length,
        slides: slides
    }});
}})();
"""


def build_collect_urls_js(post_id):
    """Return JS to collect image URLs for a carousel post."""
    return COLLECT_URLS_JS.format(post_id=post_id)


# ---------------------------------------------------------------------------
# Phase 2: Python download and file output
# ---------------------------------------------------------------------------

CONTENT_TYPE_TO_EXT = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
}


def parse_urls_result(raw_json):
    """Parse the JSON from Phase 1 (URL collection)."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError) as e:
        return None, f"Failed to parse JSON: {e}"

    if "error" in data:
        return None, data["error"]

    return data, None


def download_slide(url, slide_number, output_dir):
    """
    Download a single slide image from a signed CDN URL and save to disk.

    Names files as 'Slide 1.jpeg', 'Slide 2.jpeg', etc.
    Returns (file_path, size_bytes, None) on success or (None, 0, error_string) on failure.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=30)
        data = resp.read()

        content_type = resp.headers.get("Content-Type", "image/jpeg")
        ext = CONTENT_TYPE_TO_EXT.get(content_type, "jpeg")
        filename = f"Slide {slide_number}.{ext}"
        filepath = os.path.join(output_dir, filename)

        os.makedirs(output_dir, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(data)

        return filepath, len(data), None

    except urllib.error.HTTPError as e:
        if e.code == 403:
            return None, 0, f"HTTP 403: URL expired or access denied"
        return None, 0, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, 0, f"URL error: {e.reason}"
    except Exception as e:
        return None, 0, f"Download failed: {e}"


def download_all_slides(urls_data, output_dir):
    """
    Download all slides for a carousel post.

    Args:
        urls_data: parsed Phase 1 result (post_id, slide_count, slides[])
        output_dir: directory to write slide files

    Returns structured result dict.
    """
    result = {
        "post_id": urls_data["post_id"],
        "slide_count": urls_data["slide_count"],
        "downloaded": 0,
        "failed": 0,
        "file_paths": [],
        "errors": [],
    }

    for slide in urls_data.get("slides", []):
        slide_number = slide["index"] + 1
        url = slide.get("url")

        if not url:
            result["failed"] += 1
            result["errors"].append(f"Slide {slide_number}: no URL")
            continue

        filepath, size_bytes, error = download_slide(url, slide_number, output_dir)

        if error:
            result["failed"] += 1
            result["errors"].append(f"Slide {slide_number}: {error}")
        else:
            result["downloaded"] += 1
            result["file_paths"].append(filepath)
            print(f"  Slide {slide_number}: {size_bytes // 1024} KB -> {filepath}", file=sys.stderr)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    post_id = args[0]

    output_dir = None
    if "--output-dir" in args:
        idx = args.index("--output-dir")
        if idx + 1 < len(args):
            output_dir = args[idx + 1]

    # Parse + download mode
    if "--parse" in args:
        idx = args.index("--parse")
        if idx + 1 < len(args):
            raw_json = args[idx + 1]
        else:
            raw_json = sys.stdin.read()

        urls_data, error = parse_urls_result(raw_json)
        if error:
            print(f"ERROR: {error}", file=sys.stderr)
            sys.exit(1)

        if not output_dir:
            # No output dir — just print the URL data
            print(json.dumps(urls_data, indent=2))
            sys.exit(0)

        # Download all slides
        print(f"Downloading {urls_data['slide_count']} slides...", file=sys.stderr)
        result = download_all_slides(urls_data, output_dir)
        print(json.dumps(result, indent=2))

        if result["failed"] > 0 and result["downloaded"] > 0:
            sys.exit(2)
        elif result["failed"] > 0:
            sys.exit(1)
        sys.exit(0)

    # Default: print the JS and instructions
    js = build_collect_urls_js(post_id)
    print("--- Carousel Content Collection ---", file=sys.stderr)
    print(f"Post ID: {post_id}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Step 1: Execute the following JS on any tiktok.com page", file=sys.stderr)
    print("to collect slide image URLs:", file=sys.stderr)
    print("", file=sys.stderr)
    print(js, file=sys.stderr)
    print("", file=sys.stderr)
    print("Step 2: Parse and download:", file=sys.stderr)
    print(f"  python collect_content.py {post_id} --parse '<json_result>' --output-dir <path>", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
