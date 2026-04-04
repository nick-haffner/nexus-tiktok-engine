#!/usr/bin/env python3
"""UTM link generator, validator, and shortener.

Reads funnel.yaml + utm-conventions.yaml, assembles validated UTM links,
and writes them to registry.csv. Optionally shortens URLs via a pluggable
provider.

Usage:
    python utm_engine.py generate --base-url URL    # Generate all links from funnel
    python utm_engine.py validate                   # Validate existing registry
    python utm_engine.py shorten                    # Shorten all unshortened links
    python utm_engine.py validate-params \\
        --source instagram --medium dm \\
        --campaign waitlist_launch                  # Validate ad hoc params
"""

import csv
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, quote

import yaml

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
FUNNEL_PATH = REPO_ROOT / "strategy" / "marketing-funnel" / "funnel.yaml"
CONVENTIONS_PATH = SCRIPT_DIR / "utm-conventions.yaml"
REGISTRY_PATH = SCRIPT_DIR / "registry.csv"
CONFIG_PATH = SCRIPT_DIR / "shortener-config.yaml"

REGISTRY_FIELDS = [
    "id", "created_at", "status",
    "stage", "channel", "campaign", "touchpoint",
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "full_url", "short_url", "notes",
]


# ── Config ────────────────────────────────────────────────────────


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_conventions(path: Path = CONVENTIONS_PATH) -> dict:
    return load_yaml(path)


def load_funnel(path: Path = FUNNEL_PATH) -> dict:
    return load_yaml(path)


