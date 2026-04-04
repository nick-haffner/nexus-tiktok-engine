# CTA Strategy

Generalizable CTA strategy for TikTok carousel production. Campaign-specific details live in `campaigns/`.

## CTA Types

| Type | When to Use | What the CTA Slide Communicates |
|---|---|---|
| `none` | Pure reach/entertainment plays. Posts where the goal is algorithmic distribution, not action. | No CTA slide. Carousel ends on the last content slide. |
| `follow` | **Default.** Audience-building posts. The viewer got value and should see more. | Why following is worth it — connect to the content they just consumed. Direct, low-friction ask. |
| `campaign` | Active campaign is running and this post is a conversion touchpoint. Requires a campaign file in `campaigns/`. | Campaign-specific value prop + "link in bio." See the referenced campaign file for specifics. |

## Conversion Rules

These apply to all CTA types (follow and campaign). Derived from platform research and account performance data.

### 1. "Link in bio" over text URLs

TikTok carousel slides are not clickable. A text URL on screen requires the viewer to leave TikTok, open a browser, and type it manually — each step loses 80-95% of people. **"Link in bio" is a learned behavior on TikTok.** Users know how to do it. Always direct to "link in bio" for any action that requires leaving the app. The URL can appear as small reinforcing text, but must not be the primary call to action.

This rule does not apply to `follow` CTAs (following happens in-app).

### 2. Value prop must connect to the content

The viewer just consumed specific content (local recs, food spots, travel tips). The CTA must bridge from that content to the ask. "Want this for every city?" works. "Join our waitlist" without context does not. The viewer should understand what they get by acting.

### 3. CTA must be the final slide

No content slides after the CTA. The CTA is the last thing the viewer sees. Content after the CTA dilutes the ask and gives the viewer a reason to keep swiping instead of acting.

### 4. Visual consistency

The CTA slide must use the same text-on-photo editorial treatment as the body slides. No logos, no gradient overlays, no brand color blocks, no layout changes. The copy differentiates the CTA, not the design. A jarring visual shift signals "ad" and triggers ad blindness.

The only permitted visual difference: render the URL (if present) in the brand accent color (`#00E4DA`) with black outline instead of white.

### 5. Slide count for conversion-intent posts

When using `campaign` CTA type, prefer 5-6 total slides (including CTA). Significant viewer drop-off occurs after slide 5. Entertainment/reach carousels can run 7-10+ slides, but conversion-focused posts should be tighter.

This is guidance, not a hard rule — if the content requires more slides to deliver value before the ask, the content wins.

## CTA Copy Structure

### `follow`

- Connect to the content: what the viewer just got value from
- What they'll get by following: more of this, for more cities, weekly, etc.
- Keep it short — 2-3 lines max
- No URL needed (following is an in-app action)

### `campaign`

- Connect to the content (same as follow)
- State what they get by acting — concrete, not abstract
- "Link in bio" as the primary action directive
- URL as small reinforcing text only
- Read the campaign file in `campaigns/` for campaign-specific value prop and landing page details

## What NOT to Do

- **No logos on CTA slides.** For pre-launch or small brands, logos provide negligible brand recall and pattern-match to scam ads.
- **No "Read more in the caption" as the CTA.** This defers the ask to a place most viewers won't read. The CTA slide itself must carry the action.
- **No vague asks.** "Join us" or "Check us out" without a concrete value prop. The viewer must understand what they get.
- **No content after the CTA.** The CTA is the exit slide.
- **No heavy branding.** Dark backgrounds, gradient overlays, or suddenly different fonts signal "ad" and decrease trust.
