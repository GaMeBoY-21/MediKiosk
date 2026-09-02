#!/usr/bin/env bash
#
# Start the whole MediKiosk stack for a demo. The only thing to run on the day.
#
#   ./dev.sh            start everything, live
#   ./dev.sh --replay   start with VITE_REPLAY=true (no network, no API quota)
#   ./dev.sh --check    run preflight only and exit
#
# Launcher only: it never edits app/, ai/ or frontend/, and never prints the
# contents of .env or any secret -- presence is reported, values are not.

set -euo pipefail

# Job control, so each child lands in its own process group and can be killed
# as a group. uvicorn --reload forks a worker; killing only the parent leaves
# that worker holding :8000, which is how the port ends up occupied next time.
set -m

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"
VENV="$ROOT/venv"
ENV_FILE="$ROOT/app/.env"
CRED_FILE="$ROOT/app/.demo-credentials"
HEALTH_TIMEOUT=30

REPLAY=false
CHECK_ONLY=false

API_PID=""
WEB_PID=""

# ---------------------------------------------------------------- output

if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
  BOLD="$(tput bold)"; RED="$(tput setaf 1)"; GREEN="$(tput setaf 2)"
  YELLOW="$(tput setaf 3)"; DIM="$(tput dim)"; RESET="$(tput sgr0)"
else
  BOLD=""; RED=""; GREEN=""; YELLOW=""; DIM=""; RESET=""
fi

ok()   { printf '  %s[ok]%s   %s\n' "$GREEN" "$RESET" "$1"; }
warn() { printf '  %s[warn]%s %s\n' "$YELLOW" "$RESET" "$1"; }
info() { printf '  %s[..]%s   %s\n' "$DIM" "$RESET" "$1"; }

# Every failure names the file and the command that fixes it. A preflight that
# just says "failed" costs more time than no preflight at all.
die() {
  printf '\n  %s[FAIL] %s%s\n' "$RED$BOLD" "$1" "$RESET" >&2
  shift
  for line in "$@"; do printf '    %s\n' "$line" >&2; done
  printf '\n' >&2
  exit 1
}

# ------------------------------------------------------------------ args

usage() {
  cat <<'USAGE'
Usage: ./dev.sh [--replay] [--check]

  --replay   Serve the recorded session (VITE_REPLAY=true). No network, no
             Gemini quota. A red REPLAY badge shows on every screen.
  --check    Run preflight checks only, then exit. Run this before a rehearsal.
  --help     This message.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --replay) REPLAY=true ;;
    --check)  CHECK_ONLY=true ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1" "Run ./dev.sh --help for usage." ;;
  esac
  shift
done

# ------------------------------------------------------------- port check

# lsof is on macOS and most Linux images; ss/netstat cover the rest.
pids_on_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
  elif command -v ss >/dev/null 2>&1; then
    ss -lptnH "sport = :$port" 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u || true
  else
    netstat -anv 2>/dev/null | awk -v p=":$port" '$0 ~ p && /LISTEN/ {print $9}' | sort -u || true
  fi
}

require_free_port() {
  local port="$1" what="$2" pids
  pids="$(pids_on_port "$port")"
  [ -z "$pids" ] && { ok "port $port free ($what)"; return 0; }

  local detail=""
  for p in $pids; do
    local cmd
    cmd="$(ps -o comm= -p "$p" 2>/dev/null | sed 's|.*/||' || true)"
    detail="${detail}    PID $p  ${cmd:-unknown}"$'\n'
  done
  die "port $port is already in use ($what)" \
      "Something is already listening. Usually a previous run that was not shut down." \
      "" \
      "${detail%$'\n'}" \
      "" \
      "Free it with:" \
      "    kill $(echo "$pids" | tr '\n' ' ')" \
      "or, if it will not go quietly:" \
      "    kill -9 $(echo "$pids" | tr '\n' ' ')"
}

# ---------------------------------------------------------------- env read

# Reads one key WITHOUT echoing its value anywhere. Used for presence checks
# and for the two non-secret values shown in the summary (model, username).
env_value() {
  local key="$1" file="$2"
  [ -f "$file" ] || return 0
  sed -n "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//p" "$file" \
    | head -1 | sed 's/[[:space:]]*$//' | tr -d '"'"'"''
}

# ---------------------------------------------------------------- preflight

