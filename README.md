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

## Project structure

```text
.
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