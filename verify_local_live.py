"""One authorized end-to-end local HTTP check with fictional content."""
import json
import os
import threading
from http.client import HTTPConnection
from pathlib import Path
import server

if not os.environ.get("CLOCKED_API_KEY"):
    raise SystemExit("A locally configured API key is required.")
source = json.loads(Path("live-input-fictional.json").read_text(encoding="utf-8"))["text"]
httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
server.PORT = httpd.server_port
thread = threading.Thread(target=httpd.serve_forever, daemon=True)
thread.start()
try:
    conn = HTTPConnection("127.0.0.1", server.PORT, timeout=50)
    conn.request("POST", "/api/analyze", json.dumps({"text": source, "consent": True}), {"Content-Type": "application/json"})
    response = conn.getresponse()
    result = json.loads(response.read())
    conn.close()
    if response.status != 200:
        raise SystemExit(f"Local HTTP request failed: {response.status}; {result.get('error', 'unknown')}")
    steps = result.get("result", {}).get("steps", [])
    assert len(steps) == 3 and all(s.get("status") == 200 for s in steps), "A pipeline step did not succeed."
    evidence = steps[0]["result"]["fields"]
    assert evidence["budget"]["value"] == "$240", "Unexpected budget extraction."
    assert steps[1]["result"]["answers"]["ai_permission"]["choice"] == "allowed", "Unexpected AI-use classification."
    assert steps[2]["result"]["fields"]["follow_up"]["value"], "No follow-up question returned."
    print("Local HTTP -> Clocked -> local HTTP: successful; 3 steps; budget and policy verified.")
    print("Billed credits:", result.get("credits", "not reported"))
finally:
    httpd.shutdown()
    httpd.server_close()
