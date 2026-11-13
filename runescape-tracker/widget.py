"""
RuneScape Tracker desktop widget
--------------------------------
A small window that stays on top of your other windows and shows each saved
account's total level and the XP it gained today or this week.

Run it with:
    python3 widget.py
"""

import queue
import threading
import tkinter as tk

import tracker

REFRESH_MINUTES = 15

# Colors for the window
BACKGROUND = "#1e1e24"
TEXT = "#e8e6e3"
DIM = "#8a8a94"
GOLD = "#f2c14e"
GREEN = "#6fcf7f"
RED = "#e86a6a"


class Widget:
    def __init__(self, window):
        self.window = window
        self.period = tk.StringVar(value="day")
        # Internet lookups happen in the background so the window never freezes.
        # When a lookup finishes, its result waits in this queue until the window picks it up.
        self.results = queue.Queue()
        self.timer = None  # the next automatic refresh

        window.title("RS Tracker")
        window.configure(bg=BACKGROUND, padx=12, pady=10)
        window.attributes("-topmost", True)  # stay on top of other windows
        window.resizable(False, False)

        self.build_header()
        self.accounts_frame = tk.Frame(window, bg=BACKGROUND)
        self.accounts_frame.pack(fill="x", pady=(8, 8))
        self.build_add_box()

        self.refresh()
        self.check_for_results()

    # ---------- Building the window ----------

    def build_header(self):
        header = tk.Frame(self.window, bg=BACKGROUND)
        header.pack(fill="x")
        tk.Label(header, text="⚔ RS Tracker", fg=GOLD, bg=BACKGROUND,
                 font=("Helvetica", 14, "bold")).pack(side="left")
        tk.Button(header, text="↻", command=self.refresh, width=2,
                  highlightbackground=BACKGROUND).pack(side="right")
        for period in ["week", "day"]:
            tk.Radiobutton(header, text=period, value=period, variable=self.period,
                           command=self.refresh, fg=TEXT, bg=BACKGROUND,
                           selectcolor=BACKGROUND, activebackground=BACKGROUND).pack(side="right")

    def build_add_box(self):
        box = tk.Frame(self.window, bg=BACKGROUND)
        box.pack(fill="x")
        self.name_entry = tk.Entry(box, width=18)
        self.name_entry.pack(side="left", fill="x", expand=True)
        self.name_entry.bind("<Return>", lambda event: self.add_account())
        tk.Button(box, text="Add", command=self.add_account,
                  highlightbackground=BACKGROUND).pack(side="left", padx=(6, 0))
        self.status = tk.Label(self.window, text="", fg=DIM, bg=BACKGROUND, font=("Helvetica", 10))
        self.status.pack(anchor="w", pady=(4, 0))

    def show_row(self, name, text, detail, color):
        row = tk.Frame(self.accounts_frame, bg=BACKGROUND)
        row.pack(fill="x", pady=3)
        top = tk.Frame(row, bg=BACKGROUND)
        top.pack(fill="x")
        tk.Label(top, text=name, fg=TEXT, bg=BACKGROUND,
                 font=("Helvetica", 12, "bold")).pack(side="left")
        tk.Button(top, text="✕", width=1, command=lambda: self.remove_account(name),
                  highlightbackground=BACKGROUND).pack(side="right")
        tk.Label(top, text=text, fg=color, bg=BACKGROUND,
                 font=("Helvetica", 12)).pack(side="right", padx=6)
        if detail:
            tk.Label(row, text=detail, fg=DIM, bg=BACKGROUND, font=("Helvetica", 10),
                     justify="left").pack(anchor="w")

    # ---------- Getting the data ----------

    def refresh(self):
        """Look up every saved account in the background."""
        names = tracker.load_accounts()
        for child in self.accounts_frame.winfo_children():
            child.destroy()
        if not names:
            tk.Label(self.accounts_frame, text="Add an account below to start.",
                     fg=DIM, bg=BACKGROUND).pack(anchor="w")
            return
        self.status.config(text="Updating…")
        period = self.period.get()
        threading.Thread(target=self.look_up, args=(names, period), daemon=True).start()

    def look_up(self, names, period):
        """Runs in the background: fetch each account, then hand the results to the window."""
        rows = []
        for name in names:
            try:
                total_level = tracker.fetch_stats(name)["Overall"]["level"]
                gains = tracker.fetch_gains(name, period)
                xp = gains.pop("Overall", {"xp": 0})["xp"]
                top_skills = sorted(gains.items(), key=lambda item: item[1]["xp"], reverse=True)[:3]
                detail = "   ".join(f"{skill} +{gain['xp']:,}" for skill, gain in top_skills)
                rows.append((name, f"Lvl {total_level}  ·  +{xp:,} xp", detail, GREEN if xp else TEXT))
            except tracker.TrackerError as error:
                rows.append((name, "", str(error), RED))
        self.results.put(rows)

    def check_for_results(self):
        """Every half second, see if a background lookup has finished."""
        try:
            rows = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            for child in self.accounts_frame.winfo_children():
                child.destroy()
            for row in rows:
                self.show_row(*row)
            self.status.config(text=f"Gains this {self.period.get()} · refreshes every {REFRESH_MINUTES} min")
            # Cancel any automatic refresh already waiting, so only one is ever scheduled.
            if self.timer:
                self.window.after_cancel(self.timer)
            self.timer = self.window.after(REFRESH_MINUTES * 60 * 1000, self.refresh)
        self.window.after(500, self.check_for_results)

    # ---------- Buttons ----------

    def add_account(self):
        name = self.name_entry.get().strip()
        if name:
            tracker.add_account(name)
            self.name_entry.delete(0, "end")
            self.refresh()

    def remove_account(self, name):
        tracker.remove_account(name)
        self.refresh()


if __name__ == "__main__":
    window = tk.Tk()
    Widget(window)
    window.mainloop()
