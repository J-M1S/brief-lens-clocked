# BriefLens

A work-in-progress entry for the Clocked Build Challenge. It helps independent workers inspect a public or fictional project brief before agreeing to terms. It uses Clocked's **Extract** to display verbatim source spans, **Decide** to surface AI-use / external-contact policy signals, and **Fill** to suggest one clearly labeled question. People make the decision; confidence is not proof or a safety rating.

## Run locally

Python 3.10+ is enough; no dependencies are installed. Run `python server.py`, then open `http://127.0.0.1:8765/`. “Try a fictional example” shows a labeled, recorded response from Clocked and does not make a new request. If the recording is unavailable, the example falls back to clearly labeled illustrative data.

For a real analysis, set `CLOCKED_API_KEY` in the server process environment and restart it. The key never belongs in this repository, the browser, screenshots, or a public deployment. The app binds only to 127.0.0.1. A new analysis sends the entered brief to Clocked and can consume credits. Never paste confidential materials, credentials, or other people's personal data without authorization. The server does not save inputs.

The three-step request was executed successfully on fictional data in Clocked's official playground on October 29, 2026 (12 credits). On October 30, a direct call through the local server's API client also returned HTTP 200 for all three steps (12 credits); its fictional response is included. An earlier direct call had received HTTP 403; following Clocked support's guidance, the client now sends a descriptive User-Agent. These checks and unit tests do not establish general model quality. Errors, missing data, unmatched source offsets and ambiguous policy choices are surfaced for manual review. Requests are not automatically retried after timeouts because a retry could incur extra cost.

This local prototype is not hardened for public hosting or multi-user traffic. A public production deployment would require user authentication, abuse controls, cost limits, proper privacy review, and safe credential handling.

## Challenge status

The entry was saved on October 30, 2026. The public demonstration replays a recorded API result; the application in this repository makes live requests when run locally with the user's own API key. On November 6, the local browser interface was exercised with the fictional indoor-plant brief: the live response reported 8 credits, matched the $240 budget and article deliverable to the source, flagged the unspecified deadline and revisions, and generated a clarification question. This is one functional check, not an accuracy benchmark. The public repository begins with its initial commit after earlier work; the earlier development history was not preserved. A [screen recording of a November 7 live run](https://brief-lens-demo-2026.nuttygnat129.chatgpt.site/) shows a fictional brief being analyzed; it was captured at approximately 3–4 frames per second with the final frame held for readability.
