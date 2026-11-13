# RuneScape Account Tracker

Look up Old School RuneScape players, see how much XP they've gained, and keep a small always-on-top window on your desktop.

**Privacy:** the only thing saved on your computer is the list of account names (`data/accounts.json`). Stats are never saved. Current stats come from the official hiscores. XP gains come from [Wise Old Man](https://wiseoldman.net), a free website that keeps each player's stat history.

## The desktop widget

```
cd runescape-tracker
python3 widget.py
```

Type an account name, press **Add**, and the window shows each account's total level and the XP it gained today (or this week). It refreshes every 15 minutes. You can also click **↻** to refresh. Click **✕** to remove an account.

The widget needs Tk, which you install once with `brew install python-tk@3.15`.

## The command line

```
python3 tracker.py check  "Lynx Titan"                 # current stats
python3 tracker.py gains  "Lynx Titan" --period day    # XP gained (day, week or month)
python3 tracker.py add    "Lynx Titan"                 # save a name for the widget
python3 tracker.py remove "Lynx Titan"
python3 tracker.py list
```

Use quotes around names that have spaces.

## Ideas to try next

- Show boss kill counts. Wise Old Man's gains also include a `"bosses"` list.
- Change the widget's colors at the top of `widget.py`.
- Add a "month" choice to the widget.
