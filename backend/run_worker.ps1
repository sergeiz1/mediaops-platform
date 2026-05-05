$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"

New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null

$workerCmd = '".\.venv\Scripts\celery.exe" -A app.workers.celery_app:celery_app worker --loglevel=info --pool=solo 2>&1'
cmd /c $workerCmd |
  ForEach-Object { "$_" } |
  Tee-Object -FilePath ".\logs\worker.log" -Append
