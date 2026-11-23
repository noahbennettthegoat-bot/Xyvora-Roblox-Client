# Xyvora Roblox Client

Xyvora is an early-stage **Roblox client for Linux** project.

This repository currently includes a **localhost web UI preview** that showcases the intended look and feel of the client before native launcher/runtime integration.

## What's in this preview

- **Linux device detection** via `/api/system` (OS, distro, architecture, capabilities)
- **Support for all Linux distros/architectures** in the preview, with a clear unsupported-device message for non-Linux devices
- **Android Runtime (Waydroid)** as the default runtime option, plus Proton/Wine options where applicable
- **Capability-aware UI** that shows runtime/renderer options based on detected device support
- **Multiple themes**: Xyvora, Cipher, Midnight, Ocean (saved in browser local storage)
- **Original triangle-eye cipher logo** for Xyvora branding
- Desktop-style client UI: Home, Discover, Library, Friends, Messages, Settings

## Run the UI locally

### Requirements

- Python 3.9+ (tested with Python 3.11)

### Start the preview server

From the repository root:

```bash
python3 server.py
```

Then open:

```text
http://localhost:3000
```

### Optional arguments

```bash
python3 server.py --host 0.0.0.0 --port 3000
```

- `--host` defaults to `0.0.0.0`
- `--port` defaults to `3000`

## System detection API

The preview server exposes:

```text
GET /api/system
```

It returns detected platform information used by the UI, including:

- supported/unsupported status
- OS/distro/family/version
- architecture
- detected capabilities (Waydroid, Vulkan, OpenGL, Proton, Wine)
- available runtime/renderer options
- package hint for the detected Linux family

## Main launcher (`Main.py`)

`Main.py` is the main Xyvora launcher script. It uses an **Android runtime on Linux (Waydroid)** to run the Roblox Android client - the same general method used by Sober (running Roblox through Android compatibility on Linux).

### Commands

```bash
python3 Main.py check                 # Detect device/support and runtime readiness
python3 Main.py setup                 # Show/setup guidance for Waydroid
python3 Main.py status --json         # Runtime/device status
python3 Main.py ui --port 3000        # Start the UI preview server
python3 Main.py config --init         # Write default config to ~/.config/xyvora/config.json
python3 Main.py run --dry-run --install-apk --apk /path/to/roblox.apk --start-session
python3 Main.py run --install-apk --apk /path/to/roblox.apk --start-session
```

### What `run` does

1. Verifies Linux device support and Waydroid availability
2. Optionally starts a Waydroid session
3. Optionally installs a Roblox Android APK into Waydroid
4. Launches `com.roblox.client` through `waydroid app launch`

> Note: Full launch requires a Linux system with Waydroid/binder support and a Roblox Android APK. Use `--dry-run` to verify the launch flow without executing commands.

## Project structure

```text
.
├── .gitignore
├── Main.py
├── README.md
├── server.py
└── ui/
    ├── app.js
    ├── index.html
    └── styles.css
```

## Notes

- This is a **UI preview** only. Launch/play actions, messaging, and account features are mocked for demonstration.
- Device support is currently focused on **Linux**. Non-Linux devices display an unsupported-device message.
- Runtime detection is best-effort in the preview; full launcher integration will validate/install dependencies.