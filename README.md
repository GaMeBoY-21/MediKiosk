# MediKiosk

An AI-assisted patient intake kiosk that conducts a guided interview, extracts structured clinical data, and hands off a physician-reviewable summary.

## Running it

One command starts everything:

```
./dev.sh
```

It runs a preflight first (virtualenv, dependencies, `app/.env`, node modules,
free ports, database), starts the backend, waits for `/health` to actually
answer, and only then starts the kiosk. If anything is wrong it stops and names
the file and the command that fixes it.

```
./dev.sh --check     preflight only — run this before a rehearsal
./dev.sh --replay    serve the recorded session: no network, no API quota
./dev.sh --help      usage
```

Both processes run in the foreground with their logs interleaved and prefixed
`[api]` and `[web]`. **Ctrl-C stops both**, including uvicorn's reload worker —
nothing is left holding a port for the next run.

When it is up:

| | |
|---|---|
| Backend | <http://localhost:8000> (API docs at `/docs`) |
| Kiosk | <http://localhost:5173> |
| Physician console | <http://localhost:5173/physician> |

The startup block also prints which model is in use, whether the database is
Postgres or the SQLite fallback, and whether the mode is LIVE or REPLAY — so
what is being demonstrated is never in doubt.

### Before the first run

`app/.env` is not in git. Create it and set two values:

```
GEMINI_API_KEY=...             # https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.5-flash-lite
```

`GEMINI_MODEL` has no default on purpose: Google retires model names without
notice, and a stale default fails every request with a 404.

For the physician console, `app/.env` also needs `AUTH_SECRET`,
`CLINICIAN_USERNAME` and `CLINICIAN_PASSWORD`. See `.env.example` for the full
list. The demo login is printed at startup; its password is in
`app/.demo-credentials`, which is also not in git.

`DATABASE_URL` is optional. Leave it unset and the backend uses a local SQLite
file, which is what the demo runs on.

### If the venue wifi fails

```
./dev.sh --replay
```

Serves a real recorded session from `frontend/public/replay/session.json` —
genuine model output, genuine red flag — with no API calls at all. A red
**REPLAY** badge stays on screen throughout so a recording is never mistaken
for a live run. Re-record with `python3 scripts/record_replay.py` while the
stack is running.

## Tests

```
python3 -m unittest discover -s ai -p "test_*.py"
```
