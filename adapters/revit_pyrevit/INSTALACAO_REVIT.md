# Plugin Vigora no Revit — instalação

Versões: **Revit 2024, 2025 e 2026** · **pyRevit 5.x** · **Python 3.11+** (o motor roda fora do Revit).

1. Instale o **Python 3.12** (python.org) marcando *Add python.exe to PATH*.
2. Instale o **pyRevit 5** (github.com/pyrevitlabs/pyRevit/releases) e abra o Revit uma vez.
3. Clone o repositório: `git clone https://github.com/SEU_USUARIO/vigora-frame-engine C:\vigora-frame-engine`
   (ou copie a pasta para `C:\vigora-frame-engine`, sem acento no caminho).
4. No PowerShell, dentro da pasta: `powershell -ExecutionPolicy Bypass -File adapters\revit_pyrevit\instalar.ps1`
   — instala as dependências, registra a extensão e grava o `config.json` com os caminhos.
5. Abra o Revit: aparece a aba **Vigora** (se não aparecer: aba pyRevit → *Reload*).

Instalação manual (sem o script): `pip install -e C:\vigora-frame-engine`; pyRevit → Settings →
*Custom Extension Directories* → adicionar `C:\vigora-frame-engine\adapters\revit_pyrevit`; editar
`adapters\revit_pyrevit\config.json` com o caminho do `python.exe` e do repositório.

## A aba Vigora

| Painel | Botão | O que faz |
|---|---|---|
| Projeto | **Configurar projeto** | sistema wood/steel, formato A1/A0, dados da legenda (cliente, RT, CREA, ART), padrão de treliça/espaçamento/beiral |
| Projeto | **Tipos de parede** | marca quais tipos do Revit são externos e portantes |
| Framing | **Verificar modelo** | checagem rápida, sem criar peças; lista com **Mostrar no modelo** (seleciona e dá zoom) |
| Framing | **Gerar framing** | projeto inteiro → peças 3D no modelo + planilha, pranchas, arquivos de máquina; 2ª vez atualiza só o que mudou |
| Framing | **Últimos resultados** | reabre a lista de erros sem rodar de novo |
| Elementos | **Telhado** | (com telhado selecionado) apoio, tipo de treliça, espaçamento, recuo da mestra |
| Elementos | **Paredes** | (com paredes selecionadas) portante / não portante / externa / interna |
| Elementos | **Entrepiso** | (com o piso selecionado) direção das vigas |
| Elementos | **Caixa d'água** | adicionar (automática ou clicando), trocar modelo, remover |
| Saídas | **Pranchas** | gera A1 ou A0 e abre o PDF |
| Saídas | **Abrir saídas** | pasta `<modelo>_vigora` ao lado do .rvt |

Nada precisa ser selecionado para Verificar/Gerar: vale para o **projeto inteiro**.
As escolhas ficam em `<modelo>.vigora.json` ao lado do .rvt (pode ir para o controle de versão junto).

## Primeiro teste (pontos a confirmar no Revit real)

- Telhado: o valor de `SlopeAngle` da borda é lido como tangente (subida/percurso). Confirmar a inclinação
  que aparece na verificação; se vier errada, avisar (1 linha a corrigir em `vigora_revit.py`).
- Pisos: contorno lido do esboço do piso (Revit 2022+).
- Peças geradas são *DirectShape* (Modelo genérico) — não editar à mão; gerar de novo.
