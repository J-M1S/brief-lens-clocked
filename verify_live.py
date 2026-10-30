"""One explicitly authorized Clocked check using only fictional data."""
import json
import os
import re
from urllib.error import HTTPError
from pathlib import Path
import server

text = ("Fictional request: Please prepare one 1,200-word article about caring for indoor plants. "
        "The budget is $240 for the first article. We can provide a style guide. "
        "AI-generated drafts are allowed, but a person must check all facts. "
        "Please send a short outline before writing.")
key = os.environ.get("CLOCKED_API_KEY", "")
if not key:
    raise SystemExit("A locally configured API key is required.")
try:
    result = server.clocked_call(text, key)
except HTTPError as exc:
    body = exc.read(4096).decode("utf-8", errors="replace").replace(key, "[REDACTED]")
    body = re.sub(r"clk_(?:live|test)_[A-Za-z0-9_-]+", "[REDACTED]", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = " ".join(body.split())[:500]
    raise SystemExit(f"Live check failed: HTTP {exc.code}; server={exc.headers.get('server', 'unknown')}; response={body}")
except Exception as exc:
    # Avoid displaying response bodies, source data or secrets on errors.
    raise SystemExit(f"Live check failed: {type(exc).__name__}; HTTP status {getattr(exc, 'code', 'unavailable')}")
Path("live-check-fictional.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
steps = result.get("result", {}).get("steps", [])
print("Billed credits:", result.get("credits", "not reported"))
for step in steps:
    print("Step:", step.get("name"), "status:", step.get("status"), "has result:", isinstance(step.get("result"), dict))
    if step.get("error"):
        print("  Error:", json.dumps(step["error"], ensure_ascii=False))
print("Response saved with fictional content only.")
