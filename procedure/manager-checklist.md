# Manager Action Checklist

This is a quick-reference compilation of every action the manager takes during the procedure. Claude will direct you to each of these at the appropriate time — you don't need to track where you are manually.

---

## Phase 0 — Ideation

- [ ] **Review concept pitches.** Claude presents 4-5 concepts (city + framework + angle + format), including one wildcard. Select one, mix elements, or request new options.
- [ ] **Provide local recommendations.** Share your Nexus database entries, personal knowledge, or raw ideas for the chosen city/concept.
- [ ] **Approve the outline.** Review Claude's slide outline. Reply with **"Outline Approved. Proceed to Phase 1."** or request changes.

## Phase 1 — Copywriting

- [ ] **Select a hook.** Claude presents 2-3 hook options. Pick one or request a different direction.
- [ ] **Approve the slide text.** Review the full draft for tone, accuracy, and text density. Reply with **"Approved."** or request revisions. Claude saves `copy.md` and creates the carousel directory automatically.

## Phase 2 — Image Sourcing (in ChatGPT)

- [ ] **Open ChatGPT** with web search enabled (Plus/Team/Enterprise tier).
- [ ] **Paste the prompt** Claude generated at the end of Phase 1.
- [ ] **Review image options.** ChatGPT presents 3-4 options per slide.
- [ ] **Download selected images.** Right-click and save to a local folder.
- [ ] **Rename files sequentially** (Slide1.jpg, Slide2.jpg, etc.).
- [ ] **Save raw images** to the carousel's `raw-images/` directory.
- [ ] **Confirm to Claude:** Reply with **"Images Selected and Downloaded."**

## Phase 3 — Assembly (in Gemini)

- [ ] **Open Gemini** (Advanced/Pro tier recommended).
- [ ] **Upload the renamed images** from Phase 2.
- [ ] **Paste the prompt** Claude generated at the end of Phase 2.
- [ ] **Review rendered images.** Check for typos, text placement, safe zone violations, and visual artifacts.
- [ ] **Request corrections** in Gemini if needed. Return to Claude if text needs shortening.
- [ ] **Download final images** once approved.
- [ ] **Save final slides** to the carousel's `final-slides/` directory.

## Phase 4 — Title, Caption & Hashtags (in ChatGPT)

- [ ] **Open ChatGPT.** Paste the prompt Claude generated at the end of Phase 3.
- [ ] **Review the output.** ChatGPT generates a single recommendation for title, caption, and hashtags. Revise in ChatGPT if needed.
- [ ] **Save to `caption.md`** in the carousel directory.

## Posting

- [ ] **Upload to TikTok** as a carousel.
- [ ] **Add title, caption, and hashtags** from `caption.md`.
- [ ] **Review sound.** TikTok will suggest one — check the "Popular" section for trending sounds. Always post with a sound.
- [ ] **Post.**
- [ ] **Update README.md** in the carousel directory with post date, view counts, and notes.
