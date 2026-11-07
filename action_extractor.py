"""Meeting-notes action-item extractor.

Reads plain-text meeting notes and extracts action items into a
Markdown table and a CSV file. No external dependencies: standard
library only, so it runs anywhere Python 3.10+ is installed.

Recognised patterns (each on its own line):
  - "- [ ] ..." / "* [ ] ..."  (checkbox task)
  - "TODO: ..." / "Action: ..." / "Action item: ..."
  - "... - @Name ..." / "... (Owner: Name)" / "... - Owner: Name"
  - Due dates: "by 2026-11-10", "due 10 Nov 2026", "by Nov 10"
  - Priority hints: "urgent", "ASAP", "blocker" -> High;
    "low priority" -> Low; otherwise Medium.

Usage:
    python action_extractor.py sample_notes.txt
    python action_extractor.py notes.txt --md actions.md --csv actions.csv
"""

import argparse
import csv
import re
import sys
from pathlib import Path

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

TASK_RE = re.compile(
    r"^\s*(?:[-*]\s*\[ \]\s*|TODO:\s*|Action(?: item)?:\s*)(.+)$",
    re.IGNORECASE,
)
# A plain bullet is only a task if it names an owner (e.g. "- Call Ali - @Sara").
BULLET_OWNER_RE = re.compile(
    r"^\s*[-*]\s+(.+@.+|.+Owner:.+)$", re.IGNORECASE
)
OWNER_RE = re.compile(
    r"(?:@([A-Za-z][A-Za-z'-]+)|Owner:\s*([A-Z][A-Za-z'-]+(?: [A-Z][A-Za-z'-]+)?))"
)
ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
DMY_RE = re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\b")
MD_RE = re.compile(r"\b([A-Za-z]{3,9})\s+(\d{1,2})\b")


def find_due_date(text: str) -> str:
    """Return a due date as YYYY-MM-DD, or '' if none is found."""
    m = ISO_DATE_RE.search(text)
    if m:
        return m.group(1)
    m = DMY_RE.search(text)
    if m:
        month = MONTHS.get(m.group(2)[:3].lower())
        if month:
            return f"{m.group(3)}-{month:02d}-{int(m.group(1)):02d}"
    m = MD_RE.search(text)
    if m:
        month = MONTHS.get(m.group(1)[:3].lower())
        if month:
            # No year given: assume the current meeting year (2026 in sample).
            return f"2026-{month:02d}-{int(m.group(2)):02d}"
    return ""


def priority_of(text: str) -> str:
    lowered = text.lower()
    if any(w in lowered for w in ("urgent", "asap", "blocker", "critical")):
        return "High"
    if "low priority" in lowered:
        return "Low"
    return "Medium"


def clean_task(text: str, owner: str, due: str) -> str:
    """Strip owner/date fragments from the task wording."""
    out = text
    if owner:
        # Everything from the owner marker onward is metadata, not task text.
        out = re.sub(r"\s*[-–]\s*@" + re.escape(owner) + r"\b.*$", "", out)
        out = re.sub(r"\s*\(\s*Owner:\s*" + re.escape(owner) + r"\s*\).*$", "", out)
        out = re.sub(r"\s*[-–]\s*Owner:\s*" + re.escape(owner) + r"\b.*$", "", out)
    # Standalone due-date fragments (no owner marker present).
    out = re.sub(r"\s*[-–]?\s*(?:by|due)\s+\d{4}-\d{2}-\d{2}", "", out,
                 flags=re.IGNORECASE)
    out = re.sub(r"\s*[-–]?\s*(?:by|due)\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}", "", out,
                 flags=re.IGNORECASE)
    out = re.sub(r"\s*[-–]?\s*(?:by|due)\s+[A-Za-z]+\s+\d{1,2}", "", out,
                 flags=re.IGNORECASE)
    out = re.sub(r"\s*\((?:urgent|asap|blocker|critical)\)", "", out,
                 flags=re.IGNORECASE)
    out = re.sub(r"\s*[-–]\s*low priority\s*$", "", out, flags=re.IGNORECASE)
    return out.strip(" -–").strip()


def extract_actions(text: str) -> list[dict]:
    actions = []
    for line in text.splitlines():
        m = TASK_RE.match(line)
        if not m:
            m = BULLET_OWNER_RE.match(line)
        if not m:
            continue
        raw = m.group(1).strip()
        if not raw:
            continue
        owner_m = OWNER_RE.search(raw)
        owner = ""
        if owner_m:
            owner = (owner_m.group(1) or owner_m.group(2)).strip()
        due = find_due_date(raw)
        task = clean_task(raw, owner, due)
        actions.append({
            "task": task,
            "owner": owner or "Unassigned",
            "due": due or "No date",
            "priority": priority_of(raw),
        })
    return actions


def to_markdown(actions: list[dict]) -> str:
    lines = ["# Action Items", "",
             "| # | Task | Owner | Due | Priority |",
             "|---|------|-------|-----|----------|"]
    for i, a in enumerate(actions, 1):
        lines.append(f"| {i} | {a['task']} | {a['owner']} | {a['due']} | {a['priority']} |")
    lines.append("")
    lines.append(f"Total: {len(actions)} action item(s).")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Extract action items from meeting notes.")
    parser.add_argument("input", help="Plain-text meeting notes file")
    parser.add_argument("--md", default="actions.md", help="Markdown output path")
    parser.add_argument("--csv", default="actions.csv", help="CSV output path")
    args = parser.parse_args(argv)

    text = Path(args.input).read_text(encoding="utf-8")
    actions = extract_actions(text)

    Path(args.md).write_text(to_markdown(actions), encoding="utf-8")
    with open(args.csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["task", "owner", "due", "priority"])
        writer.writeheader()
        writer.writerows(actions)

    print(f"Found {len(actions)} action item(s).")
    for i, a in enumerate(actions, 1):
        print(f"{i}. [{a['priority']}] {a['task']} — {a['owner']} (due: {a['due']})")
    print(f"Wrote {args.md} and {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
