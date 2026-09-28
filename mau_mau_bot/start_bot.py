#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Telegram bot to play UNO in group chats
# Copyright (c) 2016 Jannes Höke <uno@jhoeke.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Modify this file if you want a different startup sequence, for example using
# a Webhook

import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


_ARCADE_FILE = os.path.join(os.path.dirname(__file__), "arcade", "index.html")


def _load_arcade():
    try:
        with open(_ARCADE_FILE, "rb") as handle:
            return handle.read()
    except OSError:
        return None


_ARCADE_HTML = _load_arcade()


class _HealthHandler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/arcade", "/arcade/", "/arcade/index.html"):
            if not _ARCADE_HTML:
                self._send(503, b"arcade unavailable", "text/plain")
                return
            self._send(200, _ARCADE_HTML, "text/html; charset=utf-8")
            return
        if path not in ("/", "/health", "/keep-alive"):
            self.send_response(404)
            self.end_headers()
            return
        self._send(200, b"ok", "text/plain")

    def log_message(self, format, *args):
        return


def _serve_health():
    port = int(os.environ.get("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    server.serve_forever()


def _ping_public_url():
    base = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base:
        return
    target = base + "/health"
    while True:
        time.sleep(10 * 60)
        try:
            urllib.request.urlopen(target, timeout=30).read()
        except Exception:
            pass


def start_bot(updater):
    threading.Thread(target=_serve_health, name="health", daemon=True).start()
    threading.Thread(target=_ping_public_url, name="keep-awake", daemon=True).start()
    updater.start_polling()
