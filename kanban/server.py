#!/usr/bin/env python3
"""Kanban story server — REST API + MCP tools + Dashboard.

Usage:
  python .opencode/kanban/server.py          → HTTP only (dashboard on KANBAN_HTTP_PORT, default 8765)
  python .opencode/kanban/server.py --mcp    → MCP stdio + background HTTP (started by OpenCode)

Ports (override via .opencode/.env or env vars):
  KANBAN_HTTP_PORT=8765   — dashboard / REST API port
  OPENCODE_PORT=4096      — OpenCode TUI bridge port (or set OPENCODE_SERVER_URL directly)
"""

import os
import sys
import json
import asyncio
import threading
import logging
import copy
import fcntl
import socket
import time
import atexit
from pathlib import Path
from datetime import date, datetime
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
LOG_FILE = HERE / "kanban.log"


def _load_dotenv(path: Path) -> None:
    """Load key=value pairs from a .env file without overwriting existing env vars."""
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# Load .opencode/.env when present (HERE = .opencode/kanban/ → parent = .opencode/)
_load_dotenv(HERE.parent / ".env")

# ── Configurable ports ───────────────────────────────────────────────
# Override via .opencode/.env or environment variables before launch.
KANBAN_HTTP_PORT: int = int(os.environ.get("KANBAN_HTTP_PORT", "8765"))
OPENCODE_PORT: int = int(os.environ.get("OPENCODE_PORT", "4096"))
APP_TITLE: str = os.environ.get("APP_TITLE", "Kanban")

# ── Debug flag (env var or --debug CLI argument) ─────────────────────
# Enable with: KANBAN_DEBUG=1 python server.py --mcp
#          or: python server.py --debug
#          or: python server.py --mcp --debug
KANBAN_DEBUG: bool = os.environ.get("KANBAN_DEBUG", "0") == "1" or "--debug" in sys.argv

_log_level = logging.DEBUG if KANBAN_DEBUG else logging.INFO

# Console handler (stderr — safe in --mcp mode since MCP protocol uses stdout)
_console_handler = logging.StreamHandler(sys.stderr)
_console_handler.setFormatter(logging.Formatter("%(message)s"))
_console_handler.setLevel(_log_level)

# File handler
_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
_file_handler.setLevel(_log_level)

log = logging.getLogger("kanban")
log.propagate = False  # don't double-log via root
log.setLevel(_log_level)
log.addHandler(_console_handler)
log.addHandler(_file_handler)

# In-memory ring buffer of the last 50 trigger events for /api/debug
_debug_events: list[dict] = []
_debug_lock = threading.Lock()


def _debug(event: dict) -> None:
    from datetime import datetime
    event["ts"] = datetime.now().isoformat(timespec="seconds")
    log.info(f"  [debug] {event}")
    with _debug_lock:
        _debug_events.append(event)
        if len(_debug_events) > 50:
            _debug_events.pop(0)


def _mcp_debug(tool: str, direction: str, **fields) -> None:
    """Log an MCP tool call with its parameters and result summary.

    direction: "in"  → logs the tool name + input params (▶)
               "out" → logs the result summary (◀)
    No-op when KANBAN_DEBUG is False.
    """
    if not KANBAN_DEBUG:
        return
    arrow = "▶" if direction == "in" else "◀"
    kv_parts = []
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, (dict, list)):
            kv_parts.append(f"{k}={json.dumps(v, ensure_ascii=False)}")
        else:
            kv_parts.append(f"{k}={v!r}")
    suffix = ("  " + "  ".join(kv_parts)) if kv_parts else ""
    log.debug(f"[MCP] {arrow} {tool}{suffix}")


# ── Shared version counter (file-based, visible across processes) ─────
_version_lock = threading.Lock()


def _read_version() -> int:
    try:
        return int(VERSION_FILE.read_text().strip())
    except Exception:
        return 0


