"""
Derive data: triage and orchestrate content classification for carousel posts.

Reads captured content (slide images, captions) and populates derived database
fields through vision AI and classification. Does not access TikTok or require
Chrome — works entirely from the filesystem and database.

Usage:
    python store/scripts/derive_data.py                # triage + derive
    python store/scripts/derive_data.py --triage-only  # triage only

Reads:  store/data/analytics/analytics.db
        store/data/posts/{slug}/slides/ (slide images)
        store/data/posts/{slug}/caption.md (captions)
        store/data/strategy/frameworks.md (classification definitions)
Writes: carousel_details (slide_texts, visual_summary, has_cta, cta_type, cta_text)
        nexus_post_metadata (framework, slide_layout)
        posts (content_topics)

Exit codes:
    0 -- Success
    1 -- Fatal error
"""

import glob
import json
import math
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
DB_PATH = os.path.join(MODULE_ROOT, "store", "data", "analytics", "analytics.db")
POSTS_DIR = os.path.join(MODULE_ROOT, "store", "data", "posts")
FRAMEWORKS_PATH = os.path.join(MODULE_ROOT, "store", "data", "strategy", "frameworks.md")

BATCH_SIZE = 5

# ---------------------------------------------------------------------------
# Model requirement for vision-dependent steps.
#
# Steps 1 (transcribe_slide_texts) and 2 (generate_visual_summary) are
# vision-dependent and MUST be executed by Opus. When the orchestrating
# procedure launches agents for these steps, it must specify model="opus".
#
# Steps 3-6 (framework, slide_layout, CTA, content_topics) are deterministic
# Python classifiers and are model-independent.
# ---------------------------------------------------------------------------
VISION_MODEL = "opus"

# ---------------------------------------------------------------------------
# Stored prompts — natural language instructions for Claude-executed units.
# Editable for quality improvements. Used by units 1 and 2.
# ---------------------------------------------------------------------------

TRANSCRIBE_PROMPT = """Read each slide image and extract ALL visible text exactly as displayed.

Rules:
- Capture text verbatim including capitalization and line breaks.
- Include all emojis as they appear (\u274c, \u2705, \u2615, \U0001f32e, \U0001f305, \U0001f306, \U0001f37d, \U0001f319, \U0001f97e, \U0001f52d, \U0001f30a, \U0001f3ac, etc.).
- Include heading/category labels (e.g., "Morning", "Wasted", "Local", location names).
- Preserve the reading order: headings first, then body text.
- Use \\n for line breaks within a slide's text.
- If a slide has NO text overlay (image only), use an empty string.
- Do NOT add text that is not visually present on the slide.
- Do NOT omit text that IS visually present, even if partially obscured.
- Ignore watermarks, TikTok UI elements (swipe arrows, dots), and logos unless
  the logo contains readable text (e.g., "nexus" logo text is NOT captured,
  but "nexus-concierge.com" URL text IS captured).

Output format: JSON array of strings, one per slide, in slide order.
Example: ["Hook text here", "\U0001f305 Morning\\nWasted \u274c\\nHollywood Walk of Fame.", "", "CTA text"]
"""

VISUAL_SUMMARY_PROMPT = """Examine every slide image in this carousel and produce a detailed visual description.

For each slide, describe what you see in full — the photo or graphic background,
all text overlays (content, font treatment, color, size, placement), any logos or
branding, emoji usage, structural elements (headings, dividers, labels), and the
overall composition. Note details that could affect content performance: text
readability and contrast, photo quality (professional, amateur, AI-generated),
information density, negative space, color palette and mood, hook strength
(slide 1), CTA visibility and placement (final slides), and visual rhythm or
variety across the set.

Output format:
- One section per slide: "Slide N:" followed by the description.
- After all slides: "Overall:" with 2-3 sentences on patterns, consistency,
  and anything notable about the carousel as a whole (dimensions, aspect ratio,
  branding cadence, structural template).

Be thorough. A downstream analyst will use this description without seeing the
images. Details you omit are details they cannot analyze.
"""


