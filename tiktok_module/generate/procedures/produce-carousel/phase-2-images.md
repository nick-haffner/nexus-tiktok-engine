# Phase 2: AI Visual Sourcing & Selection

This phase is executed in **ChatGPT** (or Perplexity), not Claude. Claude's role here is to generate the prompt and guide the manager through the process. The manager executes the image sourcing in the external tool.

## Phase 2 Acceptance Criteria

Before proceeding to Phase 3, the manager should verify:

- [ ] Are there 3-4 distinct, real image options presented for every slide?
- [ ] Are the images geographically accurate (no AI-generated fake landmarks or incorrect storefronts)?
- [ ] Are the images portrait-friendly (can be cropped to 9:16 vertical)?
- [ ] Do the images look authentic and user-generated rather than overly polished stock?

---

## What Claude Does in This Phase

Claude has already generated the ChatGPT prompt during the Phase 1 handoff. If the manager needs the prompt regenerated or adjusted, do so. Otherwise, Claude is on standby.

If the manager returns with questions about image selection (e.g., "which of these two would render better?"), advise based on:
- Which image has more visual contrast with the text overlay area.
- Which image better reinforces the slide's message.
- Which image is more clearly portrait-friendly.

## What the Manager Does in This Phase

> **MANAGER ACTION (in ChatGPT):**
>
> 1. Open ChatGPT with web search enabled (Plus/Team/Enterprise tier).
> 2. Paste the prompt Claude generated at the end of Phase 1.
> 3. Review the image options ChatGPT presents for each slide.
> 4. Right-click and save the selected images to a local folder.
> 5. **Rename the files sequentially** (e.g., Slide1.jpg, Slide2.jpg, Slide3.jpg) so Gemini applies the correct text in Phase 3.
> 6. Save the raw images to the carousel's `raw-images/` directory.

## Sourcing Rules (Included in ChatGPT Prompt)

These rules are embedded in the prompt Claude generates, but are listed here for reference:

- **Hook & CTA Slides:** Iconic, aesthetic establishing shots of the city (skylines, golden hour landmarks).
- **For contrast frameworks:** Source images that visually reinforce the contrast — crowded/chaotic for the trap, inviting/authentic for the local pick.
- **For recommendation frameworks:** Source images that make each spot look appealing and authentic.
- **Generative AI Ban:** Do NOT use generative AI (DALL-E, Midjourney, etc.) to create images of specific local businesses or real-world landmarks.
- Prioritize user-generated style photos from Google Maps/Yelp over polished stock.

## Manager Review Gate 2

When the manager returns, they should confirm: **"Images Selected and Downloaded."**

Claude then proceeds to generate the Gemini prompt for Phase 3. Tell the manager:

*"Great. Now open a new Gemini chat (Advanced/Pro tier recommended). Upload the renamed image files and paste the prompt below. Gemini will composite the approved text onto the images following our typography and safe zone rules."*

Generate the Gemini prompt. It should include:
- The full approved slide text from `copy.md`.
- The complete visual identity and rendering rules from [brand-rules.md](brand-rules.md) (typography, safe zones, anti-jumping) and branding philosophy from [brand-voice.md](../../data/strategy/brand-voice.md).
- Explicit instructions for Gemini to composite the text onto the uploaded images in slide order.
- A reminder that spelling must be 100% accurate and that the ❌/✅ emojis should be rendered clearly (or omitted if they consistently distort).

> **MANAGER ACTION:** Copy the Gemini prompt. Open Gemini, upload the images, paste the prompt. Proceed to Phase 3.
