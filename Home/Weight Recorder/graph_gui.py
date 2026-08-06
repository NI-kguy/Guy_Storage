import tkinter as tk
from tkinter import messagebox, ttk

from pymysql.err import OperationalError

from SQL import (
    TABLE_CONFIG,
    create_table,
    load_runtime_config,
    read_distinct_names,
    read_graph_data,
    read_graph_data_by_name,
)


class GraphGuiApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Weight and Gain/Loss Graphs")
        self.root.geometry("1100x760")

        self.table_name = TABLE_CONFIG["table_name"]
        self.status_var = tk.StringVar(value="Ready")
        self.rows: list[dict] = []

        self.weight_canvas: tk.Canvas | None = None
        self.gain_canvas: tk.Canvas | None = None
        self._build_ui()
        self.refresh_graph()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            container,
            text=f"Graph View: {self.table_name}",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor=tk.W)

        subtitle = ttk.Label(
            container,
            text="Top: Weight (kg) | Bottom: Gain/Loss (kg)",
            font=("Segoe UI", 10),
        )
        subtitle.pack(anchor=tk.W, pady=(2, 8))

        # --- Controls: Name filter + Refresh ---
        controls_frame = ttk.Frame(container)
        controls_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(controls_frame, text="Filter by Name:").pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.name_combo = ttk.Combobox(
            controls_frame, state="readonly", width=20
        )
        self.name_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.name_combo.bind("<<ComboboxSelected>>", self._on_name_selected)

        ttk.Button(
            controls_frame, text="Refresh Graph", command=self.refresh_graph
        ).pack(side=tk.LEFT)

        # --- Chart canvases ---
        chart_frame = ttk.Frame(container)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.weight_canvas = tk.Canvas(
            chart_frame,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#cccccc",
        )
        self.weight_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.gain_canvas = tk.Canvas(
            chart_frame,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#cccccc",
        )
        self.gain_canvas.pack(fill=tk.BOTH, expand=True)

        # --- Status bar ---
        status = ttk.Label(
            container, textvariable=self.status_var, anchor=tk.W
        )
        status.pack(fill=tk.X, pady=(8, 0))

        self.root.bind("<Configure>", self._on_resize)

    def _populate_name_combo(self) -> None:
        """Load distinct names into the filter combobox."""
        try:
            names = read_distinct_names(self.table_name)
        except Exception:
            names = []
        values = ["All"] + names
        self.name_combo["values"] = values
        if not self.name_combo.get():
            self.name_combo.set("All")

    def _on_name_selected(self, _event: tk.Event = None) -> None:
        self.refresh_graph()

    def _on_resize(self, _event: tk.Event = None) -> None:
        if (
            self.weight_canvas
            and self.gain_canvas
            and self.weight_canvas.winfo_width() > 50
            and self.weight_canvas.winfo_height() > 50
            and self.gain_canvas.winfo_width() > 50
            and self.gain_canvas.winfo_height() > 50
        ):
            self.draw_graph()

    def _to_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def refresh_graph(self) -> None:
        """Load data and redraw graphs."""
        self._populate_name_combo()
        selected_name = self.name_combo.get()

        try:
            if selected_name and selected_name != "All":
                self.rows = read_graph_data_by_name(
                    selected_name, self.table_name
                )
            else:
                self.rows = read_graph_data(self.table_name)

            self.draw_graph()
            label = selected_name if selected_name != "All" else "all users"
            self.status_var.set(
                f"Showing {len(self.rows)} row(s) for {label}."
            )
        except Exception as exc:
            self.status_var.set(f"Read error: {exc}")
            messagebox.showerror("Read Error", str(exc))

    def draw_graph(self) -> None:
        """Clear and redraw both graphs."""
        self.weight_canvas.delete("all")
        self.gain_canvas.delete("all")

        width = max(self.weight_canvas.winfo_width(), 1)
        height = max(self.weight_canvas.winfo_height(), 1)

        if not self.rows:
            self.weight_canvas.create_text(
                width // 2,
                height // 2,
                text="No data available. Insert rows first.",
                fill="#555555",
                font=("Segoe UI", 12),
            )
            self.gain_canvas.create_text(
                width // 2,
                height // 2,
                text="No data available. Insert rows first.",
                fill="#555555",
                font=("Segoe UI", 12),
            )
            return

        dates = []
        for r in self.rows:
            created = r.get("created_at", "")
            if hasattr(created, "strftime"):
                dates.append(created.strftime("%Y-%m-%d"))
            else:
                dates.append(str(created))
        weights = [self._to_float(r.get("Weight")) for r in self.rows]
        gains = [self._to_float(r.get("Gain_Loss")) for r in self.rows]

        self._draw_single_graph(
            canvas=self.weight_canvas,
            title="Weight (kg)",
            x_labels=dates,
            values=weights,
            color="#1e6ad3",
        )
        self._draw_single_graph(
            canvas=self.gain_canvas,
            title="Gain/Loss (kg)",
            x_labels=dates,
            values=gains,
            color="#2e9d55",
        )

    def _draw_single_graph(
        self,
        canvas: tk.Canvas,
        title: str,
        x_labels: list[str],
        values: list[float],
        color: str,
    ) -> None:
        """Draw a single line graph on the canvas."""
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        y_min = min(values)
        y_max = max(values)
        if y_min == y_max:
            y_min -= 1.0
            y_max += 1.0

        left_pad = 70
        right_pad = 30
        top_pad = 34
        bottom_pad = 70

        plot_w = max(width - left_pad - right_pad, 1)
        plot_h = max(height - top_pad - bottom_pad, 1)

        x0 = left_pad
        y0 = top_pad
        x1 = left_pad + plot_w
        y1 = top_pad + plot_h

        # Title
        canvas.create_text(
            x0, 14, text=title, fill=color, anchor="w",
            font=("Segoe UI", 11, "bold"),
        )

        # Plot area border
        canvas.create_rectangle(x0, y0, x1, y1, outline="#b8b8b8")

        # Y-axis ticks and grid
        y_ticks = 5
        for i in range(y_ticks + 1):
            ratio = i / y_ticks
            y = y1 - ratio * plot_h
            val = y_min + ratio * (y_max - y_min)
            canvas.create_line(x0, y, x1, y, fill="#efefef")
            canvas.create_text(
                x0 - 8, y, text=f"{val:.2f}", anchor="e",
                fill="#444444", font=("Segoe UI", 9),
            )

        # X-axis points
        count = len(x_labels)
        if count == 1:
            x_points = [x0 + plot_w / 2]
        else:
            step = plot_w / (count - 1)
            x_points = [x0 + idx * step for idx in range(count)]

        def y_coord(value: float) -> float:
            return y1 - ((value - y_min) / (y_max - y_min)) * plot_h

        points = []
        for idx, x in enumerate(x_points):
            y_val = y_coord(values[idx])
            points.append((x, y_val))

        # X-axis labels
        for idx, x in enumerate(x_points):
            if idx % max(1, count // 8) == 0 or idx == count - 1:
                canvas.create_line(x, y1, x, y1 + 4, fill="#666666")
                canvas.create_text(
                    x, y1 + 16, text=x_labels[idx], anchor="n",
                    fill="#444444", font=("Segoe UI", 9), angle=20,
                )

        # Draw the line and points
        self._draw_series(canvas, points, color)

    def _draw_series(
        self,
        canvas: tk.Canvas,
        points: list[tuple[float, float]],
        color: str,
    ) -> None:
        """Draw a data series as a line with circle markers."""
        if not points:
            return

        flat: list[float] = []
        for x, y in points:
            flat.extend([x, y])

        if len(points) > 1:
            canvas.create_line(*flat, fill=color, width=2, smooth=True)

        for x, y in points:
            canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3, fill=color, outline=color
            )


def main() -> None:
    load_runtime_config()
    try:
        create_table()
    except OperationalError as err:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Database Connection Error",
            "Unable to connect to MySQL.\n\n"
            "Check that your DB service is running and DB settings are "
            "correct (.env or db_config.py).\n\n"
            f"Details: {err}",
        )
        root.destroy()
        return

    root = tk.Tk()
    GraphGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
