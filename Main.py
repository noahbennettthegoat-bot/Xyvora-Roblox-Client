#!/usr/bin/env python3
"""
Xyvora - Roblox Linux Client (Main entry point)

This is the main launcher script for Xyvora. It uses an Android runtime on
Linux (Waydroid) to run the Roblox Android client - the same general method
used by Sober (running Roblox through Android compatibility on Linux).

Commands:
  check      Detect device/support and runtime readiness
  setup      Guide/perform Android runtime (Waydroid) setup checks
  ui         Start the local Xyvora UI preview server
  run        Launch Roblox through the Android runtime
  status     Show current runtime/session status

Examples:
  python3 Main.py check
  python3 Main.py ui --port 3000
  python3 Main.py run --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_NAME = "Xyvora"
APP_VERSION = "0.3.0"
ROBLOX_PACKAGE = "com.roblox.client"
ROBLOX_ACTIVITY = "com.roblox.client.startup.ActivitySplash"
DEFAULT_UI_PORT = 3000
DEFAULT_UI_HOST = "0.0.0.0"

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "xyvora"
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "xyvora"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "xyvora"
LOG_DIR = DATA_DIR / "logs"
CONFIG_FILE = CONFIG_DIR / "config.json"
APK_DIR = DATA_DIR / "apk"
DEFAULT_APK_PATH = APK_DIR / "roblox.apk"

# Official-ish / configurable APK source. Users can override with --apk or config.
# We do not bundle APKs; this is a configurable download target.
DEFAULT_APK_URL = os.environ.get(
    "XYVORA_ROBLOX_APK_URL",
    "https://www.apkmirror.com/apk/roblox-corporation/roblox/",  # informational fallback; direct download requires user-supplied URL
)

SUPPORTED_LINUX_ARCHES = {"x86_64", "arm64", "armv7", "riscv64", "x86"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging(verbose: bool = False) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("xyvora")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG if verbose else logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    try:
        fh = logging.FileHandler(LOG_DIR / "xyvora.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass

    return logger


# ---------------------------------------------------------------------------
# System detection
# ---------------------------------------------------------------------------


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


def linux_family(os_release: dict[str, str]) -> str:
    ident = (os_release.get("ID") or "").lower()
    like = (os_release.get("ID_LIKE") or "").lower()
    tokens = set(ident.split()) | set(like.replace(",", " ").split())

    def has(*names: str) -> bool:
        return any(n in tokens or n == ident for n in names)

    if has("arch", "manjaro", "endeavouros", "artix", "garuda", "cachyos"):
        return "arch"
    if has("debian", "ubuntu", "linuxmint", "pop", "elementary", "kali", "raspbian", "zorin"):
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
    return ident or "linux"


def normalize_arch(machine: str) -> str:
    machine = (machine or "").lower()
    return {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "armv7l": "armv7",
        "armv8l": "arm64",
        "riscv64": "riscv64",
        "i686": "x86",
        "i386": "x86",
    }.get(machine, machine or "unknown")


@dataclass
class SystemInfo:
    supported: bool
    os_system: str
    distro_id: str
    distro_name: str
    distro_version: str
    family: str
    arch: str
    machine: str
    waydroid_installed: bool
    waydroid_initialized: bool
    waydroid_session_running: bool
    binder_available: bool
    vulkan_available: bool
    opengl_available: bool
    adb_installed: bool
    python_version: str
    package_hint: str
    support_message: str


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_cmd(cmd: list[str], timeout: int = 15, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=check,
    )


def detect_waydroid_initialized() -> bool:
    # Waydroid typically stores images/data under /var/lib/waydroid
    markers = [
        Path("/var/lib/waydroid/waydroid.cfg"),
        Path("/var/lib/waydroid/images/system.img"),
        Path("/var/lib/waydroid/overlay"),
    ]
    return any(p.exists() for p in markers)


def detect_waydroid_session_running() -> bool:
    if not command_exists("waydroid"):
        return False
    try:
        proc = run_cmd(["waydroid", "status"], timeout=10)
        out = (proc.stdout + "\n" + proc.stderr).lower()
        return "session:\t\trunning" in out or "session: running" in out or "container:\t\trunning" in out
    except Exception:
        return False


def detect_binder() -> bool:
    return any(Path(p).exists() for p in ("/dev/binder", "/dev/binderfs/binder", "/dev/anbox-binder"))


def detect_vulkan() -> bool:
    return bool(
        command_exists("vulkaninfo")
        or Path("/usr/share/vulkan/icd.d").exists()
        or Path("/etc/vulkan/icd.d").exists()
    )


def detect_opengl() -> bool:
    return bool(
        command_exists("glxinfo")
        or Path("/usr/lib/xorg/modules/extensions/libglx.so").exists()
        or Path("/usr/lib64/xorg/modules/extensions/libglx.so").exists()
    )


def package_hint_for(family: str) -> str:
    hints = {
        "arch": "sudo pacman -S waydroid lxc python-gbinder",
        "debian": "sudo apt install waydroid curl ca-certificates",
        "fedora": "sudo dnf install waydroid",
        "suse": "sudo zypper install waydroid",
        "nixos": "Enable virtualisation.waydroid.enable = true; in your NixOS configuration",
        "gentoo": "emerge --ask app-emulation/waydroid",
        "void": "sudo xbps-install -S waydroid",
        "alpine": "sudo apk add waydroid (community repo may be required)",
        "slackware": "Install Waydroid from SlackBuilds or your preferred package source",
        "solus": "sudo eopkg install waydroid",
    }
    return hints.get(family, "Install Waydroid using your Linux distro's package manager")


def detect_system() -> SystemInfo:
    sysname = platform.system().lower()
    machine = platform.machine().lower() or "unknown"
    arch = normalize_arch(machine)
    os_release = read_os_release() if sysname == "linux" else {}
    distro_id = (os_release.get("ID") or ("linux" if sysname == "linux" else sysname)).lower()
    distro_name = os_release.get("PRETTY_NAME") or os_release.get("NAME") or platform.system()
    distro_version = os_release.get("VERSION_ID") or os_release.get("VERSION") or ""
    family = linux_family(os_release) if sysname == "linux" else sysname

    supported = sysname == "linux" and arch in SUPPORTED_LINUX_ARCHES
    waydroid_installed = command_exists("waydroid")
    waydroid_initialized = detect_waydroid_initialized() if sysname == "linux" else False
    waydroid_session_running = detect_waydroid_session_running() if sysname == "linux" else False
    binder_available = detect_binder() if sysname == "linux" else False
    vulkan_available = detect_vulkan() if sysname == "linux" else False
    opengl_available = detect_opengl() if sysname == "linux" else False
    adb_installed = command_exists("adb")

    if sysname != "linux":
        support_message = "Sorry, this device isn't supported yet. Xyvora currently supports Linux devices."
    elif arch not in SUPPORTED_LINUX_ARCHES:
        support_message = f"Sorry, Linux architecture '{arch}' isn't supported yet."
    else:
        support_message = ""

    return SystemInfo(
        supported=supported,
        os_system=sysname,
        distro_id=distro_id,
        distro_name=distro_name,
        distro_version=distro_version,
        family=family,
        arch=arch,
        machine=machine,
        waydroid_installed=waydroid_installed,
        waydroid_initialized=waydroid_initialized,
        waydroid_session_running=waydroid_session_running,
        binder_available=binder_available,
        vulkan_available=vulkan_available,
        opengl_available=opengl_available,
        adb_installed=adb_installed,
        python_version=platform.python_version(),
        package_hint=package_hint_for(family) if sysname == "linux" else "",
        support_message=support_message,
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "runtime": "android-waydroid",
    "apk_path": str(DEFAULT_APK_PATH),
    "apk_url": DEFAULT_APK_URL,
    "ui_host": DEFAULT_UI_HOST,
    "ui_port": DEFAULT_UI_PORT,
    "auto_start_ui": False,
    "roblox_package": ROBLOX_PACKAGE,
}


def load_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cfg.update(loaded)
        except Exception:
            pass
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Android runtime / Waydroid management
# ---------------------------------------------------------------------------


def ensure_supported(info: SystemInfo, logger: logging.Logger) -> None:
    if not info.supported:
        msg = info.support_message or "This device is not supported."
        logger.error(msg)
        raise SystemExit(2)


def waydroid_status_text() -> str:
    if not command_exists("waydroid"):
        return "waydroid: not installed"
    try:
        proc = run_cmd(["waydroid", "status"], timeout=10)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        return out or err or "waydroid: status unavailable"
    except Exception as e:
        return f"waydroid: status check failed ({e})"


def check_runtime(info: SystemInfo, logger: logging.Logger) -> int:
    print(f"{APP_NAME} {APP_VERSION} - device check")
    print("-" * 60)
    print(f"Supported:          {'yes' if info.supported else 'no'}")
    print(f"OS:                 {info.distro_name} ({info.os_system})")
    print(f"Distro family:      {info.family}")
    print(f"Architecture:       {info.arch} ({info.machine})")
    print(f"Python:             {info.python_version}")
    print(f"Waydroid installed: {'yes' if info.waydroid_installed else 'no'}")
    print(f"Waydroid init:      {'yes' if info.waydroid_initialized else 'no'}")
    print(f"Waydroid session:   {'running' if info.waydroid_session_running else 'not running'}")
    print(f"Binder available:   {'yes' if info.binder_available else 'no'}")
    print(f"Vulkan:             {'yes' if info.vulkan_available else 'no'}")
    print(f"OpenGL:             {'yes' if info.opengl_available else 'no'}")
    print(f"ADB installed:      {'yes' if info.adb_installed else 'no'}")
    print(f"Config file:        {CONFIG_FILE}")
    print(f"Data dir:           {DATA_DIR}")
    if info.package_hint:
        print(f"Package hint:       {info.package_hint}")
    if info.support_message:
        print(f"Support message:    {info.support_message}")

    print("\nRuntime status:")
    print(textwrap.indent(waydroid_status_text(), "  "))

    if not info.supported:
        logger.error(info.support_message)
        return 2

    problems: list[str] = []
    if not info.waydroid_installed:
        problems.append("Waydroid is not installed. Install it to use the Android runtime.")
    if info.waydroid_installed and not info.waydroid_initialized:
        problems.append("Waydroid is not initialized. Run: sudo waydroid init")
    if info.waydroid_installed and not info.waydroid_session_running:
        problems.append("Waydroid session is not running. Run: waydroid session start (or start the Waydroid service).")
    if not info.binder_available:
        problems.append("Binder device not detected. Waydroid needs binder support (kernel/module).")

    if problems:
        print("\nReadiness issues:")
        for p in problems:
            print(f"  - {p}")
        print("\nXyvora uses an Android runtime (Waydroid) to run the Roblox Android client on Linux.")
        return 1

    print("\nReady: Android runtime looks available for launch.")
    return 0


def setup_runtime(info: SystemInfo, logger: logging.Logger, assume_yes: bool = False) -> int:
    ensure_supported(info, logger)
    print(f"{APP_NAME} setup - Android Runtime (Waydroid)")
    print(f"Detected: {info.distro_name} ({info.arch})")
    print(f"Suggested install: {info.package_hint}")

    if not info.waydroid_installed:
        print("\nWaydroid is missing. Install it with your package manager, then re-run:")
        print(f"  {info.package_hint}")
        print("After install, initialize Waydroid:")
        print("  sudo waydroid init")
        return 1

    if not info.waydroid_initialized:
        cmd = ["sudo", "waydroid", "init"]
        print("\nWaydroid needs initialization.")
        print(f"Command: {' '.join(cmd)}")
        if assume_yes:
            logger.info("Running: %s", " ".join(cmd))
            proc = subprocess.run(cmd)
            return proc.returncode
        print("Re-run with --yes to execute this command, or run it manually.")
        return 1

    if not info.waydroid_session_running:
        print("\nWaydroid session is not running.")
        print("Start it with one of:")
        print("  waydroid session start")
        print("  sudo systemctl start waydroid-container")
        return 1

    print("\nWaydroid looks initialized and running.")
    return 0


# ---------------------------------------------------------------------------
# APK / launch
# ---------------------------------------------------------------------------


def resolve_apk_path(cfg: dict[str, Any], cli_apk: str | None) -> Path:
    if cli_apk:
        return Path(cli_apk).expanduser().resolve()
    return Path(str(cfg.get("apk_path", DEFAULT_APK_PATH))).expanduser().resolve()


def install_apk(apk_path: Path, logger: logging.Logger, dry_run: bool = False) -> int:
    if not apk_path.exists():
        logger.error("APK not found: %s", apk_path)
        logger.error("Provide a Roblox Android APK via --apk or place it at the configured apk_path.")
        return 1
    cmd = ["waydroid", "app", "install", str(apk_path)]
    print(f"Installing APK: {apk_path}")
    if dry_run:
        print(f"[dry-run] {' '.join(cmd)}")
        return 0
    proc = subprocess.run(cmd)
    return proc.returncode


def launch_roblox(info: SystemInfo, cfg: dict[str, Any], args: argparse.Namespace, logger: logging.Logger) -> int:
    ensure_supported(info, logger)

    apk_path = resolve_apk_path(cfg, args.apk)
    package = args.package or str(cfg.get("roblox_package", ROBLOX_PACKAGE))
    dry_run = bool(args.dry_run)

    if not info.waydroid_installed:
        msg = "Waydroid is not installed. Run 'python3 Main.py setup' for guidance."
        if dry_run:
            logger.warning(msg + " (continuing due to --dry-run)")
        else:
            logger.error(msg)
            return 1

    # Start session if requested/needed (best-effort).
    if not info.waydroid_session_running:
        print("Waydroid session is not running.")
        if args.start_session:
            start_cmd = ["waydroid", "session", "start"]
            if dry_run:
                print(f"[dry-run] {' '.join(start_cmd)}  # should be run in background")
            else:
                print("Starting Waydroid session in background...")
                try:
                    subprocess.Popen(start_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(3)
                except Exception as e:
                    logger.error("Failed to start waydroid session: %s", e)
                    return 1
        else:
            msg = "Run with --start-session or start Waydroid manually."
            if dry_run:
                print(f"[dry-run] {msg}")
            else:
                print(msg)
                return 1

    if args.install_apk or args.apk:
        rc = install_apk(apk_path, logger, dry_run=dry_run)
        if rc != 0:
            return rc

    launch_cmd = ["waydroid", "app", "launch", package]
    print(f"Launching {package} via Android runtime (Waydroid)...")
    if dry_run:
        print(f"[dry-run] {' '.join(launch_cmd)}")
        return 0

    proc = subprocess.run(launch_cmd)
    if proc.returncode != 0:
        logger.error("Failed to launch %s. Is the Roblox APK installed in Waydroid?", package)
        logger.error("Try: python3 Main.py run --apk /path/to/roblox.apk --install-apk")
        return proc.returncode

    print("Launch command sent successfully.")
    return 0


# ---------------------------------------------------------------------------
# UI server
# ---------------------------------------------------------------------------


def run_ui(info: SystemInfo, cfg: dict[str, Any], args: argparse.Namespace, logger: logging.Logger) -> int:
    if not UI_DIR.exists():
        logger.error("UI directory not found: %s", UI_DIR)
        return 1
    host = args.host or str(cfg.get("ui_host", DEFAULT_UI_HOST))
    port = int(args.port or cfg.get("ui_port", DEFAULT_UI_PORT))

    # Reuse existing server.py for the preview.
    server_py = ROOT / "server.py"
    if not server_py.exists():
        logger.error("server.py not found at %s", server_py)
        return 1

    cmd = [sys.executable, str(server_py), "--host", host, "--port", str(port)]
    print(f"Starting {APP_NAME} UI on http://{host}:{port}")
    if not info.supported:
        print(f"Warning: {info.support_message}")
    logger.info("Running: %s", " ".join(cmd))
    try:
        proc = subprocess.run(cmd)
        return proc.returncode
    except KeyboardInterrupt:
        print("\nUI server stopped.")
        return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Main.py",
        description=f"{APP_NAME} - Roblox Linux client launcher using an Android runtime (Waydroid).",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Check device support and runtime readiness")
    p_check.add_argument("--json", action="store_true", help="Output system info as JSON")

    p_setup = sub.add_parser("setup", help="Guide/setup Android runtime (Waydroid)")
    p_setup.add_argument("--yes", action="store_true", help="Run safe setup commands when possible")

    p_status = sub.add_parser("status", help="Show Waydroid/runtime status")
    p_status.add_argument("--json", action="store_true", help="Output as JSON")

    p_ui = sub.add_parser("ui", help="Start the local UI preview server")
    p_ui.add_argument("--host", default=None, help=f"Host to bind (default: {DEFAULT_UI_HOST})")
    p_ui.add_argument("--port", type=int, default=None, help=f"Port to bind (default: {DEFAULT_UI_PORT})")

    p_run = sub.add_parser("run", help="Launch Roblox through Android runtime (Waydroid)")
    p_run.add_argument("--apk", default=None, help="Path to Roblox APK to install/use")
    p_run.add_argument("--install-apk", action="store_true", help="Install APK before launch")
    p_run.add_argument("--package", default=None, help=f"Android package name (default: {ROBLOX_PACKAGE})")
    p_run.add_argument("--start-session", action="store_true", help="Try to start Waydroid session if not running")
    p_run.add_argument("--dry-run", action="store_true", help="Print actions without executing launch/install commands")

    p_cfg = sub.add_parser("config", help="Show or initialize config")
    p_cfg.add_argument("--init", action="store_true", help="Write default config file")
    p_cfg.add_argument("--json", action="store_true", help="Output config as JSON")

    return parser


def cmd_status(info: SystemInfo, as_json: bool) -> int:
    payload = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "system": asdict(info),
        "waydroid_status": waydroid_status_text(),
    }
    if as_json:
        print(json.dumps(payload, indent=2))
        return 0 if info.supported else 2
    print(f"{APP_NAME} status")
    print(f"Supported: {info.supported}")
    print(f"Device: {info.distro_name} / {info.arch}")
    print(f"Android runtime: {'ready' if info.waydroid_installed and info.waydroid_session_running else 'not ready'}")
    print("\n" + waydroid_status_text())
    return 0 if info.supported else 2


def cmd_config(cfg: dict[str, Any], init: bool, as_json: bool, logger: logging.Logger) -> int:
    if init:
        save_config(cfg)
        logger.info("Config written to %s", CONFIG_FILE)
    if as_json:
        print(json.dumps(cfg, indent=2))
    else:
        print(f"Config file: {CONFIG_FILE}")
        print(json.dumps(cfg, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logger = setup_logging(verbose=bool(getattr(args, "verbose", False)))

    cfg = load_config()
    info = detect_system()

    if args.command == "check":
        if args.json:
            print(json.dumps(asdict(info), indent=2))
            return 0 if info.supported else 2
        return check_runtime(info, logger)

    if args.command == "setup":
        return setup_runtime(info, logger, assume_yes=bool(args.yes))

    if args.command == "status":
        return cmd_status(info, as_json=bool(args.json))

    if args.command == "ui":
        return run_ui(info, cfg, args, logger)

    if args.command == "run":
        return launch_roblox(info, cfg, args, logger)

    if args.command == "config":
        return cmd_config(cfg, init=bool(args.init), as_json=bool(args.json), logger=logger)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
