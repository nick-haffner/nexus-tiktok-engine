# Backup Procedure

## Purpose

Snapshot all `.claude/` files to a local backup directory outside the
repository tree before destructive operations or session boundaries.
Backups are additive-only and locked after creation.

## Backup Location

`C:\Users\nickh\.claude-backups\nexusmvp\[ISO-timestamp]\`

Where `[ISO-timestamp]` is the current UTC time in `YYYY-MM-DDTHH-MM-SSZ`
format (colons replaced with hyphens for Windows path compatibility).

## Procedure

### 1. Create backup directory

```bash
BACKUP_DIR="C:/Users/nickh/.claude-backups/nexusmvp/$(date -u '+%Y-%m-%dT%H-%M-%SZ')"
mkdir -p "$BACKUP_DIR"
```

### 2. Copy all .claude/ files

```bash
cp -r .claude/. "$BACKUP_DIR/"
```

This copies all contents including dotfile directories (e.g., `.aras/`).
The `.` source avoids bash glob expansion, which skips dotfiles by default.
The `.claude/` directory itself is not copied — only its contents,
preserving the internal directory structure.

### 3. Lock backup (read-only)

```bash
attrib +R "$BACKUP_DIR"\\. //S
```

Sets all backed-up files to read-only. This prevents accidental
modification of historical backups.

### 4. Verify

Confirm the backup directory exists and contains files:

```bash
ls -a "$BACKUP_DIR"
```

If the directory is empty or does not exist, report failure to the
managing developer and halt the invoking protocol.

## Retention

Backups accumulate indefinitely for v1. No cleanup or rotation is
performed. Each invocation creates a new timestamped directory.

## Invocation Points

This procedure is invoked by:

- **cpm-pause** — before Step 3 (Update Documentation)
- **close-aras.md** — before Step 5 (Remove directory junctions)
- **close-branch.md** — before Step 5 (Remove directory junction)
