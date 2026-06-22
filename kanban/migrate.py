#!/usr/bin/env python3
"""One-shot migration: pars USER_STORIES.md + progress.json → user-stories/*.json"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent
USER_STORIES = HERE / "docs" / "USER_STORIES.md"
PROGRESS = HERE / "scripts" / "progress.json"
OUTPUT = HERE / "user-stories"

MD_PHASE = re.compile(r"^## Phase (\d+) — (.+)$")
MD_STORY = re.compile(r"^### US (\d+\.\d+) — (.+)$")
MD_AC = re.compile(r"^- \[([ x])\] (.+)$")
MD_BOLD = re.compile(r"\*\*(.+?)\*\*")


def parse_ac_text(line: str) -> str:
    return line.strip()


def parse_description(lines: list[str]) -> str:
    text = " ".join(l.strip() for l in lines if l.strip()).strip()
    text = MD_BOLD.sub(r"\1", text)
    return text


def parse_stories_from_md() -> dict:
    phases_md = {}
    current_phase = None
    current_phase_name = None
    current_story = None
    current_desc_lines = []
    current_acs = []
    in_desc = False
    in_ac = False

    for line in USER_STORIES.read_text().splitlines():
        phase_match = MD_PHASE.match(line)
        if phase_match:
            current_phase = int(phase_match.group(1))
            current_phase_name = phase_match.group(2)
            phases_md[current_phase] = {"name": current_phase_name, "stories": {}}
            current_story = None
            continue

        story_match = MD_STORY.match(line)
        if story_match:
            if current_story:
                phases_md[current_phase]["stories"][current_story] = {
                    "title": current_story_title,
                    "description": parse_description(current_desc_lines),
                    "acs": current_acs,
                }
            current_story = f"US {story_match.group(1)}"
            current_story_title = story_match.group(2)
            current_desc_lines = []
            current_acs = []
            in_desc = True
            in_ac = False
            continue

        if current_story is None:
            continue

        ac_match = MD_AC.match(line)
        if ac_match:
            in_desc = False
            in_ac = True
            checked = ac_match.group(1) == "x"
            text = ac_match.group(2).strip()
            current_acs.append({"id": len(current_acs) + 1, "text": text, "checked": checked})
            continue

        if line.strip().startswith("---"):
            continue

        stripped = line.strip()
        if in_desc and stripped:
            if stripped == "**AC :**":
                in_desc = False
                in_ac = True
                continue
            current_desc_lines.append(stripped)
        elif in_ac and stripped == "":
            pass

    if current_story:
        phases_md[current_phase]["stories"][current_story] = {
            "title": current_story_title,
            "description": parse_description(current_desc_lines),
            "acs": current_acs,
        }

    return phases_md


def load_progress() -> dict:
    return json.loads(PROGRESS.read_text())


def merge_and_export():
    md_data = parse_stories_from_md()
    progress = load_progress()
    now = "2026-06-20"

    total = 0
    for phase in progress["phases"]:
        pid = phase["id"]
        pname = phase["name"]
        for story in phase.get("stories", []):
            sid = story["id"]
            md_phase = md_data.get(pid, {})
            md_story = md_phase.get("stories", {}).get(sid, {})

            acs = md_story.get("acs", [ac_from_progress(story)])
            # If story is completed, mark all ACs as checked
            if story["status"] == "completed":
                for ac in acs:
                    ac["checked"] = True

            us = {
                "id": sid,
                "phase": pid,
                "phase_name": pname,
                "title": md_story.get("title", story["title"]),
                "description": md_story.get("description", ""),
                "priority": story["priority"],
                "status": story["status"],
                "acceptance_criteria": acs,
                "tdd": story.get("tdd", {"status": "pending", "tests": 0, "coverage": "0%", "notes": ""}),
                "qa": story.get("qa", {"status": "pending", "ac_covered": "0/0", "notes": ""}),
                "notes": story.get("notes", ""),
                "refine_decisions": [],
                "secops_report": {},
                "created_at": now,
                "updated_at": now,
            }

            filename = sid.lower().replace(" ", "-").replace(".", "-")
            (OUTPUT / f"{filename}.json").write_text(json.dumps(us, indent=2, ensure_ascii=False))
            total += 1
            print(f"  {sid} → user-stories/{filename}.json")

    print(f"\n  Total: {total} stories exported")


def ac_from_progress(story: dict) -> list:
    return []


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    merge_and_export()
    print("\nMigration complete. Run: python .opencode/kanban/server.py")