preflight() {
  printf '\n%sPreflight%s\n' "$BOLD" "$RESET"

  # --- python + venv
  command -v python3 >/dev/null 2>&1 \
    || die "python3 not found" "Install Python 3.11+ and re-run." \
           "  macOS:  brew install python@3.12" \
           "  Debian: sudo apt install python3 python3-venv"
  ok "python3 $(python3 --version 2>&1 | awk '{print $2}')"

  if [ ! -x "$VENV/bin/python" ]; then
    warn "no virtualenv at venv/ -- creating one (first run only)"
    python3 -m venv "$VENV" \
      || die "could not create the virtualenv" \
             "Try:  python3 -m venv venv" \
             "On Debian/Ubuntu you may need:  sudo apt install python3-venv"
    ok "created venv/"
  else
    ok "venv/ present"
  fi

  PY="$VENV/bin/python"

  # Deps live in the venv, not the system interpreter. Checked by import
  # rather than by pip list, because that is what actually has to work.
  if ! "$PY" -c 'import fastapi, uvicorn, sqlalchemy, pydantic_settings' >/dev/null 2>&1; then
    warn "backend dependencies missing in venv/ -- installing (first run only)"
    "$PY" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
    "$PY" -m pip install --quiet -r "$ROOT/requirements.txt" \
      || die "pip install failed" \
             "Install by hand and re-run:" \
             "    venv/bin/python -m pip install -r requirements.txt"
    ok "installed backend dependencies"
  else
    ok "backend dependencies present"
  fi

  # --- secrets: presence only, never the value
  [ -f "$ENV_FILE" ] \
    || die "app/.env is missing" \
           "The backend reads its key and model from that file." \
           "Create it from the template:" \
           "    cp .env.example app/.env" \
           "then fill in GEMINI_API_KEY and GEMINI_MODEL."

  # Count the key pool. Values are never printed -- only how many there are.
  # Quota is metered per Google Cloud project, so these have to come from
  # different accounts to be worth anything; .env.example says so.
  local key model fallback n found=0 models=1
  for n in 1 2 3 4 5; do
    [ -n "$(env_value "GEMINI_API_KEY_$n" "$ENV_FILE")" ] && found=$((found + 1))
  done
  key="$(env_value GEMINI_API_KEY "$ENV_FILE")"
  if [ "$found" -eq 0 ] && [ -n "$key" ]; then
    found=1
  fi
  [ "$found" -gt 0 ] \
    || die "no Gemini API key in app/.env" \
           "Set at least one of:" \
           "    GEMINI_API_KEY=..." \
           "    GEMINI_API_KEY_1=...   (through GEMINI_API_KEY_5)" \
           "Get keys at https://aistudio.google.com/apikey" \
           "Each numbered key must come from a DIFFERENT Google account:" \
           "quota is per project, so five keys from one account share one" \
           "allowance and buy nothing." \
           "" \
           "Or demo without any API at all:" \
           "    ./dev.sh --replay"
  ok "Gemini keys: $found configured in app/.env (values not shown)"

  model="$(env_value GEMINI_MODEL "$ENV_FILE")"
  [ -n "$model" ] \
    || die "GEMINI_MODEL is not set in app/.env" \
           "Deliberately has no default -- Google retires model names without" \
           "notice and a stale default takes the whole app down with 404s." \
           "Set, for example:" \
           "    GEMINI_MODEL=gemini-3.5-flash-lite"
  ok "GEMINI_MODEL = $model"
  MODEL="$model"

  fallback="$(env_value GEMINI_MODEL_FALLBACK "$ENV_FILE")"
  if [ -n "$fallback" ]; then
    models=2
    MODEL_FALLBACK="$fallback"
    ok "GEMINI_MODEL_FALLBACK = $fallback"
  else
    MODEL_FALLBACK=""
    ok "GEMINI_MODEL_FALLBACK unset (single-model pool)"
  fi

  # The number that matters on the day: how many independent daily quotas.
  KEY_COUNT="$found"
  MODEL_COUNT="$models"
  POOL_COUNT=$((found * models))
  ok "Gemini: $found keys x $models models = $POOL_COUNT pools"

  # --- node + frontend deps
  command -v node >/dev/null 2>&1 \
    || die "node not found" "Install Node 18+ and re-run." "  macOS: brew install node"
  command -v npm >/dev/null 2>&1 \
    || die "npm not found" "It ships with Node. Reinstall Node and re-run."
  ok "node $(node --version) / npm $(npm --version)"

  if [ ! -d "$ROOT/frontend/node_modules" ]; then
    warn "frontend/node_modules missing -- running npm install (first run only)"
    ( cd "$ROOT/frontend" && npm install ) \
      || die "npm install failed" "Install by hand and re-run:" "    cd frontend && npm install"
    ok "installed frontend dependencies"
  else
    ok "frontend/node_modules present"
  fi

  # --- database: say which one, so it is never a surprise mid-demo
  local dburl
  dburl="$(env_value DATABASE_URL "$ENV_FILE")"
  [ -z "$dburl" ] && dburl="$(env_value DATABASE_URL "$ROOT/.env")"
  if [ -n "$dburl" ]; then
    if "$PY" - "$dburl" <<'PYCHECK' >/dev/null 2>&1
import sys
from sqlalchemy import create_engine
create_engine(sys.argv[1]).connect().close()
PYCHECK
    then
      ok "PostgreSQL reachable -- demoing on Postgres"
      DB_MODE="PostgreSQL"
    else
      die "DATABASE_URL is set but the database is not reachable" \
          "Start it, or unset DATABASE_URL in app/.env to use the SQLite fallback." \
          "  macOS:  brew services start postgresql" \
          "  Linux:  sudo systemctl start postgresql"
    fi
  else
    ok "DATABASE_URL not set -- using the SQLite fallback (./medikiosk.db)"
    DB_MODE="SQLite (medikiosk.db)"
  fi

  # --- ports
  require_free_port "$API_PORT" "backend"
  require_free_port "$WEB_PORT" "frontend"

  # --- replay fixture, only when it is about to be used
  if [ "$REPLAY" = true ]; then
    [ -f "$ROOT/frontend/public/replay/session.json" ] \
      || die "--replay requested but no recording exists" \
             "Record one against a running backend:" \
             "    ./dev.sh            # in one terminal" \
             "    python3 scripts/record_replay.py"
    ok "replay recording present"
  fi

  printf '  %s%s all checks passed%s\n' "$GREEN" "$BOLD" "$RESET"
}

