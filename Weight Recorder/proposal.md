# Weight Recorder UI — Proposal

## Overview

A Python desktop application for recording and visualizing daily weight data. The UI allows multiple users to log their weight, automatically calculates daily gain/loss, and provides interactive graphs filtered by user name.

---

## Current State

The existing implementation provides:

- **gui.py** — Main table manager (insert rows, view latest 20 rows, open graph window)
- **graph_gui.py** — Line graph visualization (weight + gain/loss over time)
- **SQL.py** — Database layer using PyMySQL (MySQL/MariaDB via Aiven cloud)
- **db_config.py** — Connection credentials (hardcoded — to be migrated)

### What's Working

| Feature | Status |
|---------|--------|
| Insert Name, Day, Weight | ✅ Done |
| Auto-calculate Gain/Loss | ⚠️ Partial — compares against the last row regardless of Name |
| View latest rows | ✅ Done (limited to 20) |
| Graph (weight + gain/loss) | ⚠️ Partial — shows all data, no Name filter |
| Edit existing data | ❌ Not implemented |
| Delete data | ❌ Not implemented in UI (SQL function exists) |
| Day as weekday selector | ❌ Currently free-text input |
| Secure credential storage | ❌ Password hardcoded in source |

---

## Proposed Changes

### 1. Fix Gain/Loss Calculation (Per-User)

**Problem:** Currently compares against the global latest row, not the latest row for the same Name.

**Solution:** Add a SQL helper that fetches the most recent weight for a given Name:

```python
def read_latest_weight_by_name(name: str, table_name: str | None = None) -> float | None:
    """SELECT Weight FROM table WHERE Name = %s ORDER BY id DESC LIMIT 1"""
```

Update `insert_row()` to call this function with the entered Name.

**Gain/Loss semantics (defined):**
- Gain/Loss = current weight − most recent prior record **for the same Name** (by insertion order / `id`).
- If no prior record exists for that Name, Gain/Loss = 0.0.
- Gain/Loss is **not** recalculated when older records are edited or deleted. It reflects the delta at insertion time. This is a documented limitation that keeps the system simple and predictable.

---

### 2. Day Field — Weekday Selector (Stores Full Date)

**Problem:** Users currently type the date manually, which is error-prone and inconsistent.

**Solution:** Replace the free-text Day entry with a read-only `ttk.Combobox` showing weekday names, but **store the full date (`YYYY-MM-DD`)** internally.

```python
DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
```

**Behavior:**
- The combobox displays weekday names (Sunday–Saturday) — read-only, users cannot type arbitrary text.
- Default selection: today's weekday (auto-detected via `datetime.date.today().strftime("%A")`).
- On insert, the selected weekday maps to the **actual date** of that weekday in the current week:
  - If user selects "Monday" on a Monday → stores `2026-05-19`.
  - If user selects "Saturday" on a Monday → stores the most recent Saturday (`2026-05-17`).
- The `Day` column stores `YYYY-MM-DD` strings (existing `VARCHAR(50)` — no schema change needed).
- The table view displays the full date. The graph uses the full date for chronological X-axis ordering.
- Edit dialog also uses a weekday combobox, pre-selected to match the stored date's weekday.

**Legacy data migration:**
- Existing records with date strings (e.g., `"2026-04-10"`) remain valid and display correctly.
- No migration step required — both old date strings and new date strings are in the same format.

---

### 3. Edit Existing Data

**UI Change:** Double-click a row in the table to open an edit dialog.

**Workflow:**
1. User double-clicks a row → a modal dialog opens pre-filled with current values.
2. User modifies Name, Day (weekday combobox), or Weight → clicks "Save".
3. Gain/Loss is recalculated for **this row only** based on the previous record for that Name.
4. Downstream records are NOT recalculated (no cascading updates).
5. Table refreshes.

**New SQL function:**

```python
def update_data(row_id: int, updates: dict, table_name: str | None = None) -> int:
    """UPDATE table SET col1=%s, col2=%s WHERE id = %s"""
```

---

### 4. Delete Data from UI

**UI Change:** Add a "Delete" button that operates on the currently selected row.

**Workflow:**
1. User selects a row in the table.
2. Clicks "Delete" → confirmation dialog appears.
3. On confirm, calls existing `remove_data(row_id=...)`.
4. Downstream Gain/Loss values are NOT recalculated (documented limitation).
5. Table refreshes.

**Safety:** Always show a confirmation messagebox before deletion.

---

### 5. Graph Filtered by Name

**UI Change:** Add a Name dropdown (combobox) above the graph canvases.

**Workflow:**
1. On graph window open, populate combobox with distinct Names from the database.
2. User selects a Name → graph redraws showing only that user's data.
3. "All" option shows combined data (current behavior).
4. X-axis uses the `Day` column (full date `YYYY-MM-DD`) for chronological ordering.

**New SQL functions:**

```python
def read_distinct_names(table_name: str | None = None) -> list[str]:
    """SELECT DISTINCT Name FROM table ORDER BY Name"""

def read_graph_data_by_name(name: str, table_name: str | None = None) -> list[dict]:
    """SELECT Day, Weight, Gain_Loss FROM table WHERE Name = %s ORDER BY id ASC"""
```

---

### 6. Paginated Data View (20 Rows Per Page)

**Problem:** The UI currently shows only the latest 20 rows with no way to browse older records.

**Solution:** Add "Previous" and "Next" pagination buttons below the table.

