#!/usr/bin/env python3
"""Generate a Mermaid funnel diagram from funnel.yaml.

The YAML file is the single source of truth for the marketing funnel.
The generated Markdown file is a read-only render — edits to it have
no effect on the stored funnel and will be overwritten on next run.
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent


def slugify(text: str) -> str:
    """Convert text to a safe Mermaid node ID (lowercase alphanumeric + underscores)."""
    text = text.lower().replace(" ", "_").replace("-", "_")
    return re.sub(r"[^a-z0-9_]", "", text)


def validate_yaml(data: dict) -> None:
    """Raise ValueError if required funnel structure is missing."""
    if not isinstance(data, dict) or "stages" not in data:
        raise ValueError("YAML must contain a top-level 'stages' list")
    for i, stage in enumerate(data["stages"]):
        for key in ("name", "order"):
            if key not in stage:
                raise ValueError(f"Stage {i} is missing required key '{key}'")
        for channel in stage.get("channels", []):
            if "name" not in channel:
                raise ValueError(
                    f"A channel in stage '{stage['name']}' is missing 'name'"
                )
            for campaign in channel.get("campaigns", []):
                if "name" not in campaign:
                    raise ValueError(
                        f"A campaign in channel '{channel['name']}' is missing 'name'"
                    )
                for tp in campaign.get("touchpoints", []):
                    if "name" not in tp:
                        raise ValueError(
                            f"A touchpoint in campaign '{campaign['name']}' is missing 'name'"
                        )
            for tp in channel.get("touchpoints", []):
                if "name" not in tp:
                    raise ValueError(
                        f"A standalone touchpoint in channel '{channel['name']}' is missing 'name'"
                    )


def generate_mermaid(funnel_path: str, output_path: str = None) -> str:
    funnel_path = Path(funnel_path).resolve()

    with open(funnel_path) as f:
        data = yaml.safe_load(f)

    validate_yaml(data)

    if not output_path:
        output_path = str(funnel_path.parent / "funnel.md")

    lines = ["```mermaid", "graph TD"]
    node_id = 0

    def next_id(prefix: str) -> str:
        nonlocal node_id
        node_id += 1
        return f"{prefix}_{node_id}"

    def touchpoint_label(tp: dict) -> str:
        medium = tp.get("medium", "")
        variants = ", ".join(tp.get("content_variants", []))
        parts = [p for p in (medium, variants) if p]
        subtitle = " | ".join(parts)
        label = tp["name"]
        if subtitle:
            label += f"<br/><small>{subtitle}</small>"
        return label

    for stage in data["stages"]:
        stage_slug = slugify(stage["name"])
        stage_id = f"s_{stage_slug}"
        stage_label = f"{stage['order']}. {stage['name'].upper()}"
        lines.append("")
        lines.append(f"    subgraph {stage_id}[\"{stage_label}\"]")
        lines.append("        direction LR")

        for channel in stage.get("channels", []):
            ch_slug = slugify(channel["name"])
            ch_id = f"ch_{ch_slug}_{stage_slug}"
            lines.append("")
            lines.append(f"        subgraph {ch_id}[\"{channel['name']}\"]")
            lines.append("            direction TB")

            for campaign in channel.get("campaigns", []):
                cp_slug = slugify(campaign["name"])
                cp_id = f"cp_{cp_slug}_{ch_slug}_{stage_slug}"
                lines.append("")
                lines.append(f"            subgraph {cp_id}[\"{campaign['name']}\"]")
                lines.append("                direction TB")

                for tp in campaign.get("touchpoints", []):
                    tp_id = next_id("tp")
                    lines.append(f"                {tp_id}[\"{touchpoint_label(tp)}\"]")

                lines.append("            end")

            # Standalone touchpoints (channel-level, outside any campaign)
            for tp in channel.get("touchpoints", []):
                tp_id = next_id("tp")
                lines.append(f"            {tp_id}[\"{touchpoint_label(tp)}\"]")

            lines.append("        end")

        lines.append("    end")

    # Connect stages vertically
    stage_ids = [slugify(f"s_{s['name']}") for s in data["stages"]]
    lines.append("")
    for i in range(len(stage_ids) - 1):
        lines.append(f"    {stage_ids[i]} --> {stage_ids[i + 1]}")

    lines.append("```")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "# Marketing Funnel\n\n"
        f"> **Generated:** {timestamp}  \n"
        f"> **Source:** `{funnel_path.name}`  \n"
        "> \n"
        "> This file is auto-generated from the YAML source of truth.\n"
        "> **Do not edit this file** -- changes here will not update the funnel\n"
        "> and will be overwritten on the next run. To modify the funnel,\n"
        f"> edit `{funnel_path.name}` and re-run `{Path(__file__).name}`.\n\n"
    )

    md_content = header + "\n".join(lines) + "\n"

    with open(output_path, "w") as f:
        f.write(md_content)

    return output_path


if __name__ == "__main__":
    default_input = str(SCRIPT_DIR / "funnel.yaml")
    funnel_file = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    result = generate_mermaid(funnel_file, output_file)
    print(f"Generated: {result}")
