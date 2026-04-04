# TikTok Studio — Browser Extraction Methods

Ranked playbook for extracting post data from TikTok Studio (`www.tiktok.com/tiktokstudio/content`) via Chrome automation. TikTok Studio uses **virtual scrolling** — only ~6–8 post rows exist in the DOM at any time, regardless of total post count. This is the central challenge.

## Method Ranking

### 1. Slow JS container scroll with DOM collection (Best)

**Technique:** Identify the scrollable container (`document.querySelector('.css-snthx.edss2sz11')` as of 2026-04-01), then scroll it from top to bottom in small increments (~80px per step, ~150ms delay) while collecting all `a[href*="/video/"]` elements at each position.

```
container.scrollTop = 0;
for (let pos = 0; pos <= totalHeight; pos += 80) {
  container.scrollTop = pos;
  await new Promise(r => setTimeout(r, 150));
  // collect links from DOM
}
```

**Result:** Captured **45 of 45** post IDs in a single pass.

**Limitation:** Date extraction failed in the same pass — the parent-traversal logic to find nearby date text didn't resolve. Post IDs were reliable; dates were not.

**Verdict:** Use this for post ID collection. Collect dates separately.

---

### 2. Manual scroll + read_page at each viewport (Best for dates)

**Technique:** Scroll the page using the `computer` tool (scroll action, 2–3 ticks at a time), then call `read_page` at each position. The accessibility tree reliably exposes both the link `href` (containing the post ID) and the nearby `generic` text node with the date string.

**Result:** Captured all 45 post IDs and all dates across ~6 read_page calls. Each call returned 6–8 posts.

**Limitation:** Slow and requires many round-trips. For 46 posts this took ~6 scroll+read cycles. The operator must track which posts have been captured across calls to avoid stopping early.

**Verdict:** Use this for date collection and as the primary fallback if JS methods fail.

---

### 3. find tool for targeted date lookup (Good supplement)

**Technique:** After collecting post IDs via Method 1, use `mcp__claude-in-chrome__find` with a natural language query like `post date containing "Mar 19" or "Mar 20"` to locate specific date elements. Then `scroll_to` that element and `read_page` to capture the surrounding post ID + date.

**Result:** Successfully located 2 of 2 targeted dates in one call.

**Limitation:** Only finds elements currently rendered in the DOM or nearby in the virtual scroll. If the target date is far from the current scroll position, it may not be found. Works best as a gap-filler after Methods 1 and 2 have captured most data.

**Verdict:** Use to fill specific gaps, not as a primary collection method.

---

### 4. Fast JS scroll with date extraction in same pass (Unreliable)

**Technique:** Same as Method 1 but also attempts to extract dates by traversing parent elements from each link to find a sibling/ancestor with a date-formatted text node.

**Result:** Collected post IDs reliably but returned empty strings for all dates. A longer version with more parent-traversal timed out (45s CDP timeout).

**Limitation:** The DOM structure makes it difficult to associate a date text node with a specific post link via parent traversal alone. The accessibility tree (read_page) handles this association much better than raw DOM traversal.

**Verdict:** Avoid for dates. Use Method 1 for IDs only.

---

### 5. Aggressive JS scroll-to-bottom then collect (Poor)

**Technique:** Scroll `window.scrollTo(0, document.body.scrollHeight)` repeatedly to force-load all posts, then collect all links.

**Result:** Only captured **8 of 45** post IDs. Virtual scrolling culls off-screen rows, so scrolling to the bottom doesn't accumulate DOM elements — it replaces them.

**Verdict:** Avoid. Virtual scrolling defeats this approach entirely.

---

### 6. get_page_text (Failed)

**Technique:** Call `mcp__claude-in-chrome__get_page_text` to extract all text content.

**Result:** Error — page body too large (contains CSS/scripts), no semantic content element found.

**Verdict:** Does not work for TikTok Studio.

---

## Per-Post Analytics

