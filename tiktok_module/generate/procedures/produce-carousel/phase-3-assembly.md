# Phase 3: AI Final Rendering & Assembly

This phase is executed in **Gemini** (Nano Banana 2), not Claude. Claude's role is to generate the prompts (done at the end of Phase 2) and guide the manager through QA. The manager executes the rendering in Gemini.

## Phase 3 Acceptance Criteria

Before final sign-off, the manager should verify:

- [ ] Has Gemini successfully merged the approved text onto the images in a 4:5 aspect ratio?
- [ ] Is the text highly legible, center-aligned, in a bold white sans-serif font with a dark outline/shadow? (Minor generative artifacts in the font are acceptable, but spelling must be 100% accurate.)
- [ ] Has Gemini respected the TikTok safe zones (right margin and bottom 20% clear of text)?
- [ ] Are the ❌ and ✅ icons clearly identifiable? (If Gemini consistently distorts them, omit them from the prompt and add them natively in the TikTok app later.)
- [ ] Are the Nexus logo (Hook and CTA slides) and a swipe arrow (Hook slide) present?
- [ ] Are body slides clean and editorial (no logo, no URL watermark)?

---

## Critical: One Slide Per Turn

**Gemini crashes frequently when asked to render all slides in a single turn.** Even when instructed to render only one slide, Gemini may attempt to render all slides if it has the text for multiple slides in context.

Therefore, Claude must generate **one prompt per slide:**

### Prompt 0 — The Context Prompt (No Rendering)

This prompt establishes the full design system **without requesting any rendering.** It includes:

- All design rules (aspect ratio, typography, safe zones, anti-jumping, branding elements).
- **Reference images** from a previous carousel uploaded as attachments — these show Gemini the target visual style. The manager should upload 2-3 final slides from a previous carousel as visual reference.
- **No raw images for this carousel.** No slide text. No rendering instructions.
- Ends by asking Gemini to **confirm receipt** of the instructions and reference slides.

This ensures Gemini absorbs the design system without attempting to render anything. The manager confirms Gemini's acknowledgment before proceeding.

**Standard Prompt 0 text:**

```
I'm building a TikTok carousel. I'll be sending you slides one at a time. For each, I'll upload one raw image and give you the text to composite onto it. You render one finished slide per message.
The reference images I've uploaded are from a previous carousel — they show the target visual style. Match this style for all slides you render.

Design Rules (Apply to every slide)
Aspect Ratio: Crop or expand the image to exactly 4:5 vertical (1080x1350px).
Font: Bold, sans-serif ("Classic" TikTok font style). White text with a heavy black outline for maximum contrast against any background.
Alignment: All text center-aligned horizontally, placed in the center 60-70% of the image vertically.
Safe Zones: No text in the top 150px, the bottom 20%, or near the right-hand edge.
Anti-Jumping: Keep text at the exact same X/Y coordinates across all slides. Consistency prevents visual jumping when swiping.
Spelling: Must be 100% accurate. Double-check every word.
Branding Rules
All slides are clean and editorial — no logo, no gradient overlays, no watermarks.
The final slide's URL will be rendered in a different color (I'll provide the hex code when we get there). That's the only visual difference across the entire carousel.
Confirm your receipt of these instructions and the reference slides and I will proceed to provide you with the text and image for Slide 1.
```

### Prompt 1 (Slide 1) — First Rendering Prompt

Sent after Gemini confirms receipt of Prompt 0. Includes:

- **Slide 1's raw image** uploaded as an attachment.
- **Only Slide 1's text.** No other slide text.
- Any slide-specific instructions (e.g., Nexus logo, swipe arrow for hook slides).

### Prompts 2-N (Remaining Slides) — Follow-Up Prompts

Each subsequent prompt is sent as a **follow-up message in the same Gemini chat.** It includes:

