# CLAUDE.md — Study Companion

## Shared PM2 Setup — READ BEFORE TOUCHING PROCESSES

This Mac runs multiple web apps under a single PM2 instance (user: `family`). **Killing PM2 or running `pm2 delete all` / `pm2 kill` will take down ALL of these sites, not just this one.**

### Current PM2 Processes

| PM2 Name | Port | App | Directory | Start Command |
|----------|------|-----|-----------|---------------|
| `couple-companion` | 8000 | Couple Companion | `/Volumes/External/claude_projects/counseling_apps/couple_companion` | `pm2 start .venv/bin/uvicorn --name couple-companion --interpreter none -- main:app --port 8000` |
| `mighty-oaks` | 3000 | MightyOaks LMS | `/Volumes/NetworkStorage/hybrid` | `pm2 start server.js --name mighty-oaks` |
| `adhd-align` | 5003 | ADHD/Align | `/Volumes/External/adhd` | `pm2 start npm --name adhd-align -- start -- -p 5003` |
| `study-companion` | — | **This app (Study Companion)** | `/Volumes/External/Logos4/tools/workbench` | `pm2 start app.py --name study-companion --interpreter python3` |

TendFlock (port 3001) runs under a separate `tendflock` user with its own PM2 — it is not in this process list.

### Rules

- **NEVER run `pm2 kill`, `pm2 delete all`, or `pm2 stop all`** — this kills every app above
- **NEVER kill processes on ports 3000, 5003, 8000, or 3001** — those are other apps
- Only restart **this app** by name: `pm2 restart study-companion`
- After any PM2 change, run `pm2 save` to persist across reboots
- PM2 auto-starts on boot via a LaunchAgent (`~/Library/LaunchAgents/pm2.family.plist`)

### If This App Needs to Be Re-Added to PM2

```bash
cd /Volumes/External/Logos4/tools/workbench
pm2 start app.py --name study-companion --interpreter python3
pm2 save
```

### If PM2 Itself Is Down

```bash
pm2 ping          # Check if PM2 daemon is alive
pm2 resurrect     # Restore all saved processes from ~/.pm2/dump.pm2
```

### Full PM2 Recovery (All Apps)

If `~/.pm2/dump.pm2` is corrupted and `pm2 resurrect` fails:

```bash
# Re-add each app manually
cd /Volumes/External/claude_projects/counseling_apps/couple_companion
pm2 start .venv/bin/uvicorn --name couple-companion --interpreter none -- main:app --port 8000

cd /Volumes/NetworkStorage/hybrid
pm2 start server.js --name mighty-oaks

cd /Volumes/External/adhd
pm2 start npm --name adhd-align -- start -- -p 5003

cd /Volumes/External/Logos4/tools/workbench
pm2 start app.py --name study-companion --interpreter python3

pm2 save
```
