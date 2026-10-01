# Publica este repositório no GitHub como PRIVADO (uma vez).
# Requisitos: Git (git-scm.com) e GitHub CLI (cli.github.com). Uso, na pasta do repositório:
#   powershell -ExecutionPolicy Bypass -File publicar_no_github.ps1
$ErrorActionPreference = "Stop"
$nome = "vigora-frame-engine"
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "Instale o GitHub CLI: https://cli.github.com" }
gh auth status 2>$null; if ($LASTEXITCODE -ne 0) { gh auth login --web }
gh repo create $nome --private --source . --remote origin --push --description "Vigora Frame Engine: framing wood/steel frame, pranchas NBR e plugin Revit"
Write-Host "Publicado (privado). Clone em outra máquina com: gh repo clone $nome"