def load_shortener_config(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        return {"provider": "none"}
    return load_yaml(path)


def load_registry(path: Path = REGISTRY_PATH) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_registry(rows: list[dict], path: Path = REGISTRY_PATH) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# ── Validation ────────────────────────────────────────────────────


def flatten_allowed_values(param: str, conventions: dict) -> list[str] | None:
    """Extract flat list of allowed values for a parameter. Returns None if
    the parameter uses only patterns (no fixed list)."""
    av = conventions.get("allowed_values", {}).get(param)
    if av is None:
        return None

    if isinstance(av, list):
        return av

    if isinstance(av, dict):
        values = []
        for key, val in av.items():
            if key.endswith("_pattern") or key == "pattern":
                continue
            if isinstance(val, list):
                values.extend(val)
            elif isinstance(val, str):
                values.append(val)
        return values if values else None

    return None


def get_patterns(param: str, conventions: dict) -> list[str]:
    """Extract regex-convertible patterns for a parameter."""
    av = conventions.get("allowed_values", {}).get(param, {})
    if not isinstance(av, dict):
        return []

    patterns = []
    for key, val in av.items():
        if key.endswith("_pattern") or key == "pattern":
            regex = re.escape(val)
            regex = regex.replace(r"\{", "(?P<").replace(r"\}", ">[a-z0-9_]+)")
            regex = f"^{regex}$"
            patterns.append(regex)
    return patterns


def validate_rules(value: str, conventions: dict) -> list[str]:
    """Validate a param value against formatting rules."""
    errors = []
    rules = conventions.get("rules", {})

    if rules.get("case") == "lowercase" and value != value.lower():
        errors.append(f"'{value}' must be lowercase")

    sep = rules.get("separator", "underscore")
    if sep == "underscore" and (" " in value or "-" in value):
        errors.append(f"'{value}' must use underscores, not spaces or hyphens")

    max_len = rules.get("max_length", 50)
    if len(value) > max_len:
        errors.append(f"'{value}' exceeds max length of {max_len}")

    if rules.get("encoding") == "url_safe" and value != quote(value, safe="_"):
        errors.append(f"'{value}' contains non-URL-safe characters")

    return errors


def validate_param(param: str, value: str, conventions: dict) -> list[str]:
    """Validate a single UTM parameter value against conventions."""
    if not value:
        return []

    errors = validate_rules(value, conventions)

    allowed = flatten_allowed_values(param, conventions)
    patterns = get_patterns(param, conventions)

    if allowed and value in allowed:
        return errors

    if patterns:
        for pattern in patterns:
            if re.match(pattern, value):
                return errors

    if allowed or patterns:
        errors.append(
            f"'{value}' is not a recognized {param} value. "
            f"Allowed: {allowed or 'pattern-based'}. "
            f"Add it to utm-conventions.yaml if intentional."
        )

    return errors


def validate_campaign_prefix(value: str, conventions: dict) -> list[str]:
    """Check campaign value starts with a valid prefix."""
    av = conventions.get("allowed_values", {}).get("utm_campaign", {})
    prefixes = av.get("campaign_prefixes", []) if isinstance(av, dict) else []
    if not prefixes:
        return []

    rules = conventions.get("rules", {})
    if not rules.get("prefix_campaigns", False):
        return []

    for prefix in prefixes:
        if value.startswith(prefix + "_") or value == prefix:
            return []

    return [
        f"Campaign '{value}' must start with a valid prefix: "
        f"{', '.join(prefixes)}"
    ]


def validate_link(params: dict, conventions: dict) -> list[str]:
    """Validate a full set of UTM params against conventions."""
    errors = []

    for param in ("utm_source", "utm_medium", "utm_campaign"):
        if not params.get(param):
            errors.append(f"Missing required parameter: {param}")

    for param in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"):
        val = params.get(param, "")
        if val:
            errors.extend(validate_param(param, val, conventions))

    if params.get("utm_campaign"):
        errors.extend(validate_campaign_prefix(params["utm_campaign"], conventions))

    return errors


# ── Link Generation ───────────────────────────────────────────────


def make_id(params: dict) -> str:
    """Generate a short deterministic hash from UTM params."""
    raw = "|".join(params.get(k, "") for k in (
        "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"
    ))
    return hashlib.sha256(raw.encode()).hexdigest()[:8]


def assemble_url(base_url: str, params: dict) -> str:
    """Build full UTM URL from base + params."""
    utm_params = {
        k: v for k, v in params.items()
        if k.startswith("utm_") and v
    }
    return f"{base_url}?{urlencode(utm_params)}"


def _process_touchpoint(tp: dict, stage: dict, channel: dict,
                        campaign_name: str, base_url: str,
                        conventions: dict, existing_ids: set,
                        new_rows: list, all_errors: list,
                        timestamp: str) -> None:
    """Process a single touchpoint, expanding content_variants into individual links."""
    variants = tp.get("content_variants", [None])
    if not variants:
        variants = [None]

    for variant in variants:
        params = {
            "utm_source": channel["name"],
            "utm_medium": tp.get("medium", ""),
            "utm_campaign": campaign_name,
            "utm_content": variant or "",
            "utm_term": "",
        }

        link_id = make_id(params)
        if link_id in existing_ids:
            continue

        errors = validate_link(params, conventions)
        if errors:
            label = f"{channel['name']}/{campaign_name}/{tp['name']}"
            if variant:
                label += f"/{variant}"
            all_errors.append((label, errors))
            continue

        row = {
            "id": link_id,
            "created_at": timestamp,
            "status": "active",
            "stage": stage["name"],
            "channel": channel["name"],
            "campaign": campaign_name,
            "touchpoint": tp["name"],
            **params,
            "full_url": assemble_url(base_url, params),
            "short_url": "",
            "notes": tp.get("description", ""),
        }
        new_rows.append(row)
        existing_ids.add(link_id)


def generate(base_url: str = None,
             funnel_path: Path = FUNNEL_PATH,
             conventions_path: Path = CONVENTIONS_PATH,
             registry_path: Path = REGISTRY_PATH) -> None:
    """Generate all UTM links from funnel and write to registry."""
    funnel = load_funnel(funnel_path)
    conventions = load_conventions(conventions_path)
    existing = load_registry(registry_path)
    existing_ids = {row["id"] for row in existing}

    if not base_url:
        base_url = load_registry_base_url(registry_path)
    if not base_url:
        print("  Error: No base URL provided.")
        print("  Usage: python utm_engine.py generate --base-url https://example.com")
        sys.exit(1)

    new_rows = []
    all_errors = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for stage in funnel.get("stages", []):
        for channel in stage.get("channels", []):
            for campaign in channel.get("campaigns", []):
                for tp in campaign.get("touchpoints", []):
                    _process_touchpoint(
                        tp, stage, channel, campaign["name"], base_url,
                        conventions, existing_ids, new_rows, all_errors,
                        timestamp,
                    )

            # Standalone touchpoints (channel-level, outside any campaign)
            for tp in channel.get("touchpoints", []):
                _process_touchpoint(
                    tp, stage, channel, "", base_url,
                    conventions, existing_ids, new_rows, all_errors,
                    timestamp,
                )

    if all_errors:
        print(f"\n  VALIDATION ERRORS ({len(all_errors)} links rejected):\n")
        for label, errs in all_errors:
            print(f"  {label}:")
            for e in errs:
                print(f"    - {e}")
        print()

    combined = existing + new_rows
    save_registry(combined, registry_path)
    print(f"  Generated: {len(new_rows)} new links")
    print(f"  Skipped:   {len(existing)} existing links")
    print(f"  Rejected:  {len(all_errors)} links with validation errors")
    print(f"  Registry:  {registry_path}")


def load_registry_base_url(registry_path: Path) -> str | None:
    """Try to read base_url from a companion config or first existing row."""
    existing = load_registry(registry_path)
    if existing:
        url = existing[0].get("full_url", "")
        if "?" in url:
            return url.split("?")[0]
    return None


# ── Standalone Validation ─────────────────────────────────────────


def validate_registry(conventions_path: Path = CONVENTIONS_PATH,
                      registry_path: Path = REGISTRY_PATH) -> None:
    """Validate all entries in the registry against conventions."""
    conventions = load_conventions(conventions_path)
    rows = load_registry(registry_path)

    if not rows:
        print("  Registry is empty.")
        return

    error_count = 0
    for row in rows:
        params = {k: row.get(k, "") for k in (
            "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"
        )}
        errors = validate_link(params, conventions)
        if errors:
            error_count += 1
            print(f"\n  [{row.get('id', '?')}] {row.get('touchpoint', '?')}:")
            for e in errors:
                print(f"    - {e}")

    if error_count == 0:
        print(f"  All {len(rows)} links passed validation.")
    else:
        print(f"\n  {error_count}/{len(rows)} links have errors.")


def validate_adhoc(**kwargs) -> None:
    """Validate ad hoc UTM params from CLI flags."""
    conventions = load_conventions()
    params = {
        "utm_source": kwargs.get("source", ""),
        "utm_medium": kwargs.get("medium", ""),
        "utm_campaign": kwargs.get("campaign", ""),
        "utm_content": kwargs.get("content", ""),
        "utm_term": kwargs.get("term", ""),
    }
    errors = validate_link(params, conventions)
    if errors:
        print("  Validation failed:")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  Valid.")


# ── Shortener ─────────────────────────────────────────────────────


def shorten_url(url: str, config: dict) -> str | None:
    """Shorten a URL using the configured provider."""
    provider = config.get("provider", "none")

    if provider == "none":
        return None

    if not HAS_REQUESTS:
        print("  'requests' package required for shortening. pip install requests")
        return None

    if provider == "short_io":
        return _shorten_short_io(url, config)
    elif provider == "ulvis":
        return _shorten_ulvis(url)
    else:
        print(f"  Unknown shortener provider: {provider}")
        return None


def _shorten_short_io(url: str, config: dict) -> str | None:
    api_key = config.get("api_key", "")
    domain = config.get("domain", "short.io")
    if not api_key:
        print("  short.io requires api_key in shortener-config.yaml")
        return None
    try:
        resp = requests.post(
            "https://api.short.io/links/public",
            json={"originalURL": url, "domain": domain},
            headers={"Authorization": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("shortURL")
    except Exception as e:
        print(f"  short.io error: {e}")
        return None


def _shorten_ulvis(url: str) -> str | None:
    try:
        resp = requests.post(
            "https://ulvis.net/api/v1/shorten",
            json={"url": url},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("url") or data.get("url")
    except Exception as e:
        print(f"  ulvis error: {e}")
        return None


def shorten_registry(registry_path: Path = REGISTRY_PATH) -> None:
    """Shorten all unshortened URLs in the registry."""
    config = load_shortener_config()
    if config.get("provider", "none") == "none":
        print("  No shortener configured. Create shortener-config.yaml with:")
        print("    provider: short_io  # or ulvis")
        print("    api_key: your_key   # for short.io")
        return

    rows = load_registry(registry_path)
    shortened = 0

    for row in rows:
        if row.get("short_url"):
            continue
        if not row.get("full_url"):
            continue

        result = shorten_url(row["full_url"], config)
        if result:
            row["short_url"] = result
            shortened += 1

    save_registry(rows, registry_path)
    print(f"  Shortened: {shortened} links")


# ── CLI ───────────────────────────────────────────────────────────


def parse_adhoc_args(args: list[str]) -> dict:
    """Parse --key value pairs from CLI args."""
    params = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            key = args[i][2:]
            params[key] = args[i + 1]
            i += 2
        else:
            i += 1
    return params


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        cli_params = parse_adhoc_args(sys.argv[2:])
        generate(base_url=cli_params.get("base-url"))
    elif command == "validate":
        validate_registry()
    elif command == "shorten":
        shorten_registry()
    elif command == "validate-params":
        params = parse_adhoc_args(sys.argv[2:])
        validate_adhoc(**params)
    else:
        print(f"  Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
