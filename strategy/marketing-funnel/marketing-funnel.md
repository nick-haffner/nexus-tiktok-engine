# Marketing Funnel Documentation

## What this is

This directory stores the marketing funnel as a structured YAML file and generates a visual diagram from it. The funnel maps how a prospect moves from first hearing about the product to converting and referring others.

The funnel is organized into four levels:

| Level | What it represents | Example |
|---|---|---|
| **Stage** | Where the prospect is in their journey | Awareness, Interest, Signup, Referral |
| **Channel** | The platform or source delivering the message | Instagram, TikTok, a specific partner |
| **Campaign** | The coordinated effort grouping related touchpoints | `waitlist_launch`, `waitlist_partnerpush` |
| **Touchpoint** | A specific piece of content or interaction the prospect encounters | A launch carousel, a DM, a bio link |

### What is a touchpoint?

A touchpoint is either a **single, specific piece of content** (e.g., "Launch carousel v1") or a **generalized group of similar interactions** (e.g., "Warm DM" representing all personalized DMs sent to engaged followers). Use whichever granularity is meaningful for tracking. If you need to distinguish between variants of the same touchpoint for UTM tracking, list them under `content_variants` rather than creating separate touchpoints.

### UTM mapping

The funnel hierarchy maps directly to UTM parameters for link tracking:

| Funnel level | UTM parameter | Example value |
|---|---|---|
| `channel.name` | `utm_source` | `instagram` |
| `campaign.name` | `utm_campaign` | `waitlist_launch` |
| `touchpoint.medium` | `utm_medium` | `organic_social` |
| `touchpoint.content_variants` | `utm_content` | `carousel_v1` |

This means every touchpoint in the funnel has a complete UTM signature derived from its position in the hierarchy.

---

## How to read the diagram

The generated diagram (`funnel.md`) renders a visual map of the funnel using Mermaid. The visual hierarchy is:

- **Outermost boxes** = Stages (numbered, flowing top to bottom)
  - **Middle boxes** = Channels (arranged side by side within a stage)
    - **Innermost boxes** = Campaigns (stacked within a channel)
      - **Nodes** = Touchpoints (leaf items showing name, medium, and content variants)

Touchpoints that exist outside any campaign appear directly inside their channel box, without a campaign wrapper.

Arrows connect stages to show the progression of the funnel. There are no arrows within a stage -- containment (being inside a box) communicates the relationship.

---

## How to edit the funnel

### Source of truth

`funnel.yaml` is the single source of truth for the marketing funnel. All edits go here.

`funnel.md` is a generated output file. It is timestamped, and any manual edits to it will be overwritten the next time the diagram is regenerated. Changes to `funnel.md` do not change the stored funnel.

### YAML structure

The file follows this structure:

```yaml
stages:

  - order: 1                  # Display order (integer, ascending)
    name: stage_name           # Stage identifier (lowercase, underscores)
    description: "..."         # Human-readable purpose of this stage
    channels:

      - name: channel_name     # Platform or source (lowercase, underscores)
        campaigns:
          - name: campaign_name  # Campaign identifier (lowercase, underscores)
            touchpoints:
              - name: Touchpoint Name     # Display name (title case, shown in diagram)
                description: "..."        # What this touchpoint is (not shown in diagram)
                medium: medium_type       # Delivery mechanism (maps to utm_medium)
                content_variants:         # List of variant identifiers (maps to utm_content)
                  - variant_a
                  - variant_b

        # Optional: standalone touchpoints outside any campaign
        touchpoints:
          - name: Standalone Touchpoint
            description: "..."
            medium: medium_type
            content_variants:
              - variant_x
```

### Required vs optional fields

