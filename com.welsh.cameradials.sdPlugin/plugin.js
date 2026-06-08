"use strict";
const fs = require("fs");
const path = require("path");
const net = require("net");
const { spawn, exec } = require("child_process");

const DIR = __dirname;
const IPC_PIPE = "\\\\.\\pipe\\mpv-cam";

function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : null; }
const PORT = arg("-port");
const PLUGIN_UUID = arg("-pluginUUID");
const REGISTER_EVENT = arg("-registerEvent");

// ---------------------------------------------------------------------------
// Config. Source of truth (highest priority first):
//   1. Per-action Stream Deck settings (set in the Property Inspector)
//   2. config.json next to this file  (also read by the optional HA bridge)
//   3. built-in safe defaults
// Nothing here is hard-wired to a specific person's cameras / NVR / paths.
// ---------------------------------------------------------------------------
const DEFAULTS = { nvr: "", mpv: "mpvnet.exe", cameras: [] };

function readFileConfig() {
  try { return JSON.parse(fs.readFileSync(path.join(DIR, "config.json"), "utf8")); }
  catch (e) { return {}; }
}
// "FRONT DOOR = abc123" per line -> [{ n, id }]; blank lines and #comments ignored
function parseCamsText(text) {
  if (!text) return [];
  return String(text).split(/\r?\n/).map(l => l.trim())
    .filter(l => l && !l.startsWith("#"))
    .map(l => { const i = l.indexOf("="); if (i < 0) return null;
      const n = l.slice(0, i).trim(), id = l.slice(i + 1).trim();
      return n && id ? { n, id } : null; })
    .filter(Boolean);
}
function normCams(arr) {
  if (!Array.isArray(arr)) return [];
  return arr.map(c => ({ n: (c.n || c.name || "").trim(), id: (c.id || "").trim() }))
            .filter(c => c.n && c.id);
}

let NVR = DEFAULTS.nvr, MPV = DEFAULTS.mpv, CAMS = [];
// merge file config (base) with the live per-action settings (override)
function applyConfig(settings) {
  const file = readFileConfig();
  NVR = (settings && settings.nvr) || file.nvr || DEFAULTS.nvr;
  MPV = (settings && settings.mpv) || file.mpv || DEFAULTS.mpv;
  const fromSettings = parseCamsText(settings && settings.camsText);
  CAMS = fromSettings.length ? fromSettings : normCams(file.cameras);
  if (camIdx >= CAMS.length) camIdx = 0;
}

const CONFIGURED = () => CAMS.length > 0 && NVR;
function camUrl(cam) { return "rtsps://" + NVR + "/" + cam.id + "?enableSrtp"; }

// send one or more mpv JSON IPC commands over the named pipe (no-op if mpv isn't running)
function ipcMany(cmds) {
  try {
    const sock = net.connect(IPC_PIPE, () => { for (const c of cmds) sock.write(JSON.stringify({ command: c }) + "\n"); sock.end(); });
    sock.on("error", () => {});
  } catch (e) {}
}
function showSwapping() { if (CAMS[camIdx]) ipcMany([["show-text", "Swapping to " + CAMS[camIdx].n, 4000]]); }

function dataUri(file) {
  try { return "data:image/png;base64," + fs.readFileSync(path.join(DIR, file)).toString("base64"); }
  catch (e) { return ""; }
}
const ICON_CAM = dataUri("imgs/cctv.png");

const SCROLLER = "com.welsh.cameradials.scroller";

let camIdx = 0, camOpen = false;
const scrollerCtx = new Set();
let ws, openTimer = null;

function send(o) { try { ws.send(JSON.stringify(o)); } catch (e) {} }
function setLayout(ctx) { send({ event: "setFeedbackLayout", context: ctx, payload: { layout: "layouts/camdial.json" } }); }
function setDial(ctx, name, sub, icon) { send({ event: "setFeedback", context: ctx, payload: { name, sub, icon } }); }
function renderCam(status) {
  if (!CONFIGURED()) { scrollerCtx.forEach(c => setDial(c, "SET UP", "open settings", ICON_CAM)); return; }
  const name = camOpen ? CAMS[camIdx].n : "CAMERAS";
  let sub;
  if (!camOpen) sub = "tap to view";
  else if (status === "swapping") sub = "swapping…";
  else sub = "● LIVE";
  scrollerCtx.forEach(c => setDial(c, name, sub, ICON_CAM));
}

