# 💰 Expense Tracker

A lightweight, single-file Python command-line application for recording income and expenses, categorizing transactions, filtering history, and exporting financial data — with exact decimal arithmetic and strict input validation.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup](#setup)
- [Usage](#usage)
- [Financial Calculation Logic](#financial-calculation-logic)
- [Filtering](#filtering)
- [Validation Rules](#validation-rules)
- [Data Storage & Export](#data-storage--export)
- [Sample Report](#sample-report)
- [Project Structure](#project-structure)
- [Security & Privacy](#security--privacy)
- [License](#license)

---

## Features

- **Record transactions** with date, category, amount, type (`income` / `expense`) and an optional note
- **Real-time analytics**: total income, total expenses, net balance, and per-category spending with percentage share
- **Flexible filtering** by custom date range, category, and transaction type (combinable)
- **Local persistence**: auto-saves to `transactions.json` after every change
- **Export** any filtered view to **CSV**, **JSON**, or a formatted **text report**
- **Import** transactions from CSV or JSON (invalid rows are skipped and reported)
- **Strict validation**: rejects negative/zero amounts, impossible dates, and malformed input
- **Exact money math** using Python's `Decimal` — no floating-point errors
- **Optional pie chart** of expenses by category (Matplotlib)
- **Sample dataset generator** for instant demos

## Tech Stack

| Component | Purpose |
|---|---|
| Python 3.8+ | Core language |
| `decimal` | Exact monetary arithmetic |
| `datetime` | Date parsing and range filtering |
| `csv` / `json` | Persistence, import and export |
| `dataclasses` | Transaction data model |
| Matplotlib *(optional)* | Category pie chart |

**No API keys, no database, no network access, no accounts required.**

## Setup

### 1. Prerequisites

- Python 3.8 or newer — check with:
  ```bash
  python --version
  ```

### 2. Get the project

```bash
git clone <your-repository-url>
cd expense-tracker
```

### 3. (Optional) Install chart support

The app runs with the standard library only. To enable the pie chart:

```bash
pip install matplotlib
```

### 4. Run

```bash
python expense_tracker.py
```

### 5. (Optional) Generate sample data

```bash
python expense_tracker.py --sample
```

This creates `transactions.json`, `sample_transactions.csv`, `sample_transactions.json`, and `sample_report.txt` with 18 diverse records.

## Usage

The app opens an interactive menu:

```
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
```

### Adding a transaction

```
Add transaction
  Date [2026-10-15]:                 <- press Enter for today
  Type (income/expense): expense
  Category: Food
  Amount: 250.50
  Note (optional): Lunch
  Saved: #19 expense 250.50 on 2026-10-15
```

> Enter amounts as **positive** numbers. The `type` field decides whether it is income or an expense.

### Filtering

Leave any filter blank (press Enter) to skip it:

```
Start date (YYYY-MM-DD): 2025-01-01
End date   (YYYY-MM-DD): 2025-01-31
Category: Food
Type (income/expense):
```

## Financial Calculation Logic

All money is stored and computed as `Decimal` and rounded to 2 decimal places using `ROUND_HALF_UP`.

| Metric | Formula |
|---|---|
| **Total Income** | Sum of `amount` where `type = income` |
| **Total Expenses** | Sum of `amount` where `type = expense` |
| **Net Balance** | Total Income − Total Expenses |
| **Category Total** | Sum of `expense` amounts grouped by category |
| **Category Share** | Category Total ÷ Total Expenses × 100 |

- A negative net balance means spending exceeded income.
- Totals are recalculated from the selected (filtered) records on every request, so figures are always consistent with what is displayed.
- Income records are excluded from category expenditure totals.

## Filtering

- Date ranges are **inclusive** on both ends: `start ≤ date ≤ end`.
- Date, category, and type filters can be combined; all conditions must match.
- If the start date is after the end date, the two are swapped automatically.
- Category matching is case-insensitive (`food` = `Food`).
- Results are sorted by date, then by ID.

## Validation Rules

| Field | Rule |
|---|---|
| Amount | Must be a finite number **greater than 0**. Negative, zero, `NaN`, `inf`, and non-numeric values are rejected |
| Date | Must be a real calendar date in `YYYY-MM-DD` (e.g. `2025-02-30` is rejected) |
| Type | Must be `income` or `expense` |
| Category | Required, maximum 30 characters |

Invalid input shows an error message and re-prompts; the program does not crash.

## Data Storage & Export

- **Primary store:** `transactions.json` (auto-saved after every add/delete/import)
- **Amounts are saved as strings** to avoid float rounding on reload
- **Export formats:** CSV, JSON, plain-text report
- **Import:** CSV with columns `date, category, amount, type, note` or a JSON list of the same fields

Example CSV:

```csv
id,date,category,amount,type,note
1,2025-01-01,Salary,55000.00,income,January salary
2,2025-01-02,Rent,15000.00,expense,Monthly rent
3,2025-01-03,Food,1250.75,expense,Groceries
```

## Sample Report

Generated from the included sample dataset (18 records):

```
Expense Report
==============
Records   : 18

Total Income   :     122,500.00
Total Expenses :      56,279.99
Net Balance    :      66,220.01

Expenses by category:
  Rent                30,000.00  (53.3%)
  Travel               8,600.00  (15.3%)
  Shopping             4,599.00  (8.2%)
  Utilities            4,080.50  (7.3%)
  Food                 3,051.25  (5.4%)
  Education            2,999.00  (5.3%)
  Entertainment        2,299.99  (4.1%)
  Health                 650.25  (1.2%)
```

## Project Structure

```
expense-tracker/
├── expense_tracker.py          # Complete application (single file)
├── README.md                   # Documentation
├── .gitignore                  # Keeps personal data out of git
├── sample_transactions.csv     # Sample dataset (generated with --sample)
├── sample_transactions.json    # Sample dataset (generated with --sample)
└── sample_report.txt           # Sample report (generated with --sample)
```

## Security & Privacy

- **Zero secrets:** the project uses no API keys, passwords, tokens, or credentials of any kind, and none are present in the source or git history.
- **Fully offline:** the app makes no network requests; all data stays on your machine.
- **Personal data stays out of git:** your real transactions live in `transactions.json`, which is excluded via `.gitignore`. Only the synthetic sample files are meant to be committed.

Recommended `.gitignore`:

```gitignore
# Personal financial data
transactions.json
export*.csv
export*.json
export*.txt

# Python
__pycache__/
*.pyc
.venv/

# Secrets (defensive, none are used by this project)
.env
*.key
*.pem
```

Before your first commit, you can verify nothing sensitive is staged:

```bash
git status
git diff --cached
```

## License

Released under the MIT License. Feel free to use, modify, and distribute.
