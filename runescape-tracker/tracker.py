"""
RuneScape Account Tracker
-------------------------
Looks up an Old School RuneScape player's skills on the official hiscores,
saves a "snapshot" each time you check, and shows how much XP you've gained.

Usage:
    python3 tracker.py check   "Player Name"
    python3 tracker.py gains   "Player Name"
    python3 tracker.py history "Player Name"
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# The free, public hiscores address. {} gets replaced by the player's name.
HISCORES_URL = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.json?player={}"

# Snapshots are saved in a "data" folder next to this file.
DATA_FOLDER = Path(__file__).parent / "data"


# ---------- Getting data from the internet ----------

def fetch_stats(player):
    """Download a player's skills. Returns a dict like {"Attack": {"level": 99, "xp": 13034431}, ...}"""
    url = HISCORES_URL.format(urllib.parse.quote(player))
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            sys.exit(f"Player '{player}' was not found on the hiscores. Check the spelling?")
        sys.exit(f"The hiscores website had a problem (error {error.code}). Try again later.")
    except urllib.error.URLError:
        sys.exit("Couldn't reach the hiscores website. Are you connected to the internet?")

    stats = {}
    for skill in data["skills"]:
        # Unranked skills come back as -1; treat those as 0 XP.
        stats[skill["name"]] = {"level": skill["level"], "xp": max(skill["xp"], 0)}
    return stats


# ---------- Saving and loading snapshots ----------

def snapshot_file(player):
    """The file where this player's snapshots are stored, e.g. data/zezima.json"""
    return DATA_FOLDER / f"{player.lower()}.json"


def load_snapshots(player):
    """Return the list of saved snapshots (oldest first), or an empty list."""
    file = snapshot_file(player)
    if not file.exists():
        return []
    return json.loads(file.read_text())


def save_snapshot(player, stats):
    """Add today's stats to the player's snapshot file."""
    snapshots = load_snapshots(player)
    snapshots.append({"time": datetime.now().isoformat(timespec="seconds"), "stats": stats})
    DATA_FOLDER.mkdir(exist_ok=True)
    snapshot_file(player).write_text(json.dumps(snapshots, indent=2))


# ---------- Printing things nicely ----------

def show_stats(player, stats):
    print(f"\n  Stats for {player}\n")
    print(f"  {'Skill':<14}{'Level':>6}{'XP':>16}")
    print("  " + "-" * 36)
    for name, skill in stats.items():
        print(f"  {name:<14}{skill['level']:>6}{skill['xp']:>16,}")
    print()


def show_gains(player):
    snapshots = load_snapshots(player)
    if len(snapshots) < 2:
        sys.exit(f"Need at least 2 snapshots for '{player}'. Run 'check' again later!")

    first, latest = snapshots[0], snapshots[-1]
    print(f"\n  Gains for {player}")
    print(f"  from {first['time']}  to  {latest['time']}\n")
    print(f"  {'Skill':<14}{'Levels':>8}{'XP gained':>16}")
    print("  " + "-" * 38)

    any_gains = False
    for name, now in latest["stats"].items():
        before = first["stats"].get(name, {"level": 0, "xp": 0})
        xp_gained = now["xp"] - before["xp"]
        levels_gained = now["level"] - before["level"]
        if xp_gained > 0:
            any_gains = True
            print(f"  {name:<14}{levels_gained:>+8}{xp_gained:>+16,}")

    if not any_gains:
        print("  No XP gained yet. Go train something!")
    print()


def show_history(player):
    snapshots = load_snapshots(player)
    if not snapshots:
        sys.exit(f"No snapshots saved for '{player}' yet. Run 'check' first.")
    print(f"\n  Snapshots for {player}:\n")
    for number, snap in enumerate(snapshots, start=1):
        total_level = snap["stats"]["Overall"]["level"]
        print(f"  {number:>3}. {snap['time']}   total level {total_level}")
    print()


# ---------- The command-line menu ----------

def main():
    parser = argparse.ArgumentParser(description="Track your Old School RuneScape progress.")
    parser.add_argument("command", choices=["check", "gains", "history"],
                        help="check = look up and save, gains = show progress, history = list snapshots")
    parser.add_argument("player", help='Player name (use quotes if it has spaces, e.g. "Lynx Titan")')
    args = parser.parse_args()

    if args.command == "check":
        stats = fetch_stats(args.player)
        show_stats(args.player, stats)
        save_snapshot(args.player, stats)
        print("  Snapshot saved!\n")
    elif args.command == "gains":
        show_gains(args.player)
    elif args.command == "history":
        show_history(args.player)


# This line means "run main() when this file is started directly".
if __name__ == "__main__":
    main()
