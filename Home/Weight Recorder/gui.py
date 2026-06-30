import datetime
import math
import tkinter as tk
from tkinter import messagebox, ttk

from SQL import (
    TABLE_CONFIG,
    create_table,
    insert_data,
    load_runtime_config,
    read_latest_weight_by_name,
    read_paginated_data,
    remove_data,
    update_data,
)
from graph_gui import GraphGuiApp


PAGE_SIZE = 20

DAYS_OF_WEEK = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def _display_label(col_name: str) -> str:
    """Format column names for display with units."""
    if col_name == "Weight":
        return "Weight (kg)"
    if col_name == "Gain_Loss":
        return "Gain/Loss (kg)"
    return col_name





class EditDialog:
    """Modal dialog for editing an existing row."""

    def __init__(
        self, parent: tk.Tk, row_data: dict, table_name: str
    ) -> None:
        self.result: dict | None = None
        self.row_id = row_data["id"]
        self.table_name = table_name

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit Row #{self.row_id}")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        # Name
        ttk.Label(frame, text="Name:").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.name_entry = ttk.Entry(frame, width=30)
        self.name_entry.insert(0, str(row_data.get("Name", "")))
        self.name_entry.grid(row=0, column=1, sticky="we", pady=4)

        # Day (weekday combobox)
        ttk.Label(frame, text="Day:").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.day_combo = ttk.Combobox(
            frame, values=DAYS_OF_WEEK, state="readonly", width=28
        )
        current_day = str(row_data.get("Day", ""))
        if current_day in DAYS_OF_WEEK:
            self.day_combo.set(current_day)
        else:
            self.day_combo.set(DAYS_OF_WEEK[0])
        self.day_combo.grid(row=1, column=1, sticky="we", pady=4)

        # Weight
        ttk.Label(frame, text="Weight (kg):").grid(
            row=2, column=0, sticky="w", pady=4
        )
        self.weight_entry = ttk.Entry(frame, width=30)
        weight_val = row_data.get("Weight", "")
        self.weight_entry.insert(0, str(weight_val))
        self.weight_entry.grid(row=2, column=1, sticky="we", pady=4)

        frame.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(16, 0))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(
            side=tk.LEFT
        )

        self.dialog.wait_window()

    def _save(self) -> None:
        name = self.name_entry.get().strip()
        weekday = self.day_combo.get()
        weight_str = self.weight_entry.get().strip()

        if not name:
            messagebox.showwarning(
                "Missing Data", "Name is required.", parent=self.dialog
            )
            return
        if not weekday:
            messagebox.showwarning(
                "Missing Data", "Day is required.", parent=self.dialog
            )
            return
        try:
            weight = float(weight_str.lower().replace("kg", "").strip())
        except ValueError:
            messagebox.showwarning(
                "Invalid Data",
                "Weight must be a valid number.",
                parent=self.dialog,
            )
            return

        # Recalculate Gain/Loss based on prior record for same Name
        latest_weight = read_latest_weight_by_name(
            name, self.table_name, before_id=self.row_id
        )
        if latest_weight is not None:
            gain_loss = weight - latest_weight
        else:
            gain_loss = 0.0

        self.result = {
            "Name": name,
            "Day": weekday,
            "Weight": weight,
            "Gain_Loss": gain_loss,
        }
        self.dialog.destroy()


class TableGuiApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Weight Recorder")
        self.root.geometry("1100x700")

        self.table_name = TABLE_CONFIG["table_name"]
        self.form_entries: dict[str, ttk.Entry | ttk.Combobox] = {}
        self.graph_window: tk.Toplevel | None = None
        self.graph_app: GraphGuiApp | None = None

        # Pagination state
        self.current_page = 1
        self.total_rows = 0
        self.total_pages = 1

        self.status_var = tk.StringVar(
            value=f"Ready — table: {self.table_name}"
        )

        self._build_ui()
        self.refresh_table()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            container,
            text=f"Weight Recorder — {self.table_name}",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor=tk.W)

        # --- Form frame ---
        form_frame = ttk.LabelFrame(container, text="Insert Data", padding=10)
        form_frame.pack(fill=tk.X, pady=(10, 8))

        # Name
        ttk.Label(form_frame, text="Name:").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=4
        )
        name_entry = ttk.Entry(form_frame, width=40)
        name_entry.grid(row=0, column=1, sticky="we", pady=4)
        self.form_entries["Name"] = name_entry

        # Day (weekday combobox)
        ttk.Label(form_frame, text="Day:").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=4
        )
        day_combo = ttk.Combobox(
            form_frame, values=DAYS_OF_WEEK, state="readonly", width=38
        )
        today_weekday = datetime.date.today().strftime("%A")
        day_combo.set(today_weekday)
        day_combo.grid(row=1, column=1, sticky="we", pady=4)
        self.form_entries["Day"] = day_combo

        # Weight
        ttk.Label(form_frame, text="Weight (kg):").grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=4
        )
        weight_entry = ttk.Entry(form_frame, width=40)
        weight_entry.grid(row=2, column=1, sticky="we", pady=4)
        self.form_entries["Weight"] = weight_entry

        form_frame.columnconfigure(1, weight=1)

        # --- Buttons ---
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        ttk.Button(btn_frame, text="Insert", command=self.insert_row).pack(
            side=tk.LEFT
        )
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_table).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(
            btn_frame, text="Delete Selected", command=self.delete_selected
        ).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(
            btn_frame, text="Open Graph", command=self.open_graph_gui
        ).pack(side=tk.LEFT, padx=(8, 0))

        # --- Table frame ---
        table_frame = ttk.LabelFrame(container, text="Data View", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(table_frame, show="headings")
        y_scroll = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        x_scroll = ttk.Scrollbar(
            table_frame, orient=tk.HORIZONTAL, command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        # Double-click to edit
        self.tree.bind("<Double-1>", self._on_double_click)

        # Pagination controls
        page_frame = ttk.Frame(table_frame)
        page_frame.grid(row=2, column=0, columnspan=2, pady=(8, 0))

        self.prev_btn = ttk.Button(
            page_frame, text="◀ Previous", command=self._prev_page
        )
        self.prev_btn.pack(side=tk.LEFT)

        self.page_label = ttk.Label(
            page_frame, text="Page 1 of 1", font=("Segoe UI", 10)
        )
        self.page_label.pack(side=tk.LEFT, padx=16)

        self.next_btn = ttk.Button(
            page_frame, text="Next ▶", command=self._next_page
        )
        self.next_btn.pack(side=tk.LEFT)

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # --- Status bar ---
        status = ttk.Label(container, textvariable=self.status_var, anchor=tk.W)
        status.pack(fill=tk.X, pady=(8, 0))

    def _setup_columns(self, rows: list[dict]) -> None:
        if not rows:
            self.tree["columns"] = ()
            return

        columns = list(rows[0].keys())
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=_display_label(col))
            width = 120 if col.lower() != "id" else 70
            anchor = tk.CENTER if col.lower() == "id" else tk.W
            self.tree.column(col, width=width, anchor=anchor)

    def refresh_table(self) -> None:
        """Reload the current page of data."""
        try:
            rows, self.total_rows = read_paginated_data(
                page=self.current_page,
                page_size=PAGE_SIZE,
                table_name=self.table_name,
            )
            self.total_pages = max(1, math.ceil(self.total_rows / PAGE_SIZE))

            # Clamp page if data was deleted
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages
                rows, self.total_rows = read_paginated_data(
                    page=self.current_page,
                    page_size=PAGE_SIZE,
                    table_name=self.table_name,
                )

            self._setup_columns(rows)

            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                display_values = []
                for col in self.tree["columns"]:
                    value = row[col]
                    if col in {"Weight", "Gain_Loss"} and value is not None:
                        value = f"{value} kg"
                    display_values.append(value)
                self.tree.insert("", tk.END, values=display_values)

            self._update_pagination_ui()
            self.status_var.set(
                f"Loaded page {self.current_page}/{self.total_pages} "
                f"({self.total_rows} total rows)."
            )
        except Exception as exc:
            self.status_var.set(f"Read error: {exc}")
            messagebox.showerror("Read Error", str(exc))

    def _update_pagination_ui(self) -> None:
        self.page_label.config(
            text=f"Page {self.current_page} of {self.total_pages}"
        )
        self.prev_btn.config(
            state=tk.NORMAL if self.current_page > 1 else tk.DISABLED
        )
        self.next_btn.config(
            state=tk.NORMAL
            if self.current_page < self.total_pages
            else tk.DISABLED
        )

    def _prev_page(self) -> None:
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_table()

    def _next_page(self) -> None:
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_table()

    def insert_row(self) -> None:
        """Validate form inputs and insert a new row."""
        name = self.form_entries["Name"].get().strip()
        weekday = self.form_entries["Day"].get()
        weight_str = self.form_entries["Weight"].get().strip()

        if not name:
            messagebox.showwarning("Missing Data", "Name is required.")
            return
        if not weekday:
            messagebox.showwarning("Missing Data", "Day is required.")
            return
        try:
            weight = float(weight_str.lower().replace("kg", "").strip())
        except ValueError:
            messagebox.showwarning(
                "Invalid Data", "Weight must be a valid number."
            )
            return

        # Per-user Gain/Loss calculation
        latest_weight = read_latest_weight_by_name(name, self.table_name)
        if latest_weight is not None:
            gain_loss = weight - latest_weight
        else:
            gain_loss = 0.0

        payload = {
            "Name": name,
            "Day": weekday,
            "Weight": weight,
            "Gain_Loss": gain_loss,
        }

        try:
            inserted = insert_data(
                [payload], self.table_name, TABLE_CONFIG["insert_columns"]
            )
            # Clear form
            self.form_entries["Name"].delete(0, tk.END)
            self.form_entries["Weight"].delete(0, tk.END)
            today_weekday = datetime.date.today().strftime("%A")
            self.form_entries["Day"].set(today_weekday)

            self.current_page = 1  # Go to first page to see new entry
            self.status_var.set(
                f"Inserted {inserted} row(s). "
                f"Gain/Loss: {gain_loss:+.2f} kg."
            )
            self.refresh_table()
        except Exception as exc:
            self.status_var.set(f"Insert error: {exc}")
            messagebox.showerror("Insert Error", str(exc))

    def delete_selected(self) -> None:
        """Delete the currently selected row after confirmation."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection", "Please select a row to delete."
            )
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        columns = self.tree["columns"]

        # Find the id column index
        try:
            id_idx = list(columns).index("id")
            row_id = int(values[id_idx])
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Cannot determine row ID.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete row #{row_id}?",
        )
        if not confirm:
            return

        try:
            deleted = remove_data(self.table_name, row_id=row_id)
            self.status_var.set(f"Deleted {deleted} row(s).")
            self.refresh_table()
        except Exception as exc:
            self.status_var.set(f"Delete error: {exc}")
            messagebox.showerror("Delete Error", str(exc))

    def _on_double_click(self, event: tk.Event) -> None:
        """Open the edit dialog for the double-clicked row."""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        columns = list(self.tree["columns"])

        # Build row dict from tree values
        row_data = {}
        for idx, col in enumerate(columns):
            val = values[idx]
            # Strip " kg" suffix for numeric columns
            if col in {"Weight", "Gain_Loss"} and isinstance(val, str):
                val = val.replace(" kg", "").strip()
            row_data[col] = val

        # Ensure id is int
        try:
            row_data["id"] = int(row_data["id"])
        except (ValueError, KeyError):
            return

        dialog = EditDialog(self.root, row_data, self.table_name)
        if dialog.result:
            try:
                update_data(dialog.row_id, dialog.result, self.table_name)
                self.status_var.set(f"Updated row #{dialog.row_id}.")
                self.refresh_table()
            except Exception as exc:
                self.status_var.set(f"Update error: {exc}")
                messagebox.showerror("Update Error", str(exc))

    def open_graph_gui(self) -> None:
        """Open or focus the Graph GUI window."""
        try:
            if self.graph_window and self.graph_window.winfo_exists():
                self.graph_window.lift()
                self.graph_window.focus_force()
                if self.graph_app:
                    self.graph_app.refresh_graph()
            else:
                self.graph_window = tk.Toplevel(self.root)
                self.graph_app = GraphGuiApp(self.graph_window)
            self.status_var.set("Opened Graph window.")
        except Exception as exc:
            messagebox.showerror("Open Graph Error", str(exc))


def main() -> None:
    load_runtime_config()
    create_table()

    root = tk.Tk()
    TableGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
