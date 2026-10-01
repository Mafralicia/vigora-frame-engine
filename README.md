# Vigora Frame Engine

Motor próprio da Vigora que transforma a arquitetura (paredes, aberturas, pisos, coberturas) em **framing completo de wood frame e steel frame**. Ele gera peças com ID, ligações, placas, quantitativo, plano de corte, pranchas, arquivos de fábrica e as peças 3D para o Revit.

> **Status: RASCUNHO.** Catálogo, tabelas de verga, vãos e contraventamento têm valores de **referência** para desenvolvimento. Toda execução sai marcada como RASCUNHO até o engenheiro responsável preencher e aprovar (`approval` e `basis` no ruleset e `approved_by` em cada item do catálogo).

## Estrutura

```
catalog/        perfis, placas, fixadores, preços (YAML/CSV)
rules/          rulesets wood e steel + tabelas de verga (CSV)
limits/         limites de fábrica e transporte
src/vigora_frame/
  model.py        modelo neutro (entrada e saída)
  config.py       catálogo, regras, aprovação
  geometry.py     vetores, facetas de curva, arcos
  engine/         junções, paredes, pisos, coberturas/treliças, curvas e pilares
  validate.py     validações (V-001 ... V-073)
  quantities.py   BOM, consolidado, otimização de corte
  diff.py         atualização por diferença (ID estável)
  revit_bridge.py peças -> sólidos 3D globais para o Revit
  export/         Excel, CSV, DXF, etiquetas (PDF+QR, ZPL), pranchas PDF
  cli.py          linha de comando
adapters/revit_pyrevit/   extensão pyRevit (Exportar, Importar, Gerar framing)
examples/       4 projetos de teste
tests/          70 testes (unitários, propriedade, golden, exportação, Revit simulado)
```

## Instalação

Python 3.11 ou mais novo.

```
pip install pydantic pyyaml shapely openpyxl matplotlib reportlab ezdxf qrcode typer pytest hypothesis
```

## Uso

```
set PYTHONPATH=src            (Windows)   |   export PYTHONPATH=src   (Linux/Mac)
python -m vigora_frame.cli run examples/casa_terrea_wood.json --out out/casa
python -m vigora_frame.cli run examples/salao_de_festas.json --out out/salao --formato A0
python -m vigora_frame.cli diff out/v1/resultado.json out/v2/resultado.json
python -m pytest -q
```

Código de saída 2 = há erros de validação (ver aba `Validacao`).

## Saídas por projeto

| Arquivo | Conteúdo |
|---|---|
| `pranchas_A1.pdf` (ou `_A0`) | pranchas no padrão brasileiro com legenda Vigora (ver abaixo) |
| `pranchas_rapidas_A3.pdf` | versão rápida para conferência na tela |
| `quantitativo.xlsx` | Resumo, Precos (preencher), Materiais, Placas, Ferragens, Pecas, Plano_de_Corte, Paineis, Validacao — custos por fórmula |
| `pecas.csv`, `lista_corte.csv` | todas as peças e o corte barra a barra |
| `maquina_generico.csv` | sequência de montagem por painel (adaptar ao formato da máquina escolhida) |
| `paineis_e_trelicas.dxf` | elevações e treliças em camadas (PECAS, PLACAS, CNC, TRELICAS) |
| `etiquetas_paineis.pdf`, `etiquetas_pecas.zpl` | etiquetas com QR code (Zebra para peças) |
| `revit_solidos.json` | peças 3D para o adaptador Revit |
| `resultado.json`, `resumo.json` | resultado completo e resumo da execução |

## Pranchas A1/A0 (padrão brasileiro)

Formato e margens pela NBR 10068 (esq. 25 mm, demais 10 mm), legenda de 178 mm, zonas de referência,
marcas de dobra (NBR 13142), cotas com traço oblíquo e texto sobre a linha (NBR 10126), escalas exatas (NBR 8196).

- **Legenda Vigora**: logo em V (cobre para wood, aço para steel), fontes Archivo e IBM Plex Mono, obra, cliente,
  local, conteúdo da folha, disciplina, sistema, escala, formato, data, execução, revisão, responsável técnico,
  CREA, ART, desenho/verificação, status (RASCUNHO ou APROVADO), folha `nn/total` e código `PROJ-FRM-nnn-R00`.
- **Quadro de revisões e notas gerais** em todas as folhas.
- **Folhas**: capa (3D, índice, resumo) · planta de painéis por pavimento (norte, cotas, portas, quadro de painéis) ·
  planta de cobertura (marcas e espaçamentos) · entrepiso · elevações 1:20/1:25 (cotas acumuladas até a face
  esquerda, posições numeradas, lista de posições com corte e ângulo) · treliças por marca · detalhes típicos dos
  encontros (L, T, X, meia-esquadria) cortados do próprio modelo a 1:10, com peças numeradas, cotas face a face e
  quadro de fixações (prego/parafuso, diâmetro, comprimento, passo) · escada (planta e corte A-A 1:25) ·
  lista de materiais · validação.
