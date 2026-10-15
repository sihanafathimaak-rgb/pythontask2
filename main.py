#!/usr/bin/env python3
"""
SK 2 - Expense Tracker (Financial Logic & Analytics)
Single-file CLI app. Python 3.8+. Matplotlib optional (for charts).

Run:   python expense_tracker.py
Other: python expense_tracker.py --sample   (create sample dataset + README.md)
"""

import csv
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

DATA_FILE = "transactions.json"
CATEGORIES = ["Food", "Utilities", "Travel", "Rent", "Shopping", "Health",
              "Entertainment", "Education", "Salary", "Freelance", "Other"]
TYPES = ("income", "expense")
CENT = Decimal("0.01")


# ----------------------------------------------------------------- validation
class ValidationError(ValueError):
    pass


def parse_date(text):
    try:
        return datetime.strptime(str(text).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Date must be a real date in YYYY-MM-DD format.")


def parse_amount(text):
    """Decimal (not float) => exact money math. Rejects <=0, NaN, inf, junk."""
    try:
        amt = Decimal(str(text).strip().replace(",", ""))
    except InvalidOperation:
        raise ValidationError("Amount must be a number.")
    if not amt.is_finite():
        raise ValidationError("Amount must be a finite number.")
    if amt <= 0:
        raise ValidationError("Amount must be greater than zero "
                              "(negative/zero amounts are rejected).")
    return amt.quantize(CENT, rounding=ROUND_HALF_UP)


def parse_type(text):
    t = str(text).strip().lower()
    if t not in TYPES:
        raise ValidationError("Type must be 'income' or 'expense'.")
    return t


def parse_category(text):
    c = str(text).strip().title()
    if not c:
        raise ValidationError("Category cannot be empty.")
    if len(c) > 30:
        raise ValidationError("Category too long (max 30 chars).")
    return c


@dataclass
class Transaction:
    id: int
    date: str
    category: str
    amount: str      # stored as string -> no float rounding errors
    type: str
    note: str = ""

    @property
    def amt(self):
        return Decimal(self.amount)

    @property
    def dt(self):
        return datetime.strptime(self.date, "%Y-%m-%d").date()


def build_transaction(tid, d, category, amount, ttype, note=""):
    return Transaction(
        id=tid,
        date=parse_date(d).isoformat(),
        category=parse_category(category),
        amount=str(parse_amount(amount)),
        type=parse_type(ttype),
        note=str(note).strip(),
    )


# ------------------------------------------------------------------- tracker
class Tracker:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self.items = []
        self.load()

    def _next_id(self):
        return max((t.id for t in self.items), default=0) + 1

    def add(self, d, category, amount, ttype, note=""):
        t = build_transaction(self._next_id(), d, category, amount, ttype, note)
        self.items.append(t)
        self.save()
        return t

    def delete(self, tid):
        before = len(self.items)
        self.items = [t for t in self.items if t.id != tid]
        if len(self.items) == before:
            return False
        self.save()
        return True

    # --- filtering (date range inclusive on both ends) ---
    def filter(self, start=None, end=None, category=None, ttype=None):
        out = []
        cat = category.strip().title() if category else None
        for t in self.items:
            if start and t.dt < start:
                continue
            if end and t.dt > end:
                continue
            if cat and t.category != cat:
                continue
            if ttype and t.type != ttype:
                continue
            out.append(t)
        return sorted(out, key=lambda x: (x.dt, x.id))

    # --- analytics ---
    @staticmethod
    def summary(txns):
        income = sum((t.amt for t in txns if t.type == "income"), Decimal("0"))
        expense = sum((t.amt for t in txns if t.type == "expense"), Decimal("0"))
        by_cat = {}
        for t in txns:
            if t.type == "expense":
                by_cat[t.category] = by_cat.get(t.category, Decimal("0")) + t.amt
        by_cat = dict(sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True))
        return {"income": income, "expense": expense,
                "net": income - expense, "by_category": by_cat}

    # --- persistence ---
    def save(self, path=None):
        with open(path or self.path, "w", encoding="utf-8") as f:
            json.dump([asdict(t) for t in self.items], f, indent=2)

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                rows = json.load(f)
            self.items = [build_transaction(r["id"], r["date"], r["category"],
                                            r["amount"], r["type"], r.get("note", ""))
                          for r in rows]
        except (json.JSONDecodeError, KeyError, ValidationError) as e:
            print(f"Warning: could not read {self.path}: {e}")
            self.items = []

    def export_csv(self, txns, path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "date", "category", "amount", "type", "note"])
            for t in txns:
                w.writerow([t.id, t.date, t.category, t.amount, t.type, t.note])

    def export_json(self, txns, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(t) for t in txns], f, indent=2)

    def import_file(self, path):
        """Import CSV or JSON; invalid rows are skipped and reported."""
        rows = []
        if path.lower().endswith(".json"):
            with open(path, encoding="utf-8") as f:
                rows = json.load(f)
        else:
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        ok, bad = 0, []
        for i, r in enumerate(rows, 1):
            try:
                self.items.append(build_transaction(
                    self._next_id(), r["date"], r["category"],
                    r["amount"], r["type"], r.get("note", "")))
                ok += 1
            except (ValidationError, KeyError) as e:
                bad.append((i, str(e)))
        self.save()
        return ok, bad


