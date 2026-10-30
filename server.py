"""Local-only, standard-library server for BriefLens. Keep API keys server-side."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path
import json
import os
import uuid

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("BRIEFLENS_PORT", "8765"))
API_URL = "https://clocked.rezolve.ai/clocked/pipeline"
MAX_BODY = 30000


def pipeline_request(text):
    return {
        "text": text,
        "steps": [
            {"name": "evidence", "extract": {"fields": {
                "budget": "The stated fee, budget, or compensation amount, with currency",
                "deadline": "The stated deadline or delivery date",
                "deliverable": "The stated deliverable, output, or item to be delivered",
                "revisions": "The stated number or policy of revisions"
            }}},
            {"name": "policy", "decide": {"questions": {
                "ai_permission": {"type": "choice", "instructions": "What does the brief explicitly say about using AI? Do not infer permission from silence.",
                    "criteria": {"allowed": "AI use is explicitly allowed", "restricted": "AI use is explicitly restricted or prohibited", "not_stated": "AI use is not addressed or is ambiguous"}},
                "external_contact": {"type": "choice", "instructions": "Does the brief explicitly request communication outside the platform?",
                    "criteria": {"requested": "Off-platform contact is requested", "not_stated": "Off-platform contact is not requested or is ambiguous"}}
            }}},
            {"name": "question", "fill": {"fields": {
                "follow_up": {"type": "generate", "description": "Draft one short, polite question asking the client to clarify a material missing condition. Do not invent facts. If nothing material is missing ask which condition to confirm first.", "format": "text", "max_tokens": 80}
            }}}
        ],
        "on_error": "continue"
    }


def clocked_call(text, key):
    req = Request(API_URL, data=json.dumps(pipeline_request(text)).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": "BriefLens/1.0", "Idempotency-Key": str(uuid.uuid4())}, method="POST")
    with urlopen(req, timeout=40) as response:
        result = json.load(response)
        return {"result": result, "credits": response.headers.get("X-Clocked-Credits")}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Do not log source text, credentials, or response content.
        pass

    def send(self, status, data, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def json_response(self, status, data):
        self.send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def allowed_host(self):
        return self.headers.get("Host", "") in (f"localhost:{PORT}", f"127.0.0.1:{PORT}")

    def do_GET(self):
        if not self.allowed_host():
            return self.json_response(403, {"error": "Unsupported host."})
        files = {"/": ("index.html", "text/html; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/live-check-fictional.json": ("live-check-fictional.json", "application/json; charset=utf-8")}
        if self.path not in files:
            return self.json_response(404, {"error": "Not found."})
        name, mime = files[self.path]
        if not (ROOT / name).exists():
            return self.json_response(404, {"error": "Recorded example is unavailable."})
        self.send(200, (ROOT / name).read_bytes(), mime)

    def do_POST(self):
        if not self.allowed_host() or self.path != "/api/analyze":
            return self.json_response(403, {"error": "Unsupported request."})
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"):
            return self.json_response(403, {"error": "Unsupported origin."})
        if self.headers.get_content_type() != "application/json":
            return self.json_response(415, {"error": "JSON required."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                return self.json_response(413, {"error": "Request is too large."})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                return self.json_response(400, {"error": "JSON object required."})
            text = payload.get("text")
            if not isinstance(text, str) or not text.strip() or len(text) > 6000:
                return self.json_response(400, {"error": "Provide 1–6,000 characters of text."})
            if payload.get("consent") is not True:
                return self.json_response(400, {"error": "Confirm the external transmission notice."})
        except (ValueError, UnicodeError, json.JSONDecodeError):
            return self.json_response(400, {"error": "Invalid request."})
        key = os.environ.get("CLOCKED_API_KEY", "")
        if not key:
            return self.json_response(503, {"error": "No Clocked API key configured. The fictional demonstration remains available."})
        try:
            return self.json_response(200, clocked_call(text, key))
        except HTTPError as exc:
            # Deliberately omit the upstream body: it can contain source material.
            return self.json_response(502, {"error": f"Clocked returned HTTP {exc.code}. Nothing was accepted as a result. Check credits and request configuration."})
        except (URLError, TimeoutError, OSError, ValueError):
            return self.json_response(502, {"error": "Clocked could not be reached or its response could not be read. A timed-out request may still have consumed credits; do not automatically retry."})


if __name__ == "__main__":
    print(f"BriefLens is available at http://127.0.0.1:{PORT}/ (local access only)", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
