# Vigora Frame Engine — instalação do plugin no Revit (pyRevit 5, Revit 2024-2026).
# A raiz deste repositório É a extensão pyRevit. Forma recomendada (uma vez por computador):
#   git clone https://github.com/Mafralicia/vigora-frame-engine.git "$env:APPDATA\pyRevit\Extensions\Vigora.extension"
#   powershell -ExecutionPolicy Bypass -File "$env:APPDATA\pyRevit\Extensions\Vigora.extension\instalar.ps1"
$ErrorActionPreference = "Stop"
$ext = (Resolve-Path $PSScriptRoot).Path
Write-Host "Extensão: $ext"

# 1) a pasta precisa terminar em .extension para o pyRevit reconhecer
if (-not $ext.EndsWith(".extension")) {
  throw "A pasta precisa se chamar 'Vigora.extension'. Clone com: git clone <url> `"$env:APPDATA\pyRevit\Extensions\Vigora.extension`""
}

# 2) Python 3.11+ (o motor roda fora do Revit)
$py = $null
foreach ($c in @("py -3.13", "py -3.12", "py -3.11", "python")) {
  try { $v = Invoke-Expression "$c -c `"import sys; print(sys.version_info[:2] >= (3,11))`"" 2>$null; if ($v -eq "True") { $py = $c; break } } catch {}
}
if (-not $py) { throw "Python 3.11+ não encontrado. Instale em https://www.python.org (marque 'Add python.exe to PATH')." }
Write-Host "Python: $py"

# 3) bibliotecas do motor (no usuário, sem admin)
Invoke-Expression "$py -m pip install --user --disable-pip-version-check -r `"$ext\requirements.txt`""

# 4) se a pasta não está na pasta padrão do pyRevit, registra a pasta-mãe
$padrao = Join-Path $env:APPDATA "pyRevit\Extensions"
$mae = Split-Path $ext -Parent
if ((Resolve-Path $mae).Path -ne (Resolve-Path $padrao -ErrorAction SilentlyContinue).Path) {
  if (Get-Command pyrevit -ErrorAction SilentlyContinue) { pyrevit extensions paths add "$mae" }
  else { Write-Host "Adicione '$mae' em pyRevit > Settings > Custom Extension Directories." }
}

# 5) teste rápido do motor
$env:PYTHONPATH = "$ext\src"
Invoke-Expression "$py -c `"import vigora_frame; print('motor OK')`""
Write-Host "Pronto. No Revit: aba pyRevit > Reload. A aba 'Vigora' aparece."
