# My 10x Solution — Marwan

## 1. What problem am I solving?

Tracking personal expenses from receipts is tedious: you have to read each
receipt, decide what category it belongs to, and type the vendor, amount,
and date into a spreadsheet by hand. For anyone trying to actually keep a
monthly budget, this manual step is the part that gets skipped — and once
it's skipped, the budget stops being useful.

**ReceiptIQ** removes that manual step. You paste in a receipt's text, and
the system automatically extracts the vendor, amount, category, and date,
turns it into a tracked expense, and keeps a running monthly summary you
can view instantly or export as a PDF report.

**10x claim:** going through a stack of receipts and manually typing each
one into a spreadsheet — reading it, deciding a category, entering it — is
slow, repetitive work. With ReceiptIQ, that becomes: paste the receipt
text, move on. The system does the reading, the categorizing, and the
totaling in the background while you do something else.

**Who has this problem:** anyone trying to track personal or small-business
spending without paying for a full accounting SaaS product — freelancers,
students on a budget, or just someone who wants to know where their money
went last month without opening a spreadsheet.

## 2. How did I implement it?

The backend is a FastAPI service backed by SQLite (via SQLAlchemy), with
JWT-based authentication protecting every route that touches a user's data.

**The flow:** a user registers and logs in, then either logs an expense
manually or uploads raw receipt text. Uploading a receipt returns
immediately (HTTP 202) — the actual work of asking an LLM to extract
structured data (vendor, amount, category, date) happens afterward, in a
background task, so the API stays responsive. The LLM's JSON response is
validated against a strict schema before it's trusted and turned into an
expense; every LLM call is logged with token counts and an estimated cost,
regardless of whether the extraction succeeds. Separately, a scheduled job
(not tied to any request) periodically refreshes cached monthly summaries
for every user. Monthly totals are expensive to compute (they scan every
expense in the month), so they're cached and only recomputed when new data
invalidates them. Finally, a user can request a PDF report for any month,
built with reportlab from the same cached summary data.

### Concepts implemented — 7 of 7, no swaps needed

| Concept | Implementation |
|---|---|
| API endpoints | FastAPI routers for auth, expenses, receipts, and reports, each with Pydantic-validated input and correct status codes (201, 202, 204, 401, 404, 409) |
| Database | SQLAlchemy models (`User`, `Expense`, `Receipt`, `CostLog`, `CacheEntry`) persisted to SQLite |
| Authentication | Bcrypt-hashed passwords, JWT issuance on login, a dependency (`get_current_user`) that every protected route requires |
| Background / cron jobs | Receipt extraction runs as a `BackgroundTasks` job after the response is sent; a separate APScheduler job runs on a fixed interval to refresh caches — genuinely off any request |
| Reporting (PDF) | `reportlab` generates a real downloadable PDF with totals, a category breakdown table, and an itemized list |
| Caching | Monthly aggregates are computed once, stored in a `CacheEntry` table with a TTL, served from cache on repeat requests, and invalidated whenever an expense in that month changes |
| LLM integration | One narrow job — extract structured fields from receipt text — behind an endpoint, validated against a Pydantic schema before being trusted, with every call's token usage and estimated cost logged to `CostLog` |

Since all 7 core concepts fit the project naturally, I didn't need either of
the two allowed swaps.

### Steps to run it

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY and a SECRET_KEY
pip install -r requirements.txt
python seed.py               # creates a demo user + sample expenses
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs, log in as `demo@example.com` /
`demo12345`, and follow the 5-minute demo path in the README.

Docker alternative: `docker compose up --build` after copying `.env.example`
to `.env`.
