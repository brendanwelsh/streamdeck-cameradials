# Bring the mpv.net camera window to the PRIMARY monitor, maximize it, make it topmost + foreground.
# Retries until the window handle is ready (RTSPS streams take a moment to create the window).
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinPos {
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int x, int y, int cx, int cy, uint flags);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@
Add-Type -AssemblyName System.Windows.Forms
$scr = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$TOPMOST = New-Object IntPtr(-1)
for ($i = 0; $i -lt 25; $i++) {
    $p = Get-Process mpvnet -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if ($p) {
        $h = $p.MainWindowHandle
        [WinPos]::ShowWindow($h, 9) | Out-Null                                                  # SW_RESTORE
        [WinPos]::SetWindowPos($h, $TOPMOST, $scr.X + 80, $scr.Y + 80, 1280, 720, 0x0040) | Out-Null  # onto primary, topmost
        Start-Sleep -Milliseconds 120
        [WinPos]::ShowWindow($h, 3) | Out-Null                                                  # SW_MAXIMIZE
        [WinPos]::SetWindowPos($h, $TOPMOST, 0, 0, 0, 0, 0x0003) | Out-Null                     # keep topmost (NOMOVE|NOSIZE)
        [WinPos]::SetForegroundWindow($h) | Out-Null
        break
    }
    Start-Sleep -Milliseconds 150
}
