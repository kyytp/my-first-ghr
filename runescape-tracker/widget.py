"""
RuneScape Tracker desktop widget
--------------------------------
A resizable window that stays on top of your other windows. It shows one
account at a time: all 24 skill levels in a 3 x 8 grid, then the XP gained
today or this week.

Run it with:
    python3 widget.py
"""

import queue
import threading
import tkinter as tk
import urllib.request
from pathlib import Path

import tracker

REFRESH_MINUTES = 15
GRID_COLUMNS = 3

# Skill icons come from the Old School RuneScape Wiki. They're downloaded once
# into an "icons" folder and reused after that.
ICON_URL = "https://oldschool.runescape.wiki/images/{}_icon.png"
ICONS_FOLDER = Path(__file__).parent / "icons"

# Colors for the window
BACKGROUND = "#1e1e24"
CELL = "#2a2a33"
CELL_GAINED = "#26402c"  # cells for skills that gained XP get a green tint
TEXT = "#e8e6e3"
DIVIDER = "#44444f"
DIM = "#8a8a94"
GOLD = "#f2c14e"
GREEN = "#6fcf7f"
RED = "#e86a6a"


def download_icons():
    """Download any skill icons we don't have yet. Missing icons are skipped quietly."""
    ICONS_FOLDER.mkdir(exist_ok=True)
    for skill in tracker.SKILLS[1:]:
        file = ICONS_FOLDER / f"{skill}.png"
        if file.exists():
            continue
        request = urllib.request.Request(ICON_URL.format(skill), headers={"User-Agent": tracker.USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                file.write_bytes(response.read())
        except OSError:
            pass


def short_number(number):
    """Turn 1234567 into "1.2M" and 52300 into "52.3k" so it fits in a small cell."""
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}k"
    return str(number)


class Widget:
    def __init__(self, window):
        self.window = window
        self.period = tk.StringVar(value="day")
        self.account = tk.StringVar()
        # Internet lookups happen in the background so the window never freezes.
        # When a lookup finishes, its result waits in this queue until the window picks it up.
        self.results = queue.Queue()
        self.timer = None  # the next automatic refresh

        window.title("RS Tracker")
        window.configure(bg=BACKGROUND, padx=12, pady=10)
        window.attributes("-topmost", True)  # stay on top of other windows
        window.geometry("440x720")
        window.minsize(340, 520)
        # Show the RuneScape icon in the Dock, if make-app.sh has downloaded it.
        app_icon = ICONS_FOLDER / "app.png"
        if app_icon.exists():
            self.app_icon = tk.PhotoImage(file=app_icon)
            window.iconphoto(True, self.app_icon)

        self.build_header()
        self.build_skill_grid()
        self.build_gains_box()
        self.build_add_box()

        self.update_account_menu()
        self.refresh()
        self.check_for_results()
        threading.Thread(target=self.get_icons, daemon=True).start()

    # ---------- Building the window ----------

    def build_header(self):
        header = tk.Frame(self.window, bg=BACKGROUND)
        header.pack(fill="x")
        tk.Label(header, text="⚔ RS Tracker", fg=GOLD, bg=BACKGROUND,
                 font=("Helvetica", 15, "bold")).pack(side="left")
        tk.Button(header, text="↻", command=self.refresh, width=2,
                  highlightbackground=BACKGROUND).pack(side="right")

        # A thin line under the title so it has some breathing room.
        tk.Frame(self.window, height=1, bg=DIVIDER).pack(fill="x", pady=(8, 8))

        row = tk.Frame(self.window, bg=BACKGROUND)
        row.pack(fill="x")
        self.account_menu = tk.OptionMenu(row, self.account, "")
        self.account_menu.configure(bg=BACKGROUND, highlightbackground=BACKGROUND)
        self.account_menu.pack(side="left")
        self.total_label = tk.Label(row, text="", fg=GOLD, bg=BACKGROUND,
                                    font=("Helvetica", 13, "bold"))
        self.total_label.pack(side="right")

    def build_skill_grid(self):
        """24 cells (3 across, 8 down), one per skill, each with the skill name and level."""
        grid = tk.Frame(self.window, bg=BACKGROUND)
        grid.pack(fill="both", expand=True, pady=(8, 0))
        skills = tracker.SKILLS[1:]  # everything except "Overall", which goes in the header
        self.cells = {}
        for index, skill in enumerate(skills):
            row, column = divmod(index, GRID_COLUMNS)
            cell = tk.Frame(grid, bg=CELL, padx=6, pady=3)
            cell.grid(row=row, column=column, sticky="nsew", padx=2, pady=2)
            # Packed first so it claims the right-hand side of the box.
            icon = tk.Label(cell, bg=CELL)
            icon.pack(side="right", padx=(4, 0))
            name = tk.Label(cell, text=skill, fg=DIM, bg=CELL, font=("Helvetica", 10), anchor="w")
            name.pack(fill="x")
            level = tk.Label(cell, text="–", fg=TEXT, bg=CELL, font=("Helvetica", 16, "bold"), anchor="w")
            level.pack(side="left")
            gained = tk.Label(cell, text="", fg=GREEN, bg=CELL, font=("Helvetica", 10), anchor="e")
            gained.pack(side="right")
            self.cells[skill] = (cell, name, level, gained, icon)
        # Let the cells stretch when the window is resized.
        for column in range(GRID_COLUMNS):
            grid.columnconfigure(column, weight=1, uniform="skills")
        for row in range(len(skills) // GRID_COLUMNS):
            grid.rowconfigure(row, weight=1, uniform="skills")

    def build_gains_box(self):
        header = tk.Frame(self.window, bg=BACKGROUND)
        header.pack(fill="x", pady=(10, 2))
        self.gains_title = tk.Label(header, text="XP gained", fg=GOLD, bg=BACKGROUND,
                                    font=("Helvetica", 12, "bold"))
        self.gains_title.pack(side="left")
        for period in ["week", "day"]:
            tk.Radiobutton(header, text=period, value=period, variable=self.period,
                           command=self.refresh, fg=TEXT, bg=BACKGROUND,
                           selectcolor=BACKGROUND, activebackground=BACKGROUND).pack(side="right")
        # A text box scrolls on its own if the list of gains gets long.
        self.gains_text = tk.Text(self.window, height=7, bg=CELL, fg=TEXT, relief="flat",
                                  font=("Menlo", 11), padx=8, pady=6, highlightthickness=0)
        self.gains_text.pack(fill="both", expand=True)
        self.gains_text.tag_configure("dim", foreground=DIM)
        self.gains_text.tag_configure("green", foreground=GREEN)
        self.gains_text.tag_configure("red", foreground=RED)

    def build_add_box(self):
        box = tk.Frame(self.window, bg=BACKGROUND)
        box.pack(fill="x", pady=(10, 0))
        self.name_entry = tk.Entry(box, width=18)
        self.name_entry.pack(side="left", fill="x", expand=True)
        self.name_entry.bind("<Return>", lambda event: self.add_account())
        tk.Button(box, text="Add", command=self.add_account,
                  highlightbackground=BACKGROUND).pack(side="left", padx=(6, 0))
        tk.Button(box, text="Remove", command=self.remove_account,
                  highlightbackground=BACKGROUND).pack(side="left", padx=(6, 0))
        self.status = tk.Label(self.window, text="", fg=DIM, bg=BACKGROUND, font=("Helvetica", 10))
        self.status.pack(anchor="w", pady=(4, 0))

    def update_account_menu(self):
        """Fill the account dropdown with the saved names."""
        names = tracker.load_accounts()
        menu = self.account_menu["menu"]
        menu.delete(0, "end")
        for name in names:
            menu.add_command(label=name, command=lambda n=name: self.choose_account(n))
        if self.account.get() not in names:
            self.account.set(names[0] if names else "No accounts")

    def choose_account(self, name):
        self.account.set(name)
        self.refresh()

    # ---------- Getting the data ----------

    def refresh(self):
        """Look up the chosen account in the background."""
        name = self.account.get()
        if name not in tracker.load_accounts():
            self.show_message("Type an account name below and press Add.", "dim")
            return
        self.status.config(text="Updating…")
        threading.Thread(target=self.look_up, args=(name, self.period.get()), daemon=True).start()

    def look_up(self, name, period):
        """Runs in the background: fetch stats and gains, then hand them to the window."""
        try:
            self.results.put((name, period, tracker.fetch_stats(name), tracker.fetch_gains(name, period), None))
        except tracker.TrackerError as error:
            self.results.put((name, period, None, None, str(error)))

    def get_icons(self):
        """Runs in the background: download the icons, then tell the window they're ready."""
        download_icons()
        self.results.put("icons ready")

    def show_icons(self):
        self.icon_images = []  # Tk forgets images unless we keep hold of them
        for skill, (cell, name, level, gained, icon) in self.cells.items():
            file = ICONS_FOLDER / f"{skill}.png"
            if file.exists():
                image = tk.PhotoImage(file=file)
                self.icon_images.append(image)
                icon.config(image=image)

    def check_for_results(self):
        """Every half second, see if a background lookup has finished."""
        try:
            result = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            if result == "icons ready":
                self.show_icons()
                self.window.after(500, self.check_for_results)
                return
            name, period, stats, gains, error = result
            # Ignore old answers for an account or period that is no longer chosen.
            if name == self.account.get() and period == self.period.get():
                if error:
                    self.show_message(error, "red")
                    self.status.config(text="")
                else:
                    self.show_account(stats, gains, period)
                    self.status.config(text=f"Refreshes every {REFRESH_MINUTES} min")
                # Cancel any automatic refresh already waiting, so only one is ever scheduled.
                if self.timer:
                    self.window.after_cancel(self.timer)
                self.timer = self.window.after(REFRESH_MINUTES * 60 * 1000, self.refresh)
        self.window.after(500, self.check_for_results)

    # ---------- Showing the data ----------

    def show_account(self, stats, gains, period):
        self.total_label.config(text=f"Total level {stats['Overall']['level']:,}")
        for skill, (cell, name, level, gained, icon) in self.cells.items():
            xp = gains.get(skill, {}).get("xp", 0)
            color = CELL_GAINED if xp else CELL
            for part in (cell, name, level, gained, icon):
                part.config(bg=color)
            level.config(text=stats.get(skill, {}).get("level", "–"))
            gained.config(text=f"+{short_number(xp)}" if xp else "")

        self.gains_title.config(text=f"XP gained this {period}")
        self.gains_text.config(state="normal")
        self.gains_text.delete("1.0", "end")
        total = gains.pop("Overall", {"xp": 0})["xp"]
        if not gains:
            self.gains_text.insert("end", "No XP gained yet. Go train something!", "dim")
        else:
            self.gains_text.insert("end", f"{'Total':<14}{total:>+14,}\n", "green")
            for skill, gain in sorted(gains.items(), key=lambda item: item[1]["xp"], reverse=True):
                levels = f"  (+{gain['levels']} lvl)" if gain["levels"] else ""
                self.gains_text.insert("end", f"{skill:<14}{gain['xp']:>+14,}")
                self.gains_text.insert("end", f"{levels}\n", "green")
        self.gains_text.config(state="disabled")

    def show_message(self, message, color):
        """Clear the grid and show a message in the gains box instead."""
        self.total_label.config(text="")
        for cell, name, level, gained, icon in self.cells.values():
            for part in (cell, name, level, gained, icon):
                part.config(bg=CELL)
            level.config(text="–")
            gained.config(text="")
        self.gains_text.config(state="normal")
        self.gains_text.delete("1.0", "end")
        self.gains_text.insert("end", message, color)
        self.gains_text.config(state="disabled")

    # ---------- Buttons ----------

    def add_account(self):
        name = self.name_entry.get().strip()
        if name:
            tracker.add_account(name)
            self.name_entry.delete(0, "end")
            self.account.set(name)
            self.update_account_menu()
            self.refresh()

    def remove_account(self):
        tracker.remove_account(self.account.get())
        self.update_account_menu()
        self.refresh()


if __name__ == "__main__":
    window = tk.Tk()
    Widget(window)
    window.mainloop()
