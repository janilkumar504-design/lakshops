# LAKSH Ops - an on-call copilot that remembers (Hindsight)

**One persona:** the on-call SRE. **One workflow:** alert -> triage -> resolve -> learn.
**One value prop:** stop re-learning the same outage. LAKSH (your voice assistant) now recalls
past incidents, the fixes that worked, the fixes that failed, and how each engineer likes to be briefed.

## How Hindsight is used (memory is the product)

| Step | Hindsight call | What gets stored / asked |
|---|---|---|
| Setup | `create_bank(mission, retain_mission, reflect_mission)` | Bank tuned for SRE memory, one shared bank per team |
| Resolve an incident | `retain(content, timestamp, tags, metadata)` | Incident narrative + one memory per **fix that worked** + one per **fix that failed**. Tags: `service:` `cause:` `trigger:` `day:` `outcome:` `engineer:` |
| Engineer says "that didn't work" | `retain(...)` tagged `kind:feedback`, `outcome:failed_fix` | Negative memory - never lead with that fix again |
| "Remember that I like commands" | `retain(...)` tagged `kind:preference`, `engineer:` | Per-engineer response style |
| New alert | `recall(query, tags=[service:X], tags_match="any_strict")` + a second recall for the engineer's preferences | Ranked past fixes, failures to skip, style |
| "What patterns keep recurring?" / weekly handover | `reflect(query, context)` | Cross-incident insight: repeat causes, risky deploy days, fixes that keep failing |

**Learning over time (demo arc):** empty memory gives the generic checklist -> one resolution later the
same alert returns the exact fix and says "skip restarting pods" -> different engineers get different
formats -> `reflect` surfaces team-level patterns. The UI's *without vs with memory* view and the
*Memories used* panel make this visible.

## Laksh integration
`laksh.py` is your original, untouched. `laksh_voice.py` subclasses it: ops phrases go to `OpsBrain`,
everything else (open apps, YouTube, WhatsApp...) still runs through Laksh. PC actions you take during
an active incident (e.g. "open grafana") are attached to that incident's timeline when you say *resolved*.

Voice phrases: `alert payments-api latency ...` · `resolved payments-api pool exhaustion, restart did not help, fixed by rolling back the deploy took 47 min` · `that didn't work` (or `step 2 didn't work`) · `remember that I like exact commands` · `what patterns keep recurring`

## Run it (Windows)
Unzip, open a terminal **inside the `laksh-ops` folder** (type `cmd` in the Explorer address bar), then:
```bat
laksh setup     REM installs packages (uses Python 3.11 if present)
laksh check     REM proves the Hindsight connection works
laksh demo      REM scripted learning-over-time demo
laksh text      REM interactive console, no microphone needed
laksh web       REM web UI at http://localhost:8000  (click "Load 6 weeks of history")
laksh phone     REM same, reachable from your phone on the same Wi-Fi
laksh voice     REM Laksh voice assistant + memory (needs microphone + PyAudio)
laksh test      REM self-tests
```
(`python run.py <command>` does the same on any OS.) Settings live in `.env`. `HINDSIGHT_URL` is the **API**
(`https://api.hindsight.vectorize.io`), not the `ui.` dashboard. If Hindsight is unreachable or errors mid-run, the app
warns and continues on a local store (badge: `memory: local-fallback`); set `LAKSH_REQUIRE_HINDSIGHT=1` to fail loudly for the judges' demo.
`laksh voice --install-startup` registers the memory-enabled version to start with Windows.

## On your phone
The web UI is an installable PWA (manifest + service worker, touch layout, speech in/out). The memory lives in
Hindsight, so your phone and laptop share the same bank. Voice input (mic) needs **HTTPS**; typing works anywhere.

1. **Same Wi-Fi, quickest:** `laksh phone` prints the address to open
   on the phone (allow Python through the Windows firewall). Typing works; mic will not (plain http).
2. **HTTPS from your laptop (mic works):** run the server, then `cloudflared tunnel --url http://localhost:8000`
   (or `ngrok http 8000`) and open the https link on your phone. **Set `LAKSH_ACCESS_TOKEN` first** - the link is public.
3. **Always-on cloud deploy:** push this folder to GitHub, create a Render "Blueprint" from `render.yaml` (or any Docker host),
   fill `HINDSIGHT_API_KEY`, `LAKSH_ACCESS_TOKEN`, `GEMINI_API_KEY` in the dashboard. Open the URL on your phone,
   then Chrome menu -> *Install app* / Safari -> *Add to Home Screen*. The UI asks for the token once.

Phone limits: it runs the incident copilot (triage, resolve, feedback, patterns). Laksh's PC control (open apps, YouTube,
WhatsApp, volume) only works on the Windows laptop running `laksh_voice.py`.

## Layout
`laksh_ops/memory.py` Hindsight + fallback backends · `triage.py` workflow · `brain.py` intent router ·
`seed_data.py` simulated history · `server.py` + `static/` (PWA UI) · `check_hindsight.py` · `Dockerfile` + `render.yaml` · `laksh_voice.py` voice wrapper.

## Known limits
- Tested end to end on the local fallback; the Hindsight calls match the installed `hindsight-client` signatures but were not run against a live server here. Verify the recalled `tags`/`metadata` round-trip on your instance (the planner degrades to showing recalled facts if they don't).
- Fixes are grouped by exact text; free-text fixes from a real team would want normalization.
- `laksh_cache.json` (your scanned app paths) is machine-specific and not included; Laksh regenerates it.
- Set `GEMINI_API_KEY` in `.env` instead of editing `laksh.py`; the ops briefing uses `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` if present, else a template.
