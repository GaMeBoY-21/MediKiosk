# Demo day

Friday morning, in order. Each step says what you should see. If a step does
not match, the fix is on the same line — do not improvise.

If it goes wrong on the day, the answer is section 7: **Ctrl+Shift+R**. Read
that section and the last one before you start — they are the parts that are
not what you would guess.

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

- `API_KEY_INVALID` — that key is wrong. The pool now skips it automatically
  (one wasted call, then on to the next key), so it will not sink the demo —
  but fix it anyway, because a skipped key is an allowance you are not using.
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

### Switch 1 — `Ctrl+Shift+R`, from anywhere

Quota gone, keys rejected, backend dead, screen frozen — this covers all of
them, and you press it wherever you are standing. **It works from the error
screen**, which is where you will be.

Takes about **one second**. No reload, no restart, nothing to type. The red
**REPLAY** badge appears immediately and the kiosk returns to the idle screen;
start the walkthrough again from there.

You are now serving a real recorded session — genuine model output, a genuine
chest-pain red flag — with no network and no quota.

**One screen in the recording needs typing.** Every other screen is tappable
as usual. When you reach:

> *When did this chest discomfort start?*

there are no tiles: type anything (`2 days`) and press Next. It is the only
one. If you forget, the symptom is that Next stays greyed out.

The switch is one-way — there is no keystroke back to live. Pressing it again
just restarts the recording from the beginning, which is what you want if you
run the demo twice.

### Switch 2 — restart into replay

Only if the browser itself is wedged and the keystroke does nothing:

```
Ctrl-C          # in the dev.sh terminal, both processes stop
./dev.sh --replay
```

Up in about **2 seconds**, then reload the tab.

### A key runs out, or one is wrong — do nothing

The pool handles both by itself, on the next request, and the patient sees one
slightly slow question. Watch it in the status tab from step 4:

- `key 2 exhausted, switching to key 3` — that key's daily quota is spent.
- `key 2 invalid, skipping to key 3` — that key is a typo. Fix it after the
  demo; it is skipped on every model, so it costs one call and no more.

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
