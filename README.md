# ReceiptIQ

Upload a receipt as text → an LLM extracts the vendor, amount, category, and
date in the background → it becomes a tracked expense → view cached monthly
summaries and export a PDF report. Built as the "Your 10x Solution" capstone.

**The 10x claim:** manually logging and categorizing a stack of receipts
into a spreadsheet takes real time — reading each one, deciding a category,
typing it in. With ReceiptIQ, you paste the receipt text and everything
else (categorization, totals, the report) happens automatically. What was a
manual data-entry chore for a month of receipts becomes a paste-and-wait
task measured in seconds per receipt.

## Concepts implemented (5 required, 7 delivered — no swaps needed)

| # | Concept | Where it lives |
|---|---------|-----------------|
| 1 | API endpoints | `app/routers/*.py` — auth, expenses, receipts, reports, all with status codes + Pydantic validation |
| 2 | Database | `app/models.py`, `app/database.py` — SQLite via SQLAlchemy, survives restarts |
| 3 | Authentication | `app/auth.py` — bcrypt password hashing + JWT, enforced via `get_current_user` dependency on every protected route |
| 4 | Background / cron jobs | `app/services/background_jobs.py` — `process_receipt` runs off the request path via `BackgroundTasks`; `refresh_all_caches` runs on a fixed schedule via APScheduler |
| 5 | Reporting (PDF) | `app/services/pdf_report.py`, `app/routers/reports.py` — generates a real PDF with reportlab |
| 6 | Caching | `app/services/cache.py` — monthly aggregate is expensive to compute, stored in `CacheEntry`, reused within a TTL, invalidated on writes |
| 7 | LLM integration | `app/services/llm_extraction.py` — one narrow job (extract structured data from receipt text), validated against a Pydantic schema, every call logged to `CostLog` with token counts + estimated cost |

## Project structure

```
app/
  main.py            # FastAPI app, startup wiring
  database.py         # SQLAlchemy engine/session
  models.py           # User, Expense, Receipt, CostLog, CacheEntry
  schemas.py           # Pydantic request/response models
  auth.py              # hashing, JWT, get_current_user
  routers/
    auth.py            # /auth/register, /auth/login
    expenses.py         # CRUD + /expenses/summary/{year}/{month}
    receipts.py          # /receipts/upload, /receipts/{id}
    reports.py            # /reports/monthly/{year}/{month} -> PDF
  services/
    llm_extraction.py     # Claude API call + validation + cost log
    background_jobs.py     # BackgroundTasks worker + APScheduler cron
    cache.py                # get/invalidate monthly summary cache
    pdf_report.py            # reportlab PDF builder
seed.py                # demo user + sample expenses + a pending receipt
tests/                 # pytest suite (auth, expenses, caching)
```

## Run it

**Requirements:** Python 3.11+, an Anthropic API key (only needed for the
`/receipts/upload` LLM step — everything else works without it).

```bash
cp .env.example .env      # then fill in ANTHROPIC_API_KEY and SECRET_KEY
pip install -r requirements.txt
python seed.py            # creates demo user + sample data
uvicorn app.main:app --reload
```

Or with Docker:

```bash
cp .env.example .env
docker compose up --build
```

API docs (interactive): http://localhost:8000/docs

## 5-minute demo path

1. `POST /auth/login` with `demo@example.com` / `demo12345` → copy `access_token`.
2. Click **Authorize** in `/docs`, paste the token.
3. `GET /expenses` → see the seeded expenses. Note the `expense_date` on any
   one of them (they're seeded relative to today's date, so the exact
   year/month will differ depending on when you run `seed.py`).
4. `GET /expenses/summary/{year}/{month}` using the year/month from step 3
   → first call computes and caches; call it again and watch `cache_hit`
   flip to `true`.
5. `POST /receipts/upload` with `{"raw_text": "Starbucks Grande Latte $5.75 total $6.20 2024-08-14"}`
   → returns `202` immediately with `status: pending`.
6. `GET /receipts/{id}` a few seconds later → `status: done`, `expense_id` set.
   The LLM extraction ran in the background while you kept using the API.
7. `GET /reports/monthly/{year}/{month}` (same year/month as step 4) →
   downloads a PDF report.

## Tests

```bash
pytest
```

Covers registration/login, rejecting bad credentials, protected-route
enforcement, expense CRUD, and the cache hit/miss behavior.

## Future ideas (non-goals for this capstone)

- OCR from actual receipt images (currently accepts receipt *text* — no
  image pipeline, to keep the core buildable in ~3 weeks and avoid paid
  OCR services)
- Multi-currency support
- Recurring-expense detection
