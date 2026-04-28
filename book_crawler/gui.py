from __future__ import annotations

import json
import queue
import threading
import urllib.parse
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .service import RunSettings, load_run_file, run_crawler, validate_settings

HOST = "127.0.0.1"
PORT = 8765


class AppState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.cancel_event = threading.Event()
        self.events: queue.Queue[dict] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.running = False
        self.last_result: str | None = None
        self.log_path: Path | None = None

    def emit(self, event: str, message: str) -> None:
        payload = {"event": event, "message": message}
        self.events.put(payload)
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{datetime.now().isoformat(timespec='seconds')} {event}: {message}\n")


STATE = AppState()


class GuiHandler(BaseHTTPRequestHandler):
    server_version = "BookCrawlerGUI/1.0"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return
        if parsed.path == "/api/events":
            self._send_json(_drain_events())
            return
        if parsed.path == "/api/status":
            with STATE.lock:
                payload = {"running": STATE.running, "last_result": STATE.last_result}
            self._send_json(payload)
            return
        if parsed.path == "/api/results":
            query = urllib.parse.parse_qs(parsed.query)
            out_dir = query.get("out_dir", ["result"])[0]
            self._send_json(_list_results(out_dir))
            return
        if parsed.path == "/api/result":
            query = urllib.parse.parse_qs(parsed.query)
            path = query.get("path", [""])[0]
            self._send_json(_load_result_payload(path))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/validate":
            self._send_json({"errors": validate_settings(_settings_from_payload(self._read_json()))})
            return
        if parsed.path == "/api/run":
            self._send_json(_start_run(_settings_from_payload(self._read_json())))
            return
        if parsed.path == "/api/cancel":
            STATE.cancel_event.set()
            STATE.emit("cancel", "cancel requested")
            self._send_json({"ok": True})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, _format: str, *_args) -> None:
        return

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _settings_from_payload(payload: dict) -> RunSettings:
    def optional_int(name: str):
        value = str(payload.get(name, "")).strip()
        return int(value) if value else None

    return RunSettings(
        title=str(payload.get("title", "")),
        author=str(payload.get("author", "")),
        out_dir=str(payload.get("out_dir", "result")),
        max_results=int(payload.get("max_results", 20)),
        lang=str(payload.get("lang", "ko")),
        year_from=optional_int("year_from"),
        year_to=optional_int("year_to"),
        headless=bool(payload.get("headless", True)),
        dry_run=bool(payload.get("dry_run", True)),
        timeout=float(payload.get("timeout", 20)),
        retries=int(payload.get("retries", 2)),
        search_provider=str(payload.get("search_provider", "brave")),
    )


def _start_run(settings: RunSettings) -> dict:
    errors = validate_settings(settings)
    if errors:
        return {"ok": False, "errors": errors}

    with STATE.lock:
        if STATE.running:
            return {"ok": False, "errors": ["already running"]}
        STATE.running = True
        STATE.last_result = None
        STATE.cancel_event = threading.Event()
        STATE.log_path = Path(settings.out_dir).expanduser() / f"gui_{datetime.now():%Y%m%d_%H%M%S}.log"

    while not STATE.events.empty():
        STATE.events.get_nowait()

    worker = threading.Thread(target=_run_worker, args=(settings,), daemon=True)
    with STATE.lock:
        STATE.worker = worker
    worker.start()
    return {"ok": True, "errors": []}


def _run_worker(settings: RunSettings) -> None:
    def progress(event: str, message: str) -> None:
        STATE.emit(event, message)

    result = run_crawler(settings, progress_callback=progress, cancel_event=STATE.cancel_event)
    with STATE.lock:
        STATE.running = False
        STATE.last_result = str(result.run_path) if result.run_path else None
    STATE.emit(result.status, str(result.run_path or result.error or ""))


def _drain_events() -> list[dict]:
    events = []
    while True:
        try:
            events.append(STATE.events.get_nowait())
        except queue.Empty:
            return events


def _list_results(out_dir: str) -> dict:
    root = Path(out_dir).expanduser().resolve(strict=False)
    files = []
    if root.exists():
        files = [
            {"name": path.name, "path": str(path)}
            for path in sorted(root.glob("run_*.json"), reverse=True)
        ]
    return {"results": files}


def _load_result_payload(path: str) -> dict:
    if not path:
        return {"error": "path required"}
    try:
        return {"payload": load_run_file(path)}
    except Exception as exc:
        return {"error": str(exc)}


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), GuiHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"ai_crawling_books GUI: {url}")
    webbrowser.open(url)
    server.serve_forever()


