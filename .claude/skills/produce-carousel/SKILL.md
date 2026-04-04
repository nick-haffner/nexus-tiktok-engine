---
name: produce-carousel
description: "Produce a TikTok carousel from ideation through posting. Reads and executes Phase 0 (ideation), Phase 1 (copy), Phase 2 (images), Phase 3 (assembly), and Phase 4 (posting) from the tiktok_module/procedures/produce-carousel/ directory."
---

# Produce Carousel

## Arguments

- **`--cta`** (optional): Controls CTA behavior. Accepted values:
  - `none` — No CTA slide. Carousel ends on the last content slide.
  - `follow` — **Default when `--cta` is omitted.** Follow CTA slide appended to the carousel.
  - `campaign <name>` — Campaign conversion CTA. Loads campaign-specific guidance from `tiktok_module/store/data/strategy/campaigns/<name>.md`. Errors if the campaign file does not exist.

**Examples:**
```
/produce-carousel                          → follow CTA (default)
/produce-carousel --cta none               → no CTA
/produce-carousel --cta campaign waitlist   → campaign CTA, loads waitlist.md
```

## Procedure

### Pre-phase: CTA Strategy Loading

1. Parse the `--cta` argument. If omitted, set CTA type to `follow`.
2. Read `tiktok_module/store/data/strategy/cta-strategy.md` (unless CTA type is `none`).
3. If CTA type is `campaign`: read `tiktok_module/store/data/strategy/campaigns/<name>.md`. If the file does not exist, stop and tell the manager.
4. Carry the CTA type (and campaign context if applicable) through all phases.

### Phases

Read `tiktok_module/generate/procedures/produce-carousel/overview.md` for the tool stack and acceptance criteria, then read `tiktok_module/generate/procedures/produce-carousel/brand-rules.md` for rendering specs.

Execute the phases in order:

1. Read `tiktok_module/generate/procedures/produce-carousel/phase-0-ideation.md` and execute it. Present concept options to the manager for approval before proceeding.
2. Read `tiktok_module/generate/procedures/produce-carousel/phase-1-copy.md` and execute it. Present copy for approval before proceeding.
3. Read `tiktok_module/generate/procedures/produce-carousel/phase-2-images.md` and execute it. Generate the ChatGPT/Perplexity prompt for the manager to run externally.
4. Read `tiktok_module/generate/procedures/produce-carousel/phase-3-assembly.md` and execute it. Generate the Gemini prompt for the manager to run externally.
5. Read `tiktok_module/generate/procedures/produce-carousel/phase-4-posting.md` and execute it.

Each phase's procedure is self-contained — follow it as written. Always present options and let the manager choose at approval gates.