| Field | Required | Notes |
|---|---|---|
| `stage.order` | Yes | Integer. Controls display order. |
| `stage.name` | Yes | Lowercase with underscores. Must be unique across stages. |
| `stage.description` | No | Not shown in diagram. Documentation only. |
| `stage.channels` | No | A stage with no channels renders as an empty box. |
| `channel.name` | Yes | Lowercase with underscores. Can repeat across stages (e.g., `instagram` in both Awareness and Interest). |
| `channel.campaigns` | No | A channel can have campaigns, standalone touchpoints, or both. |
| `channel.touchpoints` | No | Standalone touchpoints that don't belong to a campaign. |
| `campaign.name` | Yes | Lowercase with underscores. Can repeat across channels. |
| `campaign.touchpoints` | No | A campaign with no touchpoints renders as an empty box. |
| `touchpoint.name` | Yes | Title case. This is the display label in the diagram. |
| `touchpoint.description` | No | Not shown in diagram. Documentation only. |
| `touchpoint.medium` | No | Shown in diagram subtitle. Maps to `utm_medium`. |
| `touchpoint.content_variants` | No | Shown in diagram subtitle. Each entry maps to a `utm_content` value. |

### Adding a new touchpoint

Add a new entry under the appropriate `campaign.touchpoints` list:

```yaml
              - name: New Post
                description: "A follow-up post targeting engaged users"
                medium: organic_social
                content_variants:
                  - post_followup_v1
```

### Adding a new campaign

Add a new entry under the appropriate `channel.campaigns` list:

```yaml
          - name: summer_push
            touchpoints:
              - name: Summer Carousel
                description: "Seasonal content push"
                medium: organic_social
                content_variants:
                  - carousel_summer
```

### Adding a new channel

Add a new entry under the appropriate `stage.channels` list:

```yaml
      - name: youtube
        campaigns:
          - name: waitlist_launch
            touchpoints:
              - name: Explainer video
                description: "Long-form product walkthrough"
                medium: organic_social
                content_variants:
                  - video_explainer
```

### Adding a new stage

Add a new entry to the top-level `stages` list with the next `order` number:

```yaml
  - order: 5
    name: retention
    description: "Keep converted users engaged and active"
    channels:
      - name: email
        campaigns:
          - name: onboarding_drip
            touchpoints:
              - name: Welcome email
                description: "First email after signup"
                medium: email
                content_variants:
                  - email_welcome
```

### Adding a standalone touchpoint (no campaign)

Place touchpoints directly under the channel, alongside `campaigns`:

```yaml
      - name: instagram
        campaigns:
          - name: waitlist_launch
            touchpoints:
              - ...
        touchpoints:
          - name: Pinned highlight
            description: "Persistent story highlight on the profile"
            medium: organic_social
            content_variants:
              - highlight_pinned
```

These render inside the channel box but outside any campaign box.

---

## How to regenerate the diagram

After editing `funnel.yaml`, run:

```
python strategy/marketing-funnel/generate_funnel_diagram.py
```

Or from within the `strategy/marketing-funnel/` directory:

```
python generate_funnel_diagram.py
```

The script accepts optional arguments:

```
python generate_funnel_diagram.py [input_path] [output_path]
```

- `input_path` defaults to `funnel.yaml` in the script's directory
- `output_path` defaults to `funnel.md` in the same directory as the input

### Viewing the diagram

- **VS Code:** Install the "Markdown Preview Mermaid Support" extension (bierner). Open `funnel.md` and press `Ctrl+Shift+V` for preview, or use the "Edit Diagram" button.
- **GitHub:** `funnel.md` renders natively when viewed on GitHub.
- **Mermaid Live Editor:** Copy the content between the `` ```mermaid `` fences and paste at `mermaid.live`.

### Dependencies

- Python 3.x
- `pyyaml` (`pip install pyyaml`)

---

## File inventory

| File | Role | Editable? |
|---|---|---|
| `funnel.yaml` | Source of truth for the funnel definition | Yes -- all funnel changes go here |
| `funnel.md` | Generated Mermaid diagram | No -- regenerated from YAML, manual edits are overwritten |
| `generate_funnel_diagram.py` | Script that reads YAML and writes the diagram | Yes -- modify to change diagram rendering |
| `marketing-funnel.md` | This documentation file | Yes |

---

## Validation

The script validates the YAML before generating. It checks:

- Top-level `stages` list exists
- Every stage has `name` and `order`
- Every channel has `name`
- Every campaign has `name`
- Every touchpoint (in campaigns or standalone) has `name`

If validation fails, the script prints the error and exits without writing the output file.