- The next slide's raw image uploaded as an attachment.
- The next slide's text only.
- Any slide-specific rendering instructions (e.g., "this slide gets the Nexus logo" or "this is a ❌ slide").
- A brief reminder of any rules Gemini may drift from (common: safe zones, anti-jumping, footer watermark).

Each follow-up should be short — Gemini already has the design context from Prompt 1.

### If Gemini Crashes Mid-Session

If Gemini crashes or the chat becomes unresponsive:

1. Open a new Gemini chat.
2. Re-paste Prompt 1 with the reference images and the **next unfinished slide's image** (not Slide 1 unless Slide 1 also needs re-rendering).
3. Continue with follow-up prompts from that point.

The manager does not need to re-render slides that were already successfully completed.

---

## What the Manager Does in This Phase

> **MANAGER ACTION (in Gemini):**
>
> 1. Open Gemini (Advanced/Pro tier recommended).
> 2. Upload 2-3 reference slides from a previous carousel.
> 3. Paste Prompt 0 (the context prompt — no rendering). Wait for Gemini to confirm receipt.
> 4. Upload Slide 1's raw image and paste Prompt 1. Review output. Request corrections if needed.
> 5. For each remaining slide: upload the next raw image and paste the follow-up prompt.
> 6. Review each slide as it's rendered. Request corrections before moving to the next slide.
> 7. Download all final approved images.

## Design Constraints (Included in Gemini Prompts)

These constraints are embedded in the prompts Claude generates, but are listed here for reference:

- **Aspect Ratio:** Crop or expand the background to exactly 4:5 (1080x1350px) for carousel posts.
- **Typography Styling:** Render text in a bold, sans-serif style ("Classic" TikTok font). The text must be white with a heavy black outline OR a subtle 15-20% dark gradient/drop-shadow behind the text for maximum contrast.
- **Anti-Jumping:** Keep text placement as consistent as possible across all slides (exact X/Y coordinates) to prevent visual jumping when swiping.
- **Safe Zones:** Center the text. Ensure no text bleeds into the bottom 20% or the right-hand edge.

## Slide-Specific Additions

- **Hook Slide (Slide 1):** Clean — no logo, no URL. Add a subtle visual cue (like a small arrow pointing right) prompting the user to swipe.
- **Body Slides (all body slides):** Clean and editorial. No logo, no URL watermark. Content builds trust; branding comes at the end.
- **Product / CTA Slide(s):** Visually consistent with body slides — same text-on-photo, no logo, no gradient overlay. Only visual shift: render the URL in cyan (`#00E4DA`) with black outline instead of white. The copy does the converting, not the design.

## What Claude Does in This Phase

Claude is on standby. If the manager returns with issues from Gemini rendering (e.g., text too long to fit, emoji distortion, spelling errors), Claude can:

- Suggest shortened text alternatives that preserve the meaning.
- Recommend dropping emojis from the prompt and adding them in TikTok natively.
- Regenerate individual slide prompts with adjustments.

## Manager Review Gate 3

When the manager is satisfied with all rendered images:

> **MANAGER ACTION:**
>
> 1. Download the final images from Gemini.
> 2. Save them to the carousel's `slides/` directory (e.g., `posts/city-yyyy-mm-dd/slides/`).

## Phase 4 Handoff

Once images are saved, generate the ChatGPT prompt for Phase 4 (title, caption, and hashtags). The prompt should include:

- The full approved slide text from `copy.md`.
- The city and framework context.
- Any meta-tips or bonus advice that didn't fit on the slides — these are ideal caption content.
- Instructions for ChatGPT to generate a single best recommendation with title, emoji-rich caption (2-3+ sentences), and 5-10 hashtags.

Tell the manager: *"Images are done and saved. Here is the prompt to paste into ChatGPT to generate your title, caption, and hashtags. Review the output, revise if needed, and save the result to `caption.md` in the carousel directory. Then proceed to posting."*

> **MANAGER ACTION:** Copy the ChatGPT prompt. Open ChatGPT, paste it, review output, save to `caption.md`. Proceed to posting per Phase 4.
