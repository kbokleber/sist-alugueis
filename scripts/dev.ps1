# Sobe o ambiente de desenvolvimento local (backend + frontend).
#
# Uso:
#   .\scripts\dev.ps1
#   .\scripts\dev.ps1 -BackendOnly
#   .\scripts\dev.ps1 -FrontendOnly
#
# Os logs ficam em backend\_bk.log e backend\_bk.err.log (fora do Git).

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'frontend'

function Test-Port([int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $client.Connect('127.0.0.1', $Port)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

if (-not $FrontendOnly) {
    if (Test-Port 8000) {
        Write-Host '[dev] backend ja rodando na porta 8000' -ForegroundColor DarkGray
    } else {
        Write-Host '[dev] subindo backend (uvicorn :8000)...' -ForegroundColor Cyan
        $env:DATABASE_URL = 'sqlite+aiosqlite:///./dev.db'
        Start-Process -FilePath (Join-Path $Backend 'venv\Scripts\python.exe') `
            -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000' `
            -WorkingDirectory $Backend `
            -RedirectStandardOutput (Join-Path $Backend '_bk.log') `
            -RedirectStandardError (Join-Path $Backend '_bk.err.log') `
            -WindowStyle Hidden

        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 1
            if (Test-Port 8000) { break }
        }
        if (Test-Port 8000) {
            Write-Host '[dev] backend pronto em http://127.0.0.1:8000' -ForegroundColor Green
        } else {
            Write-Host '[dev] FALHOU ao subir o backend. Veja backend\_bk.err.log' -ForegroundColor Red
            exit 1
        }
    }
}

if (-not $BackendOnly) {
    if (Test-Port 5173) {
        Write-Host '[dev] frontend ja rodando na porta 5173' -ForegroundColor DarkGray
    } else {
        Write-Host '[dev] subindo frontend (vite :5173)...' -ForegroundColor Cyan
        Start-Process -FilePath 'npm.cmd' -ArgumentList 'run', 'dev' `
            -WorkingDirectory $Frontend -WindowStyle Hidden
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 1
            if (Test-Port 5173) { break }
        }
        if (Test-Port 5173) {
            Write-Host '[dev] frontend pronto em http://127.0.0.1:5173' -ForegroundColor Green
        } else {
            Write-Host '[dev] FALHOU ao subir o frontend.' -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ''
Write-Host '[dev] tudo pronto:' -ForegroundColor Green
if (-not $FrontendOnly) { Write-Host '  API      http://127.0.0.1:8000/docs' }
if (-not $BackendOnly) { Write-Host '  App      http://127.0.0.1:5173' }
