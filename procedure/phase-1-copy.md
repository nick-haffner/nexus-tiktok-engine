# Phase 1: Copywriting & Flow Mapping

You are Claude, writing the exact slide text for the approved concept. The goal is to lock in copy for every slide in a structured format before sourcing images. Refer to [brand-rules.md](brand-rules.md) for voice, tone, and text density guidelines.

## Phase 1 Acceptance Criteria

Before presenting to the manager for approval, verify:

- [ ] Does the output contain exactly 1 Hook, the planned body slides, and 1 CTA slide?
- [ ] Does every body slide have the content required by the chosen framework?
- [ ] Is the text short enough to render legibly in the TikTok safe zone? (Aim for 2 short lines per point; 3 is acceptable; 4 needs editing.)
- [ ] Is the output formatted in a clean Markdown layout for easy reading?
- [ ] Have you flagged any slides where text density may cause Phase 3 rendering issues?

---

## Step 1.1 — Adopt the Voice

Write in the Nexus brand voice: authoritative, slightly snarky about tourist traps, fiercely loyal to local gems, and concise. Adapt the tone to the chosen framework — a "Worth It" carousel is more positive and celebratory; a "Local vs Tourist" carousel is more contrarian.

## Step 1.2 — The Hook Slide (Present Options)

The hook is the most important slide for performance — it determines whether someone stops scrolling.

Draft **2-3 hook options** with different framings. For example:
- A direct contrast hook: "Local vs Tourist in Austin 🤩"
- A curiosity hook: "Austin spots that are actually worth it ✨"
- A bold claim hook: "Stop doing Austin wrong"

Present all options to the manager and recommend your top pick with a brief reason.

> **MANAGER ACTION:** Select a hook option, or request a different direction.

## Step 1.3 — The Body Slides

Write the body slide text for the approved outline. Adapt the structure to the chosen framework:

**For contrast frameworks (Local vs Tourist, Overrated vs Underrated):**
- Category header with a relevant emoji (e.g., ☕️ Coffee, 🌮 Tex-Mex).
- The "trap" side: Name + 1-2 short lines explaining why to skip it.
- The "pick" side: Name + 1-2 short lines explaining why it's better.
- Use ❌ and ✅ icons to visually mark the contrast.

**For recommendation frameworks (Worth It, curated lists):**
- Location or category header.
- 1-3 short lines selling the recommendation.
- No contrast needed — each slide stands on its own.

**For any new/wildcard framework:**
- Adapt the structure to fit. The key constraint is that every slide must have a clear visual purpose and text that fits the rendering rules.

If you see an alternative angle or a stronger take for any body slide, call it out as an option rather than silently choosing one path.

## Step 1.4 — The CTA Slide

Write the closing slide text. The standard is: **"Travel like a local. Read more in the caption."** Variations are acceptable — match the energy of the carousel (e.g., "Plan your next trip with Nexus").

## Step 1.5 — Renderability Check

Before presenting to the manager, review every slide and flag any where:
- Text might be too dense to render cleanly at the target font size.
- The text-to-image mapping is ambiguous (Gemini won't know what to overlay where).
- Emoji or special characters might distort during Phase 3 rendering.

Note these flags alongside the draft so the manager is aware.

## Step 1.6 — Output Generation

Output the complete slide text in a clean Markdown format. Use the same structure as the `copy.md` files in `sample-tiktoks/` for consistency.

## Manager Review Gate 1

Present the drafted text to the manager.

Tell the manager: *"Here is the complete slide text. Please review for tone, accuracy, and anything you'd change. Once approved, I'll generate the prompt for ChatGPT to begin Phase 2 image sourcing. Reply with 'Approved' or let me know what to revise."*

> **MANAGER ACTION:** Review the slide text. Request revisions or reply with **"Approved."**

## Phase 2 Handoff

Once the manager approves, do the following:

1. **Write `copy.md` directly** to the carousel's directory (e.g., `resulting-tiktoks/[City]_[Date]/copy.md`). Use the same Markdown structure as the `copy.md` files in `sample-tiktoks/`. Update the slide count in the carousel's `README.md`.

2. **Generate the ChatGPT prompt.** Produce a ready-to-paste prompt for the manager to use in ChatGPT for Phase 2 image sourcing. The prompt should include:
   - The full approved slide text.
   - The image sourcing rules from [brand-rules.md](brand-rules.md).
   - Instructions for ChatGPT to present 3-4 image options per slide.

3. Tell the manager: *"Copy is approved and saved to `copy.md`. Here is the prompt to paste into ChatGPT to begin Phase 2. Open ChatGPT with web search enabled, paste the prompt below, and review the image options it presents. Once you've selected and downloaded your images, rename them sequentially (Slide1.jpg, Slide2.jpg, etc.) and save them to the `raw-images/` folder in the carousel directory. Then come back here and I'll generate the Gemini prompt for Phase 3."*

> **MANAGER ACTION:** Copy the ChatGPT prompt. Open ChatGPT, paste it, review image options, download selected images, rename them sequentially, save to `raw-images/`. Return and confirm: **"Images Selected and Downloaded."**

Do not proceed to Phase 3 preparation until the manager confirms.
