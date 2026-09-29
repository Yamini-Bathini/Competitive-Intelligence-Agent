# Foresight: competitor intelligence that remembers
Ingests competitor signals, retains each as a dated fact in Hindsight memory, detects repeated behavior, predicts moves, and scores its own predictions.

## Run (Windows, Mac, Linux)
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `HINDSIGHT_URL` + `HINDSIGHT_API_KEY` (Hindsight Cloud: https://ui.hindsight.vectorize.io, promo `MEMHACK99`) and optionally `GROQ_API_KEY`. No `set`/`export` commands needed; the app loads `.env` itself.
3. `uvicorn app.main:app --reload` then open http://localhost:8000
4. The header pill must say **memory: hindsight**. If it says local (fallback), a red banner shows the exact reason.

## Pipeline (`core.ingest`)
1 filter muted preferences, 2 atomic fact (LLM atomizes collected page diffs), 3 `retain` to Hindsight, 4 check open hypotheses (score hit/miss, open new ones), 5 flag significant signals (importance 1-5), 6 generate insight.

## Hindsight usage
`retain`: signals, predictions, outcomes, preferences (with `context` + `timestamp`). `recall`: Ask. `reflect`: weekly brief. Every call is wrapped: on failure the error shows in the activity panel and the local fallback takes over.

## Real data
- **add / watch** tab: add signals by form, or watch a page or RSS feed. Watched pages are re-checked every `CHECK_MINUTES` (default 60) while the app runs; diffs are filtered for noise and retained. RSS/Atom feeds (URL contains `/feed`, `/rss`, `.xml`, or signal type `feed`) turn each new post into a clean signal instead of a page diff; existing posts are skipped on first watch.
- Set `DB=foresight.db` (already in `.env.example`) so data survives restarts.
- Competitors are discovered from your data; no hardcoded list.

## Alerts & scheduled briefs
- Set `ALERT_WEBHOOK` to a Slack or Discord webhook: flagged signals (importance 4-5), prediction outcomes, new feed items, and the scheduled brief are posted automatically. Empty = alerts stay in the app. `Send test alert` button in add / watch verifies the wiring.
- `BRIEF_HOURS` (default 168 = weekly, 0 = off): the background loop posts a competitor brief to the webhook via `maybe_brief()`.

## Demo
Ingest next month through May, open predictions (April hypothesis, May hit), then type `ignore blog posts` and open brief.

## Not implemented
Auth, multi-workspace banks, JavaScript-rendered pages, mental models.