- Peças chanfradas (meia-esquadria) aparecem hachuradas nas elevações, com "CH 22,5°" e o ângulo na lista.
- Fontes embutidas como TrueType com Unicode: texto legível e pesquisável em qualquer leitor de PDF.
- Dados da obra em `"meta"` no projeto: `cliente`, `local`, `responsavel_tecnico`, `crea`, `art`, `desenho`,
  `data`, `revisao`.

## Regras de montagem que o motor garante

- **Bloqueios padronizados**: linhas fixas a 1,20 m e 2,40 m do piso do painel em todas as paredes
  (`blocking.fixed_rows`); a junta horizontal da placa fica sempre a 2,40 m, sobre a linha de bloqueio.
  Verga que pararia logo abaixo da junta é aumentada; se não houver peça, os bloqueios sobem em camadas encostadas.
- **Escada reta** (`"stairs"` no projeto): espelho ≤ 180 mm, piso pela regra de Blondel (2h+b), 2 ou 3 longarinas
  recortadas na CNC, pisos de W-38x286. Verificações: espelho (V-082), garganta da longarina ≥ 90 mm, altura livre
  ≥ 2,00 m sobre a linha dos bocéis (V-083), chegada na borda do vão (V-084), sem bater em parede (V-085).

- **Sem vão aleatório**: entre duas peças, ou elas se encostam, ou o vão livre é de pelo menos 60 mm (V-074).
  Peças menores que 60 mm (remendos) não são geradas.
- **Encontros sem folga e sem sobreposição em planta** (V-075), inclusive parede que para antes de encostar.
- **Pavimentos empilhados**: fundo do entrepiso = topo das paredes portantes; treliças sobre paredes da mesma altura (V-076).
- **Placas estruturais**: juntas verticais sobre montantes existentes (a placa é cortada), junta horizontal longe de vergas.
- **Junções**: L, T (bloco contínuo de montantes), X (a parede é dividida em dois T), continuação e
  meia-esquadria de 120° a 179° (montante chanfrado ou pilarete CNC). Entre 90° e 120°: não suportado (V-078).
- **Telhados**: duas águas (fink, howe, pratt), meia-água com lado alto escolhido, 4 águas (comuns, truncadas,
  mestra dupla, meias-tesouras penduradas, espigões) e telhado encostado em outro volume (`"ends": ["abut", "gable"]`).
- **Rincões (casas em L, T e U, estilo americano)**: `"ends": ["gable", "valley"]` na asa. O principal tem o beiral
  cortado na faixa da asa; a asa termina encostada na parede; treliças de rincão (marca V) apoiam sobre as águas do
  principal até a cumeeira da asa (V-088 se a cumeeira da asa passar da principal). Funciona com principal em 2 ou 4 águas.
- **Meia-água com parede alta**: `"support": "high_wall"`; treliça apoiada na parede baixa e pendurada em estribos
  na parede alta (V-086 se a parede não cobrir o telhado).
- **Platibanda (telhado embutido)**: `"support": "parapet"`, `"bearing_height"`; treliças penduradas por dentro das
  paredes, sem beiral; paredes precisam cobrir o telhado + `parapet_min` (V-086).
- **Painel de complemento**: parede mais alta que a mesa (3,20 m) é dividida em painel principal + complemento acima.
- **Alinhamento (V-087)**: beirais de telhados que se encontram na mesma cota (o aviso diz o beiral que alinha) e
  banzos iguais ao principal nos telhados encostados/rincão.

## Caixa d'água no ático (padrão Vigora)

A caixa é declarada no projeto e todo o entorno é refeito a cada geração: adicionar, mover, trocar o modelo ou
remover a qualquer momento não deixa sobras no modelo.

```json
"tanks": [{"id": "CX1", "model": "BR_1000L", "level": "L1"}]          // sem "position" = posição automática
```

- **Catálogo** `catalog/tanks.yaml`: BR_500L e BR_1000L (Fortlev/Tigre, PEAD), bacia estanque, carga cheia, folga de
  manutenção de 0,50 m; regra de apoio (viga 2×38×235, vão livre até 1,50 m).
- **Posição automática**: centro entre duas paredes portantes paralelas à cumeeira (banheiro, shaft, hall) com vão
  livre ≤ 1,50 m, na interseção com uma parede interna portante perpendicular; prioriza onde cabe sob o telhado.