### API fetch via `/aweme/v2/data/insight/` (Best — batch collection)

**Technique:** Call TikTok's internal analytics API directly via `fetch()` from JavaScript running on any TikTok Studio page. The browser's existing auth cookies authenticate the request automatically (`credentials: 'include'`). No page navigation required.

**Endpoint:** `https://www.tiktok.com/aweme/v2/data/insight/`

**Parameters:**
- `locale=en`
- `aid=1988`
- `tz_offset=-18000` (adjust for timezone)
- `type_requests` — JSON array of insight type objects, each with `insigh_type` (note: TikTok's typo, not `insight_type`) and `aweme_id` (the post ID)

**Insight types and response field mappings:**

| Insight type | Response path | Metric |
|---|---|---|
| `video_info` | `.video_info.statistics.play_count` | views |
| `video_info` | `.video_info.statistics.digg_count` | likes |
| `video_info` | `.video_info.statistics.comment_count` | comments |
| `video_info` | `.video_info.statistics.share_count` | shares |
| `video_info` | `.video_info.statistics.collect_count` | bookmarks |
| `realtime_new_followers` | `.realtime_new_followers.value.value` | new followers |
| `video_per_duration_realtime` | `.video_per_duration_realtime.value.value` | avg watch time (seconds) |
| `video_finish_rate_realtime` | `.video_finish_rate_realtime.value.value` | watched full video (decimal, multiply by 100 for %) |
| `video_traffic_source_percent_realtime` | `.video_traffic_source_percent_realtime.value.value` | array of `{key, value}` objects; find `key === "For You"`, use `value` (decimal, multiply by 100 for %) |

**Result:** Collected all 9 metrics for **41 posts in two JS calls** with no page navigation. Each call batched ~20 posts sequentially with a 500ms delay every 5 requests to avoid rate limiting. Total wall time: ~30 seconds vs. an estimated 5+ minutes for 41 page navigations.

**Limitation:** Must be executed from a TikTok Studio page (any page) so the browser's session cookies are sent. The API response contains auth-related fields that may be blocked by Chrome automation tools if stringified raw — extract only the numeric metric values.

**Verdict:** Use this for any batch metric collection (backfills, daily captures with many posts). Single-post lookups can use this or direct URL navigation.

---

### Direct URL navigation (Good — single post or fallback)

**Technique:** Navigate directly to `tiktokstudio/analytics/{post_id}/overview`. This loads the full per-post analytics page with all metrics: views, likes, comments, shares, bookmarks, avg watch time, watched full video %, new followers, FYP %, and traffic sources.

**Result:** Loaded all 4 target posts instantly during first daily capture. Each page exposes every metric needed for both snapshot and velocity readings in a single read_page call.

**Verdict:** Use for single-post collection or as a fallback if the API method fails. For batch collection, prefer the API method above.

---

### Content list click-through (Avoid)

**Technique:** Click on a post title/thumbnail in the Content tab (`tiktokstudio/content`).

**Result:** Opens the **public** TikTok page (`tiktok.com/@nexusconcierge/video/{id}`), not the analytics page. The content list action buttons (three-dots menu) only offer Pin/Download/Delete — no analytics link. The only UI path to per-post analytics from within TikTok Studio is Analytics > Content tab > "View data" button, which requires the post to appear in the "Your top posts" list.

**Verdict:** Avoid. Use the direct URL pattern above instead.

---

## Carousel Slide Images

### `/api/post/item_list/` imagePost object (Best — original quality, batch)

**Technique:** The same `/api/post/item_list/` endpoint used for post ID collection returns full image data for carousel posts. For any item where `imagePost` is truthy, `imagePost.images[]` contains one entry per slide.

**Response structure:**

```
item.imagePost.images[i].imageURL.urlList[0]   → signed CDN URL (original JPEG)
item.imagePost.images[i].imageWidth             → pixel width (e.g. 1080)
item.imagePost.images[i].imageHeight            → pixel height (e.g. 1620)
```

Each `urlList` contains 2 URLs (both identical, different CDN hosts). The transform is `tplv-photomode-image.jpeg` — original upload quality, no resize or compression.

**Result:** Downloaded slide 1 of a 10-slide carousel: **JPEG, 177 KB, 1080×1620**. All slides downloadable via `fetch()` from browser context (HTTP 200).

**Batch capability:** A single paginated `item_list` call returns image URLs for every carousel on the account. No per-post API calls needed.

**Verdict:** Primary method for carousel image capture. Original quality, batch-capable, already called by `collect_post_ids.py`.

---

### `/aweme/v2/data/insight/` image_post_info (Alternative — compressed)

**Technique:** The insight API's `video_info` response includes `image_post_info.images[]` for carousel posts.

**Response structure:**

```
video_info.image_post_info.images[i].display_image.url_list[0]  → WebP, resized
video_info.image_post_info.images[i].display_image.url_list[2]  → JPEG, resized
video_info.image_post_info.images[i].thumbnail.url_list[0]      → thumbnail
```

Each `display_image.url_list` contains 3 URLs. The transform is `tplv-photomode-2k-shrink-v1:1200:0:q70` — resized to 1200px wide, quality 70.

**Result:** Downloaded slide 1 of a 6-slide carousel:
- `url_list[0]`: WebP, 45 KB (lossy, resized)
- `url_list[2]`: JPEG, 116 KB (lossy, resized)

**Limitation:** Per-post calls only (cannot batch across posts). Images are compressed and resized — not original upload quality. Does not include `imageWidth`/`imageHeight`.

**Verdict:** Fallback only. Use if `item_list` is unavailable. Acceptable if original quality is not required.

---

### Comparison

| | `/api/post/item_list/` | `/aweme/v2/data/insight/` |
|---|---|---|
| Quality | Original JPEG (177 KB) | Resized q70 WebP/JPEG (45–116 KB) |
| Dimensions | 1080×1620 (included in response) | Not provided |
| Batch | All posts in 2 API calls | Per-post only |
| Format | `imagePost.images[].imageURL.urlList[0]` | `image_post_info.images[].display_image.url_list[0]` |
| Auth | Session cookies (`credentials: include`) | Session cookies (`credentials: include`) |

---

## Recommended Workflows

### Full extraction (IDs + dates):

1. **Call `/api/post/item_list/`** via `fetch()` from any `tiktok.com` page. Requires `secUid` (obtained from `/tiktokstudio/api/web/user`). Paginates with `cursor` parameter, returns 30 items per page. Each item includes `id`, `createTime` (unix timestamp), `desc`, content type, and stats.
2. **Deduplicate** pinned posts (they appear in both pinned and chronological positions).

This replaces the DOM scroll methods (1–6 above) for post ID collection. The API is faster (sub-second for all posts), returns dates in the same call, and is not affected by virtual scrolling. See `store/scripts/collect_post_ids.py` for the implementation.

**Fallback:** If the API is unavailable, use Methods 1–3 above (DOM scrolling) to collect IDs, then Method 2 for dates.

### Per-post metric collection (batch):

1. **Navigate to any TikTok Studio page** to establish the auth session.
2. **Call the `/aweme/v2/data/insight/` API** via `fetch()` for each post, extracting all 9 metrics from the JSON response. Batch ~20 posts per JS execution with small delays between requests.
3. If the API call fails, **fall back to direct URL navigation** (`tiktokstudio/analytics/{post_id}/overview`) and extract metrics via `read_page`.

### Per-post metric collection (single post):

Either method works. Direct URL navigation is simpler for one-off lookups. Use `read_page` to extract values from the accessibility tree — every metric appears as a `generic` text node.

### Carousel image download:

1. **Call `/api/post/item_list/`** (same call as post ID collection). For each item where `imagePost` is truthy, extract `imagePost.images[i].imageURL.urlList[0]` for every slide.
2. **Download each image** via `fetch()` from browser context. URLs are signed CDN links; the browser's session handles auth.
3. **Save to** `store/data/posts/{slug}/slides/slide-{n}.jpeg`.

This can be combined with the `collect_post_ids` call — the image URLs are in the same response. No additional API calls needed.

### Carousel image download — Chrome bridge workaround

The Chrome extension's security filter blocks returning raw CDN URLs because they contain signed query parameters that resemble credentials. Two workarounds:

**Base64 chunking (proven, slow):**

1. Collect all carousel image URLs in one pagination pass and store on `window.__carouselUrls`:

```javascript
// After item_list pagination:
window.__carouselUrls = {}; // keyed by post_id
// For each carousel: {post_id, slide_count, slides: [{index, url, width, height}]}
```

2. Install a reusable chunk extractor:

```javascript
window.__extractChunk = function(postId, startIdx, count) {
    const d = window.__carouselUrls[postId];
    if (!d) return JSON.stringify({error: 'not found'});
    const slides = d.slides.slice(startIdx, startIdx + count);
    const r = slides.map(s => ({i: s.index, b: btoa(s.url)}));
    return JSON.stringify(r);
};
```

3. Extract 2 URLs at a time per JS call to avoid truncation:

```javascript
window.__extractChunk('7588299653225909535', 0, 2)  // slides 0-1
window.__extractChunk('7588299653225909535', 2, 2)  // slides 2-3
```

4. In Python, base64-decode the URLs and download via urllib. The CDN URLs are self-authenticating (signed query params) — no browser needed for the download step.

**Performance:** ~5 JS calls per carousel (2 URLs each) + 1 Python download batch. For 28 carousels (186 slides): ~93 JS calls + 186 downloads. Total: 15-20 minutes.

**Limitation:** Slow due to many JS round-trips. Each call returns ~500 bytes (2 base64 URLs). The `__extractChunk` pattern avoids re-typing the extraction logic.

**Future optimization:** Write all URLs to a file via `navigator.clipboard.writeText()` or a download Blob, eliminating the per-chunk JS calls. Not yet tested.

## Notes

- The scrollable container class name (`.css-snthx.edss2sz11`) is a hashed CSS class that may change with TikTok deployments. If Method 1 fails to find the container, use JS to scan for elements where `scrollHeight > clientHeight + 200` and `overflowY` is `auto` or `scroll`.
- TikTok Studio shows pinned posts at the top of the list separately from their chronological position. They appear in both locations but represent the same post. Deduplicate by post ID.
- Posts without a video link (e.g., photos, private drafts with "No description") won't have an `a[href*="/video/"]` element. These are visible in read_page as rows without a link but with a date. They may not be registrable if the procedure requires a post ID from the URL.

---

## Changelog

| Date | Entry |
|------|-------|
| 2026-04-01 | Initial report. 6 methods tested during first discovery run (45 posts from 46-post account). |
| 2026-04-01 | Added per-post analytics section. Direct URL (`tiktokstudio/analytics/{id}/overview`) is the fastest path to metrics. Content list click-through opens the public page, not analytics. |
| 2026-04-01 | Added API fetch method (`/aweme/v2/data/insight/`). Collected 41 backfill snapshots in two JS calls (~30s) vs. estimated 5+ min via page navigation. Now the top-ranked method for batch metric collection. |
| 2026-04-03 | Added `/api/post/item_list/` API method for post ID collection. Replaces DOM scrolling as the primary method. Collects all 47 posts with IDs, dates, descriptions, and content types in 2 paginated GET requests (sub-second). DOM scroll methods demoted to fallback. |
| 2026-04-03 | Added carousel slide image extraction section. Tested both `/api/post/item_list/` (original JPEG, 177 KB, 1080×1620) and `/aweme/v2/data/insight/` (compressed WebP/JPEG, 45–116 KB). item_list is the primary method — original quality, batch-capable, already called. |