def connect():
    if not os.path.exists(DB_PATH):
        print("ERROR: analytics.db not found.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def load_frameworks_catalog():
    """Load the frameworks and slide layouts catalog for classification."""
    if not os.path.exists(FRAMEWORKS_PATH):
        return ""
    with open(FRAMEWORKS_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------

def get_slide_image_paths(slug):
    """Return sorted list of slide image paths for a post, or empty list."""
    slides_dir = os.path.join(POSTS_DIR, slug, "slides")
    if not os.path.isdir(slides_dir):
        return []
    files = sorted(
        [f for f in os.listdir(slides_dir) if not f.startswith(".")],
        key=lambda f: int("".join(c for c in f.split(".")[0] if c.isdigit()) or "0"),
    )
    return [os.path.join(slides_dir, f) for f in files]


def get_description(slug):
    """Read caption from caption.md or return empty string."""
    caption_path = os.path.join(POSTS_DIR, slug, "caption.md")
    if not os.path.exists(caption_path):
        return ""
    with open(caption_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Strip the "# Caption\n\n" header if present
    if content.startswith("# Caption"):
        content = content.split("\n", 2)[-1].strip()
    return content


def triage(conn):
    """
    Scan all carousel posts. Check which derived fields are NULL
    and whether slide images exist.
    """
    rows = conn.execute("""
        SELECT p.post_id, p.content_type, p.slide_count, p.content_topics,
               n.slug, n.framework, n.slide_layout,
               c.slide_texts, c.visual_summary, c.has_cta
        FROM posts p
        JOIN carousel_details c ON p.post_id = c.post_id
        LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
        WHERE p.content_type = 'carousel'
    """).fetchall()

    processable = []
    no_images = []
    fully_derived = []

    for row in rows:
        post = dict(row)
        slug = post["slug"]

        if not slug:
            no_images.append(post)
            continue

        image_paths = get_slide_image_paths(slug)
        if not image_paths:
            no_images.append(post)
            continue

        # Check which fields need derivation
        needs = []
        if post["slide_texts"] is None:
            needs.append("slide_texts")
        if post["visual_summary"] is None:
            needs.append("visual_summary")
        if post["framework"] is None:
            needs.append("framework")
        if post["slide_layout"] is None:
            needs.append("slide_layout")
        if post["has_cta"] is None:
            needs.append("cta")
        if post["content_topics"] is None:
            needs.append("content_topics")

        if not needs:
            fully_derived.append(post)
            continue

        post["needs"] = needs
        post["image_paths"] = image_paths
        post["image_count"] = len(image_paths)
        processable.append(post)

    return {
        "processable": processable,
        "no_images": no_images,
        "fully_derived": fully_derived,
    }


def print_triage(result):
    proc = result["processable"]
    no_img = result["no_images"]
    derived = result["fully_derived"]
    num_batches = math.ceil(len(proc) / BATCH_SIZE) if proc else 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Derive Data Triage -- {today}")
    print()
    print(f"Posts with slide images (processable): {len(proc)}")
    print(f"Posts without slide images (skip): {len(no_img)}")
    print(f"Posts fully derived (nothing to do): {len(derived)}")
    print()

    if proc:
        # Aggregate needs
        all_needs = {}
        for p in proc:
            for n in p["needs"]:
                all_needs[n] = all_needs.get(n, 0) + 1
        total_carousels = len(proc) + len(derived)
        print("Derivation needed:")
        for field, count in all_needs.items():
            already = total_carousels - count
            print(f"  {field:20s} {count}/{total_carousels} NULL ({already} already populated)")
        print()

        for batch_num in range(1, num_batches + 1):
            start = (batch_num - 1) * BATCH_SIZE
            end = start + BATCH_SIZE
            batch = proc[start:end]
            print(f"  Batch {batch_num} ({len(batch)} posts):")
            for p in batch:
                label = p["slug"] or p["post_id"][:16]
                needs_str = ", ".join(p["needs"])
                print(f"    {label:40s} {p['image_count']} slides  needs: {needs_str}")
    else:
        print("Nothing to derive.")


# ---------------------------------------------------------------------------
# Unit process stubs — to be implemented by terminal instance
# ---------------------------------------------------------------------------

def transcribe_slide_texts(slide_image_paths):
    """
    Read text overlays from carousel slide images.

    Claude-executed unit. The orchestrating procedure should:
        1. Print TRANSCRIBE_PROMPT to establish the instruction.
        2. Read each image at the paths in slide_image_paths (in order).
        3. Follow the prompt rules to extract visible text.
        4. Pass the resulting list to format_transcription() for validation.

    Args:
        slide_image_paths: list of file paths to slide images, ordered

    Returns:
        None — Claude fills in via format_transcription() at procedure runtime.
        The stored prompt is available as TRANSCRIBE_PROMPT.
    """
    return None


def format_transcription(slide_texts):
    """
    Validate and format slide text transcriptions provided by Claude.

    Input: list of strings — one per slide, as transcribed by Claude after
           reading each slide image. Empty string for image-only slides.

    Returns: (result_dict, error_string_or_None)
        result_dict: {texts: list, slide_count: int, empty_slides: list[int]}
    """
    if not isinstance(slide_texts, list):
        return None, "Input must be a list of strings"

    if not slide_texts:
        return None, "Empty slide list"

    cleaned = []
    empty_slides = []

    for i, text in enumerate(slide_texts):
        t = str(text).strip() if text else ""
        cleaned.append(t)
        if not t:
            empty_slides.append(i + 1)

    return {
        "texts": cleaned,
        "slide_count": len(cleaned),
        "empty_slides": empty_slides,
    }, None


def get_ground_truth(slug):
    """
    Extract slide texts from copy.md as ground truth for validation.

    Returns list of strings (one per slide) or None if copy.md not found.
    """
    copy_path = os.path.join(POSTS_DIR, slug, "copy.md")
    if not os.path.exists(copy_path):
        return None

    with open(copy_path, "r", encoding="utf-8") as f:
        content = f.read()

    slides = []
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("## Slide"):
            if current_lines:
                slides.append("\n".join(current_lines).strip())
                current_lines = []
        elif line.startswith("> "):
            current_lines.append(line[2:])

    if current_lines:
        slides.append("\n".join(current_lines).strip())

    return slides


def validate_transcription(slide_texts, ground_truth):
    """
    Compare transcribed slide texts against ground truth from copy.md.

    Word overlap measures how many ground truth words appear in the transcription.
    Returns a report dict with per-slide match assessment.
    """
    report = {
        "total_slides": len(slide_texts),
        "ground_truth_slides": len(ground_truth),
        "count_match": len(slide_texts) == len(ground_truth),
        "slides": [],
    }

    for i in range(max(len(slide_texts), len(ground_truth))):
        transcribed = slide_texts[i] if i < len(slide_texts) else "[MISSING]"
        truth = ground_truth[i] if i < len(ground_truth) else "[MISSING]"

        t_norm = re.sub(r"[^\w\s]", "", transcribed.lower()).split()
        g_norm = re.sub(r"[^\w\s]", "", truth.lower()).split()

        if g_norm:
            overlap = len(set(t_norm) & set(g_norm)) / len(set(g_norm))
        else:
            overlap = 1.0 if not t_norm else 0.0

        report["slides"].append({
            "slide": i + 1,
            "transcribed": transcribed[:80],
            "truth": truth[:80],
            "word_overlap": round(overlap, 2),
        })

    overlaps = [s["word_overlap"] for s in report["slides"]]
    report["avg_overlap"] = round(sum(overlaps) / len(overlaps), 2) if overlaps else 0
    return report


def generate_visual_summary(slide_image_paths):
    """
    Produce a natural language description of the carousel's visual properties.

    Claude-executed unit. The orchestrating procedure should:
        1. Print VISUAL_SUMMARY_PROMPT to establish the instruction.
        2. Read ALL slide images in a single pass.
        3. Follow the 6-section checklist in the prompt.
        4. Pass the resulting string to format_visual_summary() for validation.

    Args:
        slide_image_paths: list of file paths to slide images, ordered

    Returns:
        None — Claude fills in via format_visual_summary() at procedure runtime.
        The stored prompt is available as VISUAL_SUMMARY_PROMPT.
    """
    return None


def format_visual_summary(summary_text):
    """
    Validate and format a visual summary produced by following VISUAL_SUMMARY_PROMPT.

    Returns: (summary_string, error_string_or_None)
    """
    if not summary_text or not isinstance(summary_text, str):
        return None, "Visual summary must be a non-empty string"
    text = summary_text.strip()
    if len(text) < 50:
        return None, f"Visual summary too short ({len(text)} chars, minimum 50)"
    return text, None


def classify_framework(visual_summary, slide_texts, frameworks_catalog):
    """
    Classify which framework a carousel uses.

    Deterministic classifier. Returns None when ambiguous.

    Frameworks:
        local_vs_tourist: Alternating contrast pairs with "Tourist"/"Local" headings.
        worth_it: Single recommendations per slide with emoji category markers.
        the_24_hour_test: Time-block progression with Wasted/Local contrast pairs.
        overrated_vs_underrated: Contrast pairs framed as "Overrated"/"Underrated".
    """
    if not slide_texts or not visual_summary:
        return None

    texts_combined = "\n".join(str(s) for s in slide_texts).lower()

    has_tourist_local = ("tourist" in texts_combined and "local" in texts_combined)
    has_wasted_local = ("wasted" in texts_combined and "local" in texts_combined)
    has_overrated_underrated = ("overrated" in texts_combined and "underrated" in texts_combined)
    has_time_blocks = any(t in texts_combined for t in ["morning", "afternoon", "evening", "late night", "dinner"])
    has_contrast_markers = ("\u274c" in texts_combined) and ("\u2705" in texts_combined)
    has_worth_it = "worth it" in texts_combined or "worth your time" in texts_combined
    has_category_emojis = bool(re.search(r"[\U0001f97e\U0001f52d\U0001f30a\U0001f3ac\u2615\U0001f32e\U0001f3d4\U0001f3ad\U0001f3d6\U0001f3b5]", texts_combined))

    if has_time_blocks and has_wasted_local and has_contrast_markers:
        return "the_24_hour_test"
    if has_overrated_underrated and has_contrast_markers:
        return "overrated_vs_underrated"
    if has_tourist_local and has_contrast_markers and not has_time_blocks:
        return "local_vs_tourist"
    if has_category_emojis and not has_contrast_markers:
        return "worth_it"
    if has_worth_it and not has_contrast_markers:
        return "worth_it"

    return None


def classify_slide_layout(visual_summary, slide_texts, layouts_catalog):
    """
    Classify how content is arranged across slides.

    Deterministic classifier. Returns None when ambiguous.

    Layouts:
        split: Contrast pairs on separate consecutive slides (alternating).
        combined: Both sides of contrast on same slide.
        single_point: Each slide standalone, no contrast pairs.
    """
    if not slide_texts:
        return None

    x_slides = 0
    check_slides = 0
    combined_slides = 0

    for text in slide_texts:
        t = str(text)
        has_x = "\u274c" in t
        has_check = "\u2705" in t
        if has_x and has_check:
            combined_slides += 1
        elif has_x:
            x_slides += 1
        elif has_check:
            check_slides += 1

    has_contrast = (x_slides + check_slides + combined_slides) > 0

    if not has_contrast:
        return "single_point"
    if combined_slides > 0 and x_slides == 0 and check_slides == 0:
        return "combined"
    if x_slides > 0 and check_slides > 0 and combined_slides == 0:
        return "split"

    return None


def classify_cta(visual_summary, slide_texts):
    """
    Determine if the carousel has a CTA and classify it.

    Deterministic classifier. Scans last 1-2 slides for CTA signals.

    CTA types: waitlist, website, follow, engage.
    """
    if not slide_texts:
        return None

    last_slide = str(slide_texts[-1]).lower() if slide_texts else ""
    second_last = str(slide_texts[-2]).lower() if len(slide_texts) >= 2 else ""
    cta_zone = last_slide + "\n" + second_last

    has_waitlist = any(w in cta_zone for w in ["waitlist", "wait list", "join the", "sign up"])
    has_url = bool(re.search(r"[a-z0-9\-]+\.[a-z]{2,}", cta_zone))
    has_follow = any(w in cta_zone for w in ["follow us", "follow me", "follow for"])
    has_engage = any(w in cta_zone for w in [
        "save this", "share this", "read more", "read the caption",
        "in the caption", "comment", "tag a friend", "send this",
    ])
    has_travel_local = "travel like a local" in cta_zone

    if not any([has_waitlist, has_url, has_follow, has_engage, has_travel_local]):
        return {"has_cta": 0, "cta_type": None, "cta_text": None}

    cta_text = str(slide_texts[-1]).strip()

    if has_waitlist:
        cta_type = "waitlist"
    elif has_url and not has_engage:
        cta_type = "website"
    elif has_follow:
        cta_type = "follow"
    else:
        cta_type = "engage"

    return {"has_cta": 1, "cta_type": cta_type, "cta_text": cta_text}


def extract_content_topics(visual_summary, slide_texts, description):
    """
    Extract topic tags from the post's content.

    Args:
        visual_summary: describes visual content (scenes, settings, subjects)
        slide_texts: contains category headings with emoji markers
        description: full caption text with topic keywords

    Returns:
        Comma-separated string of lowercase topic tags, or None.
    """
    TOPIC_SIGNALS = {
        "food": ["food", "restaurant", "dining", "dinner", "lunch", "eat", "eats",
                 "cuisine", "menu", "dish", "plate", "meal", "market"],
        "coffee": ["coffee", "cafe", "espresso", "latte", "roast", "barista", "\u2615"],
        "brunch": ["brunch", "breakfast", "pancake", "eggs", "morning meal"],
        "tex-mex": ["tex-mex", "texmex", "mexican", "taco", "burrito", "enchilada",
                    "margarita", "\U0001f32e"],
        "bbq": ["bbq", "barbecue", "brisket", "smoked", "ribs"],
        "pizza": ["pizza", "slice", "pie", "deep dish", "tavern style"],
        "seafood": ["seafood", "fish", "oyster", "crab", "lobster", "sushi"],
        "hot-dogs": ["hot dog", "hot dogs", "hotdog"],
        "italian": ["italian", "pasta", "osteria", "trattoria"],
        "street-food": ["street food", "food truck", "vendor", "cart", "stand"],
        "nightlife": ["nightlife", "bar", "bars", "club", "clubs", "drinks",
                      "cocktail", "dancing", "night out", "late night", "\U0001f378",
                      "\U0001f379"],
        "hikes": ["hike", "hiking", "trail", "trails", "trek", "mountain",
                  "summit", "\U0001f97e"],
        "beach": ["beach", "beaches", "coast", "coastal", "ocean", "shore",
                  "sand", "surf", "pch", "pier", "malibu", "\U0001f3d6", "\U0001f30a"],
        "outdoors": ["outdoors", "outdoor", "nature", "scenic", "wilderness",
                     "camping", "kayak", "paddleboard", "park"],
        "views": ["views", "view", "skyline", "lookout", "overlook", "panorama",
                  "observatory", "sunset", "sunrise", "golden hour", "\U0001f307",
                  "\U0001f306", "\U0001f305"],
        "culture": ["museum", "gallery", "art", "theater", "theatre", "show",
                    "concert", "exhibit", "history", "architecture", "academy",
                    "\U0001f3ac", "\U0001f3a8"],
        "shopping": ["shopping", "shop", "mall", "boutique", "store"],
        "sports": ["sports", "stadium", "arena", "game", "match"],
    }

    if not slide_texts and not description and not visual_summary:
        return None

    # Build combined corpus from all sources
    corpus_parts = []
    if slide_texts:
        if isinstance(slide_texts, list):
            corpus_parts.extend(str(s) for s in slide_texts)
        elif isinstance(slide_texts, str):
            try:
                parsed = json.loads(slide_texts)
                if isinstance(parsed, list):
                    corpus_parts.extend(str(s) for s in parsed)
            except (json.JSONDecodeError, TypeError):
                corpus_parts.append(slide_texts)

    if visual_summary:
        corpus_parts.append(str(visual_summary))

    if description:
        corpus_parts.append(str(description))

    corpus = "\n".join(corpus_parts).lower()

    # Match topics using word boundary regex to avoid substring false positives
    matched = []
    for topic, signals in TOPIC_SIGNALS.items():
        for signal in signals:
            # Use word boundary for single words, plain contains for multi-word/emoji
            if " " in signal or not signal.isascii():
                if signal.lower() in corpus:
                    matched.append(topic)
                    break
            else:
                if re.search(r"\b" + re.escape(signal.lower()) + r"\b", corpus):
                    matched.append(topic)
                    break

    if not matched:
        return None

    # Deduplicate preserving order
    seen = set()
    unique = []
    for t in matched:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return ",".join(unique)


# ---------------------------------------------------------------------------
# Derive batch
# ---------------------------------------------------------------------------

def derive_post(post, frameworks_catalog, conn):
    """
    Run all derivation steps for a single post.
    Returns a result dict with what was derived and any issues.
    """
    slug = post["slug"]
    post_id = post["post_id"]
    needs = post["needs"]
    image_paths = post["image_paths"]
    description = get_description(slug)

    result = {
        "post_id": post_id,
        "slug": slug,
        "derived": {},
        "skipped": [],
        "errors": [],
        "manual_review": [],
    }

    # Step 2 — Transcribe slide texts
    slide_texts = None
    if "slide_texts" in needs:
        slide_texts = transcribe_slide_texts(image_paths)
        if slide_texts is not None:
            slide_texts_json = json.dumps(slide_texts, ensure_ascii=False)
            conn.execute(
                "UPDATE carousel_details SET slide_texts = ? WHERE post_id = ? AND slide_texts IS NULL",
                (slide_texts_json, post_id),
            )
            result["derived"]["slide_texts"] = f"{len(slide_texts)} slides"
        else:
            result["skipped"].append("slide_texts (transcription failed)")
    else:
        # Load existing slide texts
        row = conn.execute("SELECT slide_texts FROM carousel_details WHERE post_id = ?", (post_id,)).fetchone()
        if row and row["slide_texts"]:
            slide_texts = json.loads(row["slide_texts"])

    # Step 3 — Generate visual summary
    visual_summary = None
    if "visual_summary" in needs:
        visual_summary = generate_visual_summary(image_paths)
        if visual_summary is not None:
            conn.execute(
                "UPDATE carousel_details SET visual_summary = ? WHERE post_id = ? AND visual_summary IS NULL",
                (visual_summary, post_id),
            )
            result["derived"]["visual_summary"] = "done"
        else:
            result["skipped"].append("visual_summary (generation failed)")
    else:
        row = conn.execute("SELECT visual_summary FROM carousel_details WHERE post_id = ?", (post_id,)).fetchone()
        if row and row["visual_summary"]:
            visual_summary = row["visual_summary"]

    # Steps 4-7 require slide_texts and visual_summary
    if slide_texts is None or visual_summary is None:
        missing = []
        if slide_texts is None:
            missing.append("slide_texts")
        if visual_summary is None:
            missing.append("visual_summary")
        result["skipped"].append(f"classification steps (missing: {', '.join(missing)})")
        return result

    # Step 4 — Classify framework
    if "framework" in needs:
        fw = classify_framework(visual_summary, slide_texts, frameworks_catalog)
        if fw is not None:
            conn.execute(
                "UPDATE nexus_post_metadata SET framework = ? WHERE post_id = ? AND framework IS NULL",
                (fw, post_id),
            )
            result["derived"]["framework"] = fw
        else:
            result["derived"]["framework"] = "NULL"
            result["manual_review"].append("framework ambiguous")

    # Step 5 — Classify slide layout
    if "slide_layout" in needs:
        sl = classify_slide_layout(visual_summary, slide_texts, frameworks_catalog)
        if sl is not None:
            conn.execute(
                "UPDATE nexus_post_metadata SET slide_layout = ? WHERE post_id = ? AND slide_layout IS NULL",
                (sl, post_id),
            )
            result["derived"]["slide_layout"] = sl
        else:
            result["derived"]["slide_layout"] = "NULL"
            result["manual_review"].append("slide_layout ambiguous")

    # Step 6 — Classify CTA
    if "cta" in needs:
        cta = classify_cta(visual_summary, slide_texts)
        if cta is not None:
            conn.execute(
                """UPDATE carousel_details
                   SET has_cta = ?, cta_type = ?, cta_text = ?
                   WHERE post_id = ? AND has_cta IS NULL""",
                (cta["has_cta"], cta.get("cta_type"), cta.get("cta_text"), post_id),
            )
            if cta["has_cta"]:
                result["derived"]["cta"] = cta["cta_type"]
            else:
                result["derived"]["cta"] = "none"
        else:
            result["skipped"].append("cta (classification failed)")

    # Step 7 — Extract content topics
    if "content_topics" in needs:
        topics = extract_content_topics(visual_summary, slide_texts, description)
        if topics is not None:
            conn.execute(
                "UPDATE posts SET content_topics = ? WHERE post_id = ? AND content_topics IS NULL",
                (topics, post_id),
            )
            result["derived"]["content_topics"] = topics
        else:
            result["skipped"].append("content_topics (extraction failed)")

    return result


def print_batch_summary(batch_num, results):
    """Print batch summary with per-post results."""
    total = len(results)
    print(f"\n--- Batch {batch_num} Complete ({total} posts) ---")

    for r in results:
        slug = r["slug"] or r["post_id"][:16]
        derived_parts = []
        for field, val in r["derived"].items():
            derived_parts.append(f"{field}: {val}")
        derived_str = "  ".join(derived_parts) if derived_parts else "nothing derived"

        print(f"  {slug:40s} {derived_str}")

        if r["skipped"]:
            for s in r["skipped"]:
                print(f"    SKIPPED: {s}")
        if r["errors"]:
            for e in r["errors"]:
                print(f"    ERROR: {e}")

    # Suggested manual review
    manual = [r for r in results if r["manual_review"]]
    if manual:
        print()
        print("Suggested manual review:")
        for r in manual:
            slug = r["slug"] or r["post_id"][:16]
            for item in r["manual_review"]:
                print(f"  {slug}: {item}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def cmd_transcribe(args):
    """CLI handler for: derive_data.py transcribe --post <slug> [--texts '<json>'] [--validate]"""
    post_slug = None
    texts_json = None
    do_validate = "--validate" in args

    if "--post" in args:
        idx = args.index("--post")
        if idx + 1 < len(args):
            post_slug = args[idx + 1]

    if "--texts" in args:
        idx = args.index("--texts")
        if idx + 1 < len(args):
            texts_json = args[idx + 1]

    if not post_slug and not texts_json:
        print("Usage: derive_data.py transcribe --post <slug> [--texts '<json>'] [--validate]",
              file=sys.stderr)
        sys.exit(1)

    # Get slide paths
    if post_slug:
        paths = get_slide_image_paths(post_slug)
        if not paths:
            print(f"ERROR: No slides found for {post_slug}", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(paths)} slides for {post_slug}", file=sys.stderr)

    # If texts provided, validate and format
    if texts_json:
        try:
            texts = json.loads(texts_json)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

        result, error = format_transcription(texts)
        if error:
            print(f"ERROR: {error}", file=sys.stderr)
            sys.exit(1)

        if do_validate and post_slug:
            truth = get_ground_truth(post_slug)
            if truth:
                report = validate_transcription(result["texts"], truth)
                print(json.dumps(report, indent=2))
                return
            else:
                print(f"WARNING: No copy.md found for {post_slug}", file=sys.stderr)

        print(json.dumps(result, indent=2))
        return

    # No texts provided — print prompt and slide paths
    if post_slug:
        paths = get_slide_image_paths(post_slug)
        print(f"\n--- PROMPT ---\n{TRANSCRIBE_PROMPT}", file=sys.stderr)
        print(f"--- SLIDES ---", file=sys.stderr)
        for i, p in enumerate(paths):
            print(f"  Slide {i+1}: {p}", file=sys.stderr)
        print(f"\nThen validate:", file=sys.stderr)
        print(f"  python derive_data.py transcribe --post {post_slug} --texts '<json>' --validate",
              file=sys.stderr)


def main():
    args = sys.argv[1:]

    # Subcommand routing for unit testing
    if args and args[0] == "transcribe":
        cmd_transcribe(args[1:])
        sys.exit(0)
    if args and args[0] in ("--prompt", "prompt"):
        which = args[1] if len(args) > 1 else "all"
        if which in ("transcribe", "1", "all"):
            print("=== TRANSCRIBE_PROMPT ===")
            print(TRANSCRIBE_PROMPT)
        if which in ("visual_summary", "2", "all"):
            print("=== VISUAL_SUMMARY_PROMPT ===")
            print(VISUAL_SUMMARY_PROMPT)
        sys.exit(0)

    triage_only = "--triage-only" in args

    conn = connect()
    result = triage(conn)
    print_triage(result)

    if triage_only or not result["processable"]:
        conn.close()
        sys.exit(0)

    frameworks_catalog = load_frameworks_catalog()
    proc = result["processable"]
    num_batches = math.ceil(len(proc) / BATCH_SIZE)

    all_results = []

    for batch_num in range(1, num_batches + 1):
        start = (batch_num - 1) * BATCH_SIZE
        end = start + BATCH_SIZE
        batch = proc[start:end]

        print(f"\n--- Processing Batch {batch_num}/{num_batches} ---")

        batch_results = []
        for post in batch:
            slug = post["slug"] or post["post_id"][:16]
            print(f"  Deriving: {slug}...")

            try:
                post_result = derive_post(post, frameworks_catalog, conn)
                batch_results.append(post_result)
            except Exception as e:
                print(f"    ERROR: {type(e).__name__}: {e}", file=sys.stderr)
                batch_results.append({
                    "post_id": post["post_id"],
                    "slug": post["slug"],
                    "derived": {},
                    "skipped": [],
                    "errors": [str(e)],
                    "manual_review": [],
                })

        conn.commit()
        print_batch_summary(batch_num, batch_results)
        all_results.extend(batch_results)

        # Check for errors that should stop execution
        has_errors = any(r["errors"] for r in batch_results)
        if has_errors:
            print(f"\nErrors in batch {batch_num}. Stopping for diagnosis.", file=sys.stderr)
            break

    conn.close()

    # Final report
    total_derived = {}
    total_manual = []
    for r in all_results:
        for field in r["derived"]:
            total_derived[field] = total_derived.get(field, 0) + 1
        total_manual.extend(
            {"slug": r["slug"], "item": item} for item in r["manual_review"]
        )

    print(f"\n--- Derive Data Report ---")
    for field, count in total_derived.items():
        print(f"  {field}: {count} derived")
    if total_manual:
        print(f"\nSuggested manual review ({len(total_manual)}):")
        for m in total_manual:
            print(f"  {m['slug']}: {m['item']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
