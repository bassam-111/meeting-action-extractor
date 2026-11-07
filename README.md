# Meeting Action Extractor

Turns messy plain-text meeting notes into a clean, follow-up-ready list of
action items — a small operations tool for the gap between "great meeting"
and "who is actually doing what, by when?"

## What it does

`action_extractor.py` reads a `.txt` file of meeting notes and extracts:

- **Task** — from checkbox lines (`- [ ] ...`), `TODO:` lines, and `Action:` lines
- **Owner** — from `@Name` or `Owner: Name` markers (otherwise "Unassigned")
- **Due date** — normalised to `YYYY-MM-DD` from `2026-11-06`, `10 Nov 2026`,
  or `Nov 10` style dates (otherwise "No date")
- **Priority** — High if the line says urgent / ASAP / blocker / critical,
  Low for "low priority", otherwise Medium

It writes two files: a Markdown table (`actions.md`) and a CSV (`actions.csv`)
you can paste into an email, a tracker, or a spreadsheet. Plain update
bullets that are not action items are ignored.

## How to run

No external dependencies — Python 3.10+ standard library only.

```bash
python action_extractor.py sample_notes.txt
# or, with custom output paths:
python action_extractor.py notes.txt --md actions.md --csv actions.csv
```

Short example run output:

```text
Found 6 action item(s).
Wrote actions.md and actions.csv
```

## Sample output

Running it on the included `sample_notes.txt` (a weekly operations sync):

```
Found 6 action item(s).
1. [Medium] Share the updated onboarding checklist with the client success team — Ayesha (due: 2026-11-06)
2. [High] Follow up with the vendor on the delayed API access — Haroon (due: 2026-11-10)
3. [Medium] Draft the November operations summary — Bassam (due: 2026-11-12)
4. [Medium] Confirm the December shift rota with HR — Ayesha (due: No date)
5. [Low] Archive last quarter's closed tickets — Unassigned (due: No date)
6. [Medium] Book the client review call for next week — Unassigned (due: No date)
Wrote actions.md and actions.csv
```

The generated `actions.md` / `actions.csv` in this folder are that sample run.

## Files

- `action_extractor.py` — the extractor (CLI + importable `extract_actions`)
- `sample_notes.txt` — sample meeting notes
- `actions.md`, `actions.csv` — sample output
- `requirements.txt` — none needed (standard library only)

## Tested

2026-11-03: ran on `sample_notes.txt`; all assertions passed — 6 actions
extracted, owners, due dates, and priorities correct (urgent vendor follow-up
correctly flagged High, low-priority archive correctly flagged Low).
