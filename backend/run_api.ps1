param(
  [switch]$Reload
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"

New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null

$reloadArg = if ($Reload) { "--reload" } else { "" }
$pythonCmd = '".\.venv\Scripts\python.exe" -X utf8 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 ' + $reloadArg + ' 2>&1'
cmd /c $pythonCmd |
  ForEach-Object { "$_" } |
  Tee-Object -FilePath ".\logs\backend.log" -Append
