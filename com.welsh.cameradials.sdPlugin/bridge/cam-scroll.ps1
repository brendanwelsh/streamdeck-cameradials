param([string]$action='next',[int]$index=-1)
# Camera scroller used by the optional Home Assistant bridge (cam-server.ps1).
# rotate = next/prev feed, toggle = open/close, show = open a specific index (HA owns the index).
# Reads cameras / NVR / mpv path from ..\config.json so nothing is hard-wired.
$ErrorActionPreference = 'Stop'
$cfgPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'config.json'
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
$mpv = if ($cfg.mpv) { $cfg.mpv } else { 'mpvnet.exe' }
$nvr = $cfg.nvr
$cams = @($cfg.cameras)
if (-not $cams -or $cams.Count -eq 0) { Write-Error 'No cameras configured in config.json'; return }

$state = Join-Path $PSScriptRoot 'cam-index.txt'
$idx = if (Test-Path $state) { [int](Get-Content $state) } else { 0 }
if ($idx -ge $cams.Count) { $idx = 0 }
$running = Get-Process mpvnet -ErrorAction SilentlyContinue

if ($action -eq 'toggle') {
  if ($running) { Stop-Process -Name mpvnet -Force -ErrorAction SilentlyContinue; return }   # close
  # else fall through to open the current feed
} elseif ($action -eq 'show')  { if ($index -ge 0) { $idx = $index % $cams.Count } }          # open a specific feed by index
elseif ($action -eq 'next')    { $idx = ($idx + 1) % $cams.Count }
elseif ($action -eq 'prev')    { $idx = ($idx - 1 + $cams.Count) % $cams.Count }

$idx | Set-Content $state
Start-Process $mpv -ArgumentList ('"rtsps://{0}/{1}?enableSrtp"' -f $nvr, $cams[$idx].id)