# ----------------------------------------------------------------- cleanup

# Kill a whole process group. uvicorn --reload has a worker child; the Vite
# dev server has an esbuild child. Killing only the parent orphans those, and
# the orphan keeps the port.
kill_group() {
  local pid="$1"
  [ -n "$pid" ] || return 0
  kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
}

CLEANED=false
SHUTTING_DOWN=false
cleanup() {
  $CLEANED && return 0
  CLEANED=true
  # Tells the supervisor that the children are about to die on purpose, so a
  # clean Ctrl-C does not report "the backend exited" as if something broke.
  SHUTTING_DOWN=true

  # Nothing was started -- a preflight failure, --check, or --help. There is
  # nothing of ours to stop, and anything currently on those ports belongs to
  # somebody else. Preflight already printed the PID and the kill command; it
  # is not this script's business to kill a process it did not spawn.
  if [ -z "$API_PID" ] && [ -z "$WEB_PID" ]; then
    return 0
  fi

  printf '\n%sShutting down...%s\n' "$BOLD" "$RESET"
  kill_group "$WEB_PID"
  kill_group "$API_PID"

  # Give them a moment, then make sure the ports are actually released -- the
  # whole point of the trap is that the next run is not blocked.
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    [ -z "$(pids_on_port "$API_PORT")$(pids_on_port "$WEB_PORT")" ] && break
    sleep 0.3
  done
  # Force only what descends from the two processes we started. Killing
  # whatever happens to hold the port would take out an unrelated program.
  for pid in "$WEB_PID" "$API_PID"; do
    [ -n "$pid" ] || continue
    if kill -0 "$pid" 2>/dev/null; then
      warn "pid $pid did not stop, forcing"
      kill -KILL -"$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    fi
  done
  ok "both ports released"
}
trap cleanup EXIT INT TERM

# ----------------------------------------------------------------- startup

preflight

if [ "$CHECK_ONLY" = true ]; then
  printf '\n%sPreflight only (--check). Nothing was started.%s\n\n' "$DIM" "$RESET"
  trap - EXIT INT TERM
  exit 0
