<div align="center">

<img src="Docs/banner.jpg.png" alt="Foresight — Competitive Intelligence Agent — See Beyond. Stay Ahead." width="100%"/>

<br/><br/>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-foresight--one--livid.vercel.app-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://foresight-one-livid.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Hindsight](https://img.shields.io/badge/Memory-Hindsight-F0B429?style=for-the-badge)](https://hindsight.vectorize.io/)
[![Groq](https://img.shields.io/badge/LLM-Groq-FF6B35?style=for-the-badge)](https://groq.com/)
[![SQLite](https://img.shields.io/badge/Storage-SQLite-4479A1?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-4CC29A?style=for-the-badge)](LICENSE)

**[🔴 Live Demo](https://foresight-one-livid.vercel.app/)** · **[Run locally](#-run-it-locally)** · **[Demo in 60s](#-try-it-in-60-seconds)** · **[Architecture](#-architecture)** · **[API](#-api-surface)** · **[Hindsight usage](#-how-hindsight-is-used)**

</div>

<br/>

> [!NOTE]
> Competitive intelligence is only valuable when it's *cumulative*. A one‑shot query to an LLM can tell you a competitor has a pricing page. It can't tell you the pattern behind six months of moves — because it doesn't remember them. Foresight does, because [Hindsight](https://github.com/vectorize-io/hindsight) does.

<br/>

## 🧠 The before / after that this whole project is built around

<table>
<tr>
<th width="50%" align="center">Without memory</th>
<th width="50%" align="center">🔭 With Hindsight</th>
</tr>
<tr valign="top">
<td>

> "NimbusCRM has a pricing page. I don't have history on it — you'd need to check manually and compare with old notes, if you kept any."

*Generic. No dates. Starts from zero every single time.*

</td>
<td>

> "NimbusCRM cut Pro from **$49→$42** (Feb) then **$42→$35** (May) — both **~6 weeks after a sales‑hiring push**. I predicted the May cut back in April. **Scored: HIT.**"

*Dated, evidenced, and it graded its own foresight.*

</td>
</tr>
</table>

<br/>

## ✨ What it does

<table>
<tr><td>🗓️</td><td><b>Retains dated signals</b></td><td>Every pricing change, launch, hiring push, messaging shift and blog post becomes a self‑contained, timestamped fact in Hindsight</td></tr>
<tr><td>🔎</td><td><b>Answers with evidence</b></td><td><code>recall</code> surfaces the exact memories behind every answer — shown next to what a memory‑less agent would say</td></tr>
<tr><td>🧩</td><td><b>Finds repeated behavior</b></td><td>Detects patterns like <i>"hires sales → cuts price ~6 weeks later"</i> or <i>"copies competitor launches within 40 days"</i></td></tr>
<tr><td>🔮</td><td><b>Predicts, then grades itself</b></td><td>Opens a hypothesis when a pattern fires, then retains the outcome as <b>HIT</b> or <b>MISS</b> once reality catches up</td></tr>
<tr><td>🎯</td><td><b>Learns your preferences</b></td><td>Say <i>"ignore blog posts"</i> once — it's retained to memory, and every brief afterward respects it</td></tr>
<tr><td>🌐</td><td><b>Watches real pages & feeds</b></td><td>Diffs live URLs and RSS/Atom feeds on a schedule, filters cookie‑banner noise, turns real change into memory</td></tr>
<tr><td>🔔</td><td><b>Alerts you</b></td><td>Flagged signals and prediction outcomes post to Slack/Discord, plus a scheduled digest brief</td></tr>
</table>

<br/>

## 🏗 Architecture

<div align="center">
<img src="Docs/architecture.svg" alt="Signal → ingest pipeline → Hindsight bank → Ask / Brief / Timeline / Alerts" width="100%"/>
</div>

<br/>

## 🌐 Live demo

> **[foresight-one-livid.vercel.app](https://foresight-one-livid.vercel.app/)** — no install needed. Click **Ingest next month** a few times, then check **Predictions**.

<br/>

## 🚀 Run it locally

```bash
git clone <your-repo-url> foresight && cd foresight
pip install -r requirements.txt

cp .env.example .env
# HINDSIGHT_URL + HINDSIGHT_API_KEY   → hindsight.vectorize.io Cloud, promo MEMHACK99 for free credits
# GROQ_API_KEY (optional)             → LLM-written answers and briefs
# ALERT_WEBHOOK (optional)            → Slack/Discord webhook for alerts

uvicorn app.main:app --reload
```

Open **http://localhost:8000** and check the header pill:

| Pill | Meaning |
|:--|:--|
| 🟢 `memory: hindsight` | Connected — everything below is real |
| 🟡 `memory: local (fallback)` | Offline — a red banner shows the exact connection error |

```bash
curl http://localhost:8000/api/health   # {"hindsight_connected": true, "error": null}
```

<details>
<summary><b>Troubleshooting the connection</b></summary>
<br/>

- **Pill stays yellow** → `HINDSIGHT_API_KEY` is empty or invalid; check `/api/health` for the raw error.
- **Windows users** → the app loads `.env` automatically via `python-dotenv`; no `set`/`export` needed.
- **Data disappears on restart** → set `DB=foresight.db` in `.env` (already the default) so SQLite persists to disk.

</details>

<br/>

## ⏱ Try it in 60 seconds

```
1. Click "Ingest next month" a few times     → watch retain calls fill the memory panel
2. Ask: "What has NimbusCRM done on pricing?" → see the without/with-memory contrast
3. Open Predictions                          → find an April hypothesis, scored HIT in May
4. Type: "ignore blog posts" → open Brief    → blog signals gone, preference retained to memory
```

<br/>

## 🔌 API surface

| Endpoint | Purpose |
|:--|:--|
| `POST /api/signal` | Add a competitor signal by hand |
| `POST /api/collect` | Diff a live URL or RSS/Atom feed and retain what changed |
| `POST /api/ask` | Ask a question — recalls evidence, surfaces patterns |
| `GET  /api/brief` | `reflect`‑generated brief, respecting learned preferences |
| `GET  /api/predictions` | Prediction ledger — hit / miss / pending + hit‑rate |
| `GET  /api/timeline` | Full signal history per competitor, patterns highlighted |
| `GET  /api/health` | `{hindsight_connected, error}` — for scripts & CI |
| `POST /api/brief/send` | Force a brief to the alert webhook immediately |

<br/>

## 🧬 How Hindsight is used

| Operation | Where | Why |
|:--|:--|:--|
| **`retain`** | Every ingested signal · every prediction · every scored outcome · every learned preference | Each is a dated, self‑contained fact with `context` + `timestamp` |
| **`recall`** | `Ask` | Grounds every answer in stored evidence, never a guess |
| **`reflect`** | `Brief` | Synthesizes patterns and recommendations across everything retained |

Every call is wrapped — a failure logs the real error and falls back to local memory instead of crashing the app.

<br/>

## 🧱 Stack

<div>

`Python` · `FastAPI` · `SQLite` <sub>(events · predictions · preferences · snapshots)</sub> · [`hindsight-client`](https://github.com/vectorize-io/hindsight) · `Groq` <sub>(LLM)</sub> · `httpx` + `BeautifulSoup` <sub>(page & feed collection)</sub>

</div>

<br/>

## 🚧 Not yet implemented

Auth · multi‑workspace banks · JavaScript‑rendered pages (headless browser) · mental‑model battlecards per competitor

<br/>

---

<div align="center">

Built on **[Hindsight](https://github.com/vectorize-io/hindsight)** — agent memory that learns
&nbsp;·&nbsp; [docs](https://hindsight.vectorize.io/) &nbsp;·&nbsp; [what is agent memory](https://vectorize.io/what-is-agent-memory)

</div>
