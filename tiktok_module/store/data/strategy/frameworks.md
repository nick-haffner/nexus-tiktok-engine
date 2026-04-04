# Frameworks & Slide Layouts

Living catalog of content structures. Referenced by the derive data procedure (to classify existing posts) and the generate procedure (to produce new content). Performance data from `performance-insights.md` should inform which combinations to prioritize.

---

## Frameworks

A framework defines the core contrast or structural pattern of a carousel. Each framework has distinct visual and textual signatures that the derive procedure uses for classification.

| Framework | Description | Visual Signatures | Example Posts |
|---|---|---|---|
| **local_vs_tourist** | Contrasts tourist traps with local-approved alternatives. High-contrast, opinionated. | Alternating ❌/✅ slides. Red/green color coding. "Tourist Move" / "Local Move" headings. Split or combined image layouts with contrast between crowded/authentic visuals. | Seattle, Dallas, Austin, Phoenix |
| **worth_it** | Positive recommendations only — no traps. Validates places that are popular for good reason. | Single-point slides. No contrast pairs. Celebratory tone. Each slide features one recommendation with positive framing. | San Francisco |
| **the_24_hour_test** | "You have 24 hours in [City]." Time-blocked structure with "waste it" and "nail it" choices per time block. | Time-of-day headings (Morning, Afternoon, Evening, Dinner, Late Night). Alternating ❌/✅ within time blocks. Clock/time emoji markers. | Los Angeles |
| **overrated_vs_underrated** | Similar to local_vs_tourist but broader — doesn't require the location to be a "tourist trap," just overhyped. | Similar visual pattern to local_vs_tourist but with "Overrated" / "Underrated" headings instead of "Tourist" / "Local." | (unused — available) |

New frameworks are expected. When a post doesn't match any known framework, leave the classification NULL and surface for manual review.

## Slide Layouts

A slide layout defines how content is arranged across slides. Free text — new layouts are expected as the content strategy evolves.

| Layout | Description | Visual Signatures | Example Posts |
|---|---|---|---|
| **combined** | Tourist and local recommendations on the same slide. Split image, top/bottom or left/right. | Each slide contains both the ❌ and ✅ content. Denser text per slide. Two distinct images or a split-image composition. | Austin, Phoenix |
| **split** | Tourist and local recommendations on separate consecutive slides. More visual breathing room. | Odd slides are ❌ (trap), even slides are ✅ (pick). Each slide has one image and one set of text. Slides alternate in tone/color. | Seattle, LA (24-Hour Test) |
| **single_point** | Each slide is one recommendation. No contrast pairs. | One recommendation per slide. No alternating pattern. Each slide stands alone. | San Francisco (Worth It) |

New layouts are expected. Classification requires examining the visual structure of the slides.
