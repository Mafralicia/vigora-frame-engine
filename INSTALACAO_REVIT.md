# Plugin Vigora no Revit — instalação

Versões: **Revit 2024, 2025 e 2026** · **pyRevit 5.x** · **Python 3.11+** (o motor roda fora do Revit).
A raiz deste repositório **é a extensão pyRevit**: clonou na pasta de extensões → *Reload* → aba **Vigora**.

## Instalação (uma vez por computador)

1. Instale o **Python 3.12** (python.org) marcando *Add python.exe to PATH*.
2. Instale o **pyRevit 5** e o **Git** (git-scm.com).
3. No PowerShell:
   ```
   git clone https://github.com/Mafralicia/vigora-frame-engine.git "$env:APPDATA\pyRevit\Extensions\Vigora.extension"
   ```
   (repositório privado: o Git abre o navegador para você autorizar na primeira vez)
4. No Revit: aba **pyRevit → Reload**. Aparece a aba **Vigora**.
5. No primeiro clique em *Verificar* ou *Gerar*, o plugin encontra o Python sozinho e, se faltar alguma
   biblioteca do motor, pergunta e instala (1–3 min). Alternativa: rodar `instalar.ps1` da pasta clonada.

**Atualizar:** `git -C "$env:APPDATA\pyRevit\Extensions\Vigora.extension" pull` e *Reload* no pyRevit.

**Não use** o gerenciador de extensões do pyRevit (*Install custom extension*) com o repositório privado:
ele não tem como autenticar e falha com "could not decrypt tls message". O `git clone` acima resolve.

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
As escolhas ficam em `<modelo>.vigora.json` ao lado do .rvt.

## Pontos a confirmar no primeiro teste real
- Telhado: `SlopeAngle` da borda lido como tangente — conferir a inclinação na verificação.
- Pisos: contorno lido do esboço do piso (Revit 2022+).
- Peças geradas são *DirectShape* (Modelo genérico) — não editar à mão; gerar de novo.