def bump_version() -> int:
    with _version_lock:
        VERSION_FILE.touch(exist_ok=True)
        with open(VERSION_FILE, "r+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                v = int(fh.read().strip() or "0") + 1
            except ValueError:
                v = 1
            fh.seek(0)
            fh.truncate()
            fh.write(str(v))
            return v


# ── Story cache ──────────────────────────────────────────────────────
_story_cache: dict = {"ver": -1, "mtime": 0.0, "data": []}
_cache_lock = threading.Lock()



def _disk_mtime() -> float:
    """Return the max mtime of all JSON files in STORIES_DIR."""
    files = list(STORIES_DIR.glob("*.json"))
    if not files:
        return 0.0
    return max(fj.stat().st_mtime for fj in files)


def _load_from_disk() -> list[dict]:
    out = []
    for f in sorted(STORIES_DIR.glob("*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            log.warning(f"Bad JSON: {f.name}")
    out.sort(key=lambda s: (s.get("order", 9999), s["id"]))
    return out


# ── OpenCode HTTP Bridge ─────────────────────────────────────────────
OPENCODE_SERVER_URL = os.environ.get("OPENCODE_SERVER_URL", f"http://localhost:{OPENCODE_PORT}")
OPENCODE_TRIGGER_ENABLED = os.environ.get("OPENCODE_TRIGGER_ENABLED", "1") == "1"


STATUS_COMMANDS = {
    "refining":     lambda sid: ("next-story", f"refine {sid}"),
    "secops_tm":    lambda sid: ("next-story", f"secops-tm {sid}"),
    "tdd":          lambda sid: ("next-story", f"implement {sid}"),
    "secops_cr":    lambda sid: ("next-story", f"secops-cr {sid}"),
    "qa":           lambda sid: ("next-story", f"qa {sid}"),
    "simplify":     lambda sid: ("next-story", f"simplify {sid}"),
    "commit_ready": lambda sid: ("next-story", f"commit {sid}"),
}


def _tui_type_and_submit(cmd: str, base: str) -> None:
    """Create a fresh OpenCode session, navigate to it, then submit cmd.

    Each kanban trigger starts in a clean context (0 prior messages) to avoid
    context-size blowup from accumulated session history.
    """
    headers = {"Content-Type": "application/json"}
    try:
        # 1. Create a new blank session — returns {"id": "ses_...", ...}
        with urlopen(Request(f"{base}/session", data=b"{}", headers=headers), timeout=3) as resp:
            session = json.loads(resp.read())
        session_id = session["id"]

        # 2. Navigate the TUI to the new (empty) session
        select_body = json.dumps({"sessionID": session_id}).encode()
        urlopen(Request(f"{base}/tui/select-session", data=select_body, headers=headers), timeout=3)

        # Wait for the TUI to finish rendering the new session before typing into it.
        # Without this delay, append-prompt targets the old session's input box.
        time.sleep(0.5)

        # 3. Type the command
        body = json.dumps({"text": cmd}).encode()
        urlopen(Request(f"{base}/tui/append-prompt", data=body, headers=headers), timeout=3)

        # 4. Press Enter
        urlopen(Request(f"{base}/tui/submit-prompt", data=b"{}", headers=headers), timeout=3)

        # 5. Toast confirmation
        toast = json.dumps({"title": "Kanban", "message": cmd, "variant": "info"}).encode()
        urlopen(Request(f"{base}/tui/show-toast", data=toast, headers=headers), timeout=3)

        _debug({"step": "tui_submit", "command": cmd, "session_id": session_id, "base": base, "ok": True})
        log.info(f"  → TUI submitted in new session {session_id}: {cmd} → {base}")
    except Exception as e:
        _debug({"step": "tui_submit", "command": cmd, "base": base, "error": str(e)})
        log.warning(f"  ⚠ TUI submit failed ({base}): {e}")


def _resolve_target_url(target_port: int | None) -> str:
    """Return the OpenCode server URL to target.

    If target_port is given (from dashboard session selector), use it directly.
    Otherwise use the configured OPENCODE_SERVER_URL.
    """
    if target_port:
        return f"http://localhost:{target_port}"
    return OPENCODE_SERVER_URL


def trigger_opencode(story_id: str, command: str | None = None, target_port: int | None = None) -> dict:
    """Inject a slash command into a specific OpenCode TUI session.

    target_port: optional port chosen from the dashboard session selector.
    Defaults to OPENCODE_PORT (configured in .opencode/.env).
    """
    if not OPENCODE_TRIGGER_ENABLED:
        _debug({"step": "trigger", "skipped": "disabled"})
        return {"triggered": False, "disabled": True}

    cmd = command if command else f"/next-story {story_id}"
    if not cmd.startswith("/"):
        cmd = f"/{cmd}"

    base = _resolve_target_url(target_port)
    _debug({"step": "trigger", "story": story_id, "command": cmd, "target": base})
    log.info(f"  → Injecting into TUI: {cmd} → {base}")

    threading.Thread(target=_tui_type_and_submit, args=(cmd, base), daemon=True).start()

    return {"triggered": True, "story_id": story_id, "command": cmd, "target": base}


def find_stories_dir() -> Path:
    cwd = Path.cwd()
    if (cwd / "user-stories").is_dir():
        return cwd / "user-stories"
    for p in [HERE.parent.parent, HERE.parent, cwd]:
        if (p / "user-stories").is_dir():
            return p / "user-stories"
    p = cwd / "user-stories"
    p.mkdir(parents=True, exist_ok=True)
    return p


STORIES_DIR = find_stories_dir()
VERSION_FILE = STORIES_DIR.parent / ".kanban-version"
SESSIONS_FILE = STORIES_DIR.parent / ".kanban-sessions.json"

# ── Session registry (multi-instance) ───────────────────────────────
_sessions_lock = threading.Lock()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_sessions() -> dict:
    try:
        if SESSIONS_FILE.exists():
            return json.loads(SESSIONS_FILE.read_text())
    except Exception:
        pass
    return {}


def _write_sessions(sessions: dict) -> None:
    with open(SESSIONS_FILE, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        json.dump(sessions, fh, indent=2)


def _register_session() -> None:
    with _sessions_lock:
        sessions = _read_sessions()
        sessions = {pid: info for pid, info in sessions.items() if _pid_alive(int(pid))}
        sessions[str(os.getpid())] = {
            "opencode_port": OPENCODE_PORT,
            "started": datetime.now().isoformat(timespec="seconds"),
        }
        _write_sessions(sessions)
    log.info(f"  Session registered: pid={os.getpid()} opencode_port={OPENCODE_PORT}")


def _unregister_session() -> None:
    with _sessions_lock:
        sessions = _read_sessions()
        sessions.pop(str(os.getpid()), None)
        _write_sessions(sessions)


atexit.register(_unregister_session)


# ── HTTP auto-promotion (single dashboard across instances) ──────────
_http_server_running = False
_http_promote_lock = threading.Lock()


def _port_is_free(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        s.bind(("", port))
        s.close()
        return True
    except OSError:
        s.close()
        return False


def _try_start_http() -> bool:
    """Try to bind KANBAN_HTTP_PORT and start the HTTP server. Returns True if promoted."""
    global _http_server_running
    with _http_promote_lock:
        if _http_server_running:
            return True
        if not _port_is_free(KANBAN_HTTP_PORT):
            return False
        _http_server_running = True
    threading.Thread(target=run_http, daemon=True).start()
    log.info(f"  HTTP dashboard promoted on :{KANBAN_HTTP_PORT}")
    return True


def _http_watchdog() -> None:
    """Background thread: takes the HTTP port if it becomes free (e.g. master died)."""
    while True:
        time.sleep(10)
        if not _http_server_running:
            _try_start_http()


def load_all() -> list[dict]:
    current_ver   = _read_version()
    current_mtime = _disk_mtime()
    with _cache_lock:
        if (
            _story_cache["ver"] == current_ver
            and _story_cache["mtime"] == current_mtime
            and _story_cache["data"]
        ):
            return copy.deepcopy(_story_cache["data"])
    data = _load_from_disk()
    with _cache_lock:
        _story_cache["ver"]   = current_ver
        _story_cache["mtime"] = current_mtime
        _story_cache["data"]  = data
    return copy.deepcopy(data)


def load_one(story_id: str) -> dict | None:
    for s in load_all():
        if s.get("id") == story_id:
            return s
    return None


def save_one(story_id: str, data: dict):
    data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    for f in STORIES_DIR.glob("*.json"):
        try:
            with open(f, "r+") as fh:
                fcntl.flock(fh, fcntl.LOCK_EX)
                try:
                    existing = json.load(fh)
                except json.JSONDecodeError:
                    continue
                if existing.get("id") != story_id:
                    continue
                fh.seek(0)
                fh.truncate()
                json.dump(data, fh, indent=2, ensure_ascii=False)
            bump_version()
            return
        except (KeyError, OSError):
            pass
    sid = story_id.lower().replace(" ", "-").replace(".", "-")
    target = STORIES_DIR / f"{sid}.json"
    with open(target, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        json.dump(data, fh, indent=2, ensure_ascii=False)
    bump_version()


def delete_one(story_id: str) -> bool:
    for f in STORIES_DIR.glob("*.json"):
        try:
            if json.loads(f.read_text())["id"] == story_id:
                f.unlink()
                bump_version()
                return True
        except (json.JSONDecodeError, KeyError):
            pass
    return False


FLOW_STATUSES = ("pending", "refining", "secops_tm", "tdd", "secops_cr", "qa", "simplify", "commit_ready", "completed", "blocked")

def stats(stories: list[dict]) -> dict:
    s = {k: 0 for k in FLOW_STATUSES}
    tdd_stats = {"passed": 0, "failed": 0, "in_progress": 0, "pending": 0}
    qa_stats = {"passed": 0, "failed": 0, "in_progress": 0, "pending": 0}
    for st in stories:
        sts = st.get("status", "pending")
        if sts in s:
            s[sts] += 1
        t = st.get("tdd", {}).get("status", "pending")
        tdd_stats[t] = tdd_stats.get(t, 0) + 1
        q = st.get("qa", {}).get("status", "pending")
        qa_stats[q] = qa_stats.get(q, 0) + 1
    s["tdd_counts"] = tdd_stats
    s["qa_counts"] = qa_stats
    return s


def story_file(story_id: str) -> Path | None:
    for f in STORIES_DIR.glob("*.json"):
        try:
            if json.loads(f.read_text())["id"] == story_id:
                return f
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def merge_dict(base: dict, update: dict) -> dict:
    for k, v in update.items():
        if k in ("history", "_actor", "created_at", "updated_at"):
            continue  # server-managed fields — agents must not override them
        if k in ("tdd", "qa", "secops_report") and isinstance(v, dict):
            base.setdefault(k, {}).update(v)
        elif k in ("acceptance_criteria", "refine_decisions", "stack") and isinstance(v, list):
            base[k] = v
        else:
            base[k] = v
    return base


def _compute_diff(old: dict, new: dict) -> list[str]:
    skip = {"updated_at", "created_at", "history", "_actor"}
    changes = []
    keys = (set(old.keys()) | set(new.keys())) - skip
    for key in sorted(keys):
        ov, nv = old.get(key), new.get(key)
        if ov == nv:
            continue
        if key == "status":
            changes.append(f"status: {ov} → {nv}")
        elif key == "acceptance_criteria":
            on = len(ov) if isinstance(ov, list) else 0
            nn = len(nv) if isinstance(nv, list) else 0
            changes.append(f"AC: {on} → {nn}" if on != nn else "acceptance_criteria modifié")
        elif key in ("tdd", "qa"):
            ost = (ov or {}).get("status", "?")
            nst = (nv or {}).get("status", "?")
            changes.append(f"{key}.status: {ost} → {nst}" if ost != nst else f"{key} modifié")
        elif key == "implementation_guide":
            changes.append("implementation_guide défini" if not ov and nv else "implementation_guide modifié")
        elif key == "secops_report":
            changes.append("secops_report modifié")
        elif key == "stack":
            changes.append(f"stack: {nv}")
        elif key == "priority_score":
            changes.append(f"priority_score: {ov} → {nv}")
        elif key in ("description", "title", "notes", "simplify_comments"):
            changes.append(f"{key} modifié")
        else:
            changes.append(f"{key} modifié")
    return changes


def apply_update(story: dict, update: dict, default_actor: str = "dashboard") -> dict:
    """Merge update into story, compute diff, append history entry."""
    actor = update.get("_actor", default_actor)
    old_snapshot = copy.deepcopy(story)
    merge_dict(story, update)
    changes = _compute_diff(old_snapshot, story)
    if changes:
        story.setdefault("history", []).append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "by": actor,
            "changes": changes,
        })
    return story


# ── FastAPI REST ────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

rest = FastAPI(title="Kanban")
rest.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@rest.get("/api/stories")
def api_list(status: str = "", phase: str = ""):
    items = load_all()
    if status:
        items = [s for s in items if s.get("status") == status]
    if phase:
        items = [s for s in items if str(s.get("phase")) == phase]
    return items


@rest.get("/api/stories/{sid}")
def api_get(sid: str):
    s = load_one(sid)
    if not s:
        raise HTTPException(404, f"Story {sid} not found")
    return s


@rest.put("/api/stories/{sid}")
def api_update(sid: str, body: dict, no_trigger: bool = False, target_port: int | None = None):
    s = load_one(sid)
    if not s:
        raise HTTPException(404, f"Story {sid} not found")
    old_status = s.get("status", "pending")
    apply_update(s, body, default_actor="dashboard")
    new_status = s.get("status", old_status)
    save_one(sid, s)
    if not no_trigger and new_status != old_status and new_status in STATUS_COMMANDS:
        cmd_name, cmd_args = STATUS_COMMANDS[new_status](sid)
        cmd_str = f"/{cmd_name} {cmd_args}"
        trigger_result = trigger_opencode(sid, command=cmd_str, target_port=target_port)
        return {**s, "_trigger": trigger_result}
    return s


@rest.post("/api/stories")
def api_create(body: dict):
    title = body.get("title", "New Story")
    phase = body.get("phase", 7)

    existing = load_all()
    phase_items = [s for s in existing if s.get("phase") == phase]
    nums = []
    for s in phase_items:
        try:
            nums.append(int(s["id"].split(".")[1]))
        except (KeyError, IndexError, ValueError):
            pass
    n = max(nums, default=0) + 1
    sid = f"US {phase}.{n}"

    phase_names = {1: "Fondations Backend", 2: "Frontend MVP", 3: "SaaS & Monétisation",
                   4: "Mode Entreprise", 5: "Quality & Hardening", 6: "V2 & Futur", 7: "Backlog"}
    now = datetime.now().isoformat(timespec="seconds")
    next_order = max((s.get("order", 0) for s in existing if s.get("status") == "pending"), default=-1) + 1
    story = {
        "id": sid, "phase": phase, "phase_name": phase_names.get(phase, "Backlog"),
        "title": title, "description": "", "status": "pending",
        "order": next_order, "priority_score": 0,
        "acceptance_criteria": [],
        "stack": [],
        "tdd": {"status": "pending", "tests": 0, "coverage": "0%", "notes": ""},
        "qa": {"status": "pending", "ac_covered": "0/0", "notes": ""},
        "notes": "", "refine_decisions": [], "implementation_guide": {}, "secops_report": {},
        "simplify_comments": "", "history": [],
        "created_at": now, "updated_at": now,
    }
    save_one(sid, story)
    return story


@rest.patch("/api/stories/{sid}/move")
def api_move_story(sid: str, body: dict, no_trigger: bool = False, target_port: int | None = None):
    """Move a story to a new status. Body: {status, actor?}. Triggers OpenCode if applicable."""
    new_status = body.get("status")
    actor = body.get("actor", "dashboard")
    valid = set(FLOW_STATUSES)
    if not new_status or new_status not in valid:
        raise HTTPException(400, f"Invalid status. Valid: {', '.join(sorted(valid))}")
    s = load_one(sid)
    if not s:
        raise HTTPException(404, f"Story {sid} not found")
    old_status = s.get("status")
    s["status"] = new_status
    if old_status != new_status:
        s.setdefault("history", []).append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "by": actor,
            "changes": [f"status: {old_status} → {new_status}"],
        })
    save_one(sid, s)
    if not no_trigger and new_status != old_status and new_status in STATUS_COMMANDS:
        cmd_name, cmd_args = STATUS_COMMANDS[new_status](sid)
        cmd_str = f"/{cmd_name} {cmd_args}"
        trigger_result = trigger_opencode(sid, command=cmd_str, target_port=target_port)
        return {**s, "_trigger": trigger_result}
    return s


@rest.post("/api/reload")
def api_reload():
    """Force cache invalidation — picks up files written directly to disk."""
    bump_version()
    stories = load_all()
    return {"reloaded": True, "count": len(stories)}


@rest.post("/api/stories/{sid}/trigger")
def api_trigger(sid: str, target_port: int | None = None):
    """Fire the OpenCode command for the story's current status, without moving it."""
    s = load_one(sid)
    if not s:
        raise HTTPException(404, f"Story {sid} not found")
    status = s.get("status")
    if status not in STATUS_COMMANDS:
        raise HTTPException(400, f"No command defined for status '{status}'")
    cmd_name, cmd_args = STATUS_COMMANDS[status](sid)
    cmd_str = f"/{cmd_name} {cmd_args}"
    result = trigger_opencode(sid, command=cmd_str, target_port=target_port)
    return {"ok": True, "command": cmd_str, "trigger": result}


@rest.get("/api/sessions")
def api_sessions():
    """Return registered OpenCode sessions (for dashboard session selector).
    Dead sessions (process no longer running) are pruned on read.
    """
    with _sessions_lock:
        sessions = _read_sessions()
        alive = {pid: info for pid, info in sessions.items() if _pid_alive(int(pid))}
        if len(alive) != len(sessions):
            _write_sessions(alive)
    return alive


@rest.delete("/api/stories/{sid}")
def api_delete(sid: str):
    if not delete_one(sid):
        raise HTTPException(404, f"Story {sid} not found")
    return {"ok": True}


@rest.get("/api/config")
def api_config():
    return {"app_title": APP_TITLE}


@rest.get("/api/opencode/status")
def api_opencode_status():
    """Proxy to OpenCode /session/status — returns {"busy": bool}."""
    try:
        with urlopen(f"{OPENCODE_SERVER_URL}/session/status", timeout=2) as r:
            data = json.loads(r.read())
        return {"busy": bool(data)}
    except Exception:
        return {"busy": False}


@rest.get("/api/stats")
def api_stats():
    return stats(load_all())


@rest.get("/api/history")
def api_history(limit: int = 100):
    """Return the last `limit` history events across all stories, newest first."""
    events: list[dict] = []
    for s in load_all():
        for entry in s.get("history", []):
            events.append({
                "story_id": s["id"],
                "story_title": s.get("title", ""),
                "story_status": s.get("status", "pending"),
                "ts": entry.get("ts", ""),
                "by": entry.get("by", ""),
                "changes": entry.get("changes", []),
            })
    events.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return events[:limit]


@rest.get("/api/debug")
def api_debug():
    """Last trigger events — call after moving a card to diagnose issues."""
    with _debug_lock:
        return list(_debug_events)


@rest.post("/api/reorder")
def api_reorder(body: dict):
    """Reorder stories within a status column.
    Body: {"status": "pending", "order": ["US 1.1", "US 1.3", ...]}
    Updates each story's `order` field to its position index.
    """
    status = body.get("status")
    ordered_ids = body.get("order", [])
    if not status or not ordered_ids:
        raise HTTPException(400, "status and order required")
    for idx, sid in enumerate(ordered_ids):
        s = load_one(sid)
        if s and s.get("status") == status:
            s["order"] = idx
            save_one(sid, s)
    return {"ok": True, "status": status, "updated": len(ordered_ids)}


@rest.get("/api/events")
async def api_events():
    last      = _read_version()
    last_mtime = _disk_mtime()
    ticks_since_ping = 0
    mtime_ticks      = 0

    async def event_gen():
        nonlocal last, last_mtime, ticks_since_ping, mtime_ticks
        yield f"data: refresh\n\n"  # immediate sync on connect/reconnect
        while True:
            await asyncio.sleep(0.5)
            ticks_since_ping += 1
            mtime_ticks      += 1
            v = _read_version()
            if v != last:
                # version bumped by any process via bump_version()
                last       = v
                last_mtime = _disk_mtime()
                ticks_since_ping = mtime_ticks = 0
                yield f"data: refresh\n\n"
            elif mtime_ticks >= 10:  # fallback: catch direct file edits every 5 s
                mtime_ticks = 0
                m = _disk_mtime()
                if m != last_mtime:
                    last_mtime = m
                    last = bump_version()   # align version file with disk reality
                    ticks_since_ping = 0
                    yield f"data: refresh\n\n"
            elif ticks_since_ping >= 30:
                ticks_since_ping = 0
                yield ": ping\n\n"  # keepalive

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })


