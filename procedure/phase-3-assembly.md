# Phase 3: AI Final Rendering & Assembly

This phase is executed in **Gemini** (Nano Banana 2), not Claude. Claude's role is to generate the prompt (done at the end of Phase 2) and guide the manager through QA. The manager executes the rendering in Gemini.

## Phase 3 Acceptance Criteria

Before final sign-off, the manager should verify:

- [ ] Has Gemini successfully merged the approved text onto the images in a 9:16 aspect ratio?
- [ ] Is the text highly legible, center-aligned, in a bold white sans-serif font with a dark outline/shadow? (Minor generative artifacts in the font are acceptable, but spelling must be 100% accurate.)
- [ ] Has Gemini respected the TikTok safe zones (right margin and bottom 20% clear of text)?
- [ ] Are the ❌ and ✅ icons clearly identifiable? (If Gemini consistently distorts them, omit them from the prompt and add them natively in the TikTok app later.)
- [ ] Are the Nexus logo (Hook and CTA slides) and a swipe arrow (Hook slide) present?

---

## What the Manager Does in This Phase

> **MANAGER ACTION (in Gemini):**
>
> 1. Open Gemini (Advanced/Pro tier recommended).
> 2. Upload the renamed image files from Phase 2.
> 3. Paste the rendering prompt Claude generated at the end of Phase 2.
> 4. Review the rendered images Gemini produces.
> 5. If any slides need re-rendering (typos, bad placement, safe zone violations), request corrections in Gemini.
> 6. Download the final approved images.

## Design Constraints (Included in Gemini Prompt)

These constraints are embedded in the prompt Claude generates, but are listed here for reference:

- **Aspect Ratio:** Crop or expand the background to exactly 9:16 (Vertical).
- **Typography Styling:** Render text in a bold, sans-serif style ("Classic" TikTok font). The text must be white with a heavy black outline OR a subtle 15-20% dark gradient/drop-shadow behind the text for maximum contrast.
- **Anti-Jumping:** Keep text placement as consistent as possible across all slides (exact X/Y coordinates) to prevent visual jumping when swiping.
- **Safe Zones:** Center the text. Ensure no text bleeds into the bottom 20% or the right-hand edge.

## Slide-Specific Additions

- **Hook Slide (Slide 1):** Integrate the Nexus logo clearly. Add a subtle visual cue (like a small arrow pointing right) prompting the user to swipe.
- **CTA Slide (Final Slide):** Integrate the Nexus logo clearly alongside the final text.

## What Claude Does in This Phase

Claude is on standby. If the manager returns with issues from Gemini rendering (e.g., text too long to fit, emoji distortion, spelling errors), Claude can:

- Suggest shortened text alternatives that preserve the meaning.
- Recommend dropping emojis from the prompt and adding them in TikTok natively.
- Regenerate the Gemini prompt with adjustments.

## Manager Review Gate 3

When the manager is satisfied with the rendered images:

> **MANAGER ACTION:**
>
> 1. Download the final images from Gemini.
> 2. Save them to the carousel's `final-slides/` directory (e.g., `resulting-tiktoks/[City]_[Date]/final-slides/`).
> 3. Send the images to your mobile device.
> 4. Upload to TikTok as a carousel, apply trending audio, and post.

Tell the manager: *"Procedure complete. Once posted, update the carousel's README.md with the post date and check back to add view counts and performance notes."*

---

**Procedure Complete.** The files are now ready for manual upload to TikTok (where trending audio and captions will be applied).
