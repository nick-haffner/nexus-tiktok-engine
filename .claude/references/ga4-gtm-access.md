# GA4 & GTM API Access

Local-only diagnostic access to Google Analytics 4 and Google Tag Manager for the Nexus Concierge property. Not part of the application — the app fires events client-side through GTM. This access is for querying, verification, and ad-hoc reporting.

## Authentication

- **GCP Project:** `nexus-analytics-491622`
- **Service Account:** `ga4-reader@nexus-analytics-491622.iam.gserviceaccount.com`
- **Key File:** `C:/Users/nickh/OneDrive/Samsung Laptop/Desktop/Key Pairs/ga4-reader--nexus-analytics-491622--service-account-key.json`
- **Permissions:** Editor on GA4 property, Read on GTM container

## Property & Container IDs

- **GA4 Property:** 524017270
- **Prod Measurement ID:** `G-EJFTSLEVEE` (nexus-concierge.com)
- **Test Measurement ID:** `G-T9G5LW0N7G` (test.nexus-concierge.com)
- **GTM Container:** `GTM-TCBRCKT6` (account 6338764277, container 243266166)

## Query Utility

```bash
source "c:/Users/nickh/Nexus MVP GH Repository/nexusmvp/python/.venv/Scripts/activate"
python python/scripts/ga4_query.py --key "C:/Users/nickh/OneDrive/Samsung Laptop/Desktop/Key Pairs/ga4-reader--nexus-analytics-491622--service-account-key.json" <command>
```

### Commands

| Command | Purpose |
|---------|---------|
| `events` | List events with counts |
| `event-params --event <name>` | Custom parameters for a specific event |
| `realtime` | Realtime event activity (last 30 min) |
| `verify` | Run E1-E7 automated verification |
| `metadata` | List available dimensions and metrics |
| `query -d <dims> -m <metrics> --start <date> --end <date>` | Flexible query |
| `admin streams` | List GA4 data streams |
| `admin dimensions` | List registered custom dimensions |
| `gtm tags` / `triggers` / `variables` / `versions` | GTM container inspection |

### Query Examples

```bash
# Top pages by unique visitors (30 days)
... query -d pagePath -m activeUsers --start 30daysAgo --end today --order activeUsers

# Events by hostname
... query -d hostname eventName -m eventCount --start 7daysAgo --end today

# Filter to listing pages
... query -d pagePath -m activeUsers --start 7daysAgo --end today -f "pagePath~contains~/listing/"
```

## GTM Lookup Table

Hostname-based routing to GA4 measurement IDs (updated 2026-03-28, v3):

| Hostname | Measurement ID |
|----------|---------------|
| `nexus-concierge.com` | `G-EJFTSLEVEE` |
| `app.nexus-concierge.com` | `G-EJFTSLEVEE` |
| `test.nexus-concierge.com` | `G-T9G5LW0N7G` |
| `test.app.nexus-concierge.com` | `G-T9G5LW0N7G` |

## Registered Custom Dimensions

`access_channel`, `booking_id`, `service_category`, `service_type`, `step_index`, `step_name`

**Not registered (DLVs exist in GTM):** `date`, `value`, `currency` — deferred to Launch Post-Waitlist.
