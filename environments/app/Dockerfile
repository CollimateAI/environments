# syntax=docker/dockerfile:1.7
# app: a minimal live-service HTTP + WebSocket app server, warmed and left
# RUNNING so every fork wakes with it already serving. It is the reference
# "connect-from-outside" environment — a rollout (or a remote trainer) reaches
# it over host→guest ingress (a port-forward or a connect URL), not exec.
#
# It binds 0.0.0.0 directly (unlike a headless Chrome, which binds loopback and
# needs a relay), so the exposed port is reachable with no extra machinery — the
# common case for an HTTP/WS service. See docs/cookbook/live-model-server.md and
# docs/cookbook/access-models.md.
FROM python:3.12-slim

# The app server: stdlib only (http + a tiny RFC 6455 WebSocket echo) on one
# port. GET /health -> 200 (readiness), GET /json -> a small JSON body, and a
# WebSocket at /ws that echoes frames (the OpenEnv env-server shape: /health +
# a /ws socket). Swap this for your own server — the ready-state shape is the
# same: bind 0.0.0.0:$PORT, expose the port, block warm until /health is green.
COPY <<'APP' /usr/local/bin/app-server
#!/usr/bin/env python3
import base64, hashlib, json, socket, struct, threading

PORT = 8000
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def ws_accept(key):
    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()


def recv_frame(sock):
    hdr = recv_exact(sock, 2)
    if hdr is None:
        return None, b""
    b0, b1 = hdr
    op = b0 & 0x0F
    ln = b1 & 0x7F
    if ln == 126:
        ln = struct.unpack(">H", recv_exact(sock, 2))[0]
    elif ln == 127:
        ln = struct.unpack(">Q", recv_exact(sock, 8))[0]
    mask = recv_exact(sock, 4) if (b1 & 0x80) else b"\x00\x00\x00\x00"
    data = recv_exact(sock, ln) if ln else b""
    if data:
        data = bytes(c ^ mask[i & 3] for i, c in enumerate(data))
    return op, data


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        c = sock.recv(n - len(buf))
        if not c:
            return None
        buf += c
    return buf


def send_frame(sock, data, op=0x1):  # text by default
    hdr = bytearray([0x80 | op])
    n = len(data)
    if n < 126:
        hdr.append(n)
    elif n < 65536:
        hdr.append(126); hdr += struct.pack(">H", n)
    else:
        hdr.append(127); hdr += struct.pack(">Q", n)
    sock.sendall(bytes(hdr) + data)


def handle(conn):
    head = b""
    while b"\r\n\r\n" not in head:
        c = conn.recv(4096)
        if not c:
            conn.close(); return
        head += c
    lines = head.decode("latin-1").split("\r\n")
    method, path = (lines[0].split(" ") + ["", ""])[:2]
    headers = {}
    for ln in lines[1:]:
        if ":" in ln:
            k, v = ln.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    if path.startswith("/ws") and headers.get("upgrade", "").lower() == "websocket":
        conn.sendall(
            ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
             "Connection: Upgrade\r\n"
             f"Sec-WebSocket-Accept: {ws_accept(headers.get('sec-websocket-key',''))}\r\n\r\n").encode()
        )
        while True:
            op, data = recv_frame(conn)
            if op is None or op == 0x8:
                break
            if op == 0x9:  # ping -> pong
                send_frame(conn, data, op=0xA); continue
            if op in (0x1, 0x2):
                send_frame(conn, b"echo:" + data, op=op)  # echo back
        conn.close(); return

    if path.startswith("/health"):
        body = b"ok"
    elif path.startswith("/json"):
        body = json.dumps({"service": "app", "ok": True, "path": path}).encode()
    else:
        body = json.dumps({"service": "app", "routes": ["/health", "/json", "/ws"]}).encode()
    conn.sendall(
        b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body
    )
    conn.close()


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(64)
    print(f"app-server listening on 0.0.0.0:{PORT}", flush=True)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()


main()
APP

# Warm script: start the server DETACHED so it lands in the ready-state
# snapshot, then block until GET /health is 200 — the real "serving" signal.
COPY <<'WARM' /usr/local/bin/collimate-warm
#!/bin/sh
set -e
ip link set lo up 2>/dev/null || true
setsid python3 /usr/local/bin/app-server >/var/log/app.log 2>&1 < /dev/null &
for i in $(seq 1 60); do
  if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1)" 2>/dev/null; then
    echo app-ready; exit 0
  fi
  sleep 1
done
echo app-timeout >&2; exit 1
WARM

RUN chmod +x /usr/local/bin/app-server /usr/local/bin/collimate-warm \
 # Self-test the whole recipe at build time: the warm script must launch the
 # server and see /health go green, and /json + a WS echo must both answer —
 # a green build proves the live-service snapshot will serve.
 && /usr/local/bin/collimate-warm >/dev/null \
 && python3 -c "import urllib.request,json; \
assert json.load(urllib.request.urlopen('http://127.0.0.1:8000/json',timeout=5))['ok'] is True; \
print('http-ok')" \
 && python3 -c "import socket,base64,os,struct; \
s=socket.create_connection(('127.0.0.1',8000),timeout=5); k=base64.b64encode(os.urandom(16)).decode(); \
s.sendall(('GET /ws HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: '+k+'\r\nSec-WebSocket-Version: 13\r\n\r\n').encode()); \
h=s.recv(200); assert b'101' in h, h; \
m=os.urandom(4); p=b'hi'; \
s.sendall(bytes([0x81,0x80|len(p)])+m+bytes(b^m[i&3] for i,b in enumerate(p))); \
r=s.recv(64); assert b'echo:hi' in r, r; print('ws-ok')"

WORKDIR /workspace
CMD ["sleep", "infinity"]