# ------------------------------------------------------------------- display
def money(d):
    return f"{d:,.2f}"


def print_table(txns):
    if not txns:
        print("  (no transactions)")
        return
    print(f"  {'ID':<4}{'Date':<12}{'Category':<15}{'Type':<9}{'Amount':>12}  Note")
    print("  " + "-" * 70)
    for t in txns:
        sign = "+" if t.type == "income" else "-"
        print(f"  {t.id:<4}{t.date:<12}{t.category:<15}{t.type:<9}"
              f"{sign + money(t.amt):>12}  {t.note}")


def report_text(txns, title="Expense Report"):
    s = Tracker.summary(txns)
    lines = [title, "=" * len(title),
             f"Generated : {datetime.now():%Y-%m-%d %H:%M}",
             f"Records   : {len(txns)}", "",
             f"Total Income   : {money(s['income']):>14}",
             f"Total Expenses : {money(s['expense']):>14}",
             f"Net Balance    : {money(s['net']):>14}", "",
             "Expenses by category:"]
    if not s["by_category"]:
        lines.append("  (none)")
    for cat, amt in s["by_category"].items():
        pct = (amt / s["expense"] * 100) if s["expense"] else Decimal("0")
        lines.append(f"  {cat:<15}{money(amt):>14}  ({pct:.1f}%)")
    return "\n".join(lines)


def show_summary(txns):
    print("\n" + report_text(txns, "Summary") + "\n")


def plot_chart(txns):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not installed. Run: pip install matplotlib")
        return
    cats = Tracker.summary(txns)["by_category"]
    if not cats:
        print("No expenses to plot.")
        return
    plt.figure(figsize=(7, 5))
    plt.pie([float(v) for v in cats.values()], labels=cats.keys(), autopct="%1.1f%%")
    plt.title("Expenses by Category")
    plt.show()


# --------------------------------------------------------------------- input
def ask(prompt, parser, default=None, optional=False):
    while True:
        raw = input(prompt).strip()
        if not raw:
            if default is not None:
                return parser(default)
            if optional:
                return None
        try:
            return parser(raw)
        except ValidationError as e:
            print(f"  ! {e}")


def ask_filters():
    print("Leave blank to skip a filter.")
    start = ask("  Start date (YYYY-MM-DD): ", parse_date, optional=True)
    end = ask("  End date   (YYYY-MM-DD): ", parse_date, optional=True)
    if start and end and start > end:
        print("  ! Start is after end - swapping.")
        start, end = end, start
    cat = input("  Category: ").strip() or None
    ttype = input("  Type (income/expense): ").strip().lower() or None
    if ttype and ttype not in TYPES:
        print("  ! Invalid type ignored.")
        ttype = None
    return start, end, cat, ttype


def add_flow(tr):
    print("\nAdd transaction")
    d = ask(f"  Date [{date.today()}]: ", parse_date, default=str(date.today()))
    ttype = ask("  Type (income/expense): ", parse_type)
    print("  Categories: " + ", ".join(CATEGORIES))
    cat = ask("  Category: ", parse_category)
    amt = ask("  Amount: ", parse_amount)
    note = input("  Note (optional): ")
    t = tr.add(str(d), cat, amt, ttype, note)
    print(f"  Saved: #{t.id} {t.type} {money(t.amt)} on {t.date}")


# ------------------------------------------------------------ sample + readme
SAMPLE_ROWS = [
    ("2025-01-01", "Salary", "55000.00", "income", "January salary"),
    ("2025-01-02", "Rent", "15000.00", "expense", "Monthly rent"),
    ("2025-01-03", "Food", "1250.75", "expense", "Groceries"),
    ("2025-01-05", "Utilities", "2100.50", "expense", "Electricity + water"),
    ("2025-01-08", "Travel", "3400.00", "expense", "Train tickets"),
    ("2025-01-10", "Freelance", "8000.00", "income", "Website project"),
    ("2025-01-12", "Entertainment", "799.99", "expense", "Movie + dinner"),
    ("2025-01-15", "Shopping", "4599.00", "expense", "Shoes"),
    ("2025-01-18", "Health", "650.25", "expense", "Pharmacy"),
    ("2025-01-20", "Food", "480.10", "expense", "Restaurant"),
    ("2025-01-25", "Education", "2999.00", "expense", "Online course"),
    ("2025-02-01", "Salary", "55000.00", "income", "February salary"),
    ("2025-02-02", "Rent", "15000.00", "expense", "Monthly rent"),
    ("2025-02-04", "Food", "1320.40", "expense", "Groceries"),
    ("2025-02-06", "Utilities", "1980.00", "expense", "Internet + phone"),
    ("2025-02-09", "Travel", "5200.00", "expense", "Weekend trip"),
    ("2025-02-14", "Entertainment", "1500.00", "expense", "Concert"),
    ("2025-02-20", "Freelance", "4500.00", "income", "Logo design"),
]

