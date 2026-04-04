"""
Derive data unit implementations — staging file.

Contains tested implementations for derive_data.py units.
Once tested, these are integrated into derive_data.py by the IDE instance.

Units implemented here:
    1. transcribe_slide_texts   — stored prompt + format/validate
    2. generate_visual_summary  — stored prompt + format/validate
    3. classify_framework       — deterministic classifier
    4. classify_slide_layout    — deterministic classifier
    5. classify_cta             — deterministic classifier
    6. extract_content_topics   — signal-based extractor (IDE implemented)
"""

import json
import os
import re
import sys

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
POSTS_DIR = os.path.join(MODULE_ROOT, "store", "data", "posts")
FRAMEWORKS_PATH = os.path.join(MODULE_ROOT, "store", "data", "strategy", "frameworks.md")


def get_slide_image_paths(slug):
    """Return sorted list of slide image paths for a post."""
    slides_dir = os.path.join(POSTS_DIR, slug, "slides")
    if not os.path.isdir(slides_dir):
        return []
    files = []
    for f in os.listdir(slides_dir):
        match = re.match(r"Slide (\d+)\.(jpeg|jpg|png|webp)$", f, re.IGNORECASE)
        if match:
            files.append((int(match.group(1)), os.path.join(slides_dir, f)))
    files.sort(key=lambda x: x[0])
    return [path for _, path in files]


def get_ground_truth(slug):
    """Extract slide texts from copy.md as ground truth for validation."""
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


# ---------------------------------------------------------------------------
# Unit 1: transcribe_slide_texts
# ---------------------------------------------------------------------------

TRANSCRIBE_PROMPT = """Read each slide image and extract ALL visible text exactly as displayed.

Rules:
- Capture text verbatim including capitalization and line breaks.
- Include all emojis as they appear (❌, ✅, ☕, 🌮, 🌅, 🌆, 🍽, 🌙, 🥾, 🔭, 🌊, 🎬, etc.).
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
Example: ["Hook text here", "🌅 Morning\\nWasted ❌\\nHollywood Walk of Fame.", "", "CTA text"]
"""


def format_transcription(slide_texts):
    """
    Validate and format slide text transcriptions.

    Input: list of strings — one per slide, as produced by following TRANSCRIBE_PROMPT.
    Returns: (result_dict, error_string_or_None)
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


def validate_transcription(slide_texts, ground_truth):
    """Compare transcribed slide texts against ground truth from copy.md."""
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


# ---------------------------------------------------------------------------
# Unit 2: generate_visual_summary
# ---------------------------------------------------------------------------

VISUAL_SUMMARY_PROMPT = """Look at ALL slide images for this carousel as a set and produce a factual
description of the visual properties. Read every slide before writing.

Describe each of the following:

1. TEXT STYLE: Font weight, color, outline/shadow treatment. Are text overlays
   consistent across slides or do they change? Note any color-coded text
   (e.g., red for negative, green for positive, cyan for URLs).

2. LAYOUT PROGRESSION: How does content flow across slides? Is there an
   alternating pattern (e.g., ❌ then ✅)? Does each slide stand alone or do
   consecutive slides form pairs? Does the first slide differ (hook) or the
   last slide differ (CTA)?

3. PHOTO BACKGROUNDS: What subjects appear in the photos? (cityscapes, food,
   trails, interiors, crowds, etc.) Are photos location-specific or generic?

4. STRUCTURAL ELEMENTS: Are there category headings with emoji markers? Time
   blocks? Numbered lists? Section dividers?

5. BRANDING: Does a logo appear? On which slides? Is a URL displayed? What
   color/font is the URL?

6. SLIDE COUNT AND DIMENSIONS: How many slides? Portrait or landscape?

