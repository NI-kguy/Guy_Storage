# Weight Recorder — Implementation Summary

## Quick Reference

| Item | Detail |
|------|--------|
| Language | Python 3.11+ |
| GUI Framework | tkinter / ttk (stdlib) |
| Database | Aiven Cloud MySQL (PyMySQL driver) |
| Config | `.env` file via `python-dotenv` |
| Package Manager | `uv` (virtual env at `.venv`) |
| Entry Point | `python gui.py` |

---

## File Structure

```
Weight Recorder/
├── .env                  # DB credentials (not in git)
├── .env.example          # Template for .env
├── .gitignore            # Ignores .env, db_config.py, __pycache__, *.spec
├── gui.py                # Main window (form, table, pagination, edit/delete)
├── graph_gui.py          # Graph window (weight + gain/loss charts, Name filter)
├── SQL.py                # Database layer (all CRUD + pagination queries)
├── proposal.md           # Design document
├── Idea.md               # Original requirements
└── tests/
    └── test_sql.py       # 15 unit tests (mocked DB)
```

---

## Architecture

```
gui.py (TableGuiApp)
  ├── SQL.py (database functions)
  │     └── .env (credentials via python-dotenv)
  └── graph_gui.py (GraphGuiApp, opened as Toplevel)
        └── SQL.py (read graph data)
```

---

## SQL.py — Database Layer

### Configuration

- Loads `.env` once via `load_runtime_config()` → `dotenv.load_dotenv()`
- Env vars: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_TIMEOUT`
- `TABLE_CONFIG` dict defines table name, columns, and insert columns
- Table: `Weight_Log` with columns `id`, `Name`, `Day`, `Weight`, `Gain_Loss`, `created_at`

### Functions

| Function | Purpose |
|----------|---------|
| `load_runtime_config()` | Load .env into environment (idempotent) |
| `get_connection()` | Return a PyMySQL connection using env vars |
| `create_table()` | CREATE TABLE IF NOT EXISTS |
| `insert_data(rows)` | INSERT rows, returns count |
| `update_data(row_id, updates)` | UPDATE single row by id |
| `remove_data(row_id)` | DELETE row by id (or all if None) |
| `read_latest_data(limit)` | SELECT latest N rows (ORDER BY id DESC) |
| `read_paginated_data(page, page_size)` | Returns `(rows, total_count)` with LIMIT/OFFSET |
| `read_latest_weight_by_name(name)` | Latest weight for a Name (for gain/loss calc) |
| `read_distinct_names()` | All distinct Names (for dropdowns) |
| `read_graph_data()` | Day, Weight, Gain_Loss for all users (ORDER BY id ASC) |
| `read_graph_data_by_name(name)` | Same but filtered by Name |

### Conventions

- All functions accept optional `table_name` override (defaults to `TABLE_CONFIG`)
- Column/table names are f-string interpolated — safe because they come from hardcoded config only
- Uses `DictCursor` — all queries return `list[dict]`
- Each function opens and closes its own connection

---

## gui.py — Main Window

### Classes

**`TableGuiApp`** — Main application frame:
- Form: Name (Entry), Day (Combobox, Sun–Sat), Weight (Entry)
- Buttons: Insert, Refresh, Delete Selected, Open Graph
- Table: `ttk.Treeview` showing paginated data (20 rows/page)
- Pagination: Previous / Next buttons with "Page X of Y" label
- Double-click row → opens `EditDialog`

**`EditDialog`** — Modal Toplevel for editing a row:
- Pre-fills Name, Day (weekday combobox), Weight
- Recalculates Gain/Loss on save (per-Name)
- Returns updated dict or None (cancelled)

### Key Logic

- **Weekday → Date mapping**: `_weekday_to_date(weekday_name)` converts selected weekday to the most recent `YYYY-MM-DD` occurrence
- **Date → Weekday**: `_date_to_weekday(date_str)` for pre-selecting combobox in edit dialog
- **Gain/Loss**: `current_weight - read_latest_weight_by_name(name)` (0.0 if first entry)
- **Pagination state**: `current_page`, `total_rows`, `total_pages` — updates on every refresh

### Entry Point

```python
def main() -> None:
    load_runtime_config()
    create_table()
    root = tk.Tk()
    TableGuiApp(root)
    root.mainloop()
```

---

## graph_gui.py — Graph Window

### Class: `GraphGuiApp`

- Opened as `tk.Toplevel` from the main window
- Name filter combobox: "All" + distinct names from DB
- Two `tk.Canvas` charts: Weight line graph + Gain/Loss line graph
- X-axis: full date labels (`YYYY-MM-DD`)
- Auto-redraws on window resize and name selection change
- Custom `_draw_single_graph()` renders line chart with axes, labels, and data points

---

## Features Implemented

1. **Per-user Gain/Loss** — compares against last record for the same Name (by id order)
2. **Weekday selector** — combobox (Sun–Sat), stores full YYYY-MM-DD date
3. **Edit row** — double-click → modal dialog → recalculates gain/loss → saves
4. **Delete row** — select + click Delete → confirmation → removes from DB
5. **Graph by Name** — dropdown filter on graph window
6. **Pagination** — 20 rows/page, Previous/Next, disabled at boundaries
7. **Secure credentials** — .env file, not in version control

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Store full date, display weekday in combobox | Graphs need chronological order; users get simple selector |
| No cascading Gain/Loss recalculation | Edit/delete stay simple; avoids multi-row UPDATE side effects |
| Gain/Loss calculated at insertion time only | Clear semantics — delta from the user's prior entry |
| Pagination (20 rows/page) with LIMIT/OFFSET | Fast queries; users browse without loading everything |
| `.env` for credentials | Industry standard; secrets stay out of version control |
| Each SQL function manages its own connection | Simple; no shared state; safe for single-threaded tkinter |

---

## Known Limitations

1. Editing/deleting a row does NOT recalculate Gain/Loss on subsequent rows
2. Gain/Loss compares by `id` order (insertion order), not by date
3. Table/column names are f-string interpolated (safe only from hardcoded config)

---

## Running the App

```powershell
cd "F:\dev\Guy_Storage\Weight Recorder"
.venv\Scripts\python gui.py
```

### Dependencies (in `.venv`)

- `pymysql`
- `python-dotenv`
- `pytest` (dev only)