// open MAXIMIZED on the PRIMARY monitor with a clean title (komorebi/tilers ignore mpvnet.exe so it won't be tiled)
function maximizeWindow() {
  try { exec('powershell -NoProfile -ExecutionPolicy Bypass -File "' + path.join(DIR, "scripts", "cam-center.ps1") + '"', () => {}); } catch (e) {}
}
let liveTimer = null;
function markLive(ms) { if (liveTimer) clearTimeout(liveTimer); liveTimer = setTimeout(() => { if (camOpen) renderCam("live"); }, ms); }
function openCam(fresh) {
  const cam = CAMS[camIdx];
  if (!cam) return;
  if (fresh) {
    // fresh launch: new window with an IPC pipe so later switches are in-place
    try {
      spawn(MPV, ["--ontop=yes", "--input-ipc-server=" + IPC_PIPE,
        "--osd-font-size=40", "--osd-align-x=center", "--osd-align-y=center",
        "--force-media-title=" + cam.n, "--title=" + cam.n, "--osd-playing-msg=",
        "--geometry=1280x720+960+540", camUrl(cam)],
        { detached: true, stdio: "ignore" }).unref();
    } catch (e) {}
    maximizeWindow();
  } else {
    // already running: switch the feed IN PLACE via IPC (instant, no relaunch) + centered on-screen text
    ipcMany([["show-text", "Swapping to " + cam.n, 4000], ["set_property", "force-media-title", cam.n], ["loadfile", camUrl(cam)]]);
  }
  markLive(fresh ? 1600 : 1100);  // flip dial "swapping…" -> "● LIVE" once the feed should be up
}
function closeCam() { exec("taskkill /IM mpvnet.exe /F", () => {}); }
// debounce mpv launch so rapid scrolling only loads the feed you land on (name updates instantly)
let pendingFresh = false;
function scheduleOpen(fresh) {
  if (fresh) pendingFresh = true;
  if (openTimer) clearTimeout(openTimer);
  openTimer = setTimeout(() => { openTimer = null; const f = pendingFresh; pendingFresh = false; openCam(f); }, 280);
}

applyConfig(null);  // load config.json before the socket opens; settings refine it on willAppear

ws = new WebSocket("ws://127.0.0.1:" + PORT);
ws.addEventListener("open", () => send({ event: REGISTER_EVENT, uuid: PLUGIN_UUID }));
ws.addEventListener("message", (ev) => {
  let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
  const a = m.action, ctx = m.context;
  const settings = m.payload && m.payload.settings;
  switch (m.event) {
    case "willAppear":
      if (a === SCROLLER) { applyConfig(settings); setLayout(ctx); scrollerCtx.add(ctx); renderCam(); }
      break;
    case "didReceiveSettings":
      if (a === SCROLLER) { applyConfig(settings); renderCam(camOpen ? "live" : undefined); }
      break;
    case "willDisappear":
      scrollerCtx.delete(ctx);
      break;
    case "dialRotate":
      if (a === SCROLLER && CONFIGURED()) {
        const t = m.payload && m.payload.ticks ? m.payload.ticks : 0;
        const wasOpen = camOpen;
        camIdx = (camIdx + (t < 0 ? -1 : 1) + CAMS.length) % CAMS.length;
        camOpen = true; renderCam("swapping");                 // instant deck "swapping…"
        if (wasOpen) showSwapping();                            // instant ON-SCREEN "SWAPPING…" overlay
        scheduleOpen(!wasOpen);
      }
      break;
    case "dialDown":
      if (a === SCROLLER && CONFIGURED()) {
        camOpen = !camOpen;
        if (camOpen) { camIdx = 0; renderCam("swapping"); openCam(true); }  // always start on the first camera, maximized
        else { closeCam(); renderCam(); }
      }
      break;
  }
});