@rest.get("/")
def dashboard():
    return HTMLResponse((HERE / "dist" / "index.html").read_text(encoding="utf-8"))


dist_assets = HERE / "dist" / "assets"
if dist_assets.is_dir():
    rest.mount("/assets", StaticFiles(directory=str(dist_assets)), name="assets")


# ── MCP Tools ──────────────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("kanban-stories")


@mcp.tool()
def get_story(story_id: str) -> str:
    """Get the full JSON of a user story (e.g. 'US 1.3'). Returns JSON string."""
    _mcp_debug("get_story", "in", story_id=story_id)
    s = load_one(story_id)
    _mcp_debug("get_story", "out",
        found=s is not None,
        status=s.get("status") if s else None,
        tdd=s.get("tdd", {}).get("status") if s else None,
        qa=s.get("qa", {}).get("status") if s else None,
    )
    return json.dumps(s or {"error": f"Story {story_id} not found"}, ensure_ascii=False)


@mcp.tool()
def list_stories(status: str = "", phase: str = "") -> str:
    """List all stories, filtered by optional status and/or phase."""
    _mcp_debug("list_stories", "in", status=status or "(all)", phase=phase or "(all)")
    items = load_all()
    if status:
        items = [s for s in items if s.get("status") == status]
    if phase:
        items = [s for s in items if str(s.get("phase")) == phase]
    _mcp_debug("list_stories", "out", count=len(items),
        ids=[s["id"] for s in items] if KANBAN_DEBUG and len(items) <= 10 else f"{len(items)} stories",
    )
    return json.dumps(items, ensure_ascii=False)


