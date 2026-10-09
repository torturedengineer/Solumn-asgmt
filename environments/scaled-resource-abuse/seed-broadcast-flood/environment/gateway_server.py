#!/usr/bin/env python3
"""Mock third-party NotifyGateway used by the Pulsewire tasks.

This stands in for an external provider: the repository under /app talks to
it exactly like it would talk to a real HTTP API. It is infrastructure
outside the agent's control -- the same way a real SaaS provider would be --
and is NOT part of the repository the agent edits.

Behaviour that matters for grading:
  - POST /send    enforces the provider's hard per-call cap (<=50 recipients,
                   else HTTP 400) and logs every accepted call, with a
                   timestamp, to a durable JSONL file.
  - POST /confirm logs every delivery-confirmation ping the same way.
  - GET  /__stats__ returns the logged calls for both endpoints.
  - POST /__reset__ clears state between grading phases.
  - PULSEWIRE_FAIL_EVERY_NTH (env var) makes every Nth /send call return a
    transient 500, for the retry-logic variant. 0 (default) = never fails.
"""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DATA_DIR = os.environ.get("GATEWAY_DATA_DIR", "/data")
MAX_RECIPIENTS_PER_CALL = 50
FAIL_EVERY_NTH = int(os.environ.get("PULSEWIRE_FAIL_EVERY_NTH", "0"))

os.makedirs(DATA_DIR, exist_ok=True)
SEND_LOG_PATH = os.path.join(DATA_DIR, "gateway_send_log.jsonl")
CONFIRM_LOG_PATH = os.path.join(DATA_DIR, "gateway_confirm_log.jsonl")

_lock = threading.Lock()
_send_call_count = 0


def _append_log(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep container logs quiet

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _respond(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        global _send_call_count

        if self.path == "/send":
            payload = self._read_json()
            recipients = payload.get("recipients", [])
            if len(recipients) > MAX_RECIPIENTS_PER_CALL:
                self._respond(
                    400,
                    {"error": f"too many recipients in one call (max {MAX_RECIPIENTS_PER_CALL})"},
                )
                return
            with _lock:
                _send_call_count += 1
                count = _send_call_count
            if FAIL_EVERY_NTH and count % FAIL_EVERY_NTH == 0:
                self._respond(500, {"error": "transient upstream error, please retry"})
                return
            ts = time.time()
            _append_log(
                SEND_LOG_PATH,
                {"ts": ts, "recipient_count": len(recipients), "recipients": recipients},
            )
            self._respond(200, {"status": "accepted", "recipient_count": len(recipients)})
            return

        if self.path == "/confirm":
            payload = self._read_json()
            ts = time.time()
            _append_log(CONFIRM_LOG_PATH, {"ts": ts, "recipient": payload.get("recipient")})
            self._respond(200, {"status": "ok"})
            return

        if self.path == "/__reset__":
            with _lock:
                _send_call_count = 0
            for p in (SEND_LOG_PATH, CONFIRM_LOG_PATH):
                open(p, "w").close()
            self._respond(200, {"status": "reset"})
            return

        self._respond(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/__stats__":
            self._respond(
                200,
                {
                    "send_calls": _read_jsonl(SEND_LOG_PATH),
                    "confirm_calls": _read_jsonl(CONFIRM_LOG_PATH),
                },
            )
            return
        self._respond(404, {"error": "not found"})


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    server.serve_forever()