Output: 1-2 paragraphs of factual description. Do NOT evaluate quality or
suggest improvements. Describe only what is visually present.
"""


def format_visual_summary(summary_text):
    """
    Validate and format a visual summary.

    Input: string (1-2 paragraphs) produced by following VISUAL_SUMMARY_PROMPT.
    Returns: (summary_string, error_string_or_None)
    """
    if not summary_text or not isinstance(summary_text, str):
        return None, "Visual summary must be a non-empty string"
    text = summary_text.strip()
    if len(text) < 50:
        return None, f"Visual summary too short ({len(text)} chars, minimum 50)"
    return text, None


# ---------------------------------------------------------------------------
# Unit 3: classify_framework
# ---------------------------------------------------------------------------

def classify_framework(visual_summary, slide_texts, frameworks_catalog):
    """
    Classify which framework a carousel uses.

    This is a procedure for Claude to execute. Claude reads the visual summary,
    slide texts, and frameworks catalog, then determines the framework.

    Classification rules (from visual signatures):
        local_vs_tourist: Alternating ❌/✅ slides with "Tourist"/"Local" headings.
            Contrast pairs comparing tourist traps vs local alternatives.
        worth_it: List of recommended spots, each with emoji category marker
            (🥾, 🔭, 🌊, 🎬, etc.). No contrast pairs. Single recommendation per slide.
        the_24_hour_test: Time-block progression (Morning, Afternoon, Evening, Dinner,
            Late Night) with alternating ❌ Wasted / ✅ Local pairs per time block.
        overrated_vs_underrated: Similar to local_vs_tourist but framed as
            "Overrated"/"Underrated" rather than "Tourist"/"Local".

    Args:
        visual_summary: string from generate_visual_summary
        slide_texts: list of strings from transcribe_slide_texts
        frameworks_catalog: content of frameworks.md

    Returns: framework string or None if ambiguous.
    """
    if not slide_texts or not visual_summary:
        return None

    texts_combined = "\n".join(str(s) for s in slide_texts).lower()

    # Signal detection
    has_tourist_local = ("tourist" in texts_combined and "local" in texts_combined)
    has_wasted_local = ("wasted" in texts_combined and "local" in texts_combined)
    has_overrated_underrated = ("overrated" in texts_combined and "underrated" in texts_combined)
    has_time_blocks = any(t in texts_combined for t in ["morning", "afternoon", "evening", "late night", "dinner"])
    has_contrast_markers = ("❌" in texts_combined or "\u274c" in texts_combined) and ("✅" in texts_combined or "\u2705" in texts_combined)
    has_worth_it = "worth it" in texts_combined or "worth your time" in texts_combined
    has_category_emojis = bool(re.search(r"[🥾🔭🌊🎬☕🌮🏔️🎭🏖️🎵]", texts_combined))

    # Time-block progression with wasted/local pairs → the_24_hour_test
    if has_time_blocks and has_wasted_local and has_contrast_markers:
        return "the_24_hour_test"

    # Overrated/underrated framing → overrated_vs_underrated
    if has_overrated_underrated and has_contrast_markers:
        return "overrated_vs_underrated"

    # Tourist/local contrast pairs without time blocks → local_vs_tourist
    if has_tourist_local and has_contrast_markers and not has_time_blocks:
        return "local_vs_tourist"

    # List of spots with category emojis, no contrast → worth_it
    if has_category_emojis and not has_contrast_markers:
        return "worth_it"

    # Worth-it language without category emojis
    if has_worth_it and not has_contrast_markers:
        return "worth_it"

    # Ambiguous
    return None


# ---------------------------------------------------------------------------
# Unit 4: classify_slide_layout
# ---------------------------------------------------------------------------

def classify_slide_layout(visual_summary, slide_texts, layouts_catalog):
    """
    Classify how content is arranged across slides.

    Classification rules:
        split: Contrast pairs occupy separate consecutive slides. Each slide is
            either ❌ or ✅. Slides alternate (❌, ✅, ❌, ✅...).
        combined: Each slide contains both the ❌ and ✅ content for one category.
            The contrast is within a single slide, not across two.
        single_point: Each slide stands alone with one recommendation. No contrast
            pairs. Typical of worth_it framework.

    Args:
        visual_summary: string from generate_visual_summary
        slide_texts: list of strings from transcribe_slide_texts
        layouts_catalog: content of frameworks.md

    Returns: layout string or None if ambiguous.
    """
    if not slide_texts:
        return None

    # Count slides with contrast markers
    x_slides = 0
    check_slides = 0
    combined_slides = 0

    for text in slide_texts:
        t = str(text)
        has_x = "❌" in t or "\u274c" in t
        has_check = "✅" in t or "\u2705" in t

        if has_x and has_check:
            combined_slides += 1
        elif has_x:
            x_slides += 1
        elif has_check:
            check_slides += 1

    has_contrast = (x_slides + check_slides + combined_slides) > 0

    # No contrast markers at all → single_point
    if not has_contrast:
        return "single_point"

    # Both markers in same slides → combined
    if combined_slides > 0 and x_slides == 0 and check_slides == 0:
        return "combined"

    # Markers on separate slides → split
    if x_slides > 0 and check_slides > 0 and combined_slides == 0:
        return "split"

    # Mixed (some combined, some split) — ambiguous
    return None


# ---------------------------------------------------------------------------
# Unit 5: classify_cta
# ---------------------------------------------------------------------------

def classify_cta(visual_summary, slide_texts):
    """
    Determine if the carousel has a CTA and classify it.

    CTA types:
        waitlist: join/sign up/waitlist language, URL present
        website: URL reference without waitlist language
        follow: follow request
        engage: save/share/comment/read caption language
        None: no CTA detected

    Checks all slides but focuses on the last 1-2 slides where CTAs typically appear.

    Args:
        visual_summary: full visual summary string
        slide_texts: list of strings from transcribe_slide_texts

    Returns: dict with has_cta, cta_type, cta_text — or None on failure.
    """
    if not slide_texts:
        return None

    # Check all slides for CTA signals, weighted toward the end
    all_text = "\n".join(str(s) for s in slide_texts).lower()
    last_slide = str(slide_texts[-1]).lower() if slide_texts else ""
    second_last = str(slide_texts[-2]).lower() if len(slide_texts) >= 2 else ""
    cta_zone = last_slide + "\n" + second_last

    # CTA signal detection
    has_waitlist = any(w in cta_zone for w in ["waitlist", "wait list", "join the", "sign up"])
    has_url = bool(re.search(r"[a-z0-9\-]+\.[a-z]{2,}", cta_zone))
    has_follow = any(w in cta_zone for w in ["follow us", "follow me", "follow for"])
    has_engage = any(w in cta_zone for w in [
        "save this", "share this", "read more", "read the caption",
        "in the caption", "comment", "tag a friend", "send this",
    ])
    has_travel_local = "travel like a local" in cta_zone

    # No CTA signals at all
    if not any([has_waitlist, has_url, has_follow, has_engage, has_travel_local]):
        return {"has_cta": 0, "cta_type": None, "cta_text": None}

    # Extract CTA text (last slide typically)
    cta_text = str(slide_texts[-1]).strip()

    # Classify type
    if has_waitlist:
        cta_type = "waitlist"
    elif has_url and not has_engage:
        cta_type = "website"
    elif has_follow:
        cta_type = "follow"
    else:
        cta_type = "engage"

    return {"has_cta": 1, "cta_type": cta_type, "cta_text": cta_text}


# ---------------------------------------------------------------------------
# Unit 7: extract_city
# ---------------------------------------------------------------------------

def extract_city(description=None, slide_texts=None, visual_summary=None, hashtags=None):
    """
    Extract the primary city from post content.

    Uses all available content sources to identify the city. More sources
    = higher confidence. When multiple cities appear (e.g., "LA" in slide
    text but "Rome" in description), the function counts mentions across
    all sources and returns the city with the most signals.

    Args:
        description: full caption text
        slide_texts: list of slide text strings or JSON string
        visual_summary: visual description of the slides
        hashtags: comma-separated hashtag string

    Returns:
        Canonical city name string (e.g., "Dallas", "Los Angeles") or None.
    """
    CITY_ALIASES = {
        "Rome": ["rome", "eternal city"],
        "Los Angeles": ["los angeles", " in la", " la ", " la.", " la?", "la's",
                        "la!", "la,", "l.a.", "l.a"],
        "Salt Lake City": ["salt lake city", "salt lake", "slc"],
        "San Francisco": ["san francisco", "sf "],
        "New York": ["new york", "nyc", "new york city"],
        "North Bend": ["north bend"],
        "Tri-Cities": ["tri-cities", "tri cities", "tricities"],
        "Fort Worth": ["fort worth"],
        "West Coast": ["west coast"],
        "Nashville": ["nashville"],
        "Scottsdale": ["scottsdale"],
        "Seattle": ["seattle"],
        "Phoenix": ["phoenix"],
        "Chicago": ["chicago"],
        "Dallas": ["dallas"],
        "Austin": ["austin"],
        "Denver": ["denver"],
        "Denali": ["denali"],
        "Miami": ["miami"],
    }

    if not any([description, slide_texts, visual_summary, hashtags]):
        return None

    # Build weighted corpus — description and hashtags are strongest signals
    # (author's explicit labeling), visual summary and slide texts are supporting
    sources = {
        "description": "",
        "hashtags": "",
        "visual_summary": "",
        "slide_texts": "",
    }

    if description:
        sources["description"] = description.lower()

    if hashtags:
        # Expand hashtags — "dallaseats" should match "dallas"
        sources["hashtags"] = " ".join(h.lower() for h in hashtags.split(","))

    if visual_summary:
        sources["visual_summary"] = visual_summary.lower()

    if slide_texts:
        if isinstance(slide_texts, list):
            sources["slide_texts"] = "\n".join(str(s) for s in slide_texts).lower()
        elif isinstance(slide_texts, str):
            try:
                parsed = json.loads(slide_texts)
                if isinstance(parsed, list):
                    sources["slide_texts"] = "\n".join(str(s) for s in parsed).lower()
            except (json.JSONDecodeError, TypeError):
                sources["slide_texts"] = slide_texts.lower()

    # Count city signals across sources, weighted by source reliability
    WEIGHTS = {"description": 3, "hashtags": 2, "visual_summary": 1, "slide_texts": 1}
    city_scores = {}

    for city, aliases in CITY_ALIASES.items():
        score = 0
        for source_name, text in sources.items():
            if not text:
                continue
            for alias in aliases:
                if alias in text:
                    score += WEIGHTS[source_name]
                    break  # One match per source per city
        if score > 0:
            city_scores[city] = score

    if not city_scores:
        return None

    # Return the highest-scoring city
    return max(city_scores, key=city_scores.get)


# ---------------------------------------------------------------------------
# Unit 6: extract_content_topics
# ---------------------------------------------------------------------------

def extract_content_topics(visual_summary, slide_texts, description):
    """
    Extract topic tags from the post's content.

    Args:
        visual_summary: describes visual content (scenes, settings, subjects)
        slide_texts: list of strings from transcribe_slide_texts
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
        "street-food": ["street food", "food truck", "vendor"],
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

    matched = []
    for topic, signals in TOPIC_SIGNALS.items():
        for signal in signals:
            # Word boundary for single words, plain contains for multi-word/emoji
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

    seen = set()
    unique = []
    for t in matched:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return ",".join(unique)


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage:")
        print("  derive_units.py transcribe --post <slug> [--texts '<json>'] [--validate]")
        print("  derive_units.py transcribe --prompt")
        print("  derive_units.py visual_summary --post <slug> [--summary '<text>']")
        print("  derive_units.py visual_summary --prompt")
        print("  derive_units.py framework --texts '<json>' --summary '<text>'")
        print("  derive_units.py layout --texts '<json>' --summary '<text>'")
        print("  derive_units.py cta --texts '<json>' --summary '<text>'")
        print("  derive_units.py topics --texts '<json>' [--summary '<text>'] [--description '<text>']")
        sys.exit(0)

    command = args[0]
    rest = args[1:]

    def get_arg(flag):
        if flag in rest:
            idx = rest.index(flag)
            if idx + 1 < len(rest):
                return rest[idx + 1]
        return None

    if command == "transcribe":
        # --prompt: print the stored prompt
        if "--prompt" in rest:
            print(TRANSCRIBE_PROMPT)
            sys.exit(0)

        slug = get_arg("--post")
        texts_json = get_arg("--texts")
        do_validate = "--validate" in rest

        if not slug:
            print("ERROR: --post <slug> required", file=sys.stderr)
            sys.exit(1)

        paths = get_slide_image_paths(slug)
        if not paths:
            print(f"ERROR: No slides found for {slug}", file=sys.stderr)
            sys.exit(1)

        if texts_json:
            texts = json.loads(texts_json)
            result, error = format_transcription(texts)
            if error:
                print(f"ERROR: {error}", file=sys.stderr)
                sys.exit(1)

            if do_validate:
                truth = get_ground_truth(slug)
                if truth:
                    report = validate_transcription(result["texts"], truth)
                    print(json.dumps(report, indent=2))
                    sys.exit(0)
                else:
                    print(f"WARNING: No copy.md for {slug}", file=sys.stderr)

            print(json.dumps(result, indent=2))
        else:
            # No texts — print prompt and slide paths
            print(f"Found {len(paths)} slides for {slug}", file=sys.stderr)
            print(f"\n--- PROMPT ---\n{TRANSCRIBE_PROMPT}", file=sys.stderr)
            print(f"--- SLIDES ---", file=sys.stderr)
            for i, p in enumerate(paths):
                print(f"  Slide {i+1}: {p}", file=sys.stderr)
            print(f"\nThen validate:", file=sys.stderr)
            print(f"  python derive_units.py transcribe --post {slug} --texts '<json>' --validate",
                  file=sys.stderr)
        sys.exit(0)

    elif command == "visual_summary":
        # --prompt: print the stored prompt
        if "--prompt" in rest:
            print(VISUAL_SUMMARY_PROMPT)
            sys.exit(0)

        slug = get_arg("--post")
        summary = get_arg("--summary")

        if summary:
            result, error = format_visual_summary(summary)
            if error:
                print(f"ERROR: {error}", file=sys.stderr)
                sys.exit(1)
            print(result)
        elif slug:
            paths = get_slide_image_paths(slug)
            if not paths:
                print(f"ERROR: No slides found for {slug}", file=sys.stderr)
                sys.exit(1)
            print(f"Found {len(paths)} slides for {slug}", file=sys.stderr)
            print(f"\n--- PROMPT ---\n{VISUAL_SUMMARY_PROMPT}", file=sys.stderr)
            print(f"--- SLIDES ---", file=sys.stderr)
            for i, p in enumerate(paths):
                print(f"  Slide {i+1}: {p}", file=sys.stderr)
            print(f"\nThen format:", file=sys.stderr)
            print(f"  python derive_units.py visual_summary --summary '<text>'", file=sys.stderr)
        else:
            print("ERROR: --post <slug> or --summary required", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    elif command == "framework":
        texts_json = get_arg("--texts")
        summary = get_arg("--summary") or ""
        catalog = ""
        if os.path.exists(FRAMEWORKS_PATH):
            with open(FRAMEWORKS_PATH, "r", encoding="utf-8") as f:
                catalog = f.read()

        if texts_json:
            texts = json.loads(texts_json)
            result = classify_framework(summary, texts, catalog)
            print(json.dumps({"framework": result}))
        else:
            print("ERROR: --texts required", file=sys.stderr)
            sys.exit(1)

    elif command == "layout":
        texts_json = get_arg("--texts")
        summary = get_arg("--summary") or ""

        if texts_json:
            texts = json.loads(texts_json)
            result = classify_slide_layout(summary, texts, "")
            print(json.dumps({"slide_layout": result}))
        else:
            print("ERROR: --texts required", file=sys.stderr)
            sys.exit(1)

    elif command == "cta":
        texts_json = get_arg("--texts")
        summary = get_arg("--summary") or ""

        if texts_json:
            texts = json.loads(texts_json)
            result = classify_cta(summary, texts)
            print(json.dumps(result, indent=2))
        else:
            print("ERROR: --texts required", file=sys.stderr)
            sys.exit(1)

    elif command == "topics":
        texts_json = get_arg("--texts")
        summary = get_arg("--summary") or ""
        desc = get_arg("--description") or ""

        if texts_json:
            texts = json.loads(texts_json)
            result = extract_content_topics(summary, texts, desc)
            print(json.dumps({"content_topics": result}))
        else:
            print("ERROR: --texts required", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
