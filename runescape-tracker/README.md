# RuneScape Account Tracker

A small Python app that looks up an Old School RuneScape player on the official hiscores, saves a snapshot of their skills each time, and shows the XP they've gained over time.

It doesn't need any installs or API keys. It only uses Python 3, which is already on your Mac.

## How to run it

```
cd runescape-tracker
python3 tracker.py check "Lynx Titan"     # look up stats and save a snapshot
python3 tracker.py gains "Lynx Titan"     # show XP gained since the first snapshot
python3 tracker.py history "Lynx Titan"   # list every saved snapshot
```

Use quotes around names that have spaces.

## Example

```
  Stats for Lynx Titan

  Skill          Level              XP
  ------------------------------------
  Overall         2278   4,600,000,000
  Attack            99     200,000,000
  ...
```

## Where data is stored

Snapshots are saved in `data/<player>.json`. Git ignores that folder, so your data stays on your computer.

## Ideas to try next

- Add RS3 support. Its hiscores address is `https://secure.runescape.com/m=hiscore/index_lite.ws?player=NAME`, and it returns CSV instead of JSON.
- Show boss kill counts. The JSON response also contains an `"activities"` list.
- Track several accounts at once with a `check-all` command.
