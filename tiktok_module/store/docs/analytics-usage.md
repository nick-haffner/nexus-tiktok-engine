# Analytics Database Usage

Practical reference for reading from and writing to the analytics database.

## Connecting

```python
import sqlite3

db_path = r"c:\Users\nickh\Repos\nexus-tiktok-engine\analytics\analytics.db"
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys=ON")  # Required — see schema doc
cur = conn.cursor()
```

No `sqlite3` CLI is installed on this machine. All database interaction goes through Python's `sqlite3` module.

## Writing Data

### Register a new post

```python
cur.execute("""
    INSERT INTO posts (
        post_id, posted_date, description, hashtags, content_type,
        aweme_type, sound_name, slide_count, content_path,
        slug, city, hook_text, framework, angle
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "7621390157509365023",        # post_id (from TikTok)
    "2026-03-25",                 # posted_date
    "Skip the lines...",          # description (full caption)
    "DallasTX,VisitDallas",       # hashtags (comma-separated, no #)
    "carousel",                   # content_type ("carousel", "video", "photo")
    150,                          # aweme_type (TikTok's raw code)
    "Bon Bon - Fcukers",          # sound_name (nullable)
    6,                            # slide_count
    "posts/austin-2026-03-25",    # content_path (nullable)
    "austin-2026-03-25",          # slug (nexus-specific, nullable)
    "Austin",                     # city (nexus-specific, nullable)
    "Local vs Tourist in Austin", # hook_text (nexus-specific, nullable)
    "local_vs_tourist",           # framework (nexus-specific, nullable)
    "broad_city_guide",           # angle (nexus-specific, nullable)
))
conn.commit()
```

### Write a velocity reading

```python
cur.execute("""
    INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "7621390157509365023",  # post_id
    "2026-03-26T14:30:00",  # captured_at (ISO 8601 datetime)
    24,                     # hours_since_post
    "velocity",             # type
    2400,                   # views
    89,                     # likes
    7,                      # comments
    3,                      # shares
    31,                     # bookmarks
    None,                   # new_followers (not captured for velocity)
    None,                   # avg_watch_time_seconds
    None,                   # watched_full_percent
    None                    # fyp_percent
))
conn.commit()
```

### Write a snapshot reading

```python
cur.execute("""
    INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "7621390157509365023",  # post_id
    "2026-03-30T10:00:00",  # captured_at (ISO 8601 datetime)
    120,                    # hours_since_post
    "snapshot",             # type
    28000,                  # views
    913,                    # likes
    43,                     # comments
    85,                     # shares
    426,                    # bookmarks
    53,                     # new_followers
    15.53,                  # avg_watch_time_seconds
    33.6,                   # watched_full_percent
    98.7                    # fyp_percent
))
conn.commit()
```

### Record account state

```python
cur.execute("""
    INSERT INTO account VALUES (?, ?, ?)
""", ("2026-03-30", 427, 12500))
conn.commit()
```

## Reading Data

### All posts with latest reading

```sql
SELECT p.slug, p.city, p.framework, p.posted_date,
       r.type, r.views, r.likes, r.bookmarks, r.new_followers,
       ROUND((r.likes+r.comments+r.shares)*100.0/r.views, 2) AS engagement_rate,
       ROUND(r.bookmarks*100.0/r.views, 2) AS save_rate
FROM posts p
JOIN readings r ON p.post_id = r.post_id
WHERE r.captured_at = (
    SELECT MAX(r2.captured_at)
    FROM readings r2
    WHERE r2.post_id = r.post_id
)
ORDER BY r.views DESC;
```

### Framework comparison (using snapshots only)

```sql
SELECT p.framework,
       COUNT(*) AS posts,
       ROUND(AVG(r.views)) AS avg_views,
       ROUND(AVG((r.likes+r.comments+r.shares)*100.0/r.views), 2) AS avg_engagement,
       ROUND(AVG(r.bookmarks*100.0/r.views), 2) AS avg_save_rate
FROM posts p
JOIN readings r ON p.post_id = r.post_id
WHERE r.type = 'snapshot' AND r.hours_since_post >= 120
GROUP BY p.framework
ORDER BY avg_views DESC;
```

### Velocity trajectory for a single post

```sql
SELECT r.captured_at, r.hours_since_post, r.views, r.likes, r.bookmarks,
       r.views - LAG(r.views) OVER (ORDER BY r.captured_at) AS view_delta
FROM readings r
WHERE r.post_id = ?
ORDER BY r.captured_at;
```

### Velocity baseline comparison

```sql
-- Compare a post's velocity at ~24h against the rolling average of recent posts at ~24h
SELECT r.post_id, p.slug, r.views AS views_at_24h,
       ROUND(AVG(r2.views), 0) AS avg_24h_views_recent,
       ROUND(r.views * 100.0 / AVG(r2.views), 0) AS pct_of_baseline
FROM readings r
JOIN posts p ON r.post_id = p.post_id
JOIN readings r2 ON r2.hours_since_post BETWEEN 20 AND 28
    AND r2.post_id != r.post_id
JOIN posts p2 ON r2.post_id = p2.post_id
    AND p2.posted_date >= date(p.posted_date, '-30 days')
WHERE r.hours_since_post BETWEEN 20 AND 28
    AND r.post_id = ?;
```

### Account growth trajectory

```sql
SELECT captured_date, followers,
       followers - LAG(followers) OVER (ORDER BY captured_date) AS delta
FROM account
ORDER BY captured_date;
```

### Follower conversion efficiency (snapshots only)

```sql
SELECT p.slug, r.views, r.new_followers,
       ROUND(r.new_followers*1000.0/r.views, 1) AS per_1k_views
FROM posts p
JOIN readings r ON p.post_id = r.post_id
WHERE r.type = 'snapshot' AND r.hours_since_post >= 164
ORDER BY per_1k_views DESC;
```

## Conventions

- **Datetimes:** ISO 8601. Dates as `YYYY-MM-DD`, timestamps as `YYYY-MM-DDTHH:MM:SS`.
- **Framework values:** Lowercase with underscores (`local_vs_tourist`, `worth_it`, `24_hour_test`, `overrated_vs_underrated`).
- **Angle values:** Lowercase with underscores (`broad_city_guide`, `category_deep_dive`, `worth_it_list`).
- **Content type values:** `carousel`, `video`, `photo`.
- **Slug format:** `city-YYYY-MM-DD`, lowercase, hyphens (`nashville-2026-03-30`).
- **Hashtags format:** Comma-separated, `#` stripped (`DallasTX,VisitDallas,FoodFinds`).
- **Content path format:** Relative from `tiktok_module/` (`posts/nashville-2026-03-30`).
- **Nullable fields:** All posts columns except `post_id` and `posted_date`. On readings: `new_followers`, `avg_watch_time_seconds`, `watched_full_percent`, `fyp_percent` (velocity reads omit these).
