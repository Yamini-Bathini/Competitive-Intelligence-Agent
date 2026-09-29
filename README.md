<div align="center">

# 🔭 Foresight

### Competitor intelligence that remembers

*An agent that watches competitors, retains every signal in [Hindsight](https://github.com/vectorize-io/hindsight) memory, spots repeated behavior, predicts the next move — then scores itself against what actually happens.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Hindsight](https://img.shields.io/badge/Memory-Hindsight-F0B429?style=for-the-badge)](https://hindsight.vectorize.io/)
[![Groq](https://img.shields.io/badge/LLM-Groq-FF6B35?style=for-the-badge)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-4CC29A?style=for-the-badge)](LICENSE)

</div>

---

## Why this exists

Competitive intelligence is only useful when it's cumulative. A one-shot query to an LLM can tell you a competitor has a pricing page. It can't tell you:

> *"NimbusCRM has cut Pro pricing twice in five months, always 6 weeks after a sales-hiring spree — and it's doing it again right now."*

That sentence only exists because something **remembered**. Foresight is built around [Hindsight](https://hindsight.vectorize.io/) as its memory layer — every signal it sees becomes a dated, retained fact, and every answer it gives is grounded in what it recalled, not what it guessed.

<table>
<tr>
<th align="center">🧠 Without memory</th>
<th align="center">🔭 With Hindsight</th>
</tr>
<tr>
<td valign="top">

"NimbusCRM has a pricing page. You'd need to check it manually and compare with old notes, if you kept any."

</td>
<td valign="top">

"NimbusCRM cut Pro from $49→$42 (Feb) then $42→$35 (May) — both ~6 weeks after a sales-hiring push. **Predicted** the May cut in April. **Scored: HIT.**"

</td>
</tr>
</table>

---

## What it actually does

| Capability | How |
|---|---|
| 🗓️ **Retains dated signals** | Every pricing change, launch, hiring push, messaging shift and blog post is stored in Hindsight as a self-contained, timestamped fact |
| 🔍 **Answers with evidence** | `recall` pulls the exact memories behind every answer — shown side-by-side against what a memoryless agent would say |
| 🧩 **Finds repeated behavior** | Detects patterns like *"hires sales → cuts price ~6 weeks later"* or *"copies competitor launches within 40 days"* |
| 🔮 **Predicts, then grades itself** | Opens a hypothesis when a pattern fires, then retains the outcome as **HIT** or **MISS** once reality catches up |
| 🎯 **Learns your preferences** | Say *"ignore blog posts"* once — it's retained to memory and every brief after that respects it |
| 🌐 **Watches real pages & feeds** | Diffs live URLs and RSS/Atom feeds on a schedule, filters out cookie-banner noise, turns real change into memory |
| 🔔 **Alerts you** | Flags high-importance signals and prediction outcomes to a Slack/Discord webhook, plus a scheduled digest brief |

---

## Architecture

```
                    ┌─────────────────────────┐
   Signals in  ───▶ │      core.ingest()      │
  (form, page       │  1 filter muted prefs    │
   diff, feed)       │  2 atomize into facts    │
                    │  3 retain() ──────────┐ │
                    │  4 check hypotheses    │ │
                    │  5 flag importance     │ │
                    │  6 write insight        │ │
                    └────────────────────────┼─┘
                                              ▼
                                     ┌─────────────────┐
                                     │  HINDSIGHT BANK  │
                                     │  retain / recall │
                                     │     / reflect    │
                                     └────────┬─────────┘
                                              │
                     ┌────────────┬───────────┼────────────┐
                     ▼            ▼           ▼            ▼
                   Ask         Timeline     Brief      Predictions
              (recall + LLM)  (patterns)  (reflect)    (hit-rate)
```

---

## Quickstart

```bash
git clone <your-repo-url> foresight && cd foresight
pip install -r requirements.txt

cp .env.example .env
# fill in HINDSIGHT_URL + HINDSIGHT_API_KEY (Hindsight Cloud → promo MEMHACK99 for free credits)
# optional: XAI_API_KEY for Grok (defaults to XAI_MODEL=grok-4.7)
# optional fallback: GROQ_API_KEY for Groq; XAI_API_KEY takes precedence
# optional: ALERT_WEBHOOK for Slack/Discord alerts

uvicorn app.main:app --reload
```

Open **http://localhost:8000** — check the header pill:

For Vercel, add `XAI_API_KEY` as a sensitive Production Environment Variable and redeploy. Never commit `.env` or API keys.

| Pill | Meaning |
|---|---|
| 🟢 `memory: hindsight` | Connected to real Hindsight memory |
| 🟡 `memory: local (fallback)` | Offline mode — a red banner explains why, and shows the exact error |

Then run `curl http://localhost:8000/api/health` for a scriptable connection check.

---

## Try it in 60 seconds

1. Click **Ingest next month** a few times, watching the memory-activity panel fill with `retain` calls.
2. Open **Ask** → *"What has NimbusCRM done on pricing?"* — see the without/with-memory contrast.
3. Open **Predictions** → find a hypothesis opened in April, scored `HIT` in May.
4. Type **"ignore blog posts"** → open **Brief** → blog signals are gone, and the preference is retained to memory, not just stored locally.

---

## API surface

| Endpoint | Purpose |
|---|---|
| `POST /api/signal` | Add a competitor signal by hand |
| `POST /api/collect` | Diff a live URL or RSS/Atom feed and retain what changed |
| `POST /api/ask` | Ask a question — recalls evidence, shows patterns |
| `GET /api/brief` | `reflect`-generated brief, respecting learned preferences |
| `GET /api/predictions` | Prediction ledger with hit/miss/pending and hit-rate |
| `GET /api/timeline` | Full signal history per competitor, patterns highlighted |
| `GET /api/health` | `{hindsight_connected, error}` — for scripts and CI |
| `POST /api/brief/send` | Force a brief to the alert webhook immediately |

---

## How Hindsight is used

| Operation | Where | Why |
|---|---|---|
| **`retain`** | Every ingested signal, every prediction, every scored outcome, every learned preference | Each is a dated, self-contained fact with `context` + `timestamp` |
| **`recall`** | `Ask` | Grounds every answer in actual stored evidence, not a guess |
| **`reflect`** | `Brief` | Synthesizes patterns and recommendations across everything retained |

Every Hindsight call is wrapped — a failure logs the real error and falls back to local memory rather than crashing.

---

## Stack

`Python` · `FastAPI` · `SQLite` (events, predictions, preferences, snapshots) · [`hindsight-client`](https://github.com/vectorize-io/hindsight) · `Grok` via xAI (Groq fallback) · `httpx` + `BeautifulSoup` (page/feed collection)

---

## Not yet implemented

Auth · multi-workspace banks · JavaScript-rendered pages (headless browser) · mental-model battlecards per competitor

---

<div align="center">

Built on **[Hindsight](https://github.com/vectorize-io/hindsight)** — agent memory that learns · [docs](https://hindsight.vectorize.io/) · [what is agent memory](https://vectorize.io/what-is-agent-memory)

</div>
