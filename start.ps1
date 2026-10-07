$runtime = 'C:\Users\yesha\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location -LiteralPath $PSScriptRoot
if (Test-Path -LiteralPath $runtime) { & $runtime server.py } else { python server.py }
