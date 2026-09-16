"""Seed / demo data: creates a demo user and a handful of expenses across
two months, plus a couple of receipts (one already processed, one pending)
so a stranger can explore the API without creating anything by hand.

Run: python seed.py
Demo login: demo@example.com / demo12345
"""
import datetime as dt
from app.database import Base, engine, SessionLocal
from app import models, auth

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"

SAMPLE_EXPENSES = [
    ("Trader Joe's", 42.17, "groceries", -2, 5),
    ("Trader Joe's", 55.30, "groceries", -12, 3),
    ("Shell Gas Station", 38.00, "transport", -8, 1),
    ("Netflix", 15.99, "entertainment", -20, 0),
    ("Chipotle", 12.45, "dining", -6, 2),
    ("Chipotle", 13.10, "dining", -18, 4),
    ("CVS Pharmacy", 24.60, "health", -10, 6),
    ("Amazon", 67.89, "shopping", -14, 7),
    ("Uber", 22.30, "transport", -3, 0),
    ("Con Edison", 88.40, "utilities", -25, 0),
]


import calendar


def month_delta(days_ago: int, month_offset: int) -> dt.datetime:
    base = dt.datetime.utcnow() - dt.timedelta(days=days_ago)
    month = base.month - month_offset
    year = base.year
    while month < 1:
        month += 12
        year -= 1
    # Clamp the day so we never land on e.g. Feb 30, which doesn't exist.
    last_day_of_month = calendar.monthrange(year, month)[1]
    day = min(base.day, last_day_of_month)
    return base.replace(year=year, month=month, day=day)


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == DEMO_EMAIL).first()
        if not user:
            user = models.User(email=DEMO_EMAIL, hashed_password=auth.hash_password(DEMO_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print("Demo user already exists, reusing it.")

        if db.query(models.Expense).filter(models.Expense.user_id == user.id).count() == 0:
            for vendor, amount, category, days_ago, month_offset in SAMPLE_EXPENSES:
                db.add(models.Expense(
                    user_id=user.id,
                    vendor=vendor,
                    amount=amount,
                    category=category,
                    expense_date=month_delta(days_ago, month_offset),
                    source="manual",
                ))
            db.commit()
            print(f"Seeded {len(SAMPLE_EXPENSES)} sample expenses.")
        else:
            print("Expenses already seeded, skipping.")

        if db.query(models.Receipt).filter(models.Receipt.user_id == user.id).count() == 0:
            db.add(models.Receipt(
                user_id=user.id,
                raw_text="Starbucks #4521\nGrande Latte  $5.75\nTax  $0.45\nTotal  $6.20\n2024-08-14",
                status="pending",
            ))
            db.commit()
            print("Seeded 1 pending receipt (upload it via /receipts/upload flow or "
                  "let the background job pick up an existing pending row on next restart).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
