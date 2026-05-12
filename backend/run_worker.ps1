$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"

New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null

function Rotate-Log {
  param(
    [string]$Path,
    [int64]$MaxBytes = 2147483648,
    [int]$Keep = 5
  )
  if (-not (Test-Path $Path)) { return }
  $file = Get-Item $Path
  if ($file.Length -le $MaxBytes) { return }

  for ($i = $Keep; $i -ge 1; $i--) {
    $src = "$Path.$i"
    $dst = "$Path." + ($i + 1)
    if (Test-Path $src) {
      if ($i -eq $Keep) {
        Remove-Item -LiteralPath $src -Force
      } else {
        Move-Item -LiteralPath $src -Destination $dst -Force
      }
    }
  }
  Move-Item -LiteralPath $Path -Destination "$Path.1" -Force
}

Rotate-Log -Path ".\logs\worker.log"

$workerCmd = '".\.venv\Scripts\celery.exe" -A app.workers.celery_app:celery_app worker --loglevel=info --pool=solo 2>&1'
cmd /c $workerCmd |
  ForEach-Object { "$_" } |
  Tee-Object -FilePath ".\logs\worker.log" -Append
