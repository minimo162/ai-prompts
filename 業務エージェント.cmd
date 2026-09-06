@echo off
setlocal DisableDelayedExpansion
set "AI_AGENT_SOURCE=%~dp0"
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -STA -Command "$ErrorActionPreference='Stop'; try { $source=$env:AI_AGENT_SOURCE; $app=Join-Path $source 'App.ps1'; if (-not (Test-Path -LiteralPath $app -PathType Leaf)) { if (Test-Path -LiteralPath $source -PathType Container) { throw 'Source App.ps1 is missing. Check the shared release.' }; $local=Join-Path $env:LOCALAPPDATA 'AiPromptsAgent'; $p=Get-Content -LiteralPath (Join-Path $local 'app\current.json') -Raw -Encoding UTF8 | ConvertFrom-Json; if ($p.release -cnotmatch '^[0-9]+\.[0-9]+\.[0-9]+-[a-f0-9]{64}$' -or $p.app_sha256 -cnotmatch '^[a-f0-9]{64}$') { throw 'Invalid local release metadata.' }; $app=Join-Path $local ('app\'+$p.release+'\App.ps1'); if ((Get-FileHash -LiteralPath $app -Algorithm SHA256).Hash.ToLowerInvariant() -cne $p.app_sha256) { throw 'Local release integrity check failed.' } }; & $app -Mode Bootstrap -SourcePath $source; if (-not $?) { exit 1 } } catch { Write-Host $_.Exception.Message; exit 1 }"
set "AI_AGENT_EXIT=%ERRORLEVEL%"
if not "%AI_AGENT_EXIT%"=="0" pause
endlocal & exit /b %AI_AGENT_EXIT%