@mcp.tool()
def update_story(story_id: str, changes: str) -> str:
    """Update a story with partial JSON changes. Pass a JSON string with only the fields to change.
    Include "_actor" in the JSON to identify who made the change (e.g. "refine", "tdd", "qa", "secops-tm", "secops-cr", "simplify")."""
    try:
        updates = json.loads(changes)
    except json.JSONDecodeError as e:
        _mcp_debug("update_story", "in", story_id=story_id, parse_error=str(e))
        return json.dumps({"error": f"Invalid JSON in changes: {e}"})

    actor = updates.get("_actor", "agent")
    fields = [k for k in updates if k != "_actor"]
    _mcp_debug("update_story", "in", story_id=story_id, actor=actor, fields=fields)

    s = load_one(story_id)
    if not s:
        _mcp_debug("update_story", "out", error="not found")
        return json.dumps({"error": f"Story {story_id} not found"})

    old_status = s.get("status")
    old_tdd = s.get("tdd", {}).get("status")
    old_qa = s.get("qa", {}).get("status")

    apply_update(s, updates, default_actor="agent")
    save_one(story_id, s)

    new_status = s.get("status")
    new_tdd = s.get("tdd", {}).get("status")
    new_qa = s.get("qa", {}).get("status")

    _mcp_debug("update_story", "out",
        status=f"{old_status}→{new_status}" if old_status != new_status else new_status,
        tdd=f"{old_tdd}→{new_tdd}" if old_tdd != new_tdd else new_tdd,
        qa=f"{old_qa}→{new_qa}" if old_qa != new_qa else new_qa,
        history_len=len(s.get("history", [])),
    )
    return json.dumps(s, ensure_ascii=False)


