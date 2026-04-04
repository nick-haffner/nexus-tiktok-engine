# Nexus TikTok Carousel Production Procedure

## Overview

This is the production pipeline for Nexus TikTok carousels. Claude orchestrates the procedure, writes copy, and directs the manager through approval gates and tool handoffs. The manager reviews, approves, and executes actions in external tools (ChatGPT, Gemini) when directed.

## The Nexus AI Tool Stack

| Phase | Tool | Role |
|-------|------|------|
| Phase 0 (Ideation) | **Claude** | Generates concepts, researches gaps, builds the slide outline. |
| Phase 1 (Copywriting) | **Claude** | Writes and refines all slide text. |
| Phase 2 (Visual Sourcing) | **ChatGPT** (or Perplexity) | Manager pastes Claude-generated prompt. AI sources real photos via web search. |
| Phase 3 (Assembly) | **Gemini** (Nano Banana 2) | Manager pastes Claude-generated prompt. AI composites text onto images. |
| Phase 4 (Title, Caption & Hashtags) | **ChatGPT** | Manager pastes Claude-generated prompt. AI generates title, caption with emojis, and hashtags. |

## Ultimate Acceptance Criteria (The Final Product)

The final output must achieve the following:

- **Tone:** Confident, insider, contrarian, and concise. (See [brand-voice.md](../../data/strategy/brand-voice.md) for voice guidelines and [brand-rules.md](brand-rules.md) for rendering specs.)
- **Structure:** 1 Hook Slide, body slides sufficient to cover the concept, and 1 CTA Slide. (See [frameworks.md](../../data/strategy/frameworks.md) for framework/format options.)
- **Text density:** All text must render legibly within the TikTok safe zone at the target font size. Short, punchy lines — not paragraphs.
- **Visuals:** 9:16 vertical images ready for direct TikTok upload. Real photos only (no AI-generated landmarks/storefronts).
- **Formatting:** Highly legible white text with a thick black outline/drop-shadow, centered, respecting TikTok UI safe zones (right side and bottom 20% clear).