INDEX_HTML = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ai_crawling_books</title>
<style>
:root{--bg:#101418;--panel:#171d23;--text:#e9eef2;--muted:#9aa8b4;--line:#2c3640;--accent:#6ee7b7;--warn:#f7c76b;--bad:#fb7185}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Avenir Next,ui-sans-serif,sans-serif}
main{display:grid;grid-template-columns:340px 1fr;min-height:100vh}aside{border-right:1px solid var(--line);padding:20px;background:var(--panel)}
section{padding:20px}label{display:block;color:var(--muted);font-size:12px;margin:12px 0 6px}
input,select,button{width:100%;border:1px solid var(--line);border-radius:6px;background:#0f1419;color:var(--text);padding:10px;font:inherit}
button{cursor:pointer;background:#1f2a33}button.primary{background:var(--accent);color:#062017;border:0;font-weight:700}
button:disabled{opacity:.45;cursor:not-allowed}.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.checks{display:flex;gap:14px;margin:12px 0}
.checks label{display:flex;align-items:center;gap:6px;margin:0}.checks input{width:auto}.toolbar{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.notice{margin-top:14px;color:var(--warn);font-size:13px;line-height:1.45}.top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.status{color:var(--muted)}.grid{display:grid;grid-template-columns:minmax(0,1fr) 420px;gap:16px;margin-top:16px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line)}
th,td{padding:9px;border-bottom:1px solid var(--line);font-size:13px;text-align:left;vertical-align:top}tr:hover{background:#202832}
pre{white-space:pre-wrap;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px;min-height:220px}
.log{height:220px}.pill{display:inline-block;padding:2px 7px;border-radius:999px;background:#26313a;color:var(--accent);font-size:12px}
</style>
</head>
<body>
<main>
<aside>
<h1>ai_crawling_books</h1>
<label>Title</label><input id="title" placeholder="Database System Concepts">
<label>Author</label><input id="author" placeholder="Silberschatz">
<label>Output directory</label><input id="out_dir" value="result">
<div class="row">
<div><label>Provider</label><select id="search_provider"><option>brave</option><option>bing</option></select></div>
<div><label>Lang</label><input id="lang" value="ko"></div>
</div>
<div class="row">
<div><label>Max results</label><input id="max_results" type="number" min="1" value="20"></div>
<div><label>Retries</label><input id="retries" type="number" min="0" value="2"></div>
</div>
<div class="row">
<div><label>Year from</label><input id="year_from"></div>
<div><label>Year to</label><input id="year_to"></div>
</div>
<label>Timeout</label><input id="timeout" type="number" min="1" value="20">
<div class="checks">
<label><input id="headless" type="checkbox" checked>Headless</label>
<label><input id="dry_run" type="checkbox" checked>Dry run</label>
</div>
<div class="toolbar">
<button class="primary" id="run">Run</button>
<button id="cancel" disabled>Cancel</button>
</div>
<button id="refresh" style="margin-top:10px">Refresh results</button>
<div class="notice">Downloads stay blocked unless license and domain signals are strong. Manual source review still required.</div>
</aside>
<section>
<div class="top"><h2>Run review</h2><div class="status" id="status">Idle</div></div>
<div class="grid">
<div><table><thead><tr><th>Decision</th><th>Score</th><th>PDFs</th><th>Source</th></tr></thead><tbody id="rows"></tbody></table></div>
<div><div class="pill">Details</div><pre id="detail"></pre></div>
</div>
<h3>Logs</h3><pre class="log" id="log"></pre>
<h3>Saved runs</h3><pre id="runs"></pre>
</section>
</main>
<script>
const $=id=>document.getElementById(id); let lastPayload=null;
function payload(){return {title:$('title').value,author:$('author').value,out_dir:$('out_dir').value,search_provider:$('search_provider').value,lang:$('lang').value,max_results:+$('max_results').value,retries:+$('retries').value,year_from:$('year_from').value,year_to:$('year_to').value,timeout:+$('timeout').value,headless:$('headless').checked,dry_run:$('dry_run').checked}}
function log(line){$('log').textContent+=new Date().toLocaleTimeString()+' '+line+'\n';$('log').scrollTop=$('log').scrollHeight}
async function post(url,data={}){return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(r=>r.json())}
$('run').onclick=async()=>{const r=await post('/api/run',payload()); if(!r.ok){alert(r.errors.join('\n'));return} $('run').disabled=true;$('cancel').disabled=false;log('started')}
$('cancel').onclick=async()=>{await post('/api/cancel');log('cancel requested')}
$('refresh').onclick=refreshRuns;
async function poll(){const events=await fetch('/api/events').then(r=>r.json()); for(const e of events){$('status').textContent=e.event+': '+e.message;log(e.event+': '+e.message); if(e.event==='completed') await loadResult(e.message)} const s=await fetch('/api/status').then(r=>r.json()); $('run').disabled=s.running;$('cancel').disabled=!s.running; setTimeout(poll,1000)}
async function refreshRuns(){const q=new URLSearchParams({out_dir:$('out_dir').value}); const data=await fetch('/api/results?'+q).then(r=>r.json()); $('runs').innerHTML=data.results.map(x=>`<button onclick="loadResult('${x.path.replaceAll('\\\\','\\\\\\\\')}')">${x.name}</button>`).join('\n')}
async function loadResult(path){const q=new URLSearchParams({path}); const data=await fetch('/api/result?'+q).then(r=>r.json()); if(data.error){log(data.error);return} lastPayload=data.payload; renderRows(lastPayload)}
function renderRows(payload){const rows=$('rows'); rows.innerHTML=''; for(const [i,item] of (payload.results||[]).entries()){const src=item.source||{}, dec=item.decision||{}; const tr=document.createElement('tr'); tr.innerHTML=`<td>${dec.status||''}</td><td>${src.relevance_score||''}</td><td>${(item.candidates||[]).length}</td><td>${src.url||''}</td>`; tr.onclick=()=>{$('detail').textContent=JSON.stringify(item,null,2)}; rows.appendChild(tr)} $('status').textContent='Loaded '+(payload.run_id||'result')}
refreshRuns(); poll();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
