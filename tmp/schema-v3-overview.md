# Database Schema v3

`store/data/analytics/analytics.db`

---

```
┌─────────────────────────────────┐
│            posts                │  Universal TikTok data (any account)
├─────────────────────────────────┤
│ post_id        TEXT PK          │
│ posted_date    TEXT NOT NULL    │
│ posted_time    TEXT             │  <- stub
│ description    TEXT             │
│ hashtags       TEXT             │
│ content_type   TEXT             │  carousel | video | photo
│ aweme_type     INTEGER          │
│ sound_name     TEXT             │
│ sound_type     TEXT             │  <- stub
│ slide_count    INTEGER          │
│ content_path   TEXT             │
│ content_topics TEXT             │  <- stub (universal)
└────────┬───────┬───────┬────────┘
         │       │       │
         │       │       │
    ┌────▼──────────────┐│  ┌────▼──────────────┐
    │ carousel_details  ││  │  video_details    │
    ├───────────────────┤│  ├───────────────────┤
    │ post_id   TEXT PK ││  │ post_id   TEXT PK │──FK-> posts
    │ slide_texts  TEXT ││  │ duration  REAL    │  <- stub
    │ visual_sum   TEXT ││  └───────────────────┘
    │ has_cta   INTEGER ││
    │ cta_type    TEXT  ││
    │ cta_text    TEXT  ││
    └───────────────────┘│
     FK-> posts          │
                         │
    ┌────────────────────▼──────┐
    │  nexus_post_metadata      │  Company-specific (Nexus only)
    ├───────────────────────────┤
    │ post_id      TEXT PK      │──FK-> posts
    │ slug         TEXT UNIQUE  │
    │ city         TEXT         │
    │ framework    TEXT         │
    │ slide_layout TEXT         │  free text, not enum
    └───────────────────────────┘


┌───────────────────────────────────────┐
│             readings                  │  Performance snapshots (universal)
├───────────────────────────────────────┤
│ post_id                 TEXT          │──FK-> posts
│ captured_at             TEXT          │  +00:00 UTC
│ hours_since_post        INTEGER       │
│ type                    TEXT          │  velocity | snapshot
│ views                   INTEGER       │
│ likes                   INTEGER       │
│ comments                INTEGER       │
│ shares                  INTEGER       │
│ bookmarks               INTEGER       │
│ new_followers           INTEGER       │  snapshot only
│ avg_watch_time_seconds  REAL          │  snapshot only
│ watched_full_percent    REAL          │  snapshot only
│ fyp_percent             REAL          │  snapshot only
│ profile_visits          INTEGER       │  <- stub
│ search_percent          REAL          │  via API
│ profile_percent         REAL          │  via API
│ following_percent       REAL          │  via API
│ other_percent           REAL          │  via API
│                                       │
│ PK: (post_id, captured_at)            │
└───────────────────────────────────────┘


┌───────────────────────────────┐
│           account             │  Account-level checkpoints (universal)
├───────────────────────────────┤
│ captured_date  TEXT PK        │
│ followers      INTEGER        │
│ total_likes    INTEGER        │
└───────────────────────────────┘
```

**<- stub** = column exists, all values currently NULL. Ready for data when collection expands.
