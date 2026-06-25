#!/usr/bin/env python3
"""
Retroactively convert plain-text notes in user story JSON files to Markdown.

All fields rendered via MarkdownContent.vue use marked (CommonMark): a single \\n
becomes a space, so \n-separated sections collapse into one unreadable block.
This script detects and fixes those cases without touching already-valid Markdown.

Usage:
    python migrate_notes_to_markdown.py          # dry-run (preview, no writes)
    python migrate_notes_to_markdown.py --apply  # write changes to disk
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

STORIES_DIR = Path(__file__).resolve().parent.parent.parent / "user-stories"

FIELD_PATHS: list[tuple[str, ...]] = [
    ("notes",),
    ("tdd", "notes"),
    ("qa", "notes"),
    ("secops_report", "notes"),
    ("simplify_comments",),
]

# Action verbs that indicate a sentence is a discrete "did X" item.
_ACTION_RE = re.compile(
    r"^(Created?|Updated?|Added?|Fixed|Implemented|Restructured|Migrated|"
    r"Reverted|Removed|Modified|Deleted|Renamed|Built|Generated|Configured|"
    r"Créé|Modifié|Ajouté|Corrigé|Implémenté|All\s+\d|\d+\s+\w+\s+tests?)",
    re.IGNORECASE,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def get_nested(d: dict, path: tuple[str, ...]) -> str:
    for key in path:
        if not isinstance(d, dict):
            return ""
        d = d.get(key, "")
    return d if isinstance(d, str) else ""


def set_nested(d: dict, path: tuple[str, ...], value: str) -> None:
    for key in path[:-1]:
        d = d.setdefault(key, {})
    d[path[-1]] = value


def is_already_markdown(text: str) -> bool:
    """True if text already has Markdown structural elements."""
    return (
        "\n\n" in text
        or text.startswith(("## ", "# ", "- ", "**", "> ", "```", "| "))
    )


# ── conversion strategies ────────────────────────────────────────────────────

def _label_line_to_md(line: str) -> str:
    """Convert 'Label: content' line to Markdown. Returns line unchanged if no match."""
    # Label: must start with uppercase, be 2–30 chars (nominal phrase, not a sentence).
    # This prevents matching French sentences like "Le backend attend un header Auth: …"
    m = re.match(r"^([A-ZÀ-ÿ][^:\n]{1,29})\s*:\s+(.+)$", line)
    if not m:
        return line

    label = m.group(1).strip()
    content = m.group(2).strip()

    # Comma-separated list → bullet list only when:
    #   - ≥ 3 items (avoids "path/to/file, etc." false-positives)
    #   - every item is ≥ 5 chars (avoids single-char or "etc." artifacts)
    if re.search(r",\s+\S", content) and len(content) > 40:
        items = [i.strip() for i in content.split(",") if i.strip()]
        if len(items) >= 3 and all(len(i) >= 5 for i in items):
            return f"**{label}:**\n\n" + "\n".join(f"- {i}" for i in items)

    return f"**{label}:** {content}"


def convert_newline_content(text: str) -> str:
    """
    Convert \\n-separated 'Label: value' blocks to Markdown paragraphs/lists.
    Each line becomes either a bold-label paragraph or a plain paragraph,
    separated by blank lines so CommonMark treats them as distinct blocks.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return "\n\n".join(_label_line_to_md(line) for line in lines)


def try_convert_action_list(text: str) -> str:
    """
    Convert a long sentence-list of actions to a Markdown bullet list.

    Triggers only when:
    - ≥ 4 sentences (split on '. ' before uppercase / digit)
    - ≥ half the sentences start with a known action verb
    """
    sentences = re.split(r"\. (?=[A-ZÀ-ÿ\d])", text)
    if len(sentences) < 4:
        return text

    verb_count = sum(1 for s in sentences if _ACTION_RE.match(s.strip()))
    if verb_count < len(sentences) // 2:
        return text

    items = [s.strip().rstrip(".") for s in sentences if s.strip()]
    return "- " + "\n- ".join(items)


def convert_field(text: str) -> str | None:
    """
    Return the converted Markdown string, or None if no conversion needed.
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    if is_already_markdown(text):
        return None  # already structured

    if "\n" in text:
        converted = convert_newline_content(text)
    elif len(text) > 150:
        converted = try_convert_action_list(text)
    else:
        return None  # short single-paragraph text renders fine as-is

    return converted if converted != text else None


# ── file processing ───────────────────────────────────────────────────────────

def process_file(path: Path, apply: bool) -> list[tuple[str, str, str]]:
    """
    Process one story file.
    Returns list of (field_name, original, converted) tuples for changed fields.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    changes: list[tuple[str, str, str]] = []
    new_data = copy.deepcopy(data)

    for field_path in FIELD_PATHS:
        original = get_nested(data, field_path)
        converted = convert_field(original)
        if converted is not None:
            changes.append((".".join(field_path), original, converted))
            if apply:
                set_nested(new_data, field_path, converted)

    if changes and apply:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return changes


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate story notes fields from plain text to Markdown"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to disk (default: dry-run preview only)",
    )
    args = parser.parse_args()

    if not STORIES_DIR.exists():
        print(f"ERROR: stories directory not found: {STORIES_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(STORIES_DIR.glob("us-*.json"))
    mode = "APPLYING" if args.apply else "DRY RUN"
    print(f"{mode} — scanning {len(files)} story files in {STORIES_DIR}\n")

    changed_files = 0
    total_fields = 0

    for path in files:
        changes = process_file(path, apply=args.apply)
        if not changes:
            continue

        changed_files += 1
        total_fields += len(changes)
        print(f"  {path.name}")

        for field, original, converted in changes:
            orig_preview = repr(original[:120]) + ("…" if len(original) > 120 else "")
            conv_preview = repr(converted[:120]) + ("…" if len(converted) > 120 else "")
            print(f"    [{field}]")
            print(f"      BEFORE: {orig_preview}")
            print(f"      AFTER:  {conv_preview}")
        print()

    verb = "Written" if args.apply else "Would change"
    print(f"{verb}: {total_fields} field(s) across {changed_files} file(s)")
    if not args.apply and changed_files > 0:
        print("\nRun with --apply to write changes.")


if __name__ == "__main__":
    main()
