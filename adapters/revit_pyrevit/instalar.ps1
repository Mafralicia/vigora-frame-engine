# Instalação do plugin Vigora Frame Engine (Revit 2024-2026 + pyRevit 5).
# Uso (PowerShell, na pasta do repositório):  powershell -ExecutionPolicy Bypass -File adapters\revit_pyrevit\instalar.ps1
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
Write-Host "Repositório: $repo"

# 1) Python 3.11+ (o motor roda fora do Revit)
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { throw "Python 3.11+ não encontrado. Instale em https://www.python.org e marque 'Add to PATH'." }
Write-Host "Python: $py"
& $py -m pip install --upgrade pip | Out-Null
& $py -m pip install -e "$repo"

# 2) pyRevit (https://github.com/pyrevitlabs/pyRevit/releases) — versão 5.x para Revit 2025/2026
$pyrevit = (Get-Command pyrevit -ErrorAction SilentlyContinue).Source
if (-not $pyrevit) { throw "pyRevit não encontrado. Instale o pyRevit 5 e rode este script de novo." }

# 3) Registra a extensão Vigora
& pyrevit extensions paths add "$repo\adapters\revit_pyrevit"

# 4) Grava o config.json com os caminhos desta máquina
$cfg = @{ python = $py.Replace("\", "/"); repo = $repo.Replace("\", "/") } | ConvertTo-Json
Set-Content -Path "$repo\adapters\revit_pyrevit\config.json" -Value $cfg -Encoding UTF8

# 5) Teste rápido do motor
& $py -c "import sys; sys.path.insert(0, r'$repo\src'); import vigora_frame; print('motor OK')"
Write-Host "Pronto. Abra o Revit: aparece a aba 'Vigora'. (Se não aparecer: pyRevit > Reload)"
