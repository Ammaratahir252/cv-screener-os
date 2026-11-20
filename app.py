"""The browser screen. Double-click start.bat (or run: python app.py).

It only runs on this computer (127.0.0.1): nobody else on the network can open it.
Uses only Python's built-in web server, so nothing extra has to be installed.
"""
import base64
import json
import os
import re
import shutil
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from screener.approval import approve, latest_sheet, write_decisions
from screener.llm import ENDPOINTS
from screener.pipeline import ROOT, load_config, load_env, screen_folder

INBOX, OUTPUT = ROOT / "inbox", ROOT / "output"
LAST_RUN = OUTPUT / "last_run.json"
PAGE = ROOT / "ui" / "index.html"
MAX_UPLOAD = 25 * 1024 * 1024

JOB = {"running": False, "done": 0, "total": 0, "current": "", "error": ""}
LOCK = threading.Lock()


def inbox_files():
    return sorted(p.name for p in INBOX.iterdir()
                  if p.is_file() and not p.name.startswith(".")) if INBOX.exists() else []


def load_run():
    if LAST_RUN.exists():
        try:
            return json.loads(LAST_RUN.read_text(encoding="utf-8"))
        except ValueError:
            return None
    return None


def save_run(run):
    OUTPUT.mkdir(exist_ok=True)
    LAST_RUN.write_text(json.dumps(run, ensure_ascii=False, indent=1), encoding="utf-8")


def state():
    load_env()
    settings, role = load_config()
    provider = settings.get("provider", "")
    key_name = ENDPOINTS.get(provider, ("", ""))[1]
    crit = lambda c: {"id": c["id"], "label": c.get("label") or c["id"], "text": c["text"]}
    return {
        "role": role["role"],
        "must": [crit(c) for c in role["must_have"]],
        "nice": [crit(c) for c in role.get("nice_to_have", [])],
        "key_ok": bool(os.environ.get(key_name, "").strip()),
        "key_name": key_name,
        "inbox": inbox_files(),
        "run": load_run(),
        "job": dict(JOB),
    }


def run_screening():
    def progress(done, total, name):
        with LOCK:
            JOB.update(done=done, total=total, current=name)
    try:
        notices = []
        sheet, rows = screen_folder(INBOX, OUTPUT, progress=progress, notices=notices)
        save_run({"sheet": sheet.name, "time": f"{datetime.now():%d %b %Y, %H:%M}",
                  "rows": rows, "decisions": {}, "drafts": []})
        with LOCK:
            JOB.update(done=JOB["total"], error=" ".join(notices))
    except SystemExit as exc:          # plain-language stop (missing key, empty inbox, ...)
        with LOCK:
            JOB["error"] = str(exc).replace("STOPPED: ", "")
    except Exception as exc:           # never leave the screen spinning
        with LOCK:
            JOB["error"] = f"Something unexpected went wrong: {exc}. See logs/run.log."
    finally:
        with LOCK:
            JOB["running"] = False


def safe_name(name):
    name = Path(name).name.strip().lstrip(".")
    name = re.sub(r"[^\w .()+-]", "_", name)
    return name or "cv.txt"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the black window quiet
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_UPLOAD:
            raise ValueError("These files are too big together (over 25 MB). Add fewer at a time.")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        try:
            if self.path in ("/", "/index.html"):
                return self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/state":
                return self.send(200, state())
            if self.path == "/api/progress":
                with LOCK:
                    return self.send(200, dict(JOB))
            if self.path == "/api/sheet":
                sheet = latest_sheet()
                if not sheet:
                    return self.send(404, {"error": "No review sheet yet."})
                return self.send(200, sheet.read_bytes(), "text/csv; charset=utf-8",
                                 {"Content-Disposition": f'attachment; filename="{sheet.name}"'})
            self.send(404, {"error": "Not found"})
        except SystemExit as exc:
            self.send(500, {"error": str(exc)})

    def do_POST(self):
        try:
            data = self.body()
            if self.path == "/api/upload":
                INBOX.mkdir(exist_ok=True)
                added = []
                for f in data.get("files", []):
                    name = safe_name(f.get("name", ""))
                    target, n = INBOX / name, 2
                    while target.exists():
                        target = INBOX / f"{Path(name).stem} ({n}){Path(name).suffix}"
                        n += 1
                    target.write_bytes(base64.b64decode(f.get("b64", "")))
                    added.append(target.name)
                return self.send(200, {"added": added, "inbox": inbox_files()})

            if self.path == "/api/remove":
                p = INBOX / safe_name(data.get("name", ""))
                if p.is_file():
                    p.unlink()
                return self.send(200, {"inbox": inbox_files()})

            if self.path == "/api/screen":
                with LOCK:
                    if JOB["running"]:
                        return self.send(409, {"error": "Screening is already running."})
                    JOB.update(running=True, done=0, total=len(inbox_files()), current="", error="")
                threading.Thread(target=run_screening, daemon=True).start()
                return self.send(200, {"started": True})

            if self.path == "/api/decide":
                run = load_run()
                if not run:
                    return self.send(400, {"error": "Screen some CVs first."})
                decision = (data.get("decision") or "").upper()
                if decision not in ("ADVANCE", "REJECT", ""):
                    return self.send(400, {"error": "Choose Advance or Reject."})
                run["decisions"][data["file"]] = decision
                save_run(run)
                return self.send(200, {"decisions": run["decisions"]})

            if self.path == "/api/approve":
                run = load_run()
                if not run:
                    return self.send(400, {"error": "Screen some CVs first."})
                sheet = OUTPUT / run["sheet"]
                if not sheet.exists():
                    return self.send(400, {"error": f"The review sheet {run['sheet']} was moved or deleted. "
                                                    "Screen the CVs again."})
                write_decisions(sheet, run["decisions"])
                result = approve(sheet)
                run["drafts"] = result["drafts"]
                save_run(run)
                return self.send(200, result)

            if self.path == "/api/new-batch":
                files = inbox_files()
                if files:
                    dest = ROOT / "archive" / f"{datetime.now():%Y-%m-%d_%H%M%S}"
                    dest.mkdir(parents=True, exist_ok=True)
                    for name in files:
                        shutil.move(str(INBOX / name), str(dest / name))
                if LAST_RUN.exists():
                    LAST_RUN.unlink()
                return self.send(200, {"inbox": inbox_files()})

            self.send(404, {"error": "Not found"})
        except (ValueError, KeyError) as exc:
            self.send(400, {"error": str(exc) or "That request was not understood."})
        except SystemExit as exc:
            self.send(500, {"error": str(exc)})


def open_browser(url):
    """Open the screen in the default browser. Windows' own method first (most reliable)."""
    try:
        if os.name == "nt":
            os.startfile(url)
            return
    except OSError:
        pass
    try:
        if webbrowser.open(url):
            return
    except Exception:
        pass
    print(f"Could not open the browser by itself. Open your browser and go to: {url}")


def main():
    for port in range(8765, 8785):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    else:
        raise SystemExit("Could not start: ports 8765-8784 are all busy. Restart the computer and try again.")
    url = f"http://127.0.0.1:{port}"
    print(f"CV Screener is open in your browser: {url}")
    print("Keep this window open while you work. Close it when you are done.")
    if not os.environ.get("CV_SCREENER_NO_BROWSER"):
        threading.Timer(0.5, open_browser, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
