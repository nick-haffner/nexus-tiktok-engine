# Carousel Rendering Rules

Brand voice, tone, image philosophy, and branding strategy live in `../../data/strategy/brand-voice.md`. This file contains only the rendering and layout directives for carousel production.

## Content Format

### Slide Structure

Every carousel must contain:

1. **Hook Slide (Slide 1):** High-contrast title that stops the scroll. Use language appropriate to the chosen framework (e.g., "Local vs Tourist in [City] 🤩", "[City] spots that are actually worth it ✨", "[City]: Overrated vs Underrated").
2. **Body Slides:** The number and layout depend on the chosen framework and format (see `../../data/strategy/frameworks.md`). Each slide should earn its place — if a category doesn't have a strong take, cut it. If the city has depth, go longer.
3. **CTA Slide (Final Slide):** Nexus logo + closing text. Standard: "Travel like a local. Read more in the caption." Variations are acceptable (e.g., "Plan your next trip with Nexus").

### Text Density Rule

There is no hard word count. The constraint is **visual legibility at render time:**

- Aim for **2 short lines per point.** A third line is fine if the take needs it to land. Four lines means it needs editing.
- Before completing Phase 1, review every slide and flag any where text density may cause rendering issues in Phase 3.
- When in doubt, shorter is better. The image carries half the message.

## Rendering Specs

### Typography

- Bold, sans-serif style ("Classic" TikTok font).
- White text with a heavy black outline OR a subtle 15-20% dark gradient/drop-shadow behind the text for maximum contrast.
- Text must be highly legible and center-aligned.

### Layout & Safe Zones

- **Aspect Ratio:** 4:5 vertical (1080x1350px) for carousel posts. TikTok displays the caption below the image in carousels, so 4:5 prevents caption/UI overlap. (Use 9:16 only for full-screen video posts.)
- **Safe Zones:** Keep important text in the center 60-70% of the image. Avoid the top 150px (status bar) and the right-hand edge (TikTok UI buttons).
- **Anti-Jumping:** Keep text placement as consistent as possible across all slides (exact X/Y coordinates) to prevent visual jumping when swiping.

### Slide-Specific Rendering

- **Hook Slide (Slide 1):** Include a subtle visual cue (small arrow pointing right) prompting the user to swipe.
- **Body Slides:** Clean and editorial — no logo, no URL watermark.
- **CTA Slide (Final Slide):** Render the URL in cyan (`#00E4DA`) with black outline instead of white. This is the only visual difference from body slides.
