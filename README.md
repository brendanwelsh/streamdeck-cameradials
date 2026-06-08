# streamdeck-cameradials

> Elgato **Stream Deck+** dial plugin (`com.welsh.cameradials`) — a **UniFi Protect camera scroller**.
> **Rotate** the dial to switch cameras, **press** to open / close a maximized live viewer.

A no-build, raw-WebSocket Stream Deck plugin (Node 24). Everything personal — the camera list, the
NVR address, and the mpv path — is **configurable** (Property Inspector or `config.json`), so anyone
can use it.

> Previously this plugin also contained an "Audio Output" dial action. That has been split into its
> own plugin: **[streamdeck-audioswap](https://github.com/brendanwelsh/streamdeck-audioswap)**.

## What it does
- **Rotate** → switch between your configured UniFi Protect cameras.
- **Push** → open / close a maximized live viewer.
- Streams `rtsps://<NVR>/<streamId>?enableSrtp` into **mpv.net**. The first open launches mpv with a
  JSON **IPC pipe** (`\\.\pipe\mpv-cam`); subsequent switches `loadfile` **in place** (instant, no
  relaunch) with a centered "Swapping to …" overlay. The dial LCD shows the camera name +
  `● LIVE` / `swapping…`. Opening always starts on the first camera, maximized on the primary monitor.

## Install
1. Copy the `com.welsh.cameradials.sdPlugin` folder into
   `%APPDATA%\Elgato\StreamDeck\Plugins\` and restart the Stream Deck app.
   (No `npm install` / build step — Node 24 ships a global `WebSocket`.)
2. Add the **Camera Scroller** action to a Stream Deck+ dial.
3. Configure it (below).

## Configure
Two ways — pick either (Property Inspector wins if both are set):

### A. Property Inspector (recommended)
Select the dial in the Stream Deck app and fill in:
- **NVR address** — `host:port` of your UniFi Protect controller (default RTSPS port `7441`).
- **mpv.net path** — full path to `mpvnet.exe`, or just `mpvnet.exe` if it's on your PATH.
- **Cameras** — one per line, `NAME = streamId`.

### B. config.json
Copy `com.welsh.cameradials.sdPlugin/config.json.example` to `config.json` in the same folder and
edit it:
```json
{
  "nvr": "192.168.1.10:7441",
  "mpv": "mpvnet.exe",
  "cameras": [
    { "name": "FRONT DOOR", "id": "xxxxxxxxxxxxxxxx" },
    { "name": "BACKYARD",   "id": "yyyyyyyyyyyyyyyy" }
  ]
}
```
`config.json` is gitignored (it holds your camera layout + internal NVR address). It's also read by
the optional Home Assistant bridge.

### Finding a camera's stream id
The `id` is the UniFi Protect camera/stream id used in the RTSPS URL. To get it: open UniFi Protect →
camera **Settings → Advanced / RTSP**, enable an RTSP(S) stream, and copy the id segment from the
generated `rtsps://<nvr>:7441/<id>?enableSrtp` URL. (The id is the part after the port.)

## Dependencies
- **[mpv.net](https://github.com/mpvnet-player/mpv.net)** — the camera viewer (`mpvnet.exe`).
- A **UniFi Protect** controller with RTSP(S) streaming enabled, reachable on your LAN.
- Windows 10/11, Stream Deck software 6.4+, a Stream Deck+ (encoder/dial hardware).

## Optional: Home Assistant bridge
`com.welsh.cameradials.sdPlugin/bridge/` lets Home Assistant (or anything on the LAN) drive the same
mpv viewer over HTTP, so a dashboard/automation can scroll the cameras too. It reads the same
`config.json`.

```
HA ──HTTP──> cam-server.ps1 (TcpListener :8765 on the PC)
             /cam/next  /cam/prev  /cam/toggle  /cam/scroll?ticks=  /cam/show?i=  /ping
             → cam-scroll.ps1 (same mpv scroller, config-driven)
```
Set `bridgePort` and `bridgeLanCidr` in `config.json`, then run once from an **elevated** PowerShell:
```
powershell -ExecutionPolicy Bypass -File .\bridge\cam-server-setup.ps1
```
That adds a LAN-scoped firewall rule for the port and a logon task that starts the listener hidden.

## ⚠️ Before making this repo public
This repo is **private** for a reason: while the working tree is de-personalized (real cameras live in
the gitignored `config.json`, and `config.json.example` ships placeholders), the **git history still
contains real camera stream ids and an internal NVR IP** from earlier commits. Before going public:
- **Scrub history** (e.g. `git filter-repo`) to purge the old IDs/IP, **or**
- **Re-init** a fresh repo from the current tree (drop history) and force-push / re-create the remote.

Then audit once more for any private values before flipping visibility.

## Layout
- `com.welsh.cameradials.sdPlugin/plugin.js` — the plugin (config load + mpv/IPC logic)
- `com.welsh.cameradials.sdPlugin/manifest.json` — the Camera Scroller encoder action
- `com.welsh.cameradials.sdPlugin/pi/scroller.html` — Property Inspector (settings UI)
- `com.welsh.cameradials.sdPlugin/config.json.example` — config template
- `com.welsh.cameradials.sdPlugin/scripts/cam-center.ps1` — maximizes the mpv window on the primary monitor
- `com.welsh.cameradials.sdPlugin/bridge/` — optional Home Assistant HTTP bridge
- `com.welsh.cameradials.sdPlugin/layouts/` — dial LCD layouts

## Related
- **[streamdeck-audioswap](https://github.com/brendanwelsh/streamdeck-audioswap)** — the audio-output
  swap dial, split out of this plugin.
- **ulanzi-camera-switcher** — ports this camera scroller onto the Ulanzi dial.