README = """# SK 2 - Expense Tracker

Single-file Python CLI (`expense_tracker.py`) to record income/expenses,
categorize them, filter by date/category, and export to CSV/JSON.

## Run
```
python expense_tracker.py            # interactive menu
python expense_tracker.py --sample   # create sample_transactions.json/.csv + this README
pip install matplotlib               # optional, for the pie chart
```

## Financial calculation logic
- Money is stored with Python `Decimal` (never `float`), rounded to 2 places
  with ROUND_HALF_UP -> no binary floating-point errors (0.1 + 0.2 == 0.30).
- Total Income   = sum(amount) of all `income` records in the selection.
- Total Expenses = sum(amount) of all `expense` records in the selection.
- Net Balance    = Total Income - Total Expenses (negative = overspent).
- Category totals = sum of `expense` amounts grouped by category,
  sorted high to low, each with % of total expenses.
- All totals are recalculated from the filtered list every time.

## Filtering
- Date range is **inclusive** on both ends (start <= date <= end).
- Combine with category and/or type; blank filters are skipped.
- If start > end, they are swapped.

## Validation
- Amount must be a finite number > 0 (negative, zero, NaN, inf rejected).
  Direction is given by `type`, not by sign.
- Date must be a real calendar date `YYYY-MM-DD` (e.g. 2025-02-30 rejected).
- Type must be `income` or `expense`; category must be non-empty.
- Bad rows in imported files are skipped and reported.

## Persistence
- Data auto-saves to `transactions.json` after each change.
- Export any filtered view to CSV or JSON, or a text report.

## Sample report (sample dataset, all records)
```
{REPORT}
```
"""


def make_sample(tr):
    tr.items = []
    for r in SAMPLE_ROWS:
        tr.items.append(build_transaction(tr._next_id(), *r))
    tr.save()
    tr.export_csv(tr.items, "sample_transactions.csv")
    tr.export_json(tr.items, "sample_transactions.json")
    report = report_text(tr.items, "Expense Report")
    with open("sample_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(README.replace("{REPORT}", report))
    print("Created: transactions.json, sample_transactions.csv/.json, "
          "sample_report.txt, README.md")


# ---------------------------------------------------------------------- menu
MENU = """
=== Expense Tracker ===
 1. Add transaction
 2. View all transactions
 3. Filter transactions
 4. Summary (all)
 5. Summary (filtered)
 6. Delete transaction
 7. Export (CSV / JSON / report)
 8. Import CSV / JSON
 9. Pie chart (matplotlib)
10. Load sample data
 0. Exit
"""


def main():
    tr = Tracker()
    if "--sample" in sys.argv:
        make_sample(tr)
        return
    while True:
        print(MENU)
        print(f"Balance: {money(Tracker.summary(tr.items)['net'])}")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                add_flow(tr)
            elif choice == "2":
                print_table(tr.filter())
            elif choice == "3":
                res = tr.filter(*ask_filters())
                print_table(res)
                show_summary(res)
            elif choice == "4":
                show_summary(tr.items)
            elif choice == "5":
                show_summary(tr.filter(*ask_filters()))
            elif choice == "6":
                tid = input("  Transaction ID: ").strip()
                if tid.isdigit() and tr.delete(int(tid)):
                    print("  Deleted.")
                else:
                    print("  ID not found.")
            elif choice == "7":
                res = tr.filter(*ask_filters())
                fmt = input("  Format (csv/json/report): ").strip().lower()
                name = input("  File name (no extension): ").strip() or "export"
                if fmt == "csv":
                    tr.export_csv(res, name + ".csv")
                    print(f"  Saved {name}.csv ({len(res)} rows)")
                elif fmt == "json":
                    tr.export_json(res, name + ".json")
                    print(f"  Saved {name}.json ({len(res)} rows)")
                elif fmt == "report":
                    with open(name + ".txt", "w", encoding="utf-8") as f:
                        f.write(report_text(res))
                    print(f"  Saved {name}.txt")
                else:
                    print("  Unknown format.")
            elif choice == "8":
                p = input("  File path (.csv/.json): ").strip()
                ok, bad = tr.import_file(p)
                print(f"  Imported {ok} rows, skipped {len(bad)}.")
                for i, msg in bad:
                    print(f"    row {i}: {msg}")
            elif choice == "9":
                plot_chart(tr.filter(*ask_filters()))
            elif choice == "10":
                if input("  This replaces current data. Continue? (y/n): ").lower() == "y":
                    make_sample(tr)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")
        except (OSError, json.JSONDecodeError) as e:
            print(f"  ! File error: {e}")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()