@mcp.tool()
def move_story(story_id: str, new_status: str, actor: str = "agent") -> str:
    """Move a story to a new kanban column. Valid statuses: pending, refining, secops_tm, tdd, secops_cr, qa, simplify, commit_ready, completed, blocked.
    Pass actor to log who triggered the move (e.g. "refine", "tdd", "qa", "secops-cr", "simplify", "dashboard")."""
    _mcp_debug("move_story", "in", story_id=story_id, new_status=new_status, actor=actor)
    valid = set(FLOW_STATUSES)
    if new_status not in valid:
        _mcp_debug("move_story", "out", error=f"invalid status: {new_status!r}")
        return json.dumps({"error": f"Invalid status. Valid: {', '.join(sorted(valid))}"})
    s = load_one(story_id)
    if not s:
        _mcp_debug("move_story", "out", error="not found")
        return json.dumps({"error": f"Story {story_id} not found"})
    old_status = s.get("status")
    s["status"] = new_status
    if old_status != new_status:
        s.setdefault("history", []).append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "by": actor,
            "changes": [f"status: {old_status} → {new_status}"],
        })
    save_one(story_id, s)
    _mcp_debug("move_story", "out",
        old_status=old_status,
        new_status=new_status,
        changed=old_status != new_status,
    )
    return json.dumps(s, ensure_ascii=False)


@mcp.tool()
def create_story(title: str, phase: int = 7) -> str:
    """Create a new story. Returns the created story as JSON."""
    _mcp_debug("create_story", "in", title=title, phase=phase)
    existing = load_all()
    phase_items = [s for s in existing if s.get("phase") == phase]
    nums = []
    for s in phase_items:
        try:
            nums.append(int(s["id"].split(".")[1]))
        except (KeyError, IndexError, ValueError):
            pass
    n = max(nums, default=0) + 1
    sid = f"US {phase}.{n}"

    phase_names = {1: "Fondations Backend", 2: "Frontend MVP", 3: "SaaS & Monétisation",
                   4: "Mode Entreprise", 5: "Quality & Hardening", 6: "V2 & Futur", 7: "Backlog"}
    now = datetime.now().isoformat(timespec="seconds")
    next_order = max((s.get("order", 0) for s in existing if s.get("status") == "pending"), default=-1) + 1
    story = {
        "id": sid, "phase": phase, "phase_name": phase_names.get(phase, "Backlog"),
        "title": title, "description": "", "status": "pending",
        "order": next_order, "priority_score": 0,
        "acceptance_criteria": [],
        "stack": [],
        "tdd": {"status": "pending", "tests": 0, "coverage": "0%", "notes": ""},
        "qa": {"status": "pending", "ac_covered": "0/0", "notes": ""},
        "notes": "", "refine_decisions": [], "implementation_guide": {}, "secops_report": {},
        "simplify_comments": "", "history": [],
        "created_at": now, "updated_at": now,
    }
    save_one(sid, story)
    _mcp_debug("create_story", "out", id=sid, phase=phase)
    return json.dumps(story, ensure_ascii=False)


