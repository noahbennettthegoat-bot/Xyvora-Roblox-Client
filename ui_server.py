#!/usr/bin/env python3
"""Cordial UI preview/dev server.

Serves the local launcher UI from ./ui and exposes a small /api/system endpoint
for device/runtime detection. No external dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socketserver
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"


def read_os_release() -> dict[str, str]:
    data: dict[str, str] = {}
    for path in ("/etc/os-release", "/usr/lib/os-release"):
        p = Path(path)
        if not p.exists():
            continue
        try:
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
        except OSError:
            pass
        if data:
            break
    return data


def normalize_arch(machine: str) -> str:
    m = (machine or "").lower()
    return {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }.get(m, m or "unknown")


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def detect_system() -> dict[str, Any]:
    sysname = platform.system().lower()
    machine = platform.machine().lower() or "unknown"
    arch = normalize_arch(machine)
    os_release = read_os_release() if sysname == "linux" else {}
    distro = os_release.get("PRETTY_NAME") or os_release.get("NAME") or platform.system()
    distro_id = (os_release.get("ID") or "").lower()
    wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
    x11 = bool(os.environ.get("DISPLAY"))
    supported_arch = arch in {"x86_64", "aarch64"}
    supported_os = sysname == "linux"
    supported = supported_os and supported_arch

    checks = {
        "linux": supported_os,
        "arch": supported_arch,
        "wayland_session": wayland,
        "x11_session": x11,
        "flatpak": command_exists("flatpak"),
        "cargo": command_exists("cargo"),
        "rustc": command_exists("rustc"),
        "ffmpeg": command_exists("ffmpeg"),
        "vulkaninfo": command_exists("vulkaninfo"),
    }

    blockers: list[str] = []
    if not supported_os:
        blockers.append("Cordial targets Linux. This device is not running Linux.")
    if not supported_arch:
        blockers.append(f"Architecture '{arch}' is not supported yet (expected x86_64 or aarch64).")

    notes: list[str] = []
    if supported and not wayland and not x11:
        notes.append("No Wayland/X11 display detected in this environment; UI preview still works, but the client needs a graphical session.")
    if supported and not checks["flatpak"]:
        notes.append("Flatpak not detected. Flatpak is the recommended install path for Cordial.")
    if supported and not checks["cargo"]:
        notes.append("Rust toolchain not detected. Source builds need cargo/rustc.")

    return {
        "app": "Cordial",
        "supported": supported,
        "os": {
            "system": sysname,
            "distro": distro,
            "distro_id": distro_id,
            "version": os_release.get("VERSION_ID", ""),
        },
        "arch": arch,
        "machine": machine,
        "session": {
            "wayland": wayland,
            "x11": x11,
            "desktop": os.environ.get("XDG_CURRENT_DESKTOP", ""),
        },
        "checks": checks,
        "blockers": blockers,
        "notes": notes,
    }


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
        print(f"[cordial-ui] {self.address_string()} - {fmt % args}")

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] == "/api/system":
            try:
                self._send_json(detect_system())
            except Exception as e:  # pragma: no cover
                self._send_json({"error": "system_detection_failed", "detail": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Cordial launcher UI preview.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3000)
    args = parser.parse_args()

    if not UI_DIR.exists():
        raise SystemExit(f"UI directory not found: {UI_DIR}")

    handler = lambda *a, **kw: Handler(*a, directory=str(UI_DIR), **kw)  # noqa: E731

    class Server(socketserver.TCPServer):
        allow_reuse_address = True

    with Server((args.host, args.port), handler) as httpd:
        print(f"Cordial UI running at http://{args.host}:{args.port}")
        print(f"Serving: {UI_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == "__main__":
    main()
