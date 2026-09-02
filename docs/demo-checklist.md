# Demo day

Friday morning, in order. Each step says what you should see. If a step does
not match, the fix is on the same line — do not improvise.

Read the two boxes at the bottom BEFORE you start. They are the things that
are not what you would guess.

---

## 1. Fresh start (2 minutes before)

Always restart, even if it looks fine. The key pool retires spent keys for the
lifetime of the process, so yesterday's exhausted keys stay exhausted in a
server that has been running overnight. A restart clears that.

```
cd ~/projects/Medikiosk
./dev.sh --check
```

Expect, near the end:

```
  [ok]   Gemini keys: 5 configured in app/.env (values not shown)
  [ok]   GEMINI_MODEL = gemini-3.5-flash-lite
  [ok]   GEMINI_MODEL_FALLBACK = gemini-2.0-flash
  [ok]   Gemini: 5 keys x 2 models = 10 pools
  Preflight passed
```

- **Fewer than 5 keys** — a slot in `app/.env` is blank. Fine to proceed, you
  just have a smaller pool.
- **Anything red** — the message names the file and the command that fixes it.

---

## 2. Are the keys real?

`--check` counts keys. It does **not** call Google, so a typo'd or expired key
still shows as present. This is the step that catches that.

```
python3 scripts/check_keys.py
```

Expect one line per slot, all `WORKS`:

```
  GEMINI_API_KEY_1   WORKS
  GEMINI_API_KEY_2   WORKS
  ...
```

- `API_KEY_INVALID` — that key is wrong. Replace it, or blank the line so the
  pool skips it. **One bad key in slot 1 will fail every request**: an invalid
  key is not a quota error, so the pool does not fail over past it.
- `429 quota` — that key is spent for the day. Blank it or leave it; the pool
  will step over it after one wasted call.

---

## 3. Start it

```
./dev.sh
```

Expect:

```
  Backend   http://localhost:8000        (docs at /docs)
  Kiosk     http://localhost:5173
  Mode      LIVE
  Model     gemini-3.5-flash-lite  (fallback: gemini-2.0-flash)
  Gemini    5 keys x 2 models = 10 pools
```

`Mode LIVE` matters. If it says `REPLAY` you are about to demo a recording.

---

## 4. Provider status

```
curl -s localhost:8000/api/health/providers | python3 -m json.tool | head -12
```

Expect `"pools_exhausted": 0`, `"pools_remaining": 10`, and an `active` of
`key 1 of 5`. Leave this tab open — it is how you check headroom mid-demo, and
it never contains a key.

---

## 5. Warm-up session

Do one full run yourself before anyone is watching. It proves the keys work
end to end and puts the first (slowest) model call behind you.

Open <http://localhost:5173>, and in **Hindi**: tap through name, age, sex,
consent, a body region, then answer three questions by tapping tiles.

Then check the pool again. `pools_exhausted` should still be `0`.

**Budget: a full session is roughly 8-10 model calls.** The free tier is
metered per key per day, so a warm-up plus a demo is comfortably inside one
key. You have 10 pools.

---

## 6. Which language

**Demo in Hindi or Telugu.** Both are verified end to end: correct voice,
correct script, bilingual English underneath, nothing spoken uninvited.

**Avoid Marathi.** This machine has no Marathi voice installed, so the Listen
button is silent on every question. The emergency alert still speaks, in
English, deliberately — an alert nobody hears is worse than one in the wrong
language.

| Language | Voice | Listen button |
|---|---|---|
| Hindi | Lekha | speaks |
| Telugu | Geeta | speaks |
| Kannada | Soumya | speaks |
| Tamil | Vani | speaks |
| Bengali | Piya | speaks |
| English | Rishi | speaks |
| **Marathi** | **none** | **silent** |

---

## 7. If something goes wrong

> ### There is no keyboard shortcut for replay.
>
> `Ctrl+Shift+R` is a browser hard-reload. It reloads the same live build and
> changes nothing — no replay, no recovery. Replay is chosen when the server
> starts, not from the keyboard. Do not reach for it on the day.

### Switch 1 — the kiosk shows "Something went wrong"

Quota gone, keys rejected, or the backend died. One switch covers all three:

```
Ctrl-C          # in the dev.sh terminal, both processes stop
./dev.sh --replay
```

Up in about **2 seconds**. Then reload the browser tab.

You are now serving a real recorded session — genuine model output, a genuine
chest-pain red flag — with no network and no quota. A red **REPLAY** badge sits
on every screen, so nobody can mistake it for live. The full path works,
including the red flag.

In replay the interview questions are free-text: **type an answer** and press
Next. Tapping alone will not advance it.

### Switch 2 — a key runs out mid-demo

Do nothing. The pool moves to the next key on the next request, logs
`key 2 exhausted, switching to key 3`, and the patient sees one slightly slow
question. Watch it happen in the status tab from step 4.

Only if `pools_remaining` reaches `0` do you need Switch 1.

---

## 8. Shutting down

`Ctrl-C` in the dev.sh terminal. Both processes stop and both ports are
released — verified, no orphans. If a port is somehow still held:

```
lsof -ti:8000 -ti:5173 | xargs kill
```

---

## The two things most likely to catch you out

1. **A restart is not optional.** Spent keys stay spent until the process
   restarts, even after the daily quota rolls over at midnight Pacific.
2. **`--check` does not validate keys.** Run step 2. Today's rehearsal failed
   at exactly this point: five keys present, all five rejected by Google.