@mcp.tool()
def get_next_pending() -> str:
    """Get the next pending story (P0 first, earliest phase)."""
    _mcp_debug("get_next_pending", "in")
    items = [s for s in load_all() if s.get("status") == "pending" and s.get("phase") != 6]
    items.sort(key=lambda s: (
        -s.get("priority_score", 0),
        s.get("phase", 99),
        s["id"],
    ))
    if not items:
        _mcp_debug("get_next_pending", "out", result="ALL_DONE")
        return json.dumps({"message": "ALL_DONE"})
    next_s = items[0]
    _mcp_debug("get_next_pending", "out",
        story_id=next_s["id"],
        phase=next_s.get("phase"),
        pending_total=len(items),
    )
    return json.dumps(next_s, ensure_ascii=False)


@mcp.tool()
def bulk_prioritize(scores: str) -> str:
    """Set priority scores on multiple stories in one atomic call.
    scores: JSON array of {"id": "US X.Y", "score": 0-100, "rationale": "..."}.
    Higher score = picked first by get_next_pending (overrides P0/P1/P2 ordering).
    Score 0 means no special priority — falls back to the default P0→P1→P2 sort.
    Returns the updated stories sorted by descending score."""
    try:
        items = json.loads(scores)
    except json.JSONDecodeError as e:
        _mcp_debug("bulk_prioritize", "in", parse_error=str(e))
        return json.dumps({"error": f"Invalid JSON: {e}"})

    _mcp_debug("bulk_prioritize", "in", count=len(items))
    updated = []
    for item in items:
        sid = item.get("id")
        score = int(item.get("score", 0))
        rationale = item.get("rationale", "")
        if not sid:
            continue
        s = load_one(sid)
        if not s:
            continue
        old_score = s.get("priority_score", 0)
        s["priority_score"] = score
        if old_score != score:
            change = f"priority_score: {old_score} → {score}"
            if rationale:
                change += f" — {rationale}"
            s.setdefault("history", []).append({
                "ts": datetime.now().isoformat(timespec="seconds"),
                "by": "prioritize",
                "changes": [change],
            })
        save_one(sid, s)
        updated.append({"id": sid, "score": score, "rationale": rationale})

    updated.sort(key=lambda x: -x["score"])
    _mcp_debug("bulk_prioritize", "out", count=len(updated),
        top=updated[0]["id"] if updated else None,
    )
    return json.dumps({"ok": True, "count": len(updated), "order": updated}, ensure_ascii=False)