- **Apoio desacoplado da cobertura**: vigas duplas nos vãos entre as treliças (≥ 60 mm dos banzos), deck de OSB 18,3;
  nada apoia em banzo de treliça.
- **Envelope de colisão**: diâmetro da bacia, do deck até a tampa + 0,50 m. Treliças que cortam o envelope viram
  **treliças de ático** (marca A): abertura sem diagonais, montantes nas bordas.
- **Verificações**: V-090 caixa não cabe sob o telhado (diz quantos mm faltam), V-091 sem apoio, V-092 vão da viga,
  V-093 colisão 3D com qualquer peça, V-094 modelo/instalação inválidos.
- **Compras**: caixa, bacia, tubo Ø32 do ladrão até o beiral, conectores das vigas.
- **Comandos**:
  `python -m vigora_frame.cli caixa adicionar projeto.json [--modelo BR_500L] [--x 4200 --y 4200]`,
  `caixa mover projeto.json --x 7000 --y 4200` (ou `--auto`), `caixa trocar projeto.json BR_500L`,
  `caixa remover projeto.json` — cada um mostra o que mudou no modelo (peças, treliças, verificações).

## Exemplos (18 projetos, 0 erros)

| Projeto | Sistema | Destaques |
|---|---|---|
| casa_terrea_wood / _steel | wood / steel | 2 águas |
| casa_4aguas_wood / _steel | wood / steel | 4 águas, cruzamento em X, vários T |
| casa_meia_agua_wood / _steel_invertida | wood / steel | meia-água 10°, lado alto no fim / no início |
| casa_em_L_dois_telhados | wood | dois telhados (25° e 20°), anexo encostado no oitão |
| chale_40graus | wood | 2 águas 40°, cumeeira em y |
| salao_de_festas | wood | 150 m², 4 águas, portas de 2,40 m, balcão a 135°, banheiros em X |
| sobrado_wood / sobrado_4aguas | wood | 2 pavimentos, entrepiso, escada |
| pavilhao_curvo | wood | parede curva em facetas, arco, pilar |
| casa_em_T_rincao | wood | principal 2 águas + asa com rincão |
| casa_em_U_rincoes | wood | duas asas com rincão, pátio |
| casa_americana_4aguas_rincao | wood | 4 águas + asa 2 águas com rincão |
| casa_meia_agua_parede_alta | wood | meia-água 8° pendurada na parede alta, painel de complemento |
| casa_platibanda | wood | telhado embutido 10% com platibanda |
| casa_caixa_dagua | wood | caixa 1000 L no ático sobre hall portante, treliças de ático |

Novos exemplos: `python examples/make_examples.py`.

## Revit (pyRevit) — plugin v2

Instalação e uso: `adapters/revit_pyrevit/INSTALACAO_REVIT.md` (Revit 2024–2026, pyRevit 5).
Como modelar para o motor: `GUIA_MODELAGEM.md` (1 página).

- Aba **Vigora** com 4 painéis: Projeto (Configurar, Tipos de parede) · Framing (Verificar, Gerar, Últimos
  resultados) · Elementos (Telhado, Paredes, Entrepiso, Caixa d'água) · Saídas (Pranchas, Abrir saídas).
- O plugin só extrai dados brutos; toda a interpretação roda no motor (`revit_import.py`, testada):
  eixo da parede pela linha de localização, pé-direito pelo nível de cima, tipo de telhado pelas bordas com
  caimento, contorno e beiral pelas faces das paredes, rincão/encostado/parede alta/platibanda automáticos,
  direção das vigas do piso, escada reta, caixa d'água (família ou botão).
- Escolhas do usuário ficam em `<modelo>.vigora.json` ao lado do .rvt e vencem a detecção.
- Erros com o elemento do Revit e dica de correção; **Mostrar no modelo** seleciona e dá zoom.
- `python -m vigora_frame.cli revit raw.json --config modelo.vigora.json --out pasta [--verificar]`.
- **Não testado em Revit real** (testado com dados simulados: 13 casas ida e volta Revit → motor idênticas).

## O que ainda não existe

- Rincão entre telhados de inclinações diferentes com cumeeira na mesma altura (usar a mesma inclinação); treliças tesoura.
- Telhado pendurado em viga fixada na parede (ledger) e varanda sobre pilares.
- Encontros de paredes entre 90° e 120°.
- Plano de corte 2D (nesting) das placas: hoje a compra é estimada por área + 10%.
- Formato nativo de máquina específica (Hundegger, Weinmann, Howick, FrameCAD): hoje há um CSV genérico.
- Leitura de pisos e coberturas do Revit (o adaptador lê paredes e aberturas).
- Valores reais de engenharia e aprovação.