fi

printf '\n%sStarting%s\n' "$BOLD" "$RESET"

# --- backend
"$VENV/bin/python" -m uvicorn app.main:app --reload --port "$API_PORT" \
  > >(awk '{ print "[api] " $0; fflush() }') 2>&1 &
API_PID=$!
info "uvicorn started (pid $API_PID), waiting for /health..."

# The frontend must NOT start before the backend answers. Starting it early is
# what produced the "Something went wrong" screen twice this week: the kiosk
# calls /session/start on load, gets a connection refused, and shows the error
# screen before the API has finished booting.
deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
healthy=false
while [ "$(date +%s)" -lt "$deadline" ]; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    die "the backend exited during startup" \
        "Scroll up for the [api] traceback." \
        "Common causes: a bad GEMINI_API_KEY, or a syntax error in app/."
  fi
  if curl -fsS -m 2 "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
    healthy=true
    break
  fi
  sleep 0.5
done

$healthy || die "backend did not answer /health within ${HEALTH_TIMEOUT}s" \
                "It is running but not serving. Scroll up for the [api] log." \
                "Check nothing else is bound to :$API_PORT."
ok "backend healthy on :$API_PORT"

# --- frontend
if [ "$REPLAY" = true ]; then
  export VITE_REPLAY=true
  info "REPLAY mode: serving the recorded session, no API calls"
fi

( cd "$ROOT/frontend" && npm run dev -- --port "$WEB_PORT" --strictPort ) \
  > >(awk '{ print "[web] " $0; fflush() }') 2>&1 &
WEB_PID=$!
info "vite started (pid $WEB_PID), waiting for :$WEB_PORT..."

deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
served=false
while [ "$(date +%s)" -lt "$deadline" ]; do
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    die "the frontend exited during startup" "Scroll up for the [web] log."
  fi
  if curl -fsS -m 2 "http://localhost:$WEB_PORT/" >/dev/null 2>&1; then
    served=true
    break
  fi
  sleep 0.5
done

$served || die "frontend did not serve within ${HEALTH_TIMEOUT}s" "Scroll up for the [web] log."
ok "frontend serving on :$WEB_PORT"

# ------------------------------------------------------------------ summary

MODE="LIVE"
$REPLAY && MODE="REPLAY  (recorded session, no network, no quota)"
USERNAME="$(env_value CLINICIAN_USERNAME "$ENV_FILE")"
[ -n "$USERNAME" ] || USERNAME="(none seeded -- set CLINICIAN_USERNAME in app/.env)"

cat <<SUMMARY

${BOLD}MediKiosk is up${RESET}

  Backend   http://localhost:${API_PORT}        (docs at /docs)
  Kiosk     http://localhost:${WEB_PORT}
  Console   http://localhost:${WEB_PORT}/physician
  Mode      ${MODE}
  Model     ${MODEL}${MODEL_FALLBACK:+  (fallback: ${MODEL_FALLBACK})}
  Gemini    ${KEY_COUNT} keys x ${MODEL_COUNT} models = ${POOL_COUNT} pools
            status at http://localhost:${API_PORT}/api/health/providers
  Database  ${DB_MODE}
  Login     ${USERNAME}  (password in app/.demo-credentials)

${DIM}Ctrl-C stops both.${RESET}

SUMMARY

# ------------------------------------------------------------- supervise

# Whichever dies first, say which and take the other down with it. A half-dead
# stack mid-demo looks like a frontend bug and is not.
while true; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    $SHUTTING_DOWN && exit 0
    wait "$API_PID" 2>/dev/null && code=0 || code=$?
    printf '\n%s[FAIL] the backend (uvicorn) exited -- status %s%s\n' "$RED$BOLD" "$code" "$RESET" >&2
    printf '  Scroll up for the [api] log. Stopping the frontend too.\n' >&2
    exit 1
  fi
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    $SHUTTING_DOWN && exit 0
    wait "$WEB_PID" 2>/dev/null && code=0 || code=$?
    printf '\n%s[FAIL] the frontend (vite) exited -- status %s%s\n' "$RED$BOLD" "$code" "$RESET" >&2
    printf '  Scroll up for the [web] log. Stopping the backend too.\n' >&2
    exit 1
  fi
  sleep 1
done