@mcp.tool()
def get_stats() -> str:
    """Get project-wide statistics."""
    _mcp_debug("get_stats", "in")
    result = stats(load_all())
    _mcp_debug("get_stats", "out",
        **{k: v for k, v in result.items() if k not in ("tdd_counts", "qa_counts")},
    )
    return json.dumps(result, ensure_ascii=False)


# ── Entry points ───────────────────────────────────────────────────
def run_http():
    log.info("═══ Kanban Server ═══")
    log.info(f"  Stories : {STORIES_DIR}")
    log.info(f"  Count   : {len(load_all())}")
    log.info(f"  REST    : http://localhost:{KANBAN_HTTP_PORT}/api/stories")
    log.info(f"  Dashboard: http://localhost:{KANBAN_HTTP_PORT}/")
    log.info(f"  OpenCode bridge: {'ON → ' + OPENCODE_SERVER_URL if OPENCODE_TRIGGER_ENABLED else 'OFF'}")
    log.info(f"  Debug mode: {'ON — MCP calls logged to stderr + {LOG_FILE.name}' if KANBAN_DEBUG else 'OFF (set KANBAN_DEBUG=1 or --debug to enable)'}")

    import uvicorn
    uvicorn.run(rest, host="0.0.0.0", port=KANBAN_HTTP_PORT, log_level="warning")


def run_mcp():
    _register_session()
    if not _try_start_http():
        log.info(f"  Port {KANBAN_HTTP_PORT} taken — MCP-only mode, watchdog active")
        threading.Thread(target=_http_watchdog, daemon=True).start()
    import asyncio
    from mcp.server.stdio import stdio_server

    async def serve():
        async with stdio_server() as (rs, ws):
            await mcp._mcp_server.run(rs, ws, mcp._mcp_server.create_initialization_options())

    asyncio.run(serve())


if __name__ == "__main__":
    if "--mcp" in sys.argv:
        run_mcp()
    else:
        run_http()