**Behavior:**
- Display 20 rows per page, ordered by `id DESC` (newest first).
- "Next" button loads the next 20 older rows; "Previous" loads the 20 newer rows.
- Page indicator shows current position (e.g., "Page 2 of 5" or "Rows 21–40").
- Buttons are disabled at boundaries (Previous disabled on page 1, Next disabled on last page).
- Status bar shows total row count.

**New SQL function:**

```python
def read_paginated_data(
    page: int = 1,
    page_size: int = 20,
    table_name: str | None = None,
) -> tuple[list[dict], int]:
    """Fetch a page of rows and total count.

    Returns (rows, total_count) where rows are offset by (page-1)*page_size.
    SELECT * FROM table ORDER BY id DESC LIMIT %s OFFSET %s
    SELECT COUNT(*) FROM table
    """
```

---

### 7. Secure Credential Storage

**Problem:** `db_config.py` contains a plaintext database password committed to the repository.

**Solution:** Move credentials to a `.env` file and load via `python-dotenv`.

**Changes:**
- Create `.env` file with `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_TIMEOUT`.
- Create `.env.example` with placeholder values for documentation.
- Update `SQL.py` → `load_py_config_file()` to use `dotenv.load_dotenv()` instead of importing `db_config`.
- Add `.env` and `db_config.py` to `.gitignore`.
- Remove hardcoded credentials from `db_config.py` (or delete the file entirely).

---

## Proposed UI Layout

```
┌──────────────────────────────────────────────────────────┐
│  Table: Weight_Log                                       │
├──────────────────────────────────────────────────────────┤
│  ┌─ Insert Data ──────────────────────────────────────┐  │
│  │  Name:   [_______________]                         │  │
│  │  Day:    [▼ Monday      ]  (Sun–Sat dropdown)      │  │
│  │  Weight: [_______________]  (kg)                   │  │
│  │                                                    │  │
│  │  [Insert] [Refresh] [Delete Selected] [Graph]      │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Data View ────────────────────────────────────────┐  │
│  │  ID | Name  | Day        | Weight | Gain/Loss     │  │
│  │  ── | ───── | ────────── | ────── | ──────────    │  │
│  │  45 | Kevin | 2026-05-19 | 79.0kg | -0.50 kg      │  │
│  │  44 | Kevin | 2026-05-18 | 79.5kg | +0.20 kg      │  │
│  │  ...                                              │  │
│  │               (double-click to edit)               │  │
│  │                                                    │  │
│  │  [◀ Previous]  Page 1 of 5  [Next ▶]              │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Status: Loaded 20 row(s) from Weight_Log.               │
└──────────────────────────────────────────────────────────┘
```

### Graph Window

```
┌──────────────────────────────────────────────────────────┐
│  Graph View: Weight_Log                                  │
│  Filter by Name: [▼ Kevin     ] [Refresh Graph]          │
├──────────────────────────────────────────────────────────┤
│  ┌─ Weight (kg) ─────────────────────────────────────┐  │
│  │         ___/\___                                   │  │
│  │   _____/        \____                              │  │
│  │  /                                                 │  │
│  │  2026-05-12  05-14  05-16  05-18  05-19            │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌─ Gain/Loss (kg) ──────────────────────────────────┐  │
│  │       _                                            │  │
│  │  ____/ \    /\                                     │  │
│  │         \__/  \___                                 │  │
│  │  2026-05-12  05-14  05-16  05-18  05-19            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Status: Showing 15 row(s) for Kevin.                    │
└──────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

| Step | File(s) | Description |
|------|---------|-------------|
| 1 | `.env`, `.env.example`, `.gitignore` | Move credentials out of source code |
| 2 | `SQL.py` | Replace `db_config` import with `python-dotenv`; add `read_latest_weight_by_name`, `update_data`, `read_distinct_names`, `read_graph_data_by_name`, `read_paginated_data` |
| 3 | `gui.py` | Replace Day text entry with weekday combobox that stores full `YYYY-MM-DD` date |
| 4 | `gui.py` | Fix `insert_row` to use per-Name gain/loss calculation |
| 5 | `gui.py` | Add "Delete Selected" button with confirmation dialog |
| 6 | `gui.py` | Add pagination (Previous/Next buttons, 20 rows per page) |
| 7 | `gui.py` | Add double-click edit dialog (modal Toplevel with weekday combobox + pre-filled form) |
| 8 | `graph_gui.py` | Add Name combobox filter; use full date for X-axis labels |
| 9 | Tests | Add `tests/test_sql.py` covering new SQL functions |

---

## Tech Stack

- **Python 3.11+**
- **tkinter / ttk** — GUI framework (stdlib, no extra install)
- **PyMySQL** — MySQL database driver
- **python-dotenv** — Environment variable loading (new dependency)
- **Aiven Cloud MySQL** — Remote database hosting

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Store full date, display weekday in combobox | Preserves chronological ordering for graphs while giving users a simple selector |
| No cascading Gain/Loss recalculation | Keeps edits/deletes simple and predictable; avoids multi-row UPDATE side effects |
| Gain/Loss calculated at insertion time only | Clear semantics — users understand the value reflects the delta from their prior entry |
| Pagination (20 rows/page) | Keeps queries fast; users can browse all data without loading everything at once |
| `.env` for credentials | Industry standard; prevents secrets in version control |

---

## Known Limitations

1. Editing or deleting a row does NOT recalculate Gain/Loss on subsequent rows for that user.
2. If a user inserts data for a past weekday (e.g., selects "Saturday" on Monday), the Gain/Loss compares against the last inserted record by `id`, not by date order.
3. SQL table/column names are interpolated via f-strings — safe only because they come from hardcoded `TABLE_CONFIG`. New functions must maintain this convention.
