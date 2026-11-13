"""
RuneScape Account Tracker
-------------------------
Looks up an Old School RuneScape player's skills and shows how much XP they've
gained. The only thing saved on your computer is the list of account names.

Current stats come from the official hiscores. XP gains come from Wise Old Man
(wiseoldman.net), a free website that keeps each player's stat history for you.

Usage:
    python3 tracker.py check  "Player Name"
    python3 tracker.py gains  "Player Name" [--period day|week|month]
    python3 tracker.py add    "Player Name"
    python3 tracker.py remove "Player Name"
    python3 tracker.py list
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# The free, public hiscores address. {} gets replaced by the player's name.
HISCORES_URL = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.json?player={}"

# Wise Old Man's address. It remembers stat history so we don't have to.
WISE_OLD_MAN_URL = "https://api.wiseoldman.net/v2/players/{}"

# Wise Old Man asks apps to say who they are.
USER_AGENT = "my-first-ghr-runescape-tracker"

# The only file this app saves: a list of account names.
ACCOUNTS_FILE = Path(__file__).parent / "data" / "accounts.json"


class TrackerError(Exception):
    """A problem we can explain to the user in plain English."""


# ---------- Getting data from the internet ----------

def get_json(url, method="GET"):
    """Visit a web address and return the JSON it sends back."""
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise TrackerError("Player not found. Check the spelling?")
        if error.code == 429:
            raise TrackerError("Too many requests. Wait a minute and try again.")
        raise TrackerError(f"The website had a problem (error {error.code}). Try again later.")
    except urllib.error.URLError:
        raise TrackerError("Couldn't reach the website. Are you connected to the internet?")


def fetch_stats(player):
    """Current skills from the official hiscores, like {"Attack": {"level": 99, "xp": 13034431}, ...}"""
    data = get_json(HISCORES_URL.format(urllib.parse.quote(player)))
    stats = {}
    for skill in data["skills"]:
        # Unranked skills come back as -1; treat those as 0 XP.
        stats[skill["name"]] = {"level": skill["level"], "xp": max(skill["xp"], 0)}
    return stats


def fetch_gains(player, period="week"):
    """XP gained over a period (day, week or month), from Wise Old Man.

    Returns {"Attack": {"levels": 1, "xp": 52000}, ...} for skills that gained XP.
    """
    url = WISE_OLD_MAN_URL.format(urllib.parse.quote(player))
    # Ask Wise Old Man to grab fresh stats first. If it says no (for example,
    # because it updated very recently), the gains it already has are still fine.
    try:
        get_json(url, method="POST")
    except TrackerError:
        pass

    data = get_json(f"{url}/gained?period={period}")
    gains = {}
    for name, skill in data["data"]["skills"].items():
        xp = skill["experience"]["gained"]
        if xp > 0:
            gains[name.capitalize()] = {"levels": skill["level"]["gained"], "xp": xp}
    return gains


# ---------- The saved list of account names ----------

def load_accounts():
    """Return the saved account names, or an empty list."""
    if not ACCOUNTS_FILE.exists():
        return []
    return json.loads(ACCOUNTS_FILE.read_text())


def save_accounts(names):
    ACCOUNTS_FILE.parent.mkdir(exist_ok=True)
    ACCOUNTS_FILE.write_text(json.dumps(names, indent=2))


def add_account(player):
    names = load_accounts()
    if player.lower() not in [name.lower() for name in names]:
        names.append(player)
        save_accounts(names)


def remove_account(player):
    names = [name for name in load_accounts() if name.lower() != player.lower()]
    save_accounts(names)


# ---------- Printing things nicely ----------

def show_stats(player, stats):
    print(f"\n  Stats for {player}\n")
    print(f"  {'Skill':<14}{'Level':>6}{'XP':>16}")
    print("  " + "-" * 36)
    for name, skill in stats.items():
        print(f"  {name:<14}{skill['level']:>6}{skill['xp']:>16,}")
    print()


def show_gains(player, gains, period):
    print(f"\n  Gains for {player} (past {period})\n")
    if not gains:
        print("  No XP gained yet. Go train something!\n")
        return
    print(f"  {'Skill':<14}{'Levels':>8}{'XP gained':>16}")
    print("  " + "-" * 38)
    for name, gain in gains.items():
        print(f"  {name:<14}{gain['levels']:>+8}{gain['xp']:>+16,}")
    print()


# ---------- The command-line menu ----------

def main():
    parser = argparse.ArgumentParser(description="Track your Old School RuneScape progress.")
    parser.add_argument("command", choices=["check", "gains", "add", "remove", "list"],
                        help="check = current stats, gains = XP gained, "
                             "add/remove/list = manage saved account names")
    parser.add_argument("player", nargs="?", help='Player name (use quotes if it has spaces, e.g. "Lynx Titan")')
    parser.add_argument("--period", choices=["day", "week", "month"], default="week",
                        help="How far back to count gains (default: week)")
    args = parser.parse_args()

    if args.command != "list" and not args.player:
        parser.error(f"'{args.command}' needs a player name")

    try:
        if args.command == "check":
            show_stats(args.player, fetch_stats(args.player))
        elif args.command == "gains":
            show_gains(args.player, fetch_gains(args.player, args.period), args.period)
        elif args.command == "add":
            fetch_stats(args.player)  # make sure the name is real before saving it
            add_account(args.player)
            print(f"Added {args.player}.")
        elif args.command == "remove":
            remove_account(args.player)
            print(f"Removed {args.player}.")
        elif args.command == "list":
            names = load_accounts()
            print("\n".join(names) if names else "No accounts saved yet. Use 'add' to save one.")
    except TrackerError as error:
        sys.exit(error)


# This line means "run main() when this file is started directly".
if __name__ == "__main__":
    main()
