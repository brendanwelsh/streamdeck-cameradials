# Optional bridge listener: lets Home Assistant (or anything on the LAN) trigger the local camera
# scroller over HTTP, so a dashboard / automation can drive the same mpv viewer as the dial.
# Raw TcpListener on 0.0.0.0:<port> (no urlacl/admin needed). Parses the GET request line and routes:
#   /cam/next  /cam/prev  /cam/toggle      -> cam-scroll.ps1
#   /cam/scroll?ticks=<n>                  -> next/prev by sign of ticks
#   /cam/show?i=<index>                    -> open a specific feed (HA owns the index)
#   /ping                                  -> health check
# Port + LAN come from ..\config.json (bridgePort).
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$cfg  = Get-Content (Join-Path (Split-Path $root -Parent) 'config.json') -Raw | ConvertFrom-Json
$port = if ($cfg.bridgePort) { [int]$cfg.bridgePort } else { 8765 }
$log  = Join-Path $root 'cam-server.log'
function Log($m){ "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" | Add-Content -Path $log -Encoding utf8 }

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $port)
$listener.Start()
Log "cam-server started on :$port"

while ($true) {
    try {
        $client = $listener.AcceptTcpClient()
        $stream = $client.GetStream()
        $reader = [System.IO.StreamReader]::new($stream)
        $line = $reader.ReadLine()          # e.g. "GET /cam/next HTTP/1.1"
        $route = ''
        if ($line -match '^[A-Z]+\s+(\S+)\s') { $route = $matches[1] }
        $path = ($route -split '\?')[0]
        $query = if ($route -match '\?(.*)$') { $matches[1] } else { '' }
        Log "req $route"
        $body = 'ok'
        switch -Regex ($path) {
            '^/cam/(next|prev|toggle)$' {
                $act = $matches[1]
                Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"$root\cam-scroll.ps1",$act)
            }
            '^/cam/scroll$' {
                # dial rotation: ticks>0 -> next feed, ticks<0 -> prev feed
                $ticks = 1
                if ($query -match 'ticks=(-?\d+)') { $ticks = [int]$matches[1] }
                $act = if ($ticks -lt 0) { 'prev' } else { 'next' }
                Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"$root\cam-scroll.ps1",$act)
            }
            '^/cam/show$' {
                # HA owns the index and tells us exactly which feed to open
                $i = 0
                if ($query -match 'i=(\d+)') { $i = [int]$matches[1] }
                Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"$root\cam-scroll.ps1",'show',$i)
            }
            '^/ping$' { $body = 'pong' }
            default   { $body = 'unknown route' }
        }
        $resp = "HTTP/1.1 200 OK`r`nContent-Type: text/plain`r`nContent-Length: $($body.Length)`r`nConnection: close`r`n`r`n$body"
        $bytes = [System.Text.Encoding]::ASCII.GetBytes($resp)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush()
        $client.Close()
    } catch {
        Log "ERR $($_.Exception.Message)"
        try { $client.Close() } catch {}
    }
}
