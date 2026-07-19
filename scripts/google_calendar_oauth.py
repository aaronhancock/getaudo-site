#!/usr/bin/env python3
"""Authorize Audo Google APIs and save offline OAuth credentials.

The scheduler scopes remain the default for backward compatibility. Pass one or
more ``--scope`` values to create a separate least-privilege grant, such as the
Drive-only grant used by client provisioning.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import threading
import urllib.parse
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


SCOPES = (
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
    "https://www.googleapis.com/auth/gmail.send",
)


def load_client(path: Path) -> tuple[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    details = data.get("installed") or data.get("web") or data
    client_id = details.get("client_id") or details.get("clientId")
    client_secret = details.get("client_secret") or details.get("clientSecret")
    if not client_id:
        raise ValueError("The OAuth client file does not contain a client ID.")
    return client_id, client_secret or ""


def main() -> int:
    parser = argparse.ArgumentParser()
    client_source = parser.add_mutually_exclusive_group(required=True)
    client_source.add_argument("--client-file", type=Path)
    client_source.add_argument("--client-id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument(
        "--scope",
        action="append",
        dest="scopes",
        help="OAuth scope to request. Repeat for multiple scopes; defaults to scheduler scopes.",
    )
    args = parser.parse_args()
    scopes = tuple(dict.fromkeys(args.scopes or SCOPES))

    if args.client_file:
        client_id, client_secret = load_client(args.client_file)
    else:
        client_id, client_secret = args.client_id, ""
    state = secrets.token_urlsafe(24)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("ascii")).digest()).decode("ascii").rstrip("=")
    redirect_uri = f"http://127.0.0.1:{args.port}/"
    result: dict[str, str] = {}
    completed = threading.Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            result["code"] = query.get("code", [""])[-1]
            result["state"] = query.get("state", [""])[-1]
            result["error"] = query.get("error", [""])[-1]
            ok = bool(result["code"] and result["state"] == state and not result["error"])
            body = (
                "<h1>Audo Google services connected</h1><p>You can close this tab and return to Codex.</p>"
                if ok
                else "<h1>Authorization did not complete</h1><p>Return to Codex and try again.</p>"
            ).encode("utf-8")
            self.send_response(200 if ok else 400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            completed.set()

        def log_message(self, format: str, *values: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", args.port), CallbackHandler)
    server.timeout = 1
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "login_hint": "aaron@getaudo.com",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    print(json.dumps({"status": "waiting_for_authorization", "authorization_url": auth_url}), flush=True)

    try:
        while not completed.is_set():
            server.handle_request()
    except KeyboardInterrupt:
        return 130
    finally:
        server.server_close()

    if result.get("error"):
        raise RuntimeError(f"Google returned an authorization error: {result['error']}")
    if not result.get("code") or result.get("state") != state:
        raise RuntimeError("The OAuth callback did not pass the state check.")

    token_fields = {
        "client_id": client_id,
        "code": result["code"],
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    if client_secret:
        token_fields["client_secret"] = client_secret
    token_body = urllib.parse.urlencode(token_fields).encode("utf-8")
    request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            token = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            details = json.loads(exc.read().decode("utf-8"))
            reason = details.get("error_description") or details.get("error") or "OAuth token exchange failed"
        except Exception:
            reason = "OAuth token exchange failed"
        raise RuntimeError(reason) from exc
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Google did not return an offline refresh token.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "clientId": client_id,
        "refreshToken": refresh_token,
        "scope": token.get("scope", " ".join(scopes)),
    }
    if client_secret:
        payload["clientSecret"] = client_secret
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        json.dump(payload, output, indent=2)
        output.write("\n")
    print(json.dumps({"status": "authorized", "output": str(args.output)}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr, flush=True)
        raise SystemExit(1)
