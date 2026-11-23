#!/usr/bin/env python3
"""Local preview server for the Xyvora UI.

Serves the static UI from ./ui and exposes a small /api/system endpoint
used by the frontend to detect the current device/platform.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import socketserver
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"


def _read_os_release() -> dict[str, str]:
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


def _linux_family(os_release: dict[str, str]) -> str:
    ident = (os_release.get("ID") or "").lower()
    like = (os_release.get("ID_LIKE") or "").lower()
    tokens = set(ident.split()) | set(like.replace(",", " ").split())

    def has(*names: str) -> bool:
        return any(n in tokens or n == ident for n in names)

    if has("arch", "manjaro", "endeavouros", "artix", "garuda", "cachyos"):
        return "arch"
    if has("debian", "ubuntu", "linuxmint", "pop", "elementary", "kali", "raspbian"):
        return "debian"
    if has("fedora", "rhel", "centos", "rocky", "almalinux", "nobara"):
        return "fedora"
    if has("suse", "opensuse"):
        return "suse"
    if has("nixos"):
        return "nixos"
    if has("gentoo"):
        return "gentoo"
    if has("void"):
        return "void"
    if has("alpine"):
        return "alpine"
    if has("slackware"):
        return "slackware"
    if has("solus"):
        return "solus"
    if ident:
        return ident
    return "linux"


def detect_system() -> dict[str, Any]:
    sysname = platform.system().lower()  # linux, windows, darwin, ...
    machine = platform.machine().lower() or "unknown"
    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "armv7l": "armv7",
        "armv8l": "arm64",
        "riscv64": "riscv64",
        "i686": "x86",
        "i386": "x86",
    }
    arch = arch_map.get(machine, machine)

    os_release = _read_os_release() if sysname == "linux" else {}
    distro_id = (os_release.get("ID") or ("linux" if sysname == "linux" else sysname)).lower()
    distro_name = os_release.get("PRETTY_NAME") or os_release.get("NAME") or platform.system()
    distro_version = os_release.get("VERSION_ID") or os_release.get("VERSION") or ""
    family = _linux_family(os_release) if sysname == "linux" else sysname

    supported = sysname == "linux"

    # Capability detection (best-effort heuristics for the preview).
    has_waydroid = bool(shutil.which("waydroid"))
    has_wine = bool(shutil.which("wine") or shutil.which("wine64"))
    has_proton = bool(
        shutil.which("proton")
        or shutil.which("proton-experimental")
        or Path.home().joinpath(".steam/root/compatibilitytools.d").exists()
        or Path("/usr/share/steam/compatibilitytools.d").exists()
    )
    has_vulkan = bool(
        shutil.which("vulkaninfo")
        or Path("/usr/share/vulkan/icd.d").exists()
        or Path("/etc/vulkan/icd.d").exists()
    )
    has_opengl = bool(
        shutil.which("glxinfo")
        or Path("/usr/lib/xorg/modules/extensions/libglx.so").exists()
        or Path("/usr/lib64/xorg/modules/extensions/libglx.so").exists()
    )
    # Android runtime is possible on Linux through Waydroid; expose as available option on Linux.
    android_runtime_available = supported

    runtimes: list[dict[str, Any]] = []
    if supported:
        runtimes = [
            {
                "id": "android-waydroid",
                "label": "Android Runtime (Waydroid)",
                "available": android_runtime_available,
                "recommended": True,
                "reason": "" if android_runtime_available else "Requires Linux with Waydroid support.",
            },
            {
                "id": "proton",
                "label": "Proton - Experimental",
                "available": True,
                "recommended": False,
                "detected": has_proton,
                "reason": "" if has_proton else "Not detected on this system; can be installed.",
            },
            {
                "id": "wine",
                "label": "Wine / Wine-GE",
                "available": True,
                "recommended": False,
                "detected": has_wine,
                "reason": "" if has_wine else "Not detected on this system; can be installed.",
            },
        ]

    renderers: list[dict[str, Any]] = []
    if supported:
        renderers = [
            {"id": "vulkan", "label": "Vulkan (Recommended)", "available": True, "detected": has_vulkan},
            {"id": "opengl", "label": "OpenGL", "available": True, "detected": has_opengl},
        ]

    package_hints = {
        "arch": "sudo pacman -S waydroid vulkan-tools",
        "debian": "sudo apt install waydroid vulkan-tools",
        "fedora": "sudo dnf install waydroid vulkan-tools",
        "suse": "sudo zypper install waydroid vulkan-tools",
        "nixos": "Enable Waydroid and Vulkan via NixOS configuration",
        "gentoo": "emerge --ask app-emulation/waydroid",
        "void": "sudo xbps-install -S waydroid vulkan-tools",
        "alpine": "sudo apk add waydroid vulkan-tools",
        "slackware": "Install Waydroid from SlackBuilds / Vulkan packages",
        "solus": "sudo eopkg install waydroid vulkan-tools",
    }

    return {
        "supported": supported,
        "os": {
            "system": sysname,
            "distro_id": distro_id,
            "distro_name": distro_name,
            "distro_version": distro_version,
            "family": family,
        },
        "arch": arch,
        "machine": machine,
        "capabilities": {
            "waydroid": has_waydroid,
            "wine": has_wine,
            "proton": has_proton,
            "vulkan": has_vulkan,
            "opengl": has_opengl,
            "android_runtime": android_runtime_available,
        },
        "runtimes": runtimes,
        "renderers": renderers,
        "package_hint": package_hints.get(family, "Install Waydroid and Vulkan tools using your distro package manager"),
        "support_message": (
            ""
            if supported
            else "Sorry, this device isn't supported yet. Xyvora currently supports Linux devices."
        ),
    }


class XyvoraHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        print(f"[xyvora-ui] {self.address_string()} - {format % args}")

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("?") == "/api/system":
            try:
                self._send_json(detect_system())
            except Exception as exc:  # pragma: no cover - defensive
                self._send_json({"error": "system_detection_failed", "detail": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Xyvora UI locally.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=3000, help="Port to bind (default: 3000)")
    args = parser.parse_args()

    if not UI_DIR.exists():
        raise SystemExit(f"UI directory not found: {UI_DIR}")

    handler = lambda *h_args, **h_kwargs: XyvoraHandler(*h_args, directory=str(UI_DIR), **h_kwargs)  # noqa: E731

    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReusableTCPServer((args.host, args.port), handler) as httpd:
        print(f"Xyvora UI running at http://{args.host}:{args.port}")
        print(f"Serving: {UI_DIR}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == "__main__":
    main()
