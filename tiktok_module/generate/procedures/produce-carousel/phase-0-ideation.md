# Phase 0: Concept, Ideation & Prompt Preparation

You are Claude, orchestrating the Nexus TikTok carousel pipeline. The goal of this phase is to establish the core concept — city, framework, angle, and format — and build a complete slide outline so Phase 1 has all the necessary ingredients.

## Phase 0 Acceptance Criteria

Before presenting to the manager for approval, verify:

- [ ] Is there a single, approved concept (city + framework + angle + format)?
- [ ] Is there a slide outline with enough body slides to cover the concept?
- [ ] Does every planned slide have its content identified (even if roughly stated)?
- [ ] If using a contrast framework: does every slide have both sides of the contrast?
- [ ] Have you used web research to fill any gaps the manager couldn't provide?

---

## Step 0.1 — Ideation & Concept Pitches

Read [frameworks.md](../../data/strategy/frameworks.md) for the current catalog of frameworks, angles, and formats. Check `../../data/strategy/content-pipeline.md` for planned concepts, and `../../data/strategy/cities/` for any stored recommendations that could seed a new carousel. Read `../../data/strategy/performance-insights.md` to inform which frameworks, angles, and formats have performed well historically.

Present the manager with **4-5 concept pitches.** Each pitch should combine:

- **City**
- **Framework** (Local vs Tourist, Worth It, Overrated vs Underrated, or any framework from the catalog)
- **Angle** (broad city guide, category deep-dive, curated list, or any angle from the catalog)
- **Slide format** (combined, split, or single-point)

Vary the combinations — don't present 5 versions of "Local vs Tourist broad city guide." Show the manager different possibilities.

**The Wildcard Rule:** One of your pitches must always be a **completely original framework and angle that you invent.** This should be something not in the current catalog — a new structural idea, a new lens, a new way to frame city content for TikTok. If the manager selects the wildcard, add the new framework and/or angle to [frameworks.md](../../data/strategy/frameworks.md) before proceeding.

Present each pitch as a brief summary — 2-3 sentences max. Include why you think it would perform well.

> **MANAGER ACTION:** Review the pitches. Select one concept, or mix elements from multiple pitches. Respond with your choice and any modifications.

## Step 0.2 — Data Ingestion

Ask the manager for their specific recommendations for the approved concept. They will pull from the Nexus database or personal knowledge (e.g., "For Seattle, we need to recommend Taylor Shellfish and Kerry Park").

> **MANAGER ACTION:** Provide your local recommendations, database entries, or raw ideas for the chosen city/concept.

## Step 0.3 — Outline & Gap-Filling

Build a complete slide outline mapping out the full carousel.

**The Gap-Fill Rule:** If the manager provided one side of a contrast (e.g., a "Local Move" but no corresponding "Tourist Trap"), use your web research capabilities to find an accurate, highly relevant counterpart.

**The Volume Rule:** If the manager's input doesn't provide enough content to fill out the carousel, research and propose additional pairings or recommendations to round it out.

Present the outline clearly — list every slide with its planned content. Call out which items came from the manager vs. your research.

## Manager Review Gate 0

Present the complete slide outline to the manager.

Tell the manager: *"Here is the full slide outline. Please review the concept, the pairings, and the slide count. Once you approve, I'll create the carousel directory and move to Phase 1 to write the exact slide text. Reply with 'Outline Approved. Proceed to Phase 1.' or let me know what to adjust."*

> **MANAGER ACTION:** Review the outline. Tweak locations, add/remove slides, or adjust the concept. Reply with **"Outline Approved. Proceed to Phase 1."**

Do not proceed to Phase 1 until the manager explicitly approves.

## Directory Setup

Once the manager approves, create the carousel directory structure before moving to Phase 1:

```
posts/
  city-yyyy-mm-dd/
    README.md
    raw-images/      (empty — populated in Phase 2)
    slides/          (empty — populated in Phase 3)
```

Create the `README.md` with the metadata template:

```markdown
# [City] — [Framework]

- **Date posted:**
- **Slides:**
- **Framework:** [chosen framework]
- **Angle:** [chosen angle]
- **Format:** [chosen format]
- **Views:**
- **Notes:**
```

Use today's date for the directory name. The date can be updated later if posting is delayed.
