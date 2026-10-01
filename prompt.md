# VIGORA FRAME ENGINE — ESPECIFICAÇÃO TÉCNICA INTEGRAL E MASTER PROMPT DE ENGENHARIA
> **Documento Diretor de Arquitetura de Software, Engenharia Construtiva, Otimização de Manufatura e Ecossistema BIM**  
> *Versão:* 3.0-ENTERPRISE  
> *Status:* Especificação Normativa e Operacional para Desenvolvedores e Agentes Autônomos  
> *Sistemas Construtivos:* Light Wood Frame & Light Steel Frame (LSF) no Mercado Brasileiro  
> *Padrões Normativos:* ABNT NBR 14762, NBR 7190, NBR 16970-1/2, NBR 15575, NBR 6123, NBR 10068, NBR 10126, NBR 13142  

---

## SUMÁRIO GERAL

1. [Filosofia de Engenharia, Princípios e Tolerâncias Construtivas](#1-filosofia-de-engenharia-princípios-e-tolerâncias-construtivas)
2. [Fundação, Radier, Desníveis de Contrapiso e Ancoragens](#2-fundação-radier-desníveis-de-contrapiso-e-ancoragens)
3. [Paredes: Geometria Não-Ortogonal, Junções Complexas e Edge Cases](#3-paredes-geometria-não-ortogonal-junções-complexas-e-edge-cases)
4. [Paredes Altas, Mezaninos e Pé-Direito Duplo](#4-paredes-altas-mezaninos-e-pé-direito-duplo)
5. [Oitões, Paredes Chanfradas e Geometrias Curvas](#5-oitões-paredes-chanfradas-e-geometrias-curvas)
6. [Aberturas, Vãos, Vergas Especiais e Peitoris de Drenagem](#6-aberturas-vãos-vergas-especiais-e-peitoris-de-drenagem)
7. [Coberturas, Treliças Especiais, Rincões Assimétricos e Beirais](#7-coberturas-treliças-especiais-rincões-assimétricos-e-beirais)
8. [Entrepisos, Vigas I, Vigas Treliçadas, Balanços e Vibração](#8-entrepisos-vigas-i-vigas-treliçadas-balanços-e-vibração)
9. [Escadas Complexas (L, U, Patamares e Ancoragens)](#9-escadas-complexas-l-u-patamares-e-ancoragens)
10. [Instalações Prediais (MEP): Furações, Reforços e Proteções](#10-instalações-prediais-mep-furações-reforços-e-proteções)
11. [Contraventamento, Diafragmas, Shear Walls e Cargas de Vento](#11-contraventamento-diafragmas-shear-walls-e-cargas-de-vento)
12. [Cálculo Estrutural Analítico e Memorial Automatizado](#12-cálculo-estrutural-analítico-e-memorial-automatizado)
13. [Otimização Linear 1D de Barras (Column Generation & Remnants)](#13-otimização-linear-1d-de-barras-column-generation--remnants)
14. [Nesting 2D Real de Chapas e Reaproveitamento de Miolos](#14-nesting-2d-real-de-chapas-e-reaproveitamento-de-miolos)
15. [Exportadores Industriais Diretos (CAM/CNC: Hundegger, Weinmann, Howick, FrameCAD)](#15-exportadores-industriais-diretos-camcnc-hundegger-weinmann-howick-framecad)
16. [Arquitetura do Plugin Revit 2.0 (C# Nativo, IPC, Assemblies e Live View)](#16-arquitetura-do-plugin-revit-20-c-nativo-ipc-assemblies-e-live-view)
17. [Geração de Pranchas NBR, Renderizador Vetorial e Cotagem Anticolisão](#17-geração-de-pranchas-nbr-renderizador-vetorial-e-cotagem-anticolisão)
18. [Orçamento Paramétrico Integrado com SINAPI / TCPO e Mão de Obra](#18-orçamento-paramétrico-integrado-com-sinapi--tcpo-e-mão-de-obra)
19. [Catálogo Completo e Expandido de Validações (V-001 a V-135)](#19-catálogo-completo-e-expandido-de-validações-v-001-a-v-135)
20. [Arquitetura de Software Core, Paralelismo DAG e Tipagem Estrita](#20-arquitetura-de-software-core-paralelismo-dag-e-tipagem-estrita)
21. [Desempenho Térmico, Acústico e Estanqueidade (NBR 15575)](#21-desempenho-térmico-acústico-e-estanqueidade-nbr-15575)
22. [Proteção Contra Incêndio (TRRF, Compartimentação e Barreiras Corta-Fogo)](#22-proteção-contra-incêndio-trrf-compartimentação-e-barreiras-corta-fogo)
23. [Logística, Transporte, Sequenciamento de Montagem e Içamento](#23-logística-transporte-sequenciamento-de-montagem-e-içamento)
24. [Interoperabilidade IFC 4.3 / openBIM e Exportação Universal](#24-interoperabilidade-ifc-43--openbim-e-exportação-universal)
25. [Edifícios Multipavimentos (3 a 5 Andares) e Transições Estruturais](#25-edifícios-multipavimentos-3-a-5-andares-e-transições-estruturais)
26. [Catálogo Extensivo de Conectores, Fixadores e Ferragens Estruturais](#26-catálogo-extensivo-de-conectores-fixadores-e-ferragens-estruturais)
27. [Sustentabilidade, LCA/EPD e Certificações Ambientais](#27-sustentabilidade-lcaepd-e-certificações-ambientais)
28. [Estratégia de Testes Exaustivos, Fuzzing e Validação Visual](#28-estratégia-de-testes-exaustivos-fuzzing-e-validação-visual)
29. [Motor de Autocorreção e Recuperação de Erros (Auto-Heal Engine)](#29-motor-de-autocorreção-e-recuperação-de-erros-auto-heal-engine)
30. [Enciclopédia de Edge Cases e Cenários Críticos de Engenharia](#30-enciclopédia-de-edge-cases-e-cenários-críticos-de-engenharia)
31. [Regras de Ouro Invioláveis para Engenheiros e Agentes de IA](#31-regras-de-ouro-invioláveis-para-engenheiros-e-agentes-de-ia)

---

## 1. FILOSOFIA DE ENGENHARIA, PRINCÍPIOS E TOLERÂNCIAS CONSTRUTIVAS

O **Vigora Frame Engine** não é um gerador visual ou esquemático; ele é um **motor determinístico de compilação construtiva industrial**. Sua função é transformar sólidos e eixos conceituais de arquitetura em peças reais com dimensões físicas exatas, folgas de usinagem, juntas de dilatação, conexões estruturais calculadas, instruções para máquinas CNC e pranchas executivas homologadas pelas normas brasileiras.

```
       ARQUITETURA (Revit / IFC)
                 │
                 ▼  [Normalização Topológica & Resolução de Eixos]
       MODELO NEUTRO PARAMÉTRICO
                 │
                 ▼  [Motor de Regras Físicas & Verificações Normativas]
       GEOMETRIA DE MONTAGEM & ENGENHARIA ESTRUTURAL
                 │
                 ├────────────────────────┬────────────────────────┐
                 ▼                        ▼                        ▼
       FABRICAÇÃO (CAM/CNC)       PRANCHAS NBR (PDF/DXF)    BIM NATIVO (Revit 3D)
       • BTL/BTLx (Hundegger)     • NBR 10068 (Formatos)    • Structural Framing
       • WUP (Weinmann)           • NBR 10126 (Cotagem)     • Assemblies
       • CSV/HCD (Howick)         • NBR 13142 (Dobras)      • Shared Parameters
       • RFX (FrameCAD)           • NBR 8196 (Escalas)      • Quantitativos Nativos
       • Nesting 1D & 2D          • Detalhes 1:5 e 1:10     • Sincronização Bi-direcional
```

### 1.1 Hierarquia de Tolerâncias Construtivas
Toda decisão algorítmica do motor obedece à matriz de tolerâncias dimensionais:
- **Tolerância Geométrica de Modelagem (CAD/BIM)**: $\pm 0.5\text{ mm}$. Desvios menores que isso entre nós teóricos são absorvidos por snap automático.
- **Tolerância de Usinagem e Corte (CNC / Serra)**: $\pm 0.5\text{ mm}$ no comprimento, $\pm 0.2^\circ$ no ângulo de corte.
- **Folga de Dilatação / Contração Térmica e Higroscópica**:
  - Madeira (*Wood Frame*): prever folga perimetral de $2.0\text{ a }3.0\text{ mm}$ entre bordas de chapas de OSB para acomodar expansão por umidade relativa do ar.
  - Aço (*Light Steel Frame*): prever folga axial de $1.0\text{ mm}$ nas pontas de montantes inseridos em guias para evitar contato forçado e estufamento da alma sob calor.
- **Tolerâncias de Canteiro (Fundação / Concreto)**:
  - Nivelamento de radier/baldrame: $\pm 3.0\text{ mm}$ a cada $3.0\text{ m}$.
  - Esquadro de diagonais de fundação: $\pm 5.0\text{ mm}$ em vãos até $10.0\text{ m}$.
  - Se a fundação real ultrapassar essas tolerâncias, o motor aciona rotinas de calçamento estrutural (*leveling grout*) sob a guia de base.

### 1.2 Contrastes Físicos: Wood Frame vs Light Steel Frame
O motor deve isolar e respeitar as particularidades mecânicas de cada sistema:

| Parâmetro de Engenharia | Light Wood Frame | Light Steel Frame (LSF) |
|---|---|---|
| **Norma Brasileira Principal** | ABNT NBR 16970 / NBR 7190 | ABNT NBR 14762 / NBR 15253 |
| **Material Base** | Madeira serrada tratada C24/C30 (Pinus taeda / elliottii com CCA/CCB) | Aço galvanizado Z275 / ZM120 ($f_y \ge 230\text{ a }300\text{ MPa}$) |
| **Espessuras Típicas de Alma** | $38\text{ mm}$ (nominais: $38\times 89$, $38\times 140$, $38\times 235\text{ mm}$) | $0.80\text{ mm}$, $0.95\text{ mm}$, $1.25\text{ mm}$, $1.50\text{ mm}$ |
| **Modulação Típica de Eixos** | $400\text{ mm}$ ou $600\text{ mm}$ | $400\text{ mm}$ ou $600\text{ mm}$ |
| **Alinhamento de Cargas (In-Line)** | Desalinhamento tolerado até $1.5\times$ espessura da placa superior se houver placa dupla | **Obrigatório rigoroso**: montante sobre montante com tolerância máxima de $20\text{ mm}$ |
| **Fixação Típica** | Pregos eletrogalvanizados espiralados/anelados e conectores estampados | Parafusos auto-brocantes e auto-perfurantes (cabeça trombeta, wafer, sextavada) |
| **Isolamento Galvânico** | Dispensável no contato com concreto se a madeira for tratada em autoclave | **Indispensável**: manta de EPDM/neoprene contínua isolando o perfil do concreto |
| **Ponte Térmica** | Baixa condutividade térmica da madeira ($\lambda \approx 0.13\text{ W/m}\cdot\text{K}$) | Alta condutividade do aço ($\lambda \approx 50\text{ W/m}\cdot\text{K}$): exige isolamento exterior contínuo (EIFS/ETICS) |

---

## 2. FUNDAÇÃO, RADIER, DESNÍVEIS DE CONTRAPISO E ANCORAGENS

A interface entre a estrutura leve e a fundação maciça (radier, vigas baldrame ou laje de transição) é a região com maior índice de patologias em obras reais. O motor deve parametrizar todas as variáveis de contato.

```
       CORTE VERTICAL — INTERFACE PAREDE EXTERNA / RADIER
       
          Placa OSB 11.1mm (estrutural)
          │  Membrana Hidrófuga (Housewrap)
          │  │  Revestimento Externo (Siding/EIFS)
          │  │  │
          ▼  ▼  ▼
       ┌─┬──┬──┐
       │ │  │  │  Montante Estrutural
       │ │  │  │  (Madeira 38x140 ou Aço C140)
       │ │  │  │
       │ └──┴──┘
       │ ┌─────┐
       │ │  O  │  Chumbador Mecânico/Químico (M12 / 1/2")
       │ └─────┘
       │ ┌─────┐  Guia Inferior / Soleira Tratada
       │ └─────┘  Fita de Vedação e Ruptura Capilar (Manta EPDM 3mm)
       ├───────┴───────────────────────────────
       │  ◄── Dente de Pingadeira (Rebaixo de 20 a 50mm)
       └──────────────┐
                      │  Borda do Radier de Concreto
                      │  Distância mínima da borda: c_min >= 70mm
```

### 2.1 Desníveis de Contrapiso (Slab Step-Downs)
Em edificações residenciais, existem desníveis obrigatórios na face superior da laje de concreto:
1. **Desníveis de Áreas Molhadas (Banheiros, Lavanderias, Sacadas)**:
   - A laje nesses ambientes é rebaixada entre $20\text{ mm}$ e $50\text{ mm}$ para contenção de água e assentamento de ralos lineares e revestimentos cerâmicos.
   - **Regra de framing**: As paredes que delimitam o banheiro apoiam na cota do piso seco. A guia inferior da parede de divisão mantém-se na cota superior, e a vedação lateral inferior é feita com chapa cimentícia de testeira ou o montante prolonga-se localmente (*cripple stud extension*).
2. **Rebaixo de Soleiras Externas (Dente de Pingadeira)**:
   - Para impedir a infiltração de água de chuva conduzida pelo vento sob as paredes externas, a borda perimetral do radier deve possuir um rebaixo (*step-down*) de $20\text{ a }50\text{ mm}$ em relação à cota interna, ou a parede projeta-se $15\text{ mm}$ para fora do alinhamento do concreto, permitindo que a membrana hidrófuga e o revestimento exterior façam a pingadeira natural (*drip edge*).
   - O motor deve verificar a distância entre o eixo de furação do chumbador e o bordo livre do concreto:
     $$c_{real} \ge c_{min} = 1.5 \times h_{ef}$$
     Onde $h_{ef}$ é a profundidade efetiva de ancoragem do chumbador. Se $c_{real} < 70\text{ mm}$, emitir erro crítico `V-098` (risco de lascamento do bordo de concreto na furação).

### 2.2 Isolamento de Base e Ruptura Capilar
- **Fita de Vedação Perimetral (Sill Gasket / Manta EPDM)**:
  - Todo painel de base (planta do pavimento térreo) recebe automaticamente um item de hardware de vedação contínua sob toda a extensão da guia inferior (`SILL_SEAL_EPDM`).
  - No *Light Steel Frame*, a manta evita o contato químico direto do zinco com a pasta alcalina do concreto de cimento Portland, prevenindo a corrosão galvânica acelerada por umidade ascensional.
  - No *Wood Frame*, a guia de base (`BOTTOM_PLATE`) obrigatoriamente deve ser tipificada como madeira tratada sob pressão em autoclave com arseniato de cobre cromatado (CCA) ou borato (para interiores), resistente ao ataque de cupins e fungos apodrecedores (classe de risco 3 ou 4 da NBR 7190).

### 2.3 Cálculo e Disposição das Ancoragens de Base
As ancoragens de base desempenham duas funções estruturais independentes que o motor deve dimensionar:
1. **Ancoragem ao Cisalhamento (Shear Anchors)**:
   - Resiste às forças horizontais de vento e sismo na base do painel.
   - Chumbadores expansivos de aço zincado a fogo (tipo Parabolt M10/M12) ou parafusos estruturais para concreto com rosca auto-atarraxante (*concrete screws* $\varnothing 10\text{ mm}$).
   - **Espaçamento paramétrico**:
     - Máximo de $300\text{ mm}$ de cada extremidade do painel ou ponta de abertura de porta.
     - Espaçamento intermediário entre $800\text{ mm}$ e $1200\text{ mm}$ ao longo da guia.
     - Todo segmento de parede, mesmo pequeno, deve possuir no mínimo $2$ chumbadores de cisalhamento.
2. **Ancoragens de Levante e Tombamento (Hold-Downs / Tie-Downs)**:
   - Em paredes contraventadas submetidas a esforços horizontais de vento no topo, surge um momento de tombamento $M = V \times H$. A extremidade comprimida descarrega na fundação, e a extremidade tracionada tende a se levantar (*uplift*).
   - O motor calcula o esforço vertical de tração:
     $$T = \frac{V_{topo} \times H_{parede}}{L_{parede}} - 0.9 \times N_{permanente}$$
   - Se $T > 0$, um conector de retenção de carga vertical (*Hold-Down*) é inserido na ponta do painel, fixado nos montantes duplos de extremidade por meio de parafusos sextavados estruturais (ou parafusos para chapa SDS) e conectado à fundação por barra roscada ancorada quimicamente com resina epóxi em profundidade de $150\text{ a }250\text{ mm}$.

---

## 3. PAREDES: GEOMETRIA NÃO-ORTOGONAL, JUNÇÕES COMPLEXAS E EDGE CASES

A grande maioria dos softwares de mercado falha quando a arquitetura se desvia dos $90^\circ$ perfeitos. O **Vigora Frame Engine** implementa uma taxonomia geométrica analítica contínua para ângulos de $0^\circ$ a $360^\circ$.

```
       TAXONOMIA DE ENCONTROS DE PAREDES (VISTA SUPERIOR EM PLANTA)
       
       1. Canto em L (90°)       2. Encontro em T (90°)    3. Meia-Esquadria (120°-179°)
          ┌──────┬─────┐               │   │                    \     \
          │      │     │               │   │                     \     \
          │      │     │         ──────┴───┴──────                \     \
          │      └─────┘                                           \     \
          │      │                                            ──────\─────\─────
          └──────┘
       
       4. Canto Agudo (< 90°)    5. Canto Obtuso Fechado   6. Nó Estrela (Múltiplas Paredes)
             /\                     (90° a 120°)                  \     /
            /  \                      \   /                        \   /
           / /\ \                      \_/                          \_/
          / /  \ \                    │   │                       ───┼───
         / /    \ \                   │   │                         / \
                                                                   /   \
```

### 3.1 Encontros em Ângulo Obtuso Fechado (90° a 120°)
- **Problema Construtivo**: Quando duas paredes se encontram em um ângulo de, por exemplo, $105^\circ$, os eixos se cruzam, mas a face interna fica comprimida e a face externa abre um vazio angular. Se montantes convencionais forem posicionados retos, não há superfície para fixação dos painéis de gesso acartonado e OSB na quina interna.
- **Solução de Engenharia do Motor**:
  1. O algoritmo calcula a bissetriz do ângulo formado pelos vetores diretores das paredes:
     $$\vec{u}_{bis} = \frac{\vec{u}_1 + \vec{u}_2}{\|\vec{u}_1 + \vec{u}_2\|}$$
  2. As extremidades das guias superior e inferior são chanfradas com corte angular de:
     $$\alpha_{corte} = \frac{180^\circ - \theta}{2}$$
  3. No ponto de encontro, é gerado um montante bissetriz chanfrado (*slanted corner stud*) ou um conjunto composto: um montante em esquadro alinhado à parede principal somado a um sarrafo chanfrado longitudinalmente na serra CNC para oferecer o plano de apoio da parede secundária.
  4. Na face interna, é adicionado um perfil auxiliar metálico dobrado em ângulo de $105^\circ$ (*adjustable corner angle*) ou montantes duplos recuados a $38\text{ mm}$ do vértice interno, fornecendo base sólida de aparafusamento contínuo para as placas de acabamento.

### 3.2 Encontros em Ângulo Agudo (30° a 89°)
- **Problema Construtivo**: Em esquinas agudas, a interseção geométrica dos eixos das paredes projeta a quina externa a uma distância considerável do centro da parede. Montantes comuns não alcançam o bico externo sem que haja sobreposição física e interferência no corte de chapas.
- **Solução do Motor**:
  1. **Truncamento da Quina Cega**: A quina externa com espessura inferior a $50\text{ mm}$ é truncada ortogonalmente, criando uma faceta plana mínima (*blunt nose*).
  2. Um montante frontal plano (*nose stud*) é inserido no truncamento, servindo de fechamento frontal e suporte para a cantoneira de reforço e tela de fachada.
  3. No espaço interno, gera-se um bloco de enchimento sólido (*solid corner wedge*) usinado em CNC conforme os ângulos exatos das faces das paredes convergentes.

### 3.3 Clusters de Múltiplas Paredes Concorrentes (Nós Estrela de 3, 4 ou 5 Paredes)
- Quando 3 ou mais paredes convergem em um único ponto geométrico (ex: cruzamento de circulação com quartos inclinados):
  1. O motor identifica a parede contínua de maior hierarquia estrutural (externa > portante > mais espessa > mais longa).
  2. Essa parede prioritária é mantida passante.
  3. As paredes concorrentes secundárias são divididas e terminam em plano de topo cortado no ângulo da face da parede passante.
  4. Dentro do miolo da parede passante, o motor gera um bloco de reforço (*stud core cluster*) com múltiplos montantes agrupados solidariamente, garantindo que toda parede que chegue encontre um montante traseiro (*backer stud*) para fixação mecânica direta, eliminando qualquer transmissão de carga excêntrica sobre o vão livre de placas.

### 3.4 Paredes com Desvios Colineares Mínimos (Dentes de Arquitetura < 100 mm)
- Arquitetos frequentemente desenham pequenos dentes de $30\text{ a }80\text{ mm}$ em paredes para embutir pilares de concreto ou prumadas hidráulicas.
- **Regra Construtiva**: Um painel de framing não pode ter comprimento estrutural menor que $150\text{ mm}$, pois as ferramentas de fixação (pistola pneumática de pregos ou parafusadeiras elétricas) exigem espaço livre mínimo para o bocal.
- Se o dente for menor que $150\text{ mm}$, o motor emite um alerta `V-077` e aciona a rotina de *furring offset*: o painel estrutural principal segue reto e o dente arquitetural é executado como uma camada secundária de sarrafeamento (*furring channel / outrigger*), desvinculada do esqueleto de suporte.

---

## 4. PAREDES ALTAS, MEZANINOS E PÉ-DIREITO DUPLO

Paredes com pé-direito superior a $3.20\text{ m}$ (salas de estar com teto duplo, garagens com mezaninos, fachadas imponentes de $4.50\text{ a }7.00\text{ m}$) não podem ser tratadas como paredes comuns, sob risco de colapso por flambagem ou vibração induzida por vento.

```
       COMPARAÇÃO CONSTRUTIVA: BALLOON FRAMING vs PLATFORM FRAMING
       
       A) PLATFORM FRAMING (EM PISOS)           B) BALLOON FRAMING (PÉ-DIREITO DUPLO)
       
          Parede Superior                          Montante Contínuo Único (Até 6m)
          ┌─────────────┐                          ┌─────────────────────────────┐
          │             │                          │                             │
          └─────────────┘                          │  Viga de Piso Pendurada     │
          ─────────────── Placa Dupla              │  em Entalhe ou Estribo      │
          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ Viga de Borda (Rim)      │  ┌──────┐                   │
          ─────────────── Guia Inferior            │  │ Viga │                   │
          ┌─────────────┐                          │  └──────┘                   │
          │             │                          │                             │
          │ Parede Inf. │                          │                             │
          └─────────────┘                          └─────────────────────────────┘
          [Cria junta de esmagamento               [Sem descontinuidade axial;
           e linha de articulação sob vento]        ótima rigidez contra vento]
```

### 4.1 Balloon Framing vs Platform Framing para Paredes Altas
1. **Limitações do Platform Framing em Paredes Altas**:
   - Se uma parede de sala com $6.00\text{ m}$ for executada pelo método plataforma padrão (painel inferior de $3.00\text{ m}$ + vigas de entrepiso + painel superior de $3.00\text{ m}$), a interface intermediária atua como uma **linha de articulação** (*hinge point*). A pressão dinâmica do vento soprando contra a fachada tende a empurrar essa junta para dentro, gerando patologias graves de fissura e risco de colapso por flexão.
2. **Implementação de Balloon Framing Automatizado**:
   - Quando o projeto indicar uma parede alta sem laje de entrepiso intermediária contínua, o motor automaticamente desativa o fatiamento e gera montantes inteiriços contínuos (*full-height balloon studs*).
   - Se houver mezanino parcial ou passadiço ancorado nessa parede alta, as vigas do mezanino são suspensas por estribos metálicos de aba facial (*face-mount hangers*) ou apoiadas sobre uma fita de madeira/aço entalhada longitudinalmente nos montantes (*ribbon board / ledger strip*), mantendo a continuidade axial dos montantes da fachada do chão até a cobertura.

### 4.2 Dimensionamento de Montantes Contra Pressão de Vento
- O motor calcula a flecha elástica no centro do vão da parede alta sob a combinação crítica de vento (NBR 6123 e NBR 14762 / NBR 7190):
  $$w = q_k \times c_p \times s_{montante}$$
  $$\delta_{max} = \frac{5 \cdot w \cdot H^4}{384 \cdot E \cdot I_x} \le \frac{H}{360} \quad (\text{ou } \frac{H}{240} \text{ se não houver acabamento frágil})$$
- **Rotinas Automáticas de Reforço de Rigidez**:
  - Se a flecha calculada ultrapassar $H/360$:
    1. Reduzir o espaçamento entre montantes de $600\text{ mm}$ para $400\text{ mm}$ ou $300\text{ mm}$.
    2. Duplicar os montantes (*double studs* unidos alma com alma).
    3. Em *Steel Frame*, adotar perfis C compostos em caixa (*box studs* soldados por ponto ou aparafusados com parafusos wafer a cada $300\text{ mm}$) ou aumentar a espessura da chapa de $0.95\text{ mm}$ para $1.25\text{ mm}$ ou $1.50\text{ mm}$.
    4. Em *Wood Frame*, aumentar a seção transversal dos montantes de $38\times 89\text{ mm}$ para $38\times 140\text{ mm}$ ou $38\times 235\text{ mm}$ (ou madeira laminada colada - Glulam / LVL).

### 4.3 Bloqueios Intermediários e Travamento Lateral (Bridging & Blocking)
Para impedir a flambagem por flexo-torção no eixo fraco ($y-y$) dos montantes altos:
- **Linhas Fixas de Bloqueio**:
  - Para alturas $H > 3.00\text{ m}$, inserir linhas de bloqueio horizontais espaçadas a cada $1.20\text{ m}$ ou $1.50\text{ m}$.
  - Em *Wood Frame*: blocos de madeira sólida maciça (*solid wood blocking*) alternados em linha (*staggered*) para permitir pregação direta pelas cabeças, ou alinhados retos com fita contínua de travamento.
  - Em *Steel Frame*: tiras de fita metálica de aço galvanizado (*strap bracing*) fixadas em ambas as faces dos montantes combinadas com blocos de travamento acústico e estrutural de perfil U (*notch tracks / bridging channels*) passantes pelos furos de serviço da alma dos montantes e travados com cantoneiras de clipe (*clip angles*).

---

## 5. OITÕES, PAREDES CHANFRADAS E GEOMETRIAS CURVAS

### 5.1 Paredes de Oitão (Gable End Walls)
As paredes que fecham a empena triangular do telhado exigem tratamento trigonométrico refinado:
1. **Guia Superior Inclinada (Rake Track / Sloped Plate)**:
   - A guia superior tem sua inclinação calculada pelo ângulo $\theta$ do telhado ($\tan\theta = \text{declividade}$).
   - O comprimento da guia superior é dado por:
     $$L_{guia} = \frac{L_{horizontal}}{\cos\theta}$$
   - No caso de telhado duas águas simétrico, a parede é dividida na cumeeira ou gerada com duas guias inclinadas convergentes no vértice central.
2. **Montantes de Empena (Gable Studs)**:
   - Os montantes possuem alturas variáveis, calculadas analiticamente por:
     $$h_i = h_{base} + x_i \cdot \tan\theta$$
   - A ponta superior de cada montante de oitão recebe um corte chanfrado no ângulo exato $\theta$ para encostar perfeitamente na face inferior da guia superior inclinada.
3. **Beiral de Oitão em Escada (Rake Overhang / Ladder Framing)**:
   - Quando há beiral projetado além da empena da parede, o motor rebaixa o topo do oitão na espessura do caibro de beiral (normalmente $38\text{ mm}$ ou $89\text{ mm}$) e cria travessas horizontais em balanço (*outriggers / lookouts* espaçadas a $600\text{ mm}$), que partem do primeiro montante interno, passam sobre a parede de oitão e seguram a tábua de testeira do beiral (*fly rafter*), resistindo ao arrancamento por vento.

### 5.2 Paredes Curvas e Arcos Paramétricos
Projetos arquitetônicos modernos frequentemente incluem paredes com curvatura suave em planta:
1. **Algoritmo de Facetamento por Controle de Flecha (Sagita)**:
   - O arco circular de raio $R$ e ângulo total $\Delta\theta$ é decomposto em $N$ facetas lineares.
   - O número de facetas $N$ é calculado dinamicamente para que a flecha máxima da corda em relação ao arco ideal não exceda a flexibilidade admissível da placa de gesso acartonado ou OSB:
     $$f = R \left(1 - \cos\frac{\Delta\theta}{2N}\right) \le f_{admissivel}$$
     - Placa de drywall flexível $6.5\text{ mm}$: $f_{adm} = 2.0\text{ mm}$.
     - Placa de OSB $9.5\text{ mm}$: $f_{adm} = 1.0\text{ mm}$ (ou facetas de no máximo $600\text{ mm}$).
2. **Modelagem de Guias Curvadas**:
   - Em *Steel Frame*: utilização de guias flexíveis pré-estampadas com cortes nas abas (*flexible track / track snake*), permitindo curvatura contínua sem quebrar a alma do perfil.
   - Em *Wood Frame*: sobreposição de 2 ou 3 camadas de placas de compensado naval de $15\text{ mm}$ cortadas em arco contínuo na mesa CNC Router, servindo como guia superior e inferior curvada.
   - Montantes radiais posicionados orientados para o centro de curvatura do arco, mantendo as faces externas prontas para o raio de curvatura.

---

## 6. ABERTURAS, VÃOS, VERGAS ESPECIAIS E PEITORIS DE DRENAGEM

As portas e janelas interrompem a continuidade dos montantes verticais, concentrando as cargas gravitacionais do teto e pavimentos superiores nas laterais do vão.

```
       DETALHAMENTO ESTRUTURAL COMPLETO DE VÃO DE JANELA
       
                 Montantes de Altura Total (King Studs)
                 │  Montante de Apoio da Verga (Jack Stud / Trimmer)
                 │  │
                 ▼  ▼
       ──────┬───┬──┬─────────────────────────────────┬──┬───┬────── Guia Superior
             │   │  │   Montantes Curtos (Cripples)   │  │  │   │
             │   │  │   ┌───┐   ┌───┐   ┌───┐   ┌───┐ │  │  │   │
             │   │  ├───┴───┴───┴───┴───┴───┴───┴───┴─┤  │  │   │
             │   │  │   VERGA ESTRUTURAL (HEADER)     │  │  │   │
             │   │  ├─────────────────────────────────┤  │  │   │
             │   │  │                                 │  │  │   │
             │   │  │                                 │  │  │   │
             │   │  │          VÃO LIVRE              │  │  │   │
             │   │  │      DO CAIXILHO (ROUGH)        │  │  │   │
             │   │  │                                 │  │  │   │
             │   │  │                                 │  │  │   │
             │   │  ├─────────────────────────────────┤  │  │   │
             │   │  │   PEITORIL DUPLO (SILL)         │  │  │   │
             │   │  ├───┬───┬───┬───┬───┬───┬───┬───┬─┤  │  │   │
             │   │  │   │   │   │   │   │   │   │   │ │  │  │   │
       ──────┴───┴──┴───┴───┴───┴───┴───┴───┴───┴───┴─┴──┴───┴────── Guia Inferior
```

### 6.1 Tipologias Avançadas de Vergas (Headers)
O motor escolhe automaticamente a tipologia da verga com base no vão livre e no carregamento tributário:

1. **Verga Sanduíche com Isolamento Térmico (*Insulated Sandwich Header*)**:
   - Para *Wood Frame* em paredes externas: duas peças de madeira estrutural ($38\times 140\text{ mm}$ ou $38\times 235\text{ mm}$) posicionadas em cutelo, espaçadas por uma placa rígida de poliestireno expandido (EPS) de $50\text{ mm}$ no miolo.
   - Elimina a ponte térmica linear que normalmente ocorre sobre as janelas, reduzindo o risco de condensação intersticial interna e mofo no gesso.
2. **Verga em Caixa (*Box Beam Header*)**:
   - Composta por montantes superior e inferior de madeira com fechamento em ambas as faces por painéis estruturais de OSB de $15.1\text{ mm}$ colados e pregados com pregos anelados a cada $75\text{ mm}$. Atua como uma viga caixão de alta rigidez e baixíssimo peso próprio.
3. **Verga em Steel Frame (Perfil Duplo em Caixa ou em I)**:
   - Para vãos até $1.50\text{ m}$: dois perfis U enrijecidos (C) conectados alma com alma (*back-to-back*) com parafusos sextavados auto-brocantes $\varnothing 4.8\text{ mm}$ a cada $200\text{ mm}$.
   - Para vãos entre $1.50\text{ m}$ e $2.40\text{ m}$: dois perfis C em caixa (*box header*), fechados com guia U superior e inferior conformada.
   - Para vãos $> 2.40\text{ m}$ (portas-balcão de correr de salas e garagens): verga treliçada (*trussed header*) embutida no painel ou perfil laminado I metálico estrutural (W150/W200) encapsulado com conexões soldadas ou parafusadas.
4. **Verga Embutida na Guia Superior (*Flush Header*)**:
   - Quando o projeto arquitetônico especifica portas ou janelas que vão do piso até o forro (*full-height doors* sem bandeira):
   - A verga substitui a guia superior do painel, e as vigas de entrepiso ou treliças de cobertura apoiam diretamente sobre ela por meio de estribos metálicos (*flush joist hangers*).

### 6.2 Peitoris e Drenagem Ativa
- **Peitoril Duplo com Desacoplamento**:
  - Peitoril estrutural inferior + peitoril de assentamento superior.
  - Para caixilhos largos em regiões de alta pluviosidade, o peitoril superior recebe um corte longitudinal chanfrado em serra CNC com caimento de $5^\circ$ para o lado externo, garantindo que qualquer infiltração acidental pelo caixilho escorra sobre a membrana impermeabilizante e saia pelas pingadeiras inferiores (*weep holes*).
- **Montantes de Apoio de Peitoril (Sill Trimmers / Cripples)**:
  - Dispostos na mesma modulação da grade geral da parede ($400\text{ mm}$ ou $600\text{ mm}$), alinhados verticalmente com os montantes gerais para permitir a fixação dos rodapés e placas internas sem deformação.

### 6.3 Janelas de Canto Vivo (Corner Windows)
- Quando duas janelas se encontram no vértice de duas paredes perpendiculares sem montante de quina:
  1. A verga de uma das paredes é dimensionada em balanço (*cantilevered lintel*), engastada na parede adjacente com comprimento de contra-peso de pelo menos $2\times$ o comprimento do balanço.
  2. Alternativamente, o motor insere um pilar tubular quadrado de aço maciço (tubo estrutural SHS $60\times 60\times 4.75\text{ mm}$) embutido na esquadria para suportar a carga vertical de teto, permitindo visual envidraçado contínuo.

---

## 7. COBERTURAS, TRELIÇAS ESPECIAIS, RINCÕES ASSIMÉTRICOS E BEIRAIS

O motor de cobertura resolve toda a geometria tridimensional do telhado com precisão milimétrica nos nós.

```
       TIPOLOGIAS ESTRUTURAIS DE COBERTURA GERADAS PELO MOTOR
       
       A) TRELIÇA FINK PADRÃO (DUAS ÁGUAS)       B) TRELIÇA TESOURA (TETO CATEDRAL)
                 /\                                        /\
                /  \                                      /  \
               / /\ \                                    / /\ \
              //    \\                                  //    \\
             / /----\ \                                / /----\ \
            /_/______\_                               /_/  /\  \_
                                                          /  \   [Banzo inferior inclinado]
       
       C) TELHADO 4 ÁGUAS (QUADRIL / HIP ROOF)    D) RINCÃO COM TELHADO PRINCIPAL
             ┌─────────────────┐                       ┌───────────┐
            / \               / \                      │           │
           /   \   CUMEEIRA  /   \                     │ PRINCIPAL ├───┐
          /     \___________/     \                    │           │ASA│
         /                         \                   │           │ RINCÃO
        └───────────────────────────┘                  └───────────┴───┘
```

### 7.1 Treliças Tesoura (Scissor Trusses) para Tetos Inclinados/Catedrais
1. **Diferencial Geométrico**:
   - Banzo Superior com inclinação externa $\theta_{sup}$ (ex: $25^\circ$ ou $30^\circ$).
   - Banzo Inferior com inclinação interna $\theta_{inf} < \theta_{sup}$ (ex: $15^\circ$ ou $18^\circ$), gerando o teto inclinado interno sem necessidade de forro rebaixado.
2. **Empuxo Horizontal e Apoios Deslizantes**:
   - Devido à geometria não horizontal do banzo inferior, a treliça tesoura sofre deformação elástica sob carga que tende a abrir as pontas laterais (*lateral heel thrust*).
   - O motor emite aviso `V-102` e define nos nós de extremidade:
     - Apoio fixo rígido em uma das paredes com cantoneira estrutural multi-parafusada.
     - Apoio deslizante (*expansion slotted bracket*) na parede oposta, com furos oblongos que permitem uma dilatação lateral de até $12\text{ mm}$ sem induzir esforço horizontal de flexão no topo das paredes portantes.

### 7.2 Telhados de 4 Águas (Hip Roof Systems)
A montagem industrial de telhados 4 águas é resolvida com o seguinte sequenciamento de peças gerado pelo motor:
1. **Treliça Mestra de Fechamento (Girder Truss)**:
   - Posicionada a uma distância de recuo (*setback*) da parede de oitão igual a metade da largura do vão ou conforme a inclinação.
   - Fabricada com banzo duplo ou triplo, calculada para receber a carga concentrada de todas as meias-tesouras de canto.
2. **Espigões (Hip Rafters)**:
   - Peças diagonais que unem o topo da cumeeira ou vértice da mestra ao canto externo da parede.
   - O motor calcula o corte chanfrado em ângulo composto (*compound miter*) e aplica o rebaixo de apoio (*hip drop*) de $15\text{ a }25\text{ mm}$ para que o plano do compensado/OSB da água triangular assente perfeitamente no mesmo nível das águas principais.
3. **Meias-Tesouras e Meios-Caibros (Jack Trusses / Cripple Rafters)**:
   - Treliças parciais com alturas decrescentes milimétricas que apoiam de um lado no espigão e do outro na parede perimetral.

### 7.3 Rincões Assimétricos (Bastard Valleys)
- Em ampliações ou casas em L onde o corpo principal e a asa possuem inclinações distintas (ex: principal a $30\%$ e anexo a $20\%$):
  1. A cumeeira da asa é posicionada em cota inferior ou intercepta a água principal em plano inclinado.
  2. O rincão (linha de vale para captação de água) forma um ângulo em planta que **não é de 45°** em relação aos eixos das paredes.
  3. O motor calcula analiticamente a equação do plano de cada água:
     $$Z_1(x, y) = A_1 x + B_1 y + D_1$$
     $$Z_2(x, y) = A_2 x + B_2 y + D_2$$
  4. A interseção das superfícies define a curva espacial tridimensional exata da calha de rincão (*valley line*), gerando as peças de apoio de base (*sleeper boards / valley plates*) chanfradas com os dois ângulos simultâneos para receber o conjunto de treliças de sobreposição (*valley set*).

### 7.4 Platibandas Integradas e Calhas Embutidas (Parapets & Box Gutters)
- Em residências com telhado embutido (estilo contemporâneo):
  - O telhado é suportado em cotas rebaixadas por apoios embutidos por dentro dos montantes da platibanda (*pocket bearing* ou estribos de cisalhamento).
  - A parede externa continua subindo de forma contínua para formar a mureta de platibanda (mínimo de $200\text{ mm}$ de borda livre acima da cumeeira mais alta, verificação `V-086`).
  - O motor modela o rebaixo contínuo para a calha técnica metálica ou de membrana EPDM com caimento longitudinal de $0.5\%$ em direção aos condutores pluviais verticais.

---

## 8. ENTREPISOS, VIGAS I, VIGAS TRELIÇADAS, BALANÇOS E VIBRAÇÃO

O sistema de entrepiso é o diafragma horizontal responsável pela estabilidade global contra vento e pela transmissão das cargas vivas e mortas para os pavimentos inferiores.

```
       CORTE VERTICAL DO ENTREPISO — DISTRIBUIÇÃO E BLOQUEIOS
       
       Parede do Pavimento Superior
       ┌───────────┐
       │ Montante  │
       └─────┬─────┘
       ──────┴─────────────────────────── Placa Dupla de Base
       ══════════════════════════════════ Contrapiso OSB 18.3mm (T&G Macho-Fêmea)
       ┌────────────────────────┐
       │   VIGA DE BORDA (RIM)  │ ┌──────────────────────────────────────────────
       │   OU BLOQUEIO SÓLIDO   │ │ VIGA DE PISO (I-JOIST OU PERFIL C DUPLO)
       │                        │ │ Modulação a cada 400mm
       │                        │ │
       │                        │ │ [Bloqueio Intermediário no 1/3 do vão]
       └────────────────────────┘ └──────────────────────────────────────────────
       ──────┬─────────────────────────── Placa Superior da Parede de Baixo
       ┌─────┴─────┐
       │ Montante  │ Parede Portante do Pavimento Térreo (Alinhada In-Line)
       └───────────┘
```

### 8.1 Vigas I Estruturais (Wood I-Joists) e Vigas Treliçadas em Aço
1. **Wood I-Joists**:
   - Mesas superior e inferior em madeira sólida tratada ou LVL ($38\times 64\text{ mm}$ a $38\times 89\text{ mm}$) com alma central de OSB estrutural de $9.5\text{ mm}$ inserida em junta colada de alta resistência.
   - Vãos livres suportados de até $6.50\text{ m}$ sem necessidade de pilares intermediários.
2. **Vigas Treliçadas de Aço (Open-Web Steel Joists)**:
   - Perfis dobrados a frio com diagonais tubulares conformadas, permitindo a passagem totalmente livre de tubulações pesadas de esgoto ($\varnothing 100\text{ mm}$) e dutos de ar-condicionado pelo miolo do entrepiso sem furações de campo.
3. **Bloqueios de Esmagamento de Alma (Squash Blocks)**:
   - Nos pontos onde uma parede portante do segundo pavimento descarrega sobre a viga I, a alma de OSB de $9.5\text{ mm}$ não pode sofrer esmagamento vertical concentrado.
   - O motor posiciona automaticamente pares de montantes curtos maciços (*squash blocks*) colados verticalmente em ambos os lados da alma, transferindo a carga vertical da mesa superior diretamente para a parede inferior.

### 8.2 Balanços de Sacada e Projeções de Fachada (Cantilevers)
- **Relação de Engastamento Estrutural**:
  - Para cada $1.0\text{ m}$ de sacada em balanço projetada para fora, as vigas de piso devem se estender no mínimo $2.5\text{ a }3.0\text{ m}$ para dentro do pavimento interno ($L_{interno} \ge 2.5 \times L_{balanco}$).
  - As vigas do balanço são dobradas (*sister joists*) para absorver o momento fletor negativo sobre a parede de apoio.
- **Degrau Hidráulico de Sacada**:
  - O piso da sacada aberta externa é rebaixado entre $30\text{ mm}$ e $50\text{ mm}$ em relação ao piso interno. O motor altera a altura útil das vigas de balanço para criar o desnível estrutural sem necessidade de enchimentos pesados de argamassa no canteiro.

### 8.3 Desempenho Dinâmico e Controle de Vibração de Piso
Pisos leves de wood e steel frame podem apresentar flexibilidade incômoda se dimensionados apenas para resistência estática. O motor executa a análise dinâmica de conforto:
- **Cálculo da Frequência Fundamental do Piso ($f_1$)**:
  $$f_1 = \frac{\pi}{2 L^2} \sqrt{\frac{(EI)_{eff}}{m}} \ge 8.0\text{ Hz}$$
  Se $f_1 < 8.0\text{ Hz}$, o piso entra em ressonância com passos humanos normais. O motor aplica automaticamente:
  1. Redução da modulação das vigas de $600\text{ mm}$ para $400\text{ mm}$.
  2. Inclusão de linhas duplas de travamento transversal em X (*cross bridging*) no terço médio do vão.
  3. Especificação de subpiso de OSB de maior espessura ($18.3\text{ mm}$ ou $22.0\text{ mm}$ com encaixe macho-e-fêmea colado com adesivo de poliuretano nas vigas).

---

## 9. ESCADAS COMPLEXAS (L, U, PATAMARES E ANCORAGENS)

O motor estende o módulo de escadas para além de lances retos, integrando lances articulados:

```
       ESCADA EM L COM PATAMAR ESTRUTURADO — COMPONENTES DE FRAMING
       
       Pavimento Superior ════════════════════
                             │
                             ▼ Lance Superior (Stringers recortadas na CNC)
                     ┌───────────┐
                     │  PATAMAR  │ ◄── Quadro de vigas e montantes embutidos
                     │ ESTRUTURA │     na parede de quina
                     └─────┬─────┘
                           │
                           ▼ Lance Inferior (Chegada no piso térreo)
       Pavimento Térreo ══════════════════════
```

### 9.1 Geometria e Verificação de Conforto (Fórmula de Blondel)
- Altura do espelho ($h$) e largura do piso ($b$):
  $$630\text{ mm} \le 2h + b \le 645\text{ mm}$$
  - $h \le 180\text{ mm}$ (máximo admissível: $185\text{ mm}$).
  - $b \ge 270\text{ mm}$ (mínimo de pisada segura com bocel de $25\text{ mm}$).
- **Verificação de Altura Livre (Headroom Clearance)**:
  - O motor traça uma linha paralela inclinada a $2.05\text{ m}$ acima da linha dos bocéis dos degraus.
  - Qualquer aresta de viga de piso ou teto que intercepte essa zona emite imediatamente o erro crítico `V-083` com a indicação exata de quantos milímetros o vão do piso precisa ser aumentado no sentido da descida.

### 9.2 Patamares Intermediários e Longarinas CNC
- **Quadro do Patamar (Landing Frame)**:
  - Formado por vigas perimetrais duplas apoiadas em pilaretes embutidos nas paredes adjacentes.
  - O contrapiso do patamar recebe chapa de OSB de $18.3\text{ mm}$ colada e parafusada.
- **Longarinas Recortadas em Dente de Serra (Sawtooth Stringers)**:
  - Usinadas diretamente em tábuas de madeira estrutural de $38\times 286\text{ mm}$ ou chapas dobradas de aço de $2.00\text{ mm}$.
  - O motor garante que a **garganta residual da longarina** (distância perpendicular mínima entre o vértice interno do dente de serra e a borda inferior) seja sempre:
    $$t_{throat} \ge 90\text{ mm}$$
  - Número de longarinas por lance:
    - Largura útil até $900\text{ mm}$: 2 ou 3 longarinas.
    - Largura útil de $900\text{ mm}$ a $1200\text{ mm}$: 3 ou 4 longarinas (obrigatório para evitar flexão dos degraus).

---

## 10. INSTALAÇÕES PREDIAIS (MEP): FURAÇÕES, REFORÇOS E PROTEÇÕES

Furações descontroladas feitas por eletricistas e encanadores em canteiro são a principal causa de perda de garantia estrutural. O motor calcula e pré-determina todas as furações fabris.

```
       ZONAS NORMATIVAS DE FURAÇÃO EM MONTANTES E VIGAS
       
       A) MONTANTE DE PAREDE (VISTA FRONTAL)      B) VIGA DE PISO (CORTE LONGITUDINAL)
       
          ┌──────┐                                 ┌─────────────────────────────────┐
          │      │                                 │   ZONA SUPERIOR COMPRIMIDA      │
          │      │  ◄── Topo da parede             │   (PROIBIDO FUROS)              │
          ├──────┤                                 ├ - - - - - - - - - - - - - - - - ┤
          │  ()  │  ◄── Furo centralizado:         │      ()         ()              │ ◄── Furos no
          │      │      d <= 0.4 x D               ├ - - - - - - - - - - - - - - - - ┤     1/3 médio
          │      │      Dist. borda >= 15mm        │   ZONA INFERIOR TRACIONADA      │
          │      │                                 │   (PROIBIDO ENTALHES NO CENTRO) │
          │  ()  │  ◄── Espaçamento entre          └─────────────────────────────────┘
          │      │      furos >= 600mm              ◄──────── L/3 ────────►
          └──────┘
```

### 10.1 Regras Normativas para Furações (NBR 14762 e NBR 7190 / AISI S100)
1. **Montantes Verticais de Paredes**:
   - O furo deve ficar rigorosamente centrado na linha neutra da alma do perfil.
   - Diâmetro máximo do furo circular:
     $$d_{max} = 0.40 \times D_{montante}$$
     (Ex: em montante de $140\text{ mm}$, diâmetro máximo de $56\text{ mm}$; em montante de $89\text{ mm}$, diâmetro máximo de $35\text{ mm}$).
   - Distância mínima do bordo livre do furo até a aba do perfil: $\ge 15\text{ mm}$.
   - Distância entre centros de furos consecutivos no mesmo montante: $\ge 600\text{ mm}$.
2. **Vigas de Piso**:
   - É terminantemente proibido furar ou entalhar o terço central inferior das vigas (zona de tração pura sob momento fletor máximo).
   - Furos circulares são permitidos apenas na zona neutra vertical (terço médio da altura da viga) e preferencialmente próximos aos apoios, respeitando distância mínima de $1.5\times$ a altura da viga em relação ao apoio final.

### 10.2 Reforços de Alma e Chapas Antiperfuração (Nail Plates)
- **Reforços de Abertura (*Stud Shoes*)**:
  - Quando uma tubulação de esgoto de $\varnothing 75\text{ mm}$ ou $\varnothing 100\text{ mm}$ precisa passar verticalmente por um montante de parede portante de $140\text{ mm}$, a alma é excessivamente enfraquecida.
  - O motor insere um reforço metálico envolvente de aço galvanizado estrutural de $2.00\text{ mm}$ (*stud shoe*), fixado com parafusos estruturais, que reconstitui a capacidade de carga axial do montante.
- **Chapas Antiperfuração (*Nail Protection Plates*)**:
  - Em todo ponto onde um tubo de água, esgoto ou conduíte elétrico passar a menos de $32\text{ mm}$ da face frontal do montante:
  - O motor quantifica e marca a aplicação de uma chapa de aço endurecido calandrado de $1.5\text{ mm}$ de espessura ($75\times 150\text{ mm}$) fixada sobre a face frontal do montante, impedindo fisicamente que parafusos de fixação de drywall ou quadros penetrem na tubulação hidrossanitária.

---

## 11. CONTRAVENTAMENTO, DIAFRAGMAS, SHEAR WALLS E CARGAS DE VENTO

A estabilidade tridimensional de edificações estruturadas em wood e steel frame baseia-se na ação conjunta de diafragmas horizontais rígidos (pisos e coberturas) e painéis verticais de cisalhamento (*shear walls*).

### 11.1 Ação de Diafragma dos Fechamentos Estruturais
- As chapas de OSB estrutural (espessuras de $11.1\text{ mm}$ a $18.3\text{ mm}$) ou chapas cimentícias estruturais atuam como a alma de uma grande viga mista:
  - As placas absorvem os esforços de cisalhamento no plano (*shear flow* $q = V / L$).
  - As guias superior e inferior atuam como as mesas comprimida e tracionada.
  - Os montantes de extremidade atuam como enrijecedores verticais de bordo.
- **Passo de Fixação Estrutural (Nailing / Screwing Schedule)**:
  - O motor detalha o espaçamento de pregos/parafusos:
    - No perímetro das placas: passo de $100\text{ mm}$ a $150\text{ mm}$ entre fixadores, a uma distância mínima de $10\text{ mm}$ da borda da chapa.
    - Nos montantes intermediários internos do painel: passo de $200\text{ mm}$ a $300\text{ mm}$.
    - Essa especificação entra diretamente na lista de ferragens e nas instruções para as pontes automatizadas de pregar/parafusar (Weinmann WUP).

### 11.2 Distribuição de Esforços de Vento Conforme NBR 6123
1. **Velocidade Básica e Pressão Dinâmica do Vento**:
   - $V_0$ definido de acordo com o mapa de isopletas do Brasil (de $30\text{ a }50\text{ m/s}$).
   - Fatores $S_1$ (topográfico), $S_2$ (rugosidade do terreno e dimensões da edificação) e $S_3$ (fator estatístico/ocupação):
     $$V_k = V_0 \cdot S_1 \cdot S_2 \cdot S_3$$
     $$q = 0.613 \cdot V_k^2 \quad (\text{N/m}^2)$$
2. **Cálculo da Força Global de Arraste por Pavimento**:
   - O motor calcula a área de fachada exposta por orientação ($X$ e $Y$), multiplica pelos coeficientes de pressão externa e interna ($c_{pe} - c_{pi}$) e determina a força cortante total de base $V_x$ e $V_y$.
3. **Alocação de Esforço por Rigidez de Parede**:
   - A força cortante é distribuída entre os painéis contraventados proporcionalmente à sua rigidez transversal ($K_i$ calculada pela razão $L/H$ e pela rigidez das conexões).
   - O motor verifica o código `V-017`: o comprimento efetivo acumulado de paredes contraventadas em cada eixo ortogonal deve ser superior ao mínimo exigido para manter a taxa de distorção de pavimento (*story drift*) abaixo de $H/500$.

---

## 12. CÁLCULO ESTRUTURAL ANALÍTICO E MEMORIAL AUTOMATIZADO

Para validação legal e emissão de Anotação de Responsabilidade Técnica (ART) por engenheiros civis habilitados, o motor integra um pipeline analítico rigoroso:

### 12.1 Módulo Analítico NBR 14762:2010 (Light Steel Frame)
- **Método das Larguras Efetivas (MLE) e Seções Efetivas**:
  - Consideração da flambagem local da alma e mesa dos perfis C sob compressão axial e flexão.
  - Cálculo da largura reduzida $b_{ef}$ para elementos comprimidos esbeltos:
    $$b_{ef} = \rho \cdot b$$
    Onde $\rho$ é o fator de redução calculado a partir da esbeltez relativa da placa $\lambda_p$.
- **Flambagem Distorcional**:
  - Verificação analítica da rotação das abas enrijecedoras (lábios) sob compressão.
- **Flambagem Global (Flexo-Torção)**:
  - Cálculo da carga crítica de Euler e momento crítico elástico de flexo-torção ($M_e$).

### 12.2 Módulo Analítico NBR 7190:2022 (Light Wood Frame)
- **Valores de Cálculo das Propriedades da Madeira**:
  $$f_{c0,d} = \frac{k_{mod} \cdot f_{c0,k}}{\gamma_w}$$
  Onde $k_{mod} = k_{mod,1} \cdot k_{mod,2} \cdot k_{mod,3}$ (considerando classe de carregamento permanente/vento, classe de umidade de serviço e classificação visual/mecânica da madeira serrada).
- **Esbeltez e Flambagem de Montantes de Madeira**:
  $$\lambda = \frac{L_{flambagem}}{i} \le 140$$
  Cálculo do coeficiente de instabilidade $k_c$ para compressão paralela às fibras.

### 12.3 Geração do Memorial de Cálculo Automatizado
- Saída: Documento em HTML5 interativo e PDF assinado contendo:
  - Memória descritiva dos materiais e coeficientes normativos aplicados.
  - Diagrama de caminho de cargas verticais e horizontais.
  - Tabelas de tensões máximas atuantes vs admissíveis para cada montante, viga e verga crítica.
  - Gráfico de deformada elástica sob vento máximo.
  - Resumo de fatores de segurança obtidos (garantindo que todo elemento tenha $FS \ge 1.0$).

---

## 13. OTIMIZAÇÃO LINEAR 1D DE BARRAS (COLUMN GENERATION & REMNANTS)

O módulo `src/vigora_frame/quantities.py` é transformado em um sistema avançado de corte linear.

```
       PLANO DE CORTE OTIMIZADO 1D COM REAPROVEITAMENTO DE RETALHO
       
       Barra Mãe Comercial: 6000mm
       ┌───────────┬──────────────┬─────────────┬──────────┬───────────┐
       │ Peça P01  │   Peça P02   │  Peça P03   │ Peça P04 │ RETALHO   │
       │  1800mm   │    1800mm    │   1200mm    │  950mm   │ (REMNANT) │
       └───────────┴──────────────┴─────────────┴──────────┴───────────┘
       ▲           ▲              ▲             ▲          ▲
       0mm         1803mm         3606mm        4809mm     5762mm    6000mm
                   [Kerf 3mm]     [Kerf 3mm]    [Kerf 3mm] [238mm -> Descarte ou Sucata]
```

### 13.1 Formulação Matemática do Cutting Stock Problem (CSP)
- O problema é modelado como Programação Linear Inteira (ILP) com **Geração de Colunas de Gilmore-Gomory**:
  - **Minimizar**: Custo total de barras consumidas + Penalização por desperdício.
    $$\min \sum_{j \in P} c_j x_j + \sum_{r \in R} w_r y_r$$
  - **Sujeito a**: Atendimento integral da demanda de todas as peças do projeto:
    $$\sum_{j \in P} a_{ij} x_j \ge d_i \quad \forall i \in \{1, \dots, M\}$$
- **Geração de Padrões via Problema da Mochila (Knapsack Problem)**:
  - A cada iteração do método Simplex, um novo padrão de corte ótimo é gerado resolvendo um subproblema da mochila com os preços-sombra das restrições de demanda.

### 13.2 Regras Industriais de Corte
1. **Kerf Dinâmico**:
   - A espessura do disco de serra varia conforme a máquina e o material:
     - Serra para madeira (disco widia): $\text{kerf} = 3.2\text{ mm}$ a $4.2\text{ mm}$.
     - Serra para perfis de aço (fita ou serra fria): $\text{kerf} = 2.0\text{ mm}$ a $3.0\text{ mm}$.
     - Puncionadeira CNC (corte guilhotina sem viruta): $\text{kerf} = 0.0\text{ mm}$.
2. **Corte Compartilhado em Esquadria**:
   - Se a Peça A termina com corte de $45^\circ$ e a Peça B inicia com corte complementar de $45^\circ$, ambas são agrupadas consecutivamente na mesma barra para que uma única descida do disco realize o acabamento de ambas as peças, economizando tempo de ciclo e $1\text{ kerf}$ de material.
3. **Gestão e Reuso de Retalhos (Remnant Tracking)**:
   - Sobras de barra com comprimento $L_{sobra} \ge 800\text{ mm}$ são classificadas como **Retalhos Reutilizáveis (Remnants)** e registradas em um banco de dados local com etiqueta e ID único.
   - Na próxima execução de qualquer projeto, o otimizador lê a tabela de retalhos disponíveis e prioriza seu consumo antes de cortar barras comerciais novas de $6.00\text{ m}$.

---

## 14. NESTING 2D REAL DE CHAPAS E REAPROVEITAMENTO DE MIOLOS

A ausência de plano de corte 2D para painéis estruturais (OSB, compensados, placas cimentícias, drywall) é responsável por perdas de até $18\%$ de matéria-prima em fábricas desorganizadas. O módulo `src/vigora_frame/engine/nesting2d.py` elimina esse desperdício.

```
       PLANO DE CORTE 2D — CHAPA MÃE DE OSB (1200 x 2400 mm)
       
       ┌──────────────────────────────┬──────────────────────────────┐
       │                              │   Recorte Janela J01         │
       │   Fechamento Parede P01      │   Aproveitado para Bandeira  │
       │   (1200 x 1800 mm)           │   (600 x 1200 mm)            │
       │                              │                              │
       │                              ├──────────────────────────────┤
       │                              │   Peitoril P03 (300 x 800)   │
       │                              ├──────────────┬───────────────┤
       │                              │ Retalho Util │ Refugo Descart│
       └──────────────────────────────┴──────────────┴───────────────┘
       ◄─────────── Sentido Estrutural do Grão (Fibras) ───────────►
```

### 14.1 Algoritmo Guillotine MaxRects 2D
- Como a grande maioria das indústrias utiliza serras seccionadoras que realizam apenas cortes de borda a borda (*guillotine cuts*), o algoritmo deve respeitar estritamente a árvore de cortes guilhotina:
  1. Primeiro nível de corte longitudinal (*rip cut*).
  2. Segundo nível de corte transversal (*cross cut*).
  3. Terceiro nível de recorte de cantos (*trim cut*).
- **Restrição Inviolável de Sentido de Grão (Grain Orientation)**:
  - Painéis de OSB possuem maior resistência à flexão ao longo do seu comprimento longitudinal (orientação preferencial das tiras de madeira na camada externa).
  - Placas especificadas para contraventamento de paredes ou pisos não podem sofrer rotação de $90^\circ$ no plano de nesting se isso violar a especificação do cálculo estrutural. O algoritmo possui a flag booleana `allow_rotation: false` para peças estruturais primárias.

### 14.2 Reintrodução Automática de Miolos de Aberturas
- Quando um painel de parede possui uma janela de $1200\times 1200\text{ mm}$, o fechamento frontal é modelado com um recorte retangular.
- Esse miolo de $1.44\text{ m}^2$ não é descartado: o motor extrai esse polígono e o insere na fila de matéria-prima de entrada (*reusable parent sheets*).
- Peças menores do projeto (bandeiras sobre portas, peitoris, caixotes de escada, tiras de enchimento) são alocadas preferencialmente dentro desse miolo.

### 14.3 Saídas Gráficas e CNC do Nesting 2D
- **Mapa de Corte em PDF**: Desenho de cada chapa comercial com cotas de avanço da serra, numeração das peças, identificador do painel de destino e código de barras para rastreabilidade fabril.
- **Exportação DXF / G-Code para Router CNC**: Arquivo com os vetores de usinagem, ordem de furação para caixas elétricas, compensação de diâmetro de fresa (*tool radius compensation*) e micro-pontes de fixação (*tabs*) para impedir que peças soltas colidam com o cabeçote da fresa.

---

## 15. EXPORTADORES INDUSTRIAIS DIRETOS (CAM/CNC: HUNDEGGER, WEINMANN, HOWICK, FRAMECAD)

O motor comunica-se diretamente com o maquinário das principais linhas automatizadas do mundo.

```
       FLUXO DE DADOS DIRETO MOTOR -> MÁQUINAS CNC
       
                 ┌────────────────────────────────┐
                 │     VIGORA FRAME ENGINE        │
                 └──────────────┬─────────────────┘
                                │
       ┌────────────────┬───────┴────────┬────────────────┐
       ▼                ▼                ▼                ▼
   HUNDEGGER        WEINMANN          HOWICK           FRAMECAD
   (BTL / BTLx)     (WUP / WUD)       (CSV / HCD)      (RFX / Factory)
   Corte/Entalhe    Montagem/Pregar   Perfis C/U LSF   Perfis LSF
   Madeira Robótica Painéis Completos Conformação Frio Estampagem Total
```

### 15.1 Hundegger BTL / BTLx (Wood Frame)
- Formato padrão internacional para centros de usinagem robotizados Hundegger (modelos K2, Speedcut, Robot-Drive):
  - Definição da barra de madeira no sistema de coordenadas da máquina: dimensões $X, Y, Z$.
  - Mapeamento das operações tridimensionais paramétricas:
    - `LapJoint` (entalhes de meia-madeira para encaixes cruzados).
    - `JackRafterCut` (corte composto angular de espigões e rincões).
    - `Pocket` (rebaixos cegos para embutimento de estribos metálicos).
    - `Drilling` (furações passantes com diâmetro, profundidade e ângulo especificados).
    - `LogSlotting` (dentes de serra para degraus de escadas).

### 15.2 Weinmann WUP / WUD (Wood Frame & Fechamentos)
- Padrão do grupo HOMAG / Weinmann para linhas de fabricação automatizada de painéis (estações de montagem de esqueleto de madeira e pontes multifuncionais de grampeamento e fresamento de placas):
  - Camada 1: Estrutura do esqueleto de madeira (posicionamento de guias e montantes).
  - Camada 2: Folhas de OSB e sequenciamento de grampos/parafusos com passo exato de borda e meio de painel.
  - Camada 3: Trajetória de fresamento de aberturas de janelas e portas executadas após o plaqueamento do painel inteiro.
  - Camada 4: Furação de tomadas e interruptores elétricos na placa.

### 15.3 Howick CSV / HCD (Light Steel Frame)
- Formato de controle de conformadoras CNC Howick (modelos FRAMA 3200, 5600):
  - Comandos operacionais por linha de comando de avanço milimétrico de fita de aço galvanizado:
    - `SW` (*Start Web Cut*): corte inicial de esquadro.
    - `DC` (*Dimple Hole*): punção cônica rebaixada para embutimento da cabeça do parafuso auto-brocante, garantindo que o perfil fique perfeitamente liso para receber a placa de drywall sem ressaltos.
    - `PT` (*Pass Through / Service Hole*): furo oblongo de $34\times 75\text{ mm}$ para passagem de eletrodutos e canalizações.
    - `LC` (*Lip Cut*): corte do lábio enrijecedor para permitir o encaixe telescópico do montante na guia sem necessidade de corte manual.
    - `EW` (*End Web Cut*): corte final da peça.

### 15.4 FrameCAD RFX (Light Steel Frame)
- Formato proprietário de dados para perfiladeiras industriais FrameCAD:
  - Instruções de estampagem sincronizada de dobras e punções de topo e abas.
  - Impressão a jato de tinta direta (*Inkjet Print Marking*): comando que instrui a cabeça de impressão da máquina a imprimir o código da peça (ex: `W01-PN02-STUD-14`), o código do painel, a posição sequencial e a orientação (seta apontando para o topo) na alma do perfil de aço enquanto ele é perfilado.

---

## 16. ARQUITETURA DO PLUGIN REVIT 2.0 (C# NATIVO, IPC, ASSEMBLIES E LIVE VIEW)

A integração com o Autodesk Revit evolui de um script isolado para uma extensão empresarial completa.

```
       ARQUITETURA DE INTEGRAÇÃO REVIT 2.0 (IPC DE ALTA PERFORMANCE)
       
       ┌───────────────────────────────────────────────────────────────┐
       │                   AUTODESK REVIT (2024 - 2026)                 │
       │                                                               │
       │  ┌─────────────────────────┐     ┌─────────────────────────┐  │
       │  │  Revit Add-in (C# .NET) │     │   Dockable Panel (WPF)  │  │
       │  │  - Ribbon Tab "Vigora"  │◄───►│   - Árvore de Painéis   │  │
       │  │  - ExternalEvent Handler│     │   - Visualizador de Erro│  │
       │  │  - DirectContext3D (HUD)│     │   - Live Settings       │  │
       │  └────────────┬────────────┘     └─────────────────────────┘  │
       └───────────────┼───────────────────────────────────────────────┘
                       │ Comunicação Local Ultrarrápida (IPC)
                       │ Named Pipes / gRPC com Protobuf
                       ▼
       ┌───────────────────────────────────────────────────────────────┐
       │           VIGORA ENGINE CORE DAEMON (CPython 3.12)            │
       │  • Serviço em background persistente (Zero boot latency)     │
       │  • Grafo de execução paralelo & Cache de cálculo              │
       │  • Motor geométrico puro e independente                       │
       └───────────────────────────────────────────────────────────────┘
```

### 16.1 Comunicação IPC de Alta Velocidade via Named Pipes
- Eliminação do overhead de subprocessos `python.exe` e escrita intermediária de arquivos JSON em disco:
  - O motor roda como um serviço local em segundo plano (*background daemon*).
  - A comunicação com o add-in C# do Revit ocorre através de **Windows Named Pipes** transmitindo dados binários compactados via **Protocol Buffers**.
  - O tempo de transmissão de dados de um projeto com mais de 5.000 peças cai de $12\text{ segundos}$ (serialização JSON em disco) para **$150\text{ milissegundos}$**.

### 16.2 Modelagem como Famílias Estruturais Nativas e Assemblies
1. **Transição de `DirectShape` para Famílias Reais**:
   - As peças deixam de ser sólidos estáticos de modelo genérico e passam a ser instanciadas como famílias do Revit nas categorias corretas:
     - Montantes e vigas: `OST_StructuralFraming`.
     - Colunas e pilaretes: `OST_StructuralColumns`.
     - Chapas de fechamento: `OST_Parts` ou `OST_CurtainWallPanels`.
   - Permite que o engenheiro utilize filtros nativos de visibilidade gráfica do Revit (VG), tabelas nativas de materiais estruturais e conexões analíticas para cálculo externo (Robot Structural Analysis, TQS, Cypecad).
2. **Criação de Assemblies (Conjuntos) por Painel**:
   - Todas as peças pertencentes ao painel `P01` são agrupadas em um `AssemblyInstance` nativo do Revit com nome correspondente.
   - O add-in aciona o método `AssemblyViewUtils.CreateDetailSectionView()` do Revit para gerar automaticamente:
     - Vista em elevação do painel no navegador de projeto.
     - Vista em planta e corte vertical.
     - Tabela de quantitativo de peças do conjunto inserida automaticamente na folha.

### 16.3 HUD Interativo de Modelagem com DirectContext3D
- Visualização em tempo real na própria viewport 3D do Revit:
  - Ao selecionar uma parede arquitetônica, o motor desenha instantaneamente um wireframe colorido translúcido dos montantes calculados usando a API `DirectContext3D` do Revit, **sem criar elementos permanentes no banco de dados do modelo**.
  - Se o usuário mover a janela em tempo real, os montantes *king*, *jack* e a verga acompanham o movimento dinamicamente com renderização a 60 FPS.
  - O botão de confirmação efetiva a transação no documento apenas quando o usuário estiver satisfeito com a disposição do framing.

---

## 17. GERAÇÃO DE PRANCHAS NBR, RENDERIZADOR VETORIAL E COTAGEM ANTICOLISÃO

O módulo de documentação gráfica técnica é reconstruído para eliminar a dependência pesada do Matplotlib.

```
       COMPOSIÇÃO DE FOLHA A1 (NBR 10068 / NBR 10126)
       
       ┌─────────────────────────────────────────────────────────────┬──────────┐
       │ (MARGEM ESQUERDA 25mm PARA FIXAÇÃO EM PASTA)                │ NOTAS    │
       │                                                             │ GERAIS & │
       │  [VISTA 1: ELEVAÇÃO DO PAINEL — ESCALA 1:20]                │ TABELA   │
       │   Cotas em 4 linhas cascateadas sem colisão                 │ DE CORTE │
       │   Peças numeradas com balões dogleg a 45°                   │          │
       │   Juntas de dilatação e eixos de aberturas cotados          │          │
       │                                                             ├──────────┤
       │  [VISTA 2: DETALHE CONSTRUTIVO DO CANTO — ESCALA 1:5]       │ QUADRO   │
       │   Corte de topo exibindo montantes, parafusos e isolamento  │ DE       │
       │                                                             │ FIXAÇÃO  │
       │  [VISTA 3: PLANTA DE LOCAÇÃO DOS PAINÉIS — ESCALA 1:50]     ├──────────┤
       │   Orientação Norte, coordenadas de montagem, cotas totais   │ LEGENDA  │
       │                                                             │ NBR10068 │
       │ (MARGENS SUPERIOR, INFERIOR E DIREITA: 10mm)                │ (178 mm) │
       └─────────────────────────────────────────────────────────────┴──────────┘
```

### 17.1 Motor Vetorial Puro de Alta Performance (PyMuPDF / SkiaSharp)
- Geração direta de primitivas vetoriais:
  - Linhas, polígonos, textos TrueType embutidos, arcos de cota e hachuras normativas processados diretamente em buffers de memória binária.
  - Tempo de geração: prancha completa de $10\text{ painéis}$ em formato A1 renderizada em **menos de $0.5\text{ segundos}$** (redução de $95\%$ no tempo de processamento comparado com Matplotlib).

### 17.2 Algoritmo de Cotagem Anticolisão em Cascata
O motor resolve o problema crônico de sobreposição de números em projetos densos por meio de uma rotina de ordenação em 4 níveis rígidos de cotas:
1. **Linha de Cota 1 (Interna)**:
   - Mede vãos livres individuais entre montantes consecutivos e espessura das peças.
2. **Linha de Cota 2 (Vãos e Aberturas)**:
   - Mede a distância da extremidade do painel até a lateral esquerda do caixilho, a largura livre do vão e a distância até o final da parede.
3. **Linha de Cota 3 (Placas de Fechamento)**:
   - Mede os limites das juntas verticais das placas de OSB e gesso.
4. **Linha de Cota 4 (Externa Total)**:
   - Cota contínua da dimensão total de fabricação do painel de ponta a ponta.

- **Desvio Automático de Balões de Posição (Dogleg Leaders)**:
  - Quando dois montantes estão separados por menos de $80\text{ mm}$ (ex: montante *King* e *Jack* encostados), os balões circulares de marcação de peça são escalonados em alturas alternadas com linha de chamada inclinada a $45^\circ$, garantindo $100\%$ de legibilidade sem cruzamento de linhas.

### 17.3 Detalhamento Construtivo Automatizado em Escala 1:5 e 1:10
- O motor corta seções horizontais e verticais 3D diretamente dos painéis e extrai detalhes ampliados de nós críticos:
  - Detalhe de Encontro em L de Cantos Externos com manta de vedação e isolamento térmico.
  - Detalhe de Encontro em T de Paredes Internas.
  - Detalhe de Ligação de Guia de Base no Radier com calço de argamassa e chumbador.
  - Detalhe de Apoio de Treliça sobre a Guia Superior com conector anti-vento (*hurricane clip*).

---

## 18. ORÇAMENTO PARAMÉTRICO INTEGRADO COM SINAPI / TCPO E MÃO DE OBRA

A aba de custos em `src/vigora_frame/export/xlsx.py` conecta-se às referências oficiais do mercado brasileiro de construção civil.

### 18.1 Mapeamento de Códigos de Insumos Oficiais da Caixa Econômica Federal (SINAPI)
- Para cada elemento físico gerado, o motor vincula os códigos vigentes da base SINAPI desonerada e não-desonerada:

| Item do Modelo Vigora | Unid. | Código SINAPI de Referência | Descrição Técnica SINAPI |
|---|---|---|---|
| **Perfil Montante C90 LSF** | m | `39420` | Perfil de aço galvanizado para drywall/LSF, guia/montante, espessura 0.95 mm |
| **Perfil Montante C140 LSF** | m | `39422` | Perfil de aço galvanizado estrutural enrijecido montante C 140x0.95 mm |
| **Madeira Serrada C24 Pinus** | m³ | `05068` | Viga/prancha de madeira tratada pinus em autoclave com preservativo CCA |
| **Chapa OSB 11.1 mm** | m² | `39443` | Chapa de madeira compensada estrutural orientada OSB, e=11.1 mm |
| **Chapa Cimentícia 10 mm** | m² | `39438` | Placa cimentícia impermeabilizada para fechamento externo e=10 mm |
| **Placa Gesso Drywall ST 12.5** | m² | `04813` | Placa de gesso acartonado standard ST, espessura 12.5 mm |
| **Membrana Hidrófuga** | m² | `43125` | Manta/membrana de polipropileno impermeável e respirável (Housewrap) |
| **Parafuso Auto-brocante 4.2x19**| cento | `43512` | Parafuso de aço zincado auto-brocante cabeça wafer ponta broca |
| **Chumbador Expansivo 1/2"x4"**| un | `11964` | Chumbador de aço mecânico com jaqueta e cone (Parabolt) |
| **Lã de Vidro / Rocha 50 mm** | m² | `00156` | Manta isolante de lã de rocha basáltica / vidro e=50 mm, d=32 kg/m³ |

### 18.2 Estimativa Paramétrica de Homem-Hora (HH) de Fabricação e Montagem
- O orçamento calcula analiticamente o custo de mão de obra direta com base nas taxas de produtividade médias brasileiras:
  - **Corte e montagem de esqueleto de painéis em mesa de fábrica**: $0.25\text{ a }0.35\text{ HH / m}^2$ de painel.
  - **Plaqueamento e colocação de membrana em fábrica**: $0.15\text{ a }0.20\text{ HH / m}^2$.
  - **Montagem e ancoragem de painéis em canteiro de obras**: $0.30\text{ a }0.45\text{ HH / m}^2$.
  - **Montagem, içamento e travamento de treliças de cobertura**: $0.40\text{ a }0.60\text{ HH / treliça}$.

---

## 19. CATÁLOGO COMPLETO E EXPANDIDO DE VALIDAÇÕES (V-001 A V-135)

O sistema de validação é a barreira técnica que impede a fabricação de modelos com erros físicos ou normativos.

| Código | Severidade | Elemento Afetado | Condição Geométrica / Normativa Verificada | Ação Sugerida pelo Motor (Hint) |
|---|---|---|---|---|
| **V-001** | Erro | Parede | Comprimento de framing da parede inferior a $60\text{ mm}$. | Una o segmento à parede contígua ou remova o dente arquitetural. |
| **V-004** | Erro | Steel Frame | Desalinhamento (*in-line framing*) entre apoio de treliça/viga e montante inferior $> 20\text{ mm}$. | Alinhe a grade de montantes da parede com o eixo das treliças de teto. |
| **V-006** | Erro | Painel | Espaçamento entre montantes consecutivos excede o máximo normativo ($400\text{ mm}$ ou $600\text{ mm}$). | Insira um montante intermediário para garantir apoio de placas. |
| **V-011** | Aviso | Catálogo | Utilização de perfil, chapa ou conector marcado como não aprovado pelo engenheiro. | Homologue o item no catálogo ou substitua pelo item padrão. |
| **V-017** | Erro | Pavimento | Comprimento efetivo acumulado de contraventamento (*Shear Walls*) inferior ao mínimo de vento. | Aumente a quantidade de painéis com chapas estruturais ou fitas em X. |
| **V-018** | Erro | Abertura | Lateral do caixilho a menos de $100\text{ mm}$ do canto interno de parede. | Afaste a abertura do canto para permitir a montagem dos montantes *King* e *Jack*. |
| **V-019** | Erro | Abertura | Distância livre entre aberturas adjacentes inferior a $150\text{ mm}$. | Una as duas aberturas sob uma única verga contínua comum ou afaste-as. |
| **V-024** | Aviso | Parede Portante | Parede portante do piso superior sem alinhamento direto com parede estrutural abaixo. | Carga descarregará em flexão nas vigas de entrepiso; confirme a seção da viga. |
| **V-057** | Erro | Peça | Peça estrutural primária com menos de 2 pontos de conexão física modelados. | Peça solta no espaço; revise as extremidades de corte e fixadores. |
| **V-058** | Erro | Ligação | Conexão estrutural sem fixador definido ou com quantidade nula de pregos/parafusos. | Especifique o fixador padronizado em `rules/ruleset.yaml`. |
| **V-061** | Erro | Painel | Interferência volumétrica sólida (colisão) entre duas peças estruturais no mesmo plano. | Ajuste os comprimentos de corte para criar contato de face perfeito. |
| **V-062** | Erro | Placa | Borda ou junta de placa estrutural sem apoio em montante ou bloqueio de madeira/aço. | Adicione um montante de apoio (*Sheet Stud*) sob a junta de placa. |
| **V-063** | Erro | Peça | Comprimento de corte de peça superior ao maior comprimento de barra comercial em estoque. | Crie uma emenda estrutural com placa de união sobre um ponto de apoio. |
| **V-064** | Erro | Peça | Peça gerada com comprimento de corte nulo ou negativo. | Erro topológico; verifique os eixos de interseção da parede. |
| **V-071** | Erro | Piso | Polígono de contorno de piso com autointerseção ou laço geométrico aberto. | Corrija o contorno do piso no CAD/Revit para formar um polígono fechado. |
| **V-074** | Erro | Painel | Vão livre aleatório entre peças contíguas entre $2.5\text{ mm}$ e $60\text{ mm}$. | Elimine o vazio aleatório encostando as peças ou abra um vão mínimo de $60\text{ mm}$. |
| **V-075** | Erro | Encontro | Paredes se sobrepõem em planta ou possuem folga desconectada entre $0.5\text{ e }300\text{ mm}$. | Ajuste os eixos das paredes no Revit para que as pontas se unam com precisão. |
| **V-076** | Erro | Pavimento | Cota de fundo do entrepiso em desacordo com o topo das paredes portantes inferiores. | Ajuste a altura desconectada das paredes ou a restrição superior de nível. |
| **V-078** | Erro | Junção | Ângulo de encontro entre paredes fora dos padrões homologados. | Utilize ângulos em esquadro ou conforme os módulos de meia-esquadria. |
| **V-079** | Erro | Abertura | Abertura de porta ou janela interceptando a interseção de um encontro de paredes em T ou X. | Remova a abertura do ponto de cruzamento de paredes. |
| **V-082** | Erro | Escada | Espelho de degrau $> 185\text{ mm}$ ou regra de Blondel fora do intervalo de $620\text{ a }645\text{ mm}$. | Ajuste a quantidade de degraus ou o comprimento de avanço da escada. |
| **V-083** | Erro | Escada | Altura livre de passagem sobre a linha de bocéis da escada inferior a $2.00\text{ m}$. | Aumente a abertura do furo no piso superior no sentido da subida. |
| **V-084** | Erro | Escada | Último degrau da escada desalinhado da borda do vão do piso superior. | Ajuste o ponto de chegada da escada para encontrar exatamente a viga de borda. |
| **V-085** | Erro | Escada | Corpo da escada colidindo com paredes laterais não previstas. | Afaste a parede ou ajuste a largura útil da escada. |
| **V-086** | Erro | Cobertura | Parede alta ou platibanda mais baixa que a cumeeira da cobertura acrescida de $200\text{ mm}$. | Eleve o topo da parede de platibanda para cobrir totalmente o telhado. |
| **V-087** | Aviso | Cobertura | Desalinhamento de cotas de beiral entre telhados adjacentes que convergem. | Nivele a cota de apoio das vigas de testeira de ambos os telhados. |
| **V-088** | Erro | Cobertura | Cumeeira de telhado secundário de rincão ultrapassando a cota da cumeeira principal. | Reduza a inclinação ou a largura da asa para que ela apoie sob a água principal. |
| **V-090** | Erro | Caixa d'Água | Altura livre sob o telhado insuficiente para abrigar o reservatório e folga de $0.50\text{ m}$. | Mova a caixa para mais perto da cumeeira ou aumente a inclinação do telhado. |
| **V-091** | Erro | Caixa d'Água | Reservatório sem paredes portantes estruturais paralelas a até $1.50\text{ m}$ no piso inferior. | Posicione a caixa sobre o shaft ou paredes de banheiro portantes. |
| **V-092** | Erro | Caixa d'Água | Vão livre das vigas duplas de sustentação da caixa d'água superior a $1.50\text{ m}$. | Adicione parede de apoio ou aumente a seção das vigas da plataforma. |
| **V-093** | Erro | Caixa d'Água | Colisão tridimensional do envelope de manutenção da caixa com peças da cobertura. | Acione a geração de treliças de ático na zona do reservatório. |
| **V-097** | Erro | Abertura | Abertura com vão $> 900\text{ mm}$ em parede portante sem verga estrutural dimensionada. | Insira uma verga estrutural em cutelo (*header*) sobre a abertura. |
| **V-098** | Erro | Fundação | Distância de chumbador à borda do concreto inferior a $70\text{ mm}$ (risco de quebra de radier). | Recue a linha de ancoragem ou projete dente de fundação mais largo. |
| **V-099** | Erro | Piso | Flecha máxima calculada de viga de entrepiso excede $L/360$ para carga total. | Reduza o espaçamento das vigas ou utilize vigas I com maior altura de alma. |
| **V-100** | Aviso | Manufatura | Painel de parede com peso total superior a $250\text{ kg}$ sem pontos de içamento mecânico. | Preveja furos de içamento para guindaste ou divida o painel em dois menores. |
| **V-101** | Erro | Steel Frame | Parafuso estrutural aplicado a menos de $1.5\times$ seu diâmetro do bordo livre do perfil. | Reposicione o parafuso para garantir a integridade contra rasgamento da chapa. |
| **V-102** | Aviso | Treliça | Treliça tesoura com vão $> 8.00\text{ m}$ sem detalhe de apoio lateral deslizante (*slotted bracket*). | Especifique o conector deslizante para permitir a expansão lateral livre. |
| **V-103** | Erro | Instalações | Furo executado em montante com diâmetro superior a $0.4\times$ a largura da alma. | Aplique o reforço metálico de montante (*stud shoe*) ou desvie a tubulação. |
| **V-104** | Aviso | Placas | Junta vertical de chapa estrutural com defasagem inferior a $300\text{ mm}$ de canto de janela. | Reposicione as placas para que o recorte envolva o canto em formato de "C" (evita trincas). |
| **V-105** | Erro | Madeira | Umidade de equilíbrio de projeto incompatível com a classe de serviço da NBR 7190. | Especifique madeira seca em estufa com teor de umidade inferior a $18\%$. |
| **V-106** | Erro | Steel Frame | Ausência de manta de isolamento galvânico (EPDM) sob a guia inferior assentada no radier. | Aplique a fita de borracha/neoprene sob toda a extensão da base da parede. |
| **V-107** | Erro | Parede Alta | Esbeltez de montante de pé-direito duplo excede limite normativo sem travamento lateral. | Adicione linha de bloqueios sólidos ou fitas metálicas no meio do vão. |
| **V-108** | Erro | Cobertura | Beiral em balanço de oitão superior a $600\text{ mm}$ sem travessas em escada (*lookouts*). | Crie a estrutura em escada com treliça rebaixada de oitão (*drop-top truss*). |
| **V-109** | Erro | Entrepiso | Viga de piso interrompida para passagem de duto sem cabeceira de borda (*header joist*). | Envolva a abertura com vigas duplas de reforço perimetrais e estribos. |
| **V-110** | Aviso | Logística | Comprimento de painel $> 12.0\text{ m}$ ou altura $> 3.20\text{ m}$ (excede limite de transporte rodoviário). | Fatie o painel para adequação à mesa de montagem e carroceria de caminhão. |

---

## 20. ARQUITETURA DE SOFTWARE CORE, PARALELISMO DAG E TIPAGEM ESTRITA

A base de código em `src/vigora_frame/` deve ser mantida com arquitetura de alta confiabilidade:

### 20.1 Tipagem Imutável e Geometria Pura
- A geometria deixa de usar listas de números flutuantes e passa a operar com tipos imutáveis e operações vetoriais puras:
  ```python
  from pydantic import BaseModel, Field
  
  class Point2D(BaseModel):
      x: float
      y: float
      
      def distance_to(self, other: "Point2D") -> float:
          return math.hypot(self.x - other.x, self.y - other.y)
  
  class Segment2D(BaseModel):
      p0: Point2D
      p1: Point2D
      
      @property
      def length(self) -> float:
          return self.p0.distance_to(self.p1)
  ```

### 20.2 Grafo de Execução Acíclico (DAG) Paralelizado
- O arquivo `builder.py` orquestra a resolução como um grafo de fluxo de dados:
  1. `WallTopologyStage`: Executa a divisão de cruzamentos e análise de encontros.
  2. `ParallelPanelStage`: Fatura os painéis de cada parede concorrentemente em múltiplos processos.
  3. `FloorStage`: Depende das paredes portantes inferiores; calcula o diafragma de entrepiso.
  4. `RoofStage`: Lê as cotas de topo de parede e o envelope da caixa d'água; resolve as treliças.
  5. `GlobalValidationStage`: Executa a bateria de validações `V-001` a `V-135`.
  6. `ManufacturingStage`: Dispara o nesting 1D/2D e os exportadores CAM.
  7. `DrawingStage`: Compila o PDF vetorial das pranchas técnicas.

---

## 21. DESEMPENHO TÉRMICO, ACÚSTICO E ESTANQUEIDADE (NBR 15575)

A NBR 15575:2021 — Desempenho de Edificações Habitacionais — é o padrão mínimo obrigatório para toda construção habitacional no Brasil. Sistemas em *wood frame* e *steel frame* possuem características fundamentalmente distintas de alvenaria convencional, e o motor deve parametrizar todas as camadas da envoltória para garantir conformidade.

### 21.1 Desempenho Térmico: Transmitância e Capacidade Térmica

O motor calcula automaticamente o desempenho térmico de cada composição de parede a partir das camadas declaradas no catálogo:

```
       COMPOSIÇÃO TÍPICA DE PAREDE EXTERNA — WOOD FRAME (de fora para dentro)
       
       1. Revestimento externo (siding cimentício 8mm)     λ = 0.65 W/m·K
       2. Câmara de ar ventilada (25mm)                     R_ar = 0.17 m²·K/W
       3. Membrana hidrófuga respirável (Tyvek 0.5mm)       R ≈ 0.00 m²·K/W
       4. Chapa OSB estrutural (11.1mm)                     λ = 0.13 W/m·K
       5. Montantes de madeira 38x140mm + Lã de rocha 50mm
          • Seção madeira (fração 10%): λ = 0.15 W/m·K
          • Seção isolante (fração 90%): λ = 0.035 W/m·K
          → Resistência média ponderada (método das áreas)
       6. Barreira de vapor (polietileno 0.2mm)             R ≈ 0.00 m²·K/W
       7. Placa de gesso acartonado ST (12.5mm)             λ = 0.35 W/m·K
```

1. **Transmitância Térmica ($U$)**:
   - Calculada pela composição em série das resistências térmicas:
     $$U = \frac{1}{R_{si} + \sum R_i + R_{se}} \quad (\text{W/m}^2\cdot\text{K})$$
   - Onde $R_{si} = 0.13\text{ m}^2\cdot\text{K/W}$ (superfície interna) e $R_{se} = 0.04\text{ m}^2\cdot\text{K/W}$ (superfície externa).
   - **Limites NBR 15575 por zona bioclimática brasileira**:
     - Zonas 1 e 2 (Sul / Serra): $U \le 2.5\text{ W/m}^2\cdot\text{K}$.
     - Zonas 3 a 8 (Centro-Oeste, Nordeste, Norte): $U \le 3.7\text{ W/m}^2\cdot\text{K}$ para paredes de cor clara ($\alpha \le 0.6$).
   - O motor emite validação `V-111` se a composição parametrizada ultrapassar o limite da zona.

2. **Capacidade Térmica ($C_T$)**:
   - Paredes leves (*light frame*) possuem baixa inércia térmica. A norma exige:
     - $C_T \ge 130\text{ kJ/m}^2\cdot\text{K}$ para Zonas 1 a 7.
   - Soluções parametrizadas: uso de placa cimentícia de $10\text{ mm}$ interna (acumula calor) em vez de gesso, ou tijolo cerâmico de enchimento térmico no miolo da parede sem função estrutural.

3. **Pontes Térmicas em Steel Frame**:
   - A condutividade térmica do aço é ~$400\times$ maior que a da lã mineral. Os montantes de aço criam caminhos preferenciais de calor (*thermal bridges*).
   - O motor calcula o fator de correção de transmitância $U_{corrigido}$ pelo método de simulação 2D (ISO 10211) ou pelo método simplificado de fração de ponte térmica linear ($\Psi$):
     $$U_{corrigido} = U_{paralelo} + \frac{\sum \Psi_j \cdot l_j}{A_{parede}}$$
   - Se $U_{corrigido}$ ultrapassar o limite, o motor sugere aplicação de sistema ETICS (*External Thermal Insulation Composite System*) com EPS de $30\text{ a }50\text{ mm}$ colado na face exterior, sobre o OSB, eliminando completamente a ponte térmica.

### 21.2 Desempenho Acústico: Isolação Sonora Aérea e de Impacto

1. **Paredes Divisórias entre Unidades (Paredes de Geminação)**:
   - NBR 15575 Parte 4 exige:
     - $R_w \ge 45\text{ dB}$ (nível mínimo M) para paredes entre unidades autônomas.
     - $R_w \ge 50\text{ dB}$ (nível intermediário I).
   - Soluções que o motor parametriza:
     - **Montantes Alternados (*Staggered Studs*)**: Montantes de $38\times 89\text{ mm}$ alternados sobre guia de $38\times 140\text{ mm}$, eliminando a transmissão por ponte sólida. Cada face recebe placa dupla de gesso ($2\times 12.5\text{ mm}$) e lã mineral de $75\text{ mm}$ no miolo.
     - **Guias Duplas Desacopladas**: Duas guias de $38\times 89\text{ mm}$ separadas por $25\text{ mm}$ de ar ou fita resiliente amortecedora de EPDM. Transmissão exclusivamente por via aérea interna, sem ponte mecânica.
     - **Clips Resilientes e Perfis Ômega**: Fixação indireta das placas de gesso aos montantes por meio de clipes elásticos de aço mola que absorvem a vibração transmitida dos montantes antes que ela chegue ao gesso.

2. **Pisos entre Pavimentos (Isolação de Impacto)**:
   - NBR 15575 Parte 3 exige nível de ruído de impacto padronizado:
     - $L'_{nT,w} \le 80\text{ dB}$ (nível M) para pisos entre unidades.
     - $L'_{nT,w} \le 55\text{ dB}$ (nível S superior).
   - Soluções paramétrica:
     - **Piso Flutuante (*Floating Floor*)**: Contrapiso seco de OSB assentado sobre manta resiliente de polietileno expandido de $5\text{ mm}$ ou borracha reciclada de $8\text{ mm}$, desvinculado das vigas e paredes por junta perimetral.
     - **Forro Resiliente Suspenso**: Forro de gesso acartonado de $15\text{ mm}$ suspenso por tirantes com clips elásticos antivibratórios, criando câmara de $200\text{ mm}$ preenchida com lã mineral de $50\text{ mm}$.

### 21.3 Estanqueidade à Água e ao Ar

1. **Infiltração de Água de Chuva pela Fachada**:
   - O motor verifica que a composição de parede externa possui as 3 barreiras obrigatórias contra água:
     - **Camada 1 (Barreira Primária)**: Revestimento externo contínuo e juntas seladas com silicone ou EPDM.
     - **Camada 2 (Barreira Secundária)**: Membrana hidrófuga sobre o OSB (*housewrap*) com sobreposição mínima de $150\text{ mm}$ nas emendas horizontais e fita adesiva de butila nas penetrações de janela e tubulações.
     - **Camada 3 (Drenagem)**: Câmara de ar de $19\text{ a }25\text{ mm}$ entre a membrana e o revestimento, com respiros na base e no topo para equalização de pressão (*rainscreen principle*).
   - O motor quantifica automaticamente o comprimento total de fita adesiva impermeabilizante e a metragem quadrada de membrana hidrófuga, adicionando ao BOM de hardware.

2. **Infiltração de Ar (Blower Door Test)**:
   - Para atingir eficiência energética de nível Procel A, a taxa de troca de ar em despressurização a $50\text{ Pa}$ deve ser:
     $$n_{50} \le 3.0\text{ trocas/hora}$$
   - O motor identifica e sinaliza os pontos críticos de vazamento de ar:
     - Juntas entre guias inferiores e a fundação (fita de vedação contínua SILL_SEAL).
     - Penetrações de tubulações e eletrodutos através de paredes externas (selo acústico expansível ou espuma de poliuretano de baixa expansão).
     - Encontros de paredes externas com entrepisos (fita adesiva contínua de barreira de vapor nas emendas das placas de gesso).

---

## 22. PROTEÇÃO CONTRA INCÊNDIO (TRRF, COMPARTIMENTAÇÃO E BARREIRAS CORTA-FOGO)

Edificações de *light frame* são classificadas como construções combustíveis (madeira) ou semi-combustíveis (aço com chapas de gesso). O motor deve garantir conformidade com as Instruções Técnicas do Corpo de Bombeiros de cada estado e com a NBR 14432.

### 22.1 Tempo Requerido de Resistência ao Fogo (TRRF)

1. **Classificação e Exigências**:
   - Residências unifamiliares isoladas de até 2 pavimentos: TRRF = 30 min.
   - Geminações e sobrados de até 500 m²: TRRF = 30 a 60 min.
   - Edificações de uso misto ou acima de 3 pavimentos: TRRF = 60 a 90 min.

2. **Soluções Paramétrica por Composição de Parede**:
   - **30 min de TRRF**: 1 placa de gesso acartonado RF (*Fire Resistant*) de $15.0\text{ mm}$ + lã mineral de $50\text{ mm}$ no miolo + montantes de madeira ou aço.
   - **60 min de TRRF**: 2 placas de gesso acartonado RF ($2\times 15.0\text{ mm}$) em cada face + lã mineral de $75\text{ mm}$ + montantes de aço de $0.95\text{ mm}$ ou madeira tratada com retardante de chama (*fire retardant pressure treated lumber - FRTW*).
   - **90 min de TRRF**: 3 placas RF ($15+15+12.5\text{ mm}$) na face exposta + lã de rocha de $100\text{ mm}$ densificada ($40\text{ a }60\text{ kg/m}^3$).

3. **Quantificação Automática no BOM**:
   - O motor, ao detectar que a composição de parede requer TRRF > 0, adiciona ao hardware:
     - Quantidade de parafusos de comprimento adequado para múltiplas camadas de gesso ($25\text{ mm}$ para 1 placa, $45\text{ mm}$ para 2 placas, $64\text{ mm}$ para 3 placas).
     - Massa de junção e fita de papel para selagem de juntas de gesso com resistência ao fogo (tipo C).
     - Fita intumescente para selagem de furos de passagem de eletrodutos e tubulações de PVC (*fire collars* / *intumescent wraps*).

### 22.2 Barreiras Corta-Fogo (*Fire Stops* e *Draft Stops*)

1. **Fire Stops em Cavidades de Parede**:
   - No *platform framing*, cada pavimento é naturalmente compartimentado pelas guias superior e inferior que fecham a cavidade da parede na interface entre paredes e pisos. O motor deve garantir que nenhuma cavidade permaneça aberta entre pisos.
   - No *balloon framing* (pé-direito duplo), a cavidade vertical é contínua e funciona como chaminé em caso de incêndio. O motor insere automaticamente **bloqueios corta-fogo de madeira maciça de $38\text{ mm}$** ou **lã mineral compactada** na cota de cada pavimento intermediário, impedindo a propagação vertical de chamas e fumaça.

2. **Draft Stops em Sótãos e Áticos**:
   - O espaço sobre o último forro de gesso, abaixo do OSB da cobertura, constitui um volume contínuo preenchido de ar. Se houver princípio de incêndio, o fogo percorrerá toda a extensão do ático sem barreira.
   - O motor gera divisórias de lã de rocha compacta ou gesso RF a cada $250\text{ m}^2$ de projeção horizontal, conforme NFPA 13R / IT-09 (CBPMESP), inserindo automaticamente o material e a mão de obra no quantitativo.

3. **Selamento de Penetrações (Through-Penetration Firestops)**:
   - Toda tubulação que atravessa uma barreira corta-fogo (parede com TRRF ou piso entre unidades) recebe:
     - Tubo de PVC: colar intumescente (*firestop collar*) que expande e esmaga o tubo quando o plástico amolece, fechando a passagem.
     - Eletrodutos metálicos: massa intumescente moldável (*firestop putty*) aplicada ao redor do tubo na face de cada lado da parede.
     - O motor gera validação `V-112` se detectar uma tubulação passante modelada sem firestop.

---

## 23. LOGÍSTICA, TRANSPORTE, SEQUENCIAMENTO DE MONTAGEM E IÇAMENTO

A geração das peças e painéis no motor não termina no modelo geométrico 3D: o sistema deve prever toda a cadeia física até o canteiro de obras.

### 23.1 Limites Dimensionais de Transporte Rodoviário

1. **Carroceria Aberta (Caminhão Toco / Truck)**:
   - Comprimento útil de carga: $6.0\text{ a }7.5\text{ m}$ (toco) ou $9.0\text{ a }12.0\text{ m}$ (carreta).
   - Largura útil: $2.40\text{ m}$ (sem escolta) ou até $3.50\text{ m}$ com escolta e autorização especial de transporte do DNIT.
   - Altura útil empilhada: $2.60\text{ m}$ (altura máxima total do veículo com carga: $4.40\text{ m}$).

2. **Fatiamento Automático de Painéis para Transporte**:
   - O motor verifica automaticamente se o comprimento ou altura de cada painel excede o limite declarado em `limits/manufacturing.yaml`.
   - Se exceder, o painel é fatiado em 2 ou 3 segmentos no ponto de menor impacto estrutural:
     - Preferencialmente na borda de uma abertura (a junta de emenda fica no montante *King* de uma porta).
     - Se não houver abertura, no meio do vão mais longo entre montantes, com emenda de guias por placa de junção de aço galvanizado ($300\times 150\text{ mm}$) fixada com parafusos estruturais SDS.
   - Cada emenda gera uma ligação explícita no modelo (tipo `PN_SPLICE`) com fixadores quantificados.

3. **Sequência de Empilhamento no Caminhão (Loading Sequence)**:
   - Os painéis devem ser empilhados no caminhão na **ordem inversa da montagem**: o primeiro painel a ser erguido no canteiro deve ser o último (topo) da pilha.
   - O motor exporta um arquivo `sequencia_carga.csv` com a ordem de empilhamento ótima, compatível com a planta de montagem, eliminando a necessidade de remanejo de painéis pesados no local.

### 23.2 Sequência de Montagem no Canteiro (Erection Sequence)

1. **Diagrama de Montagem com Numeração Sequencial**:
   - O motor gera um mapa de planta com setas direcionais numeradas indicando a ordem de montagem de cada painel:
     - **Regra 1**: Paredes externas portantes do pavimento térreo primeiro.
     - **Regra 2**: Paredes internas portantes (que receberão entrepiso) depois.
     - **Regra 3**: Paredes divisórias internas não portantes por último no pavimento.
     - **Regra 4**: Entrepiso montado antes das paredes do pavimento superior.
     - **Regra 5**: Cobertura apenas quando todas as paredes do último nível estiverem escoradas e alinhadas.

2. **Pontos de Içamento Mecânico e Manual**:
   - Painéis com peso $\le 120\text{ kg}$: erguimento manual por equipe de 2 a 4 operários.
   - Painéis com peso entre $120\text{ e }300\text{ kg}$: uso de guindaste articulado veicular (*truck crane*) ou munck.
   - Painéis com peso $> 300\text{ kg}$: guindaste sobre esteiras ou guindaste telescópico com plano de rigging.
   - O motor calcula o centro de gravidade (CG) de cada painel considerando a distribuição de massa dos montantes, vergas e placas:
     $$x_{CG} = \frac{\sum m_i \cdot x_i}{\sum m_i} \qquad z_{CG} = \frac{\sum m_i \cdot z_i}{\sum m_i}$$
   - A posição dos olhais de elevação (*lifting eyes*) é marcada no painel de modo que o ponto de içamento fique entre $\frac{1}{4}$ e $\frac{1}{3}$ do comprimento total, contado de cada extremidade, garantindo estabilidade sem flexão excessiva.

### 23.3 Escoramento Temporário e Travamento Provisório

- Durante a montagem, painéis isolados erguidos são instáveis por flexo-torção até receberem o entrepiso ou as paredes perpendiculares definitivas.
- O motor emite notas de montagem para cada painel indicando:
  - Número de escoras diagonais temporárias necessárias (uma a cada $3.0\text{ m}$ de comprimento, mínimo 2 por painel).
  - Comprimento das escoras ($L_{escora} = \sqrt{H^2 + d^2}$, onde $d$ é o afastamento de base ao pé da parede).
  - Tipo de fixação temporária ao radier: cunha de aço galvanizado com parafuso de ancoragem rápida ou âncora de expansão reutilizável.

---

## 24. INTEROPERABILIDADE IFC 4.3 / openBIM E EXPORTAÇÃO UNIVERSAL

O motor não deve ficar preso exclusivamente ao ecossistema proprietário Autodesk Revit.

### 24.1 Exportação Nativa para IFC 4.3 (Industry Foundation Classes)

1. **Mapeamento de Entidades IFC**:
   - Cada peça gerada pelo motor é mapeada para a entidade IFC correta:
     - Montantes e vigas: `IfcMember` com `PredefinedType = STUD`, `MULLION` ou `MEMBER`.
     - Guias superior/inferior: `IfcMember` com `PredefinedType = PLATE`.
     - Chapas de fechamento: `IfcPlate` com `PredefinedType = SHEET`.
     - Treliças completas: `IfcElementAssembly` com sub-elementos `IfcMember`.
     - Conectores (parafusos, pregos): `IfcMechanicalFastener` com propriedades de diâmetro, comprimento e material.
   - Cada painel é agrupado como `IfcElementAssembly` com `AssemblyPlace = FACTORY`.

2. **PropertySets Customizados (Psets)**:
   - `Pset_VigoraFraming`:
     - `PanelID`, `WallID`, `LevelID`, `System` (wood/steel), `CutLength_mm`, `Angle_A`, `Angle_B`, `StockBar_mm`, `Weight_kg`, `Signature`.
   - `Pset_VigoraManufacturing`:
     - `MachineFile`, `NestingSheet`, `BarCode`, `QRCodeData`.
   - `Pset_VigoraStructural`:
     - `AxialCapacity_kN`, `BendingCapacity_kNm`, `UtilizationRatio`, `GoverningSafetyCode`.

3. **Exportação para Solibri, Navisworks e BIMcollab**:
   - O arquivo IFC é validado automaticamente pelo motor contra o schema IFC4x3 utilizando a biblioteca `ifcopenshell` em Python, garantindo que nenhuma instância tenha atributos obrigatórios vazios.

### 24.2 Importação de Modelos IFC do Arquiteto

- O motor aceita como entrada alternativa ao formato JSON nativo um arquivo IFC extraído de qualquer software BIM (ArchiCAD, Vectorworks, Allplan, SketchUp):
  - Paredes são lidas de `IfcWall` / `IfcWallStandardCase` com eixos, alturas e furos.
  - Aberturas são lidas de `IfcOpeningElement` com `IfcWindow` / `IfcDoor` vinculados.
  - Lajes são lidas de `IfcSlab` com contornos e furos.
  - Coberturas são lidas de `IfcRoof` com `IfcSlab` inclinadas ou `IfcRoofType`.
- O módulo `src/vigora_frame/ifc_import.py` atua como adaptador universal, análogo ao `revit_import.py`, normalizando os dados IFC para o modelo neutro `Project`.

---

## 25. EDIFÍCIOS MULTIPAVIMENTOS (3 A 5 ANDARES) E TRANSIÇÕES ESTRUTURAIS

Edificações de *light frame* no Brasil podem atingir até 5 pavimentos (12 a 15 metros de altura total), exigindo tratamento especial de cargas acumuladas e rigidez global.

### 25.1 Acúmulo de Cargas Verticais por Pavimento

- A cada pavimento adicional, os montantes dos andares inferiores recebem a carga acumulada de todos os pisos e telhados acima:
  $$N_{total} = \sum_{i=1}^{n} (G_i + Q_i) \times A_{tributária}$$
- **Dimensionamento Progressivo de Seções**:
  - Pavimentos superiores (3º ao 5º andar): montantes de seção mínima ($C90\times 0.80\text{ mm}$ ou $38\times 89\text{ mm}$).
  - Pavimento térreo e 1º andar: montantes de seção reforçada ($C140\times 1.25\text{ mm}$ em LSF ou $38\times 140\text{ mm}$ em madeira, ou montantes duplos unidos em caixa).
  - O motor calcula a tensão axial de compressão atuante em cada montante e compara com a capacidade resistente à flambagem, emitindo `V-113` se o fator de utilização exceder 90%.

### 25.2 Rigidez Global e Drift de Pavimento (Deslocamento Horizontal)

- Para edifícios de 3+ pavimentos, o deslocamento horizontal de topo sob carga de vento (*story drift*) deve ser verificado:
  $$\Delta_{topo} \le \frac{H_{total}}{500} \qquad ;\qquad \Delta_{pavimento} \le \frac{h_{entrepiso}}{400}$$
- O motor soma as rigidezes de cisalhamento de todos os painéis contraventados em cada eixo e resolve o modelo simplificado de pórtico equivalente:
  - Cada painel contraventado é modelado como uma mola diagonal com rigidez $K_i = G \cdot t \cdot L / H$.
  - O drift total é calculado iterativamente por pavimento, de baixo para cima.
  - Validação `V-114`: drift excessivo com indicação do pavimento e eixo críticos.

### 25.3 Transições Estruturais (Light Frame sobre Pilotis de Concreto)

- Em terrenos em aclive, é comum construir o pavimento térreo em estrutura de concreto armado com pilares e vigas baldrame (*pilotis*), com os pavimentos superiores em *light frame*.
- O motor deve:
  1. Receber a geometria da laje de transição superior (contorno e posição dos pilares de concreto).
  2. Verificar que cada parede portante de *light frame* apoie diretamente sobre uma viga de concreto (validação `V-115`: parede portante sobre vão livre de laje).
  3. Calcular as reações de apoio das paredes e inserir no projeto as ancoragens de base com chumbadores químicos dimensionados para a carga acumulada.

---

## 26. CATÁLOGO EXTENSIVO DE CONECTORES, FIXADORES E FERRAGENS ESTRUTURAIS

O motor mantém um banco de dados completo de todos os dispositivos de ligação usados na indústria de *light frame*, parametrizando sua geometria, capacidade, material e preço unitário.

### 26.1 Conectores Metálicos Estampados (Simpson Strong-Tie / MiTek / Pryda)

| Conector | Função Estrutural | Capacidade Típica | Material |
|---|---|---|---|
| **A34 / A35** | Ângulo de fixação de parede à placa superior ou piso | $4.5\text{ kN}$ cisalhamento | Aço galvanizado Z275, $1.0\text{ mm}$ |
| **L90 / L50** | Cantoneira de canto externo de paredes em L e T | $5.0\text{ kN}$ | Aço galvanizado Z275, $2.0\text{ mm}$ |
| **H2.5A** | Hurricane Tie — conecta treliça ao topo da parede | $7.5\text{ kN}$ arrancamento | Aço galvanizado Z600, $1.2\text{ mm}$ |
| **H10A** | Hurricane Tie de alta capacidade | $14.7\text{ kN}$ arrancamento | Aço galvanizado Z600, $1.6\text{ mm}$ |
| **LUS / HUS** | Estribo de face (*joist hanger*) para vigas de piso | $6.0\text{ a }22.0\text{ kN}$ cisalhamento | Aço galvanizado Z275, $1.5\text{ mm}$ |
| **LSSR / LSSJ** | Estribo ajustável inclinado para vigas com caimento | $8.0\text{ kN}$ | Aço galvanizado, $2.0\text{ mm}$ |
| **HTT / HDU** | Hold-Down de alta resistência a tração vertical | $22.0\text{ a }56.0\text{ kN}$ tração | Aço galvanizado endurecido, $3.0\text{ mm}$ |
| **MSTC / RSTC** | Fita contínua de fixação de topo (*strap tie*) | $18.0\text{ kN}$ tração | Aço galvanizado, $1.0\times 30\text{ mm}$ |
| **TPAH** | Base de poste ajustável (*post anchor*) | $15.0\text{ kN}$ compressão + cisalhamento | Aço galvanizado com base de chumbador |
| **BC / BCS** | Suporte de coluna/pilarete (*beam connector*) | $20.0\text{ kN}$ cisalhamento | Aço galvanizado, $2.0\text{ mm}$ |

### 26.2 Parafusos Estruturais e Pregos Especificados

| Fixador | Especificação Dimensional | Aplicação | Capacidade Unitária Estimada |
|---|---|---|---|
| **Parafuso auto-brocante wafer** | $\varnothing 4.2 \times 19\text{ mm}$ (TekScrew #8) | Fixação de montante em guia (Steel Frame) | $V_{lat} = 1.2\text{ kN}$ |
| **Parafuso auto-brocante sextavado** | $\varnothing 4.8 \times 22\text{ mm}$ (TekScrew #10) | Fixação estrutural alma-aba entre perfis C | $V_{lat} = 1.8\text{ kN}$ |
| **Parafuso SDS estrutural** | $\varnothing 6.3 \times 38\text{ mm}$ (Strong-Drive SDS) | Hold-downs e conectores pesados | $V_{lat} = 4.5\text{ kN}$ |
| **Parafuso de drywall fosfatizado** | $\varnothing 3.5 \times 32\text{ mm}$ (bugle head) | Fixação de gesso no montante (não estrutural) | — |
| **Prego espiralado galvanizado** | $\varnothing 3.3 \times 75\text{ mm}$ (8d ring shank) | Fixação de chapa OSB na borda do painel | $V_{lat} = 1.0\text{ kN}$ |
| **Prego espiralado galvanizado** | $\varnothing 3.8 \times 90\text{ mm}$ (10d ring shank) | Fixação de placa superior na guia e montante | $V_{lat} = 1.3\text{ kN}$ |
| **Prego anelado para concreto** | $\varnothing 4.0 \times 50\text{ mm}$ (cut masonry nail) | Fixação temporária de guia ao radier durante montagem | — |
| **Grampo pneumático** | $16\text{ mm} \times 9.5\text{ mm}$ crown staple | Fixação de membrana hidrófuga ao OSB | — |

### 26.3 Chapas Denteadas para Treliças (Truss Plates / Gusset Plates)

- Em *Wood Frame*, as conexões dos nós das treliças industriais são feitas por chapas metálicas com dentes estampados (*nail plates* ou *gang nails*), prensadas hidraulicamente no canteiro ou na fábrica.
- O motor calcula a área mínima da chapa denteada em cada nó da treliça:
  $$A_{placa} = \frac{F_{nó}}{f_{placa} \times n_{dens}}$$
  Onde $f_{placa}$ é a resistência por dente ($\approx 0.08\text{ a }0.12\text{ kN/dente}$) e $n_{dens}$ é a densidade de dentes por cm² ($\approx 4\text{ a }8\text{ dentes/cm}^2$).

---

## 27. SUSTENTABILIDADE, LCA/EPD E CERTIFICAÇÕES AMBIENTAIS

### 27.1 Análise de Ciclo de Vida (LCA) e Declaração Ambiental de Produto (EPD)

O motor integra um módulo de cálculo de emissões de CO₂ equivalente ($\text{kg CO}_2\text{eq}$) para todas as peças geradas:

| Material | Emissão Incorporada (Cradle-to-Gate) | Fonte |
|---|---|---|
| Madeira serrada Pinus (CCA/CCB) | $-1.1\text{ kg CO}_2\text{eq/kg}$ (sequestro de carbono biogênico) | EPD IBÁ 2023 |
| Aço galvanizado Z275 conformado | $+2.5\text{ a }3.2\text{ kg CO}_2\text{eq/kg}$ | EPD worldsteel 2022 |
| Chapa OSB 11.1 mm | $-0.9\text{ kg CO}_2\text{eq/m}^2$ | EPD APA 2022 |
| Placa de gesso ST 12.5 mm | $+3.8\text{ kg CO}_2\text{eq/m}^2$ | EPD Knauf 2023 |
| Lã de rocha basáltica 50 mm | $+1.8\text{ kg CO}_2\text{eq/m}^2$ | EPD Rockwool 2022 |
| Membrana hidrófuga PP | $+0.4\text{ kg CO}_2\text{eq/m}^2$ | EPD DuPont 2022 |

- O resumo de emissões aparece automaticamente na aba `Sustentabilidade` da planilha XLSX, com gráficos comparativos entre wood frame (carbono negativo) e steel frame (carbono positivo), auxiliando o projetista na tomada de decisão e na obtenção de créditos para certificações LEED, AQUA-HQE e Selo Casa Azul da Caixa Econômica Federal.

### 27.2 Gestão de Resíduos Sólidos de Fábrica

- O motor calcula o volume total de resíduos sólidos gerados na fabricação:
  - Retalhos de madeira: classificados como resíduo Classe B (reciclável), destinados à compostagem, queima em caldeira de biomassa ou venda como lenha/briquete.
  - Retalhos de aço galvanizado: classificados como resíduo Classe B, destinados à reciclagem em siderúrgica.
  - Pó de serra/corte: resíduo Classe A (inerte), destinado à compostagem.
- A taxa de desperdício percentual é exibida no resumo de cada projeto, permitindo que a construtora monitore o índice de desperdício e evolua processo produtivo ao longo do tempo.

---

## 28. ESTRATÉGIA DE TESTES EXAUSTIVOS, FUZZING E VALIDAÇÃO VISUAL

### 28.1 Pirâmide de Testes do Motor

```
                         ┌───────────┐
                         │ E2E Revit │ ← Testes de aceitação em Revit real (headless)
                         ├───────────┤
                       ┌─┤ Integração├─┐ ← Geração completa de projeto + validações
                       │ ├───────────┤ │
                     ┌─┤ │  Golden   │ ├─┐ ← Comparação bit-a-bit com saídas aprovadas
                     │ │ ├───────────┤ │ │
                   ┌─┤ │ │ Property  │ │ ├─┐ ← Hypothesis: inputs randômicos robustos
                   │ │ │ ├───────────┤ │ │ │
                 ┌─┤ │ │ │Unitários  │ │ │ ├─┐ ← Cada função/módulo isolado
                 │ │ │ │ └───────────┘ │ │ │ │
                 └─┴─┴─┴───────────────┴─┴─┴─┘
```

### 28.2 Testes de Propriedade com Hypothesis (Property-Based Testing)

O `hypothesis` gera milhares de projetos sintéticos com parâmetros no limite das regras construtivas:

1. **Estratégia "Paredes Loucas"**: Coordenadas aleatórias com ângulos entre $1^\circ$ e $179^\circ$, comprimentos entre $60\text{ mm}$ e $15.000\text{ mm}$, alturas entre $1.000\text{ mm}$ e $8.000\text{ mm}$.
   - **Invariante garantida**: O motor NUNCA lança exceção não tratada (`ZeroDivisionError`, `IndexError`, `ValueError`). Ele sempre emite uma `Issue` com código de erro e encerra graciosamente.
2. **Estratégia "Aberturas no Limite"**: Janelas encostadas no canto (offset = 0), janelas maiores que a parede, portas com altura igual ao pé-direito, aberturas sobrepostas.
   - **Invariante**: Toda abertura inválida é recusada com `V-018`, `V-019` ou `V-079`. Nenhuma peça de comprimento negativo é gerada.
3. **Estratégia "Telhados Extremos"**: Inclinações de $1^\circ$ a $60^\circ$, beirais de $0\text{ mm}$ a $1500\text{ mm}$, rincões com inclinações desiguais, platibandas com alturas mínimas.
   - **Invariante**: Toda treliça gerada possui nós concorrentes e polígonos com área positiva.
4. **Estratégia "Caixa d'Água Impossível"**: Posições fora do contorno das paredes, sobre paredes não portantes, sob cumeeira de telhado de 5°.
   - **Invariante**: O motor emite `V-090` a `V-094` e não gera peças de apoio fantasma.

### 28.3 Golden Master Visual Testing para Pranchas PDF

- O script `tests/test_golden_visual.py`:
  1. Gera a prancha PDF de cada projeto-exemplo com a configuração congelada.
  2. Rasteriza cada página em bitmap de 300 DPI via `pdf2image`.
  3. Calcula o SSIM (*Structural Similarity Index*) contra a imagem de referência aprovada.
  4. Se SSIM < 0.995 (variação de mais de 0.5% dos pixels), o teste FALHA, impedindo que refatorações alterem involuntariamente o layout visual das pranchas.

### 28.4 Fuzzing de Arquivos de Entrada

- Um script de fuzzing modifica aleatoriamente bytes de arquivos JSON de projeto válidos e alimenta o motor:
  - Campos numéricos substituídos por `NaN`, `Infinity`, `-0.0`, strings vazias.
  - Arrays de coordenadas com tamanho 0, 1 ou bilhões de elementos.
  - Campos obrigatórios omitidos.
  - **Invariante**: O motor retorna um `Result` vazio ou um erro Pydantic `ValidationError` com mensagem legível. Nunca um crash de segfault ou loop infinito.

---

## 29. MOTOR DE AUTOCORREÇÃO E RECUPERAÇÃO DE ERROS (AUTO-HEAL ENGINE)

Em vez de simplesmente rejeitar modelos com microdesvios de modelagem BIM, o motor pode opcionalmente corrigi-los de forma controlada e auditável.

### 29.1 Tipos de Autocorreções Implementadas

| Tipo de Desvio | Ação Automática | Limite de Tolerância | Log |
|---|---|---|---|
| **Folga entre paredes < 5 mm** | Estende a ponta da parede mais curta até encostar na outra | Máximo 5 mm de extensão automática | `V-000 info: parede W12 estendida 3.2 mm para fechar encontro com W05` |
| **Ângulo quase-reto (89.5° a 90.5°)** | Arredonda para 90.000° exatos | Desvio máximo de ±0.5° | `V-000 info: ângulo de 89.7° entre W01 e W02 normalizado para 90.0°` |
| **Parede com comprimento de 58 mm** | Absorve no painel adjacente e elimina o microssegmento | Comprimento < 60 mm | `V-000 info: segmento W14 de 58 mm absorvido no painel de W13` |
| **Abertura encostada no canto (offset = 0)** | Afasta automaticamente 100 mm do canto | Offset < 100 mm | `V-018 warning: abertura O03 em W07 afastada de 0 para 100 mm do canto` |
| **Pé-direito inconsistente (2698 mm vs 2700 mm)** | Normaliza para o nível mais próximo | Desvio < 5 mm | `V-000 info: altura de W21 normalizada de 2698.3 para 2700.0 mm` |
| **Ponta de parede flutuando 2 mm acima/abaixo da face da outra** | Projeta ortogonalmente na face mais próxima | Distância perpendicular < 5 mm | `V-000 info: ponta de W09 projetada na face de W03` |
| **Cruzamento de paredes com desvio de 3 mm do eixo** | Projeta ambas no ponto médio de interseção | Desvio < 10 mm | `V-000 info: cruzamento W15/W16 ajustado em 2.8 mm` |

### 29.2 Modo Estrito vs Modo Tolerante

- O motor aceita o parâmetro `--strict` na CLI:
  - **Modo Tolerante (padrão)**: Todas as autocorreções acima são aplicadas e registradas em `info/warning`.
  - **Modo Estrito (`--strict`)**: Qualquer desvio, por menor que seja, é reportado como `error` e o resultado é marcado como `RASCUNHO` sem correção automática. Ideal para projetos certificados onde cada milímetro deve ser intencional.

---

## 30. ENCICLOPÉDIA DE EDGE CASES E CENÁRIOS CRÍTICOS DE ENGENHARIA

Esta seção documenta exaustivamente os cenários de contorno que o motor deve resolver sem falhas. Cada cenário inclui a geometria do problema, o risco construtivo e a resposta algorítmica esperada.

### 30.1 Paredes

| # | Cenário | Risco / Efeito | Resposta do Motor |
|---|---|---|---|
| **EC-01** | Parede de $60\text{ mm}$ de comprimento (um único montante) | Painel impossível de fabricar na mesa; sem placa de bloqueio | Emitir `V-001` erro; se for faceta de curva, absorver no painel adjacente |
| **EC-02** | Parede de $12.000\text{ mm}$ reta sem aberturas | Painel único excede mesa de fábrica e caminhão | Fatiar em 2 ou 3 painéis nos pontos da grade de modulação |
| **EC-03** | Parede com 8 portas de $900\text{ mm}$ lado a lado (fachada comercial) | Quase sem montantes de altura total; verga contínua de $7.200\text{ mm}$ | Gerar viga-verga treliçada embutida no painel ou solicitar viga de aço I |
| **EC-04** | Três paredes concorrentes em T com desvio de $15\text{ mm}$ entre os eixos | Montantes de reforço desalinhados; placa de gesso sem apoio no nó | Normalizar para T único e gerar bloco de reforço contínuo |
| **EC-05** | Parede com abertura de arco (semicírculo de $1.200\text{ mm}$) | Montantes de enchimento curvos sob a verga | Gerar montantes de enchimento de arco (*arch fillers*) em CNC com polígono exato |
| **EC-06** | Parede com espessura de $300\text{ mm}$ (isolamento acústico duplo) | Montantes alternados ou guias duplas com câmara de ar | Gerar duas camadas independentes de framing com ligações flexíveis |
| **EC-07** | Parede inclinada a $85^\circ$ do plano horizontal (parede-teto de mansarda) | Montantes que não são puramente verticais | Gerar montantes angulados com cortes compostos nas pontas |
| **EC-08** | Parede com embutimento de shaft vertical de $600\times 300\text{ mm}$ (prumadas) | Interrupção de montantes para passagem de tubulação vertical | Gerar cabeceiras horizontais (headers) superior e inferior com montantes reforçados nas laterais |

### 30.2 Coberturas

| # | Cenário | Risco / Efeito | Resposta do Motor |
|---|---|---|---|
| **EC-09** | Telhado com inclinação de $2\%$ (quase plano, para calhas embutidas) | Acúmulo de água pluvial e flambagem lateral de treliças rasas | Emitir `V-116` aviso; gerar treliças rasas (*flat trusses*) com banzos de seção maior e contracaimento de $0.5\%$ para drenagem |
| **EC-10** | Telhado com inclinação de $55^\circ$ (chalé alpino) | Banzos superiores muito longos; pressão de sucção de vento extrema | Gerar treliças com montantes intermediários adicionais e travamentos anti-tombamento em X (*lateral bracing*) |
| **EC-11** | Rincão entre telhado principal a $30\%$ e asa a $15\%$ | Calha de vale não está a 45° em planta; treliças da asa não encaixam nas do principal | Calcular interseção dos 2 planos e gerar treliças de rincão cortadas no ângulo composto real |
| **EC-12** | Beiral de $1.200\text{ mm}$ de balanço sem mão-francesa | Vibração e deflexão sob vento ascendente | Emitir `V-108` erro; exigir mão-francesa ou estrutura em escada (*lookouts + outriggers*) |
| **EC-13** | Telhado em L com cumeeiras perpendiculares na mesma cota | Interseção tridimensional complexa com espigões cruzados e calha de vale | Gerar espigões e vales como peças únicas CNC com corte de ângulo composto (*compound angle jack rafters*) |
| **EC-14** | Caixa d'água de 1000 L posicionada no espigão (4 águas) | Treliças cortam o envelope em ângulo de 45° | Adaptar 4 treliças de ático (2 de cada lado do espigão), abrir e criar viga de apoio diagonal |
| **EC-15** | Dois telhados encostados com alturas de beiral diferentes (desnível de $200\text{ mm}$) | Infiltração na junta horizontal entre os dois telhados | Emitir `V-087` e gerar calha de transição com contracaimento e membrana contínua |

### 30.3 Entrepisos e Escadas

| # | Cenário | Risco / Efeito | Resposta do Motor |
|---|---|---|---|
| **EC-16** | Entrepiso com vão livre de $6.50\text{ m}$ sem paredes intermediárias | Vigas de madeira sólida não atingem a relação $L/360$ | Especificar vigas I (*I-Joists*) com alma de OSB de $300\text{ mm}$ ou vigas treliçadas de aço |
| **EC-17** | Furo de escada tangente à parede portante | Vigas de reforço (*trimmers*) não têm espaço de apoio | Emitir `V-109` e exigir que o furo se afaste pelo menos $100\text{ mm}$ da face interna da parede |
| **EC-18** | Sacada em balanço de $2.00\text{ m}$ com guarda-corpo de vidro pesado ($50\text{ kg/m}$) | Momento fletor intenso e carga de ponta no bordo livre | Gerar vigas duplas em balanço com relação $L_{int}/L_{bal} \ge 3.0$ e bloqueios de torção nas raízes |
| **EC-19** | Escada com pé-direito de $3.50\text{ m}$ e largura de $750\text{ mm}$ | Número de degraus elevado, longarinas muito longas, garganta crítica | Emitir `V-082` e `V-107` se a garganta for $< 90\text{ mm}$; sugerir aumento de seção da longarina |
| **EC-20** | Piso com aberturas de lareira ($1.200\times 1.200\text{ mm}$) | Vigas interrompidas, carga concentrada nas vigas de borda do furo | Gerar cabeceira dupla (*double header*) e vigas trimmer reforçadas com estribos de aço |

### 30.4 Fundação e Base

| # | Cenário | Risco / Efeito | Resposta do Motor |
|---|---|---|---|
| **EC-21** | Radier com desnível de $50\text{ mm}$ entre área seca e banheiro | Guias de base em cotas diferentes; pilaretes de transição | Gerar calços de madeira tratada ou cunhas de argamassa sob a guia; quantificar comprimento de shimming |
| **EC-22** | Fundação em laje nervurada com nervuras de $150\text{ mm}$ de largura | Guia de base apoiada sobre nervura estreita; chumbadores no limite de borda | Verificar $c_{min} \ge 70\text{ mm}$; emitir `V-098` se a nervura for muito estreita |
| **EC-23** | Terreno em aclive com desníveis de radier de $600\text{ mm}$ entre fachadas opostas | Paredes de um lado mais altas que as do outro; cumeeira não fica centralizada | Gerar painéis de base com montantes de comprimento variável e guia inferior escalonada em degraus |
| **EC-24** | Construção sobre laje de concreto pré-existente sem chumbadores | Ancoragem exclusivamente por parafusos de concreto (*concrete screws*) | Quantificar e espaçar ancoragens de concreto auto-atarraxantes ($\varnothing 6.5\text{ mm}$) com espaçamento máximo de $600\text{ mm}$ |

### 30.5 Instalações e MEP

| # | Cenário | Risco / Efeito | Resposta do Motor |
|---|---|---|---|
| **EC-25** | Tubo de esgoto de $\varnothing 100\text{ mm}$ passando por montante de $89\text{ mm}$ | Furo excede 100% da largura da alma; montante destruído | Emitir `V-103` erro; exigir passagem por montante de $140\text{ mm}$ ou desvio com curva de 45° |
| **EC-26** | 6 eletrodutos de $\varnothing 25\text{ mm}$ na mesma parede, todos no mesmo ponto | Concentração de furos; montantes vizinhos enfraquecidos em série | Espaçar furos em montantes alternados; emitir `V-103` se não houver espaço |
| **EC-27** | Duto de exaustão de $200\times 400\text{ mm}$ passando horizontalmente pela parede | Abertura maior que o espaço entre montantes; necessidade de cabeceira | Gerar cabeceira (*header*) horizontal na zona de passagem do duto e montantes jack de apoio lateral |
| **EC-28** | Quadro elétrico de $600\times 400\text{ mm}$ embutido em parede de $89\text{ mm}$ | Necessidade de nicho embutido com reforço perimetral | Gerar montantes e bloqueios perimetrais ao nicho; quantificar compensação de OSB |

### 30.6 Contraventamento e Cargas Extremas

| # | Cenário | Risco / Efeito | Resposta do Motor |
|---|---|---|---|
| **EC-29** | Fachada inteira de vidro sem parede de contraventamento naquele eixo | Nenhum painel de cisalhamento em uma das direções do edifício | Emitir `V-017` erro crítico; sugerir pórtico metálico rígido embutido (*steel moment frame*) atrás da esquadria |
| **EC-30** | Parede de $1.50\text{ m}$ de comprimento como único contraventamento no eixo X | Relação $H/L > 3.0$; hold-down excessivamente carregado | Emitir `V-102` erro; calcular o hold-down necessário e alertar se exceder a capacidade do conector padrão |
| **EC-31** | Região litorânea com velocidade de vento $V_0 = 50\text{ m/s}$ | Pressão dinâmica de $q = 1.530\text{ N/m}^2$; sucção na cobertura | Dimensionar hurricane clips H10A em todas as treliças; hold-downs HDU14 nos cantos; reforçar pregação de OSB para passo de $75\text{ mm}$ na borda |
| **EC-32** | Edifício de 4 pavimentos com planta totalmente assimétrica em L | Torção global sob vento lateral; centro de rigidez deslocado | Calcular excentricidade entre centro de massa e centro de rigidez; distribuir esforço adicional de torção nos painéis mais distantes |

### 30.7 Pranchas e Documentação

| # | Cenário | Risco / Efeito | Resposta do Motor |
|---|---|---|---|
| **EC-33** | Painel com 40 montantes numa parede de $12\text{ m}$ de comprimento | Sobreposição maciça de balões e cotas na elevação 1:20 | Acionar sistema anticolisão: escalonar balões em 3 alturas, reduzir tamanho de fonte de $2.5\text{ mm}$ para $2.0\text{ mm}$ e usar abreviações compactas |
| **EC-34** | Projeto com 50 painéis e 6 marcas de treliça | 30+ folhas A1; necessidade de índice e paginação automática | Gerar folha de índice com tabela de conteúdos e cross-references entre folhas (ex: "ver folha 12/30") |
| **EC-35** | Escala 1:20 não cabe na folha A1 para painel de $8\text{ m}$ de comprimento | Necessidade de quebrar a vista em 2 strips ou reduzir a escala para 1:25 | O motor seleciona automaticamente a maior escala NBR 8196 que caiba no campo de desenho disponível |
| **EC-36** | Detalhe de canto em L com 5 montantes encostados | Cotas individuais de $38\text{ mm}$ criam uma nuvem ilegível | Agrupar em uma cota total "5× 38 = 190" com seta de grupo no bloco de peças |

### 30.8 Artefatos de Modelagem Revit: Junções, Conexões Fantasma e Geometria Corrompida

O Revit possui um mecanismo de junção automática de paredes (*wall joins*) que frequentemente produz geometria ambígua, inconsistente ou matematicamente correta mas construtivamente impossível. O motor deve detectar e tratar **todos** os seguintes cenários que surgem diretamente do comportamento do Revit:

#### 30.8.1 Problemas de Junção em L, T e Cruz

| # | Cenário Revit | O que o Revit Exporta | Risco Real | Resposta do Motor |
|---|---|---|---|---|
| **EC-37** | Duas paredes em L com *Join Type = Butt* em vez de *Miter* | Eixos se encontram mas as faces externas não se tocam — resta um triângulo vazio de $\approx 90\times 90\text{ mm}$ no canto exterior | Infiltração de ar/água no canto; placa OSB sem apoio nessa região | Detectar a lacuna triangular; estender automaticamente a face externa da parede secundária até a face da primária; gerar montante de canto adicional para apoio de OSB; emitir `V-120 info` |
| **EC-38** | Duas paredes em L com *Join Type = Miter* (bissetriz a 45°) | Ambas as paredes têm guias e montantes cortados a 45° na ponta | Cortes de 45° em guias são impraticáveis em mesa de montagem; desperdiçam material e enfraquecem a ligação | Converter internamente para junção *Butt* (uma parede passa reto, a outra encosta); ignorar o corte de 45° e gerar o detalhe de canto padrão com montantes em L/U/T conforme o tipo de junção |
| **EC-39** | Junção em T onde a parede secundária não alcança o eixo da principal (gap de $2\text{ a }15\text{ mm}$) | O Revit mostra as paredes "conectadas" visualmente, mas o eixo da secundária termina $8\text{ mm}$ antes da face interna da principal | Ausência de suporte para a ponta da parede; painéis com folga no canteiro | Projetar a ponta da parede secundária na face mais próxima da parede principal; estender os eixos; recalcular o comprimento da guia e emitir `V-121 info: parede W18 estendida 8.3 mm para alcançar W05` |
| **EC-40** | Junção em T onde a parede secundária **ultrapassa** a face oposta da principal (overshoot de $5\text{ a }50\text{ mm}$) | O Revit às vezes não corta a parede secundária e seu eixo perfura a primária | A secundária gera montantes "dentro" do miolo da parede principal; peças se sobrepõem | Cortar a parede secundária na face interna da parede principal; descartar os $X\text{ mm}$ de excedente; emitir `V-122 info: overshoot de W11 cortado em 23 mm na face de W03` |
| **EC-41** | Junção em Cruz (4 paredes concorrentes no mesmo ponto) mas com 2 pares desalinhados ($\Delta = 10\text{ a }30\text{ mm}$) | O Revit trata cada par como junção T independente; os nós não coincidem | Dois blocos de reforço sobrepostos no mesmo ponto; montantes duplicados que colidem na fábrica | Unificar em uma única junção de Cruz no centroide dos 4 eixos; gerar um único pilarete composto (4 montantes em caixa) com 1 bloco de reforço contínuo; emitir `V-123 warning` |
| **EC-42** | Paredes em L com espessuras diferentes ($89\text{ mm} + 140\text{ mm}$) | O Revit alinha os eixos centrais, criando desalinhamento de $25.5\text{ mm}$ entre as faces externas | A face externa não é contínua; o OSB da face exterior de uma parede não encontra apoio na outra | Gerar montante de transição (*transition stud*) com calço de $25.5\text{ mm}$ para equalizar as faces; quantificar calço no BOM |
| **EC-43** | Junção em Y (3 paredes a $120°$ uma da outra — planta hexagonal) | O Revit exporta 3 eixos confluentes com ângulos de $120°$, sem nenhum a $90°$ | Nenhum detalhe de canto padrão (L, T, U) se aplica; montantes de canto precisam de cortes angulares especiais | Gerar detalhe de junção Y com 3 montantes posicionados a $120°$, cada um com corte de $60°$ na ponta interna; placa de gusset triangular de OSB no nó; emitir `V-124 info: junção não-ortogonal de 3 vias detectada` |
| **EC-44** | Parede curva do Revit (arco) exportada como polilinha de 12 segmentos | O Revit discretiza a curva em 12 micro-paredes de $\approx 400\text{ mm}$ cada | 12 painéis minúsculos, cada um com 2 montantes e 2 guias; junções a cada $400\text{ mm}$ com ângulo de $15°$ | Unificar segmentos consecutivos cujo ângulo entre si seja $\le 15°$ em painéis maiores; gerar montantes com cortes angulares graduais; usar chapas de OSB flexíveis ($6.0\text{ mm}$) para a face curva |

#### 30.8.2 Problemas de Alinhamento Vertical e Base/Topo

| # | Cenário Revit | O que o Revit Exporta | Risco Real | Resposta do Motor |
|---|---|---|---|---|
| **EC-45** | Paredes com *Base Constraint = Level 0* mas *Base Offset = -15 mm* | A guia inferior da parede está $15\text{ mm}$ abaixo da cota do radier | Parede flutuando ou enterrada parcialmente na fundação; guia não apoiada | Normalizar base da parede para a cota do nível; emitir `V-125 info: base offset de -15 mm em W08 ignorado` |
| **EC-46** | Paredes com *Top Constraint = Unconnected* e altura fixa de $2.700\text{ mm}$ ao lado de paredes com *Top Constraint = Level 1* a $2.680\text{ mm}$ | Paredes vizinhas portantes com $20\text{ mm}$ de diferença de altura | A placa superior de uma não é coplanar com a outra; entrepiso não apoia uniformemente | Emitir `V-126 warning: desnível de 20 mm entre topo de W03 (2700 mm) e W04 (2680 mm)`; se ambas forem portantes sob o mesmo entrepiso, normalizar para a cota do nível superior |
| **EC-47** | Parede do pavimento superior com *Base Offset = +50 mm* para "descontar" o entrepiso | A parede começa $50\text{ mm}$ acima da laje — corretamente representando o apoio sobre o entrepiso | Se o motor não reconhece esse padrão, gera paredes flutuando no ar sem apoio | Identificar que o offset corresponde à espessura do entrepiso ($\pm 15\text{ mm}$); vincular a parede ao entrepiso e não à laje bruta; emitir `V-000 info` |
| **EC-48** | Paredes com alturas distintas no mesmo nível (pé-direito de $2.700\text{ mm}$ na sala e $2.500\text{ mm}$ na cozinha) | Duas paredes portantes adjacentes com $200\text{ mm}$ de diferença no topo | A placa superior da parede mais baixa não atinge a placa superior da mais alta; lacuna estrutural | Gerar *ribbon plate* (placa de transição) na cota mais alta, apoiada sobre a parede mais baixa; preencher os $200\text{ mm}$ com montantes jack curtos (*cripples*) |
| **EC-49** | Parede do Revit com *Location Line = Finish Face: Interior* em vez de *Wall Centerline* | O eixo da parede está deslocado da linha central para a face interna do acabamento | Todos os cálculos de eixo, junção e modulação ficam deslocados em relação ao centro do framing real | Recalcular o eixo do framing a partir das camadas estruturais declaradas na family type, ignorando camadas de acabamento; emitir `V-127 info: eixo de W14 recalculado de Finish Face para Core Centerline` |

#### 30.8.3 Paredes Duplicadas, Sobrepostas e Fantasma

| # | Cenário Revit | O que o Revit Exporta | Risco Real | Resposta do Motor |
|---|---|---|---|---|
| **EC-50** | Duas paredes exatamente sobrepostas (cópia acidental com Ctrl+C no mesmo lugar) | Dois objetos `Wall` com exatamente os mesmos endpoints e altura | O motor gera 2 painéis idênticos no mesmo espaço; duplicação de material e custo | Detectar paredes com sobreposição > 95% (bounding boxes quase idênticos); manter uma e descartar a outra; emitir `V-128 warning: parede W22 descartada como duplicata de W03` |
| **EC-51** | Duas paredes paralelas encostadas (gap = $0\text{ mm}$), uma de $89\text{ mm}$ e outra de $140\text{ mm}$ | Duas paredes com faces tangentes mas sem junção Revit (não são "joined") | O motor tenta gerar 2 painéis independentes colados, com montantes de ambos ocupando a mesma zona | Verificar se a distância face-a-face é $\le 5\text{ mm}$ e as paredes são paralelas ($\theta < 1°$); se ambas forem do mesmo sistema construtivo, fundir em uma única parede de espessura combinada ou emitir `V-129 warning: paredes coladas W06/W07 — verificar intenção de parede dupla acústica` |
| **EC-52** | Parede de comprimento $0\text{ mm}$ (ponto degenerado — ocorre quando o Revit exporta parede com start == end após simplificação) | Um `Wall` com coordenadas de início e fim idênticas | Divisão por zero no cálculo de vetor direcional; crash na geração de montantes | Descartar silenciosamente; emitir `V-130 info: parede degenerada W29 (comprimento 0) descartada` |
| **EC-53** | Parede "invisível" (parede Room Separation ou parede de referência sem espessura) | Objeto `Wall` com espessura = $0\text{ mm}$ ou sem camadas estruturais | O motor tenta gerar montantes de $0\text{ mm}$ de espessura; crash ou geometria inválida | Filtrar paredes com espessura $< 38\text{ mm}$ (wood) ou $< 64\text{ mm}$ (steel) da geração de framing; emitir `V-131 info: parede não-estrutural W31 ignorada (espessura = 0 mm)` |

#### 30.8.4 Problemas de Junção Parede-Piso e Parede-Telhado

| # | Cenário Revit | O que o Revit Exporta | Risco Real | Resposta do Motor |
|---|---|---|---|---|
| **EC-54** | Parede com *Top Constraint = Roof* conectada a telhado de 2 águas, mas a parede está fora da projeção do telhado | O Revit projeta a parede até a linha do telhado — mas como a parede está fora do beiral, o topo fica horizontal (sem corte de oitão) | Parede sem corte triangular de oitão onde deveria ter | Detectar que a parede está sob a projeção do telhado + beiral; recalcular o perfil de oitão como a interseção do plano do telhado com o plano da parede; gerar montantes de oitão escalonados |
| **EC-55** | Parede que o Revit "cortou" no topo pelo telhado, gerando uma polilinha com 7 vértices em vez de retângulo | O perfil superior da parede tem um recorte triangular ou trapezoidal | Se o motor espera retângulos simples, os montantes não são gerados na zona triangular | Aceitar perfil poligonal arbitrário para cada parede; gerar montantes escalonados (*stepped studs*) para preencher o triângulo do oitão, com corte diagonal no montante de borda |
| **EC-56** | Parede de pé-direito duplo ($5.400\text{ mm}$) onde o entrepiso intermediário "corta" a parede no Revit mas não cria 2 paredes separadas | Uma única parede contínua que atravessa o nível do entrepiso | Se o motor trata como *balloon framing*, precisa gerar fire blocks na cota do entrepiso; se trata como *platform framing*, precisa fatiá-la em 2 paredes | Se `framing_system == "platform"`: fatiar automaticamente na cota de cada entrepiso, gerando guias de topo/base em cada nível; se `framing_system == "balloon"`: manter contínua mas inserir fire blocks e bloqueios de apoio para as vigas de piso |
| **EC-57** | Parede com *Top Constraint = Up to Level 2* mas o Level 2 está a $5.100\text{ mm}$ (pé-direito > $3.600\text{ mm}$ sem nível intermediário) | Uma parede de $5.100\text{ mm}$ de altura total sem corte | Montantes de madeira $38\times 89\text{ mm}$ com $5.100\text{ mm}$ de comprimento flambeiam sob carga — índice de esbeltez $\lambda > 200$ | Emitir `V-132 erro: altura de parede W15 (5100 mm) excede limite de flambagem para seção 38×89`; sugerir: (a) montantes de $38\times 140\text{ mm}$, (b) montantes duplos em caixa, ou (c) inserção de placa intermediária (*mid-height blocking*) a cada $2.400\text{ mm}$ |

#### 30.8.5 Problemas de Paredes sobre Vigas e Áreas sem Apoio

| # | Cenário Revit | O que o Revit Exporta | Risco Real | Resposta do Motor |
|---|---|---|---|---|
| **EC-58** | Parede portante no pavimento superior posicionada entre duas vigas de piso (não apoiada diretamente sobre viga ou parede abaixo) | O eixo da parede cai entre 2 vigas do entrepiso, apoiando apenas sobre o OSB de $18\text{ mm}$ do piso | Carga concentrada sobre chapa de piso sem estrutura; puncionamento do OSB; deflexão localizada | Emitir `V-133 erro crítico: parede portante W21 sobre vão livre de entrepiso`; o motor sugere: (a) inserir viga de reforço (*bearing wall support beam*) sob a parede, ou (b) mover a parede para coincidir com uma viga existente |
| **EC-59** | Parede portante do 2° andar deslocada $150\text{ mm}$ do eixo da parede portante do 1° andar | No Revit as paredes parecem alinhadas, mas os eixos têm offset | Excentricidade de carga; momento parasita na placa superior do 1° andar; deformação do entrepiso | Detectar o desalinhamento; se offset $\le$ metade da espessura da parede inferior ($\le 70\text{ mm}$ para $140\text{ mm}$): emitir `V-134 warning` e prosseguir com nota de reforço; se offset > metade: emitir `V-134 erro` e exigir realinhamento ou viga de distribuição de carga |
| **EC-60** | Pilar estrutural de concreto ou aço modelado no Revit (*Structural Column*) dentro de uma parede de *light frame* | O Revit sobrepõe o pilar com a parede; a parede "atravessa" o pilar | Montantes são gerados dentro do volume do pilar; colisão física impossível; o pilar deve ser o apoio e os montantes devem parar antes dele | Detectar pilares como furos retangulares na parede; gerar montantes que param $10\text{ mm}$ antes de cada face do pilar; inserir bloqueios horizontais de ligação parede-pilar com cantoneiras de aço ($2\times$ L90 por face) |

### 30.9 Coberturas: Geometrias Avançadas, Rincões Complexos e Interferências

Telhados são a área de maior complexidade geométrica tridimensional do *framing*. Os cenários abaixo cobrem situações que aparecem em projetos reais e que o Revit frequentemente modela de forma ambígua.

| # | Cenário | Risco / Efeito | Resposta do Motor |
|---|---|---|---|
| **EC-61** | Telhado de 4 águas (*hip roof*) com planta retangular onde o comprimento é $< 2\times$ a largura | A cumeeira é tão curta que os espigões praticamente se encontram no centro — geometria degenerando em pirâmide | Cumeeira de $200\text{ mm}$; treliça central impossível de fabricar | Se cumeeira $< 600\text{ mm}$: converter para telhado piramidal puro (4 espigões sem cumeeira); gerar viga de crista (*ridge beam*) pontual como apoio |
| **EC-62** | Telhado com mansarda (*gambrel roof*) — dois ângulos por água: $70°$ embaixo e $25°$ acima | Duas inclinações distintas na mesma água; a quebra gera um nó intermediário horizontal (placa de quebra) | A placa de quebra é um ponto de concentração de esforços; treliças de mansarda são mais complexas que as de 2 águas | Gerar treliças tipo Gambrel com banzo inferior contínuo, banzo superior em 2 segmentos e montante vertical no ponto de quebra; verificar que a placa de quebra horizontal está travada lateralmente a cada $600\text{ mm}$ |
| **EC-63** | Telhado tipo borboleta (*butterfly roof*) — 2 águas inclinadas para dentro, calha central | As águas caem para o centro da edificação em vez de para as bordas; vale/calha central recebe toda a drenagem | Sobrecarga hidráulica na calha central; deflexão da viga de vale sob peso de água acumulada durante chuvas intensas | Dimensionar a viga de vale central para carga de água acumulada (coluna d'água de $150\text{ mm} \times$ largura tributária); emitir `V-135 warning` se a capacidade de drenagem da calha central for insuficiente para o pluviômetro da região |
| **EC-64** | Telhado plano com platibanda alta ($800\text{ mm}$) e caimento de $1.5\%$ | Platibanda funciona como bacia — se o ralo entupir, a lâmina d'água pode atingir $200\text{ mm}$ | Carga adicional de $200\text{ kg/m}^2$ (lâmina de água) sobre treliças rasas projetadas para $25\text{ kg/m}^2$ | Verificar carga de empoçamento (*ponding load*); dimensionar treliças para carga de água até a cota do ladrão (*overflow scupper*); emitir `V-136 warning` se não houver ladrão modelado |
| **EC-65** | Telhado com lucerna (*dormer*) — volume que se projeta para fora do plano do telhado principal | A lucerna cria um furo retangular no plano das treliças + 3 novas mini-paredes + mini-telhado | Treliças do telhado principal são interrompidas; as vigas laterais da lucerna concentram carga nas treliças adjacentes | Gerar *dormer trimmers* (treliças duplas reforçadas nos lados da lucerna); *dormer header* (viga de cabeçalho no topo e na base do furo); gerar as 3 paredes da lucerna como painéis independentes com treliças próprias |
| **EC-66** | Telhado com lanternim (*clerestory*) — janela alta entre dois planos de telhado com alturas diferentes | Uma parede curta ($600\text{ a }1.200\text{ mm}$) com janela conecta dois planos de telhado em cotas distintas | A parede do lanternim é estrutural (carrega o telhado superior); os montantes dela são extremamente curtos e precisam de reforço contra uplift | Gerar parede de lanternim como painel portante com hurricane ties em cada montante; verificar que os montantes do lanternim estejam alinhados com as treliças de ambos os telhados (superior e inferior) |
| **EC-67** | Rincão (vale) onde os dois telhados têm inclinações **muito diferentes** ($45°$ vs $15°$) | A linha de vale em planta não é a bissetriz a $45°$ — é uma curva hiperbólica projetada (ou uma reta com ângulo irregular) | Treliças do telhado mais raso (*jack trusses*) chegam ao vale em ângulos muito oblíquos; cortes compostos extremos | Calcular o ângulo composto real (plunge + bevel) para cada treliça *jack*; se algum ângulo for $> 60°$ emitir `V-137 warning: corte composto extremo — verificar viabilidade de fabricação CNC` |
| **EC-68** | Telhado com cumeeira deslocada do centro da planta (assimétrico: uma água de $3.00\text{ m}$ e outra de $5.00\text{ m}$) | As duas águas têm inclinações diferentes para manter a mesma cota de beiral | Treliças assimétricas; reação vertical desigual nos apoios; tendência de tombamento da cumeeira para o lado mais curto | Gerar treliças assimétricas com banzos de comprimentos desiguais; verificar que a reação horizontal líquida seja absorvida pela placa de topo ou por tirantes horizontais; emitir `V-138 info: treliça assimétrica` |
| **EC-69** | Telhado em T: asa perpendicular com cumeeira mais baixa que o telhado principal | A cumeeira da asa bate na água do principal gerando um rincão + um espigão + uma calha de transição | Geometria 3D com 3 tipos de interseção de planos no mesmo ponto; peças com cortes compostos em 3 eixos | Resolver algebricamente as 3 interseções de planos; gerar peças de vale, espigão e transição como entidades separadas; cada peça recebe seus ângulos de corte A e B computados |
| **EC-70** | Beiral com canto de $135°$ (planta em ângulo obtuso) | O beiral não faz um canto reto; a terça de beiral precisa de corte a $67.5°$ | O espigão do canto obtuso é muito curto e quase paralelo à cumeeira | Calcular o ângulo do espigão obtuso ($\beta = 90° - \alpha/2$); gerar espigão com comprimento mínimo; se espigão $< 300\text{ mm}$: emitir `V-139 info` e considerar solução de canto arredondado |
| **EC-71** | Telhado com painel solar ($20\text{ kg/m}^2$) concentrado em 1 água | Carga assimétrica adicional de $500\text{ kg}$ em apenas um lado | Treliças do lado carregado precisam de seção maior; deflexão diferencial entre os dois lados da cumeeira | Aplicar carga distribuída extra apenas nas treliças sob a zona de painéis solares; verificar deflexão diferencial $\Delta_{dif} \le L/300$; se necessário reforçar com montantes adicionais ou seção maior do banzo superior |
| **EC-72** | Telhado com calha embutida no beiral (*box gutter* ou *concealed gutter*) | O beiral é fechado por baixo; a calha fica dentro de uma caixa entre o banzo inferior da treliça e a tabeira | Se a calha vazar, a água entra diretamente na cavidade do beiral e apodrece a estrutura | O motor gera a caixa da calha como elemento impermeabilizado com membrana contínua; emite `V-140 info: calha embutida — verificar impermeabilização e acesso para manutenção` |
| **EC-73** | Telhado com cumeeira ventilada (*ridge vent*) — abertura de $50\text{ mm}$ no OSB ao longo da cumeeira | A placa de OSB do telhado termina $25\text{ mm}$ antes da cumeeira de cada lado para permitir ventilação do ático | A abertura enfraquece a região de maior cisalhamento do diafragma de telhado | Verificar que o contraventamento do diafragma de telhado não depende de continuidade do OSB na cumeeira; se necessário inserir blocagem de cumeeira (*ridge blocking*) entre as treliças |
| **EC-74** | Telhado com beirais desiguais — beiral frontal de $600\text{ mm}$ e beiral lateral de $300\text{ mm}$ | As treliças de empena (*gable end*) e as treliças internas têm comprimentos de balanço diferentes | Diferentes cargas de vento nos beirais; treliças de empena com lookouts mais curtos que as laterais | Gerar treliças de empena com lookouts dimensionados para o beiral real de cada direção; verificar ancoragem de arrancamento (uplift) em cada treliça individualmente |
| **EC-75** | Telhado sobre planta em formato de U (pátio interno) — 3 trechos de telhado que se encontram em 2 rincões e 2 espigões | O Revit pode gerar cada trecho como telhado independente sem vínculos | Os rincões e espigões não são gerados automaticamente; treliças terminam no ar | Detectar arestas de telhados adjacentes que compartilham o mesmo beiral; gerar elementos de transição (vales, espigões, calhas) nas interseções; emitir `V-141 warning: telhados U não vinculados — gerando transições automaticamente` |
| **EC-76** | Telhado com recorte retangular para chaminé ($600\times 600\text{ mm}$) passando entre 2 treliças | As treliças adjacentes precisam ser reforçadas para carregar o vão aberto | Se a chaminé cai entre 2 treliças, a distância entre elas pode ser de até $1.200\text{ mm}$ sem apoio para OSB | Gerar cabeceiras (*headers*) entre as treliças adjacentes acima e abaixo do furo; reforçar as treliças adjacentes como treliças duplas (*double trimmers*); manter distância mínima de $50\text{ mm}$ entre a peça de madeira e a chaminé (fire clearance) |
| **EC-77** | Telhado onde o Revit exportou slope como $0.001°$ (praticamente horizontal, mas não exatamente $0°$) | Valores flutuantes residuais que não representam caimento real | O motor tenta gerar treliças com inclinação de $0.001°$, criando banzos superiores de $0.01\text{ mm}$ a mais numa ponta | Se inclinação $< 0.5°$: normalizar para $0°$ (telhado plano) ou para o caimento mínimo do catálogo ($1.5\%$ para telha metálica); emitir `V-142 info: inclinação residual normalizada` |
| **EC-78** | Telhado com 6+ águas em planta irregular (hexagonal, octogonal) | Múltiplos espigões convergindo num único ponto de cumeeira (pirâmide de N faces) | Nó de cumeeira com concentração de 6 peças; impossível de pregar/parafusar manualmente | Gerar *hub connector* (peça metálica central) para o nó de cumeeira poligonal; cada espigão encaixa na face correspondente do hub; quantificar o hub como peça especial CNC |

### 30.10 Detecção de Áreas de Reforço Estrutural, Pilares e Elementos Especiais

O motor deve identificar automaticamente, a partir da geometria e das cargas, todas as regiões que exigem reforço além do framing padrão.

#### 30.10.1 Pilaretes e Colunas Embutidos em Paredes

| # | Cenário | Critério de Detecção | Ação do Motor |
|---|---|---|---|
| **EC-79** | Parede portante com vão de abertura > $2.400\text{ mm}$ — verga recebe carga de telhado ou pavimento superior | A reação vertical na extremidade da verga excede a capacidade de um único montante jack | Gerar pilarete composto de 2 ou 3 montantes unidos (*multi-stud post*) sob cada extremidade da verga; o número de montantes é calculado como $n = \lceil R_{verga} / N_{montante,adm} \rceil$ |
| **EC-80** | Parede de canto que recebe carga de 2 direções (canto externo de edificação de 2+ pavimentos) | Carga axial acumulada no montante de canto é $> 1.5\times$ a carga dos montantes internos | Gerar montante de canto como coluna composta em L ($3\times$ montantes + bloqueios) em vez do detalhe simples de 2 montantes; se a carga exceder a capacidade composta: emitir `V-143 warning: considerar coluna de aço embutida` |
| **EC-81** | Viga de entrepiso com vão $> 4.00\text{ m}$ apoiada em parede abaixo — reação concentrada de $15\text{ kN}$ no ponto de apoio | O Revit mostra a viga pousando na placa superior da parede sem indicar reforço | A guia superior distribui a carga em $\approx 2\times$ montantes; se a carga por montante exceder o admissível, há esmagamento da guia | Inserir *bearing block* (bloco de apoio de madeira maciça $89\times 89\text{ mm}$) sob o ponto de carga, transferindo diretamente para o montante; se necessário, reforçar com montante duplo |
| **EC-82** | Viga baldrame de concreto com pilar intermediário — a parede de *light frame* apoiada na viga tem montantes sobre o pilar e sobre o vão livre | Montantes sobre o pilar de concreto estão em apoio rígido; montantes sobre o vão da viga estão em apoio flexível | Deformação diferencial da viga de concreto entre apoios rígidos e vão livre; trincas no revestimento | O motor verifica a cota de apoio e emite `V-144 info: distribuição desigual de apoio` se a deflexão estimada da viga de concreto exceder $L/500$ |
| **EC-83** | Parede portante com porta de correr embutida (*pocket door*) — o painel da porta desliza para dentro da cavidade da parede | A cavidade de embutimento ocupa $\approx 1.000\text{ mm}$ de parede onde os montantes são substituídos por trilhos metálicos de $1.6\text{ mm}$ sem função estrutural | A zona do pocket não tem montantes; a carga que viria desses montantes é redistribuída para os adjacentes | Gerar verga contínua sobre toda a zona do pocket (incluindo a cavidade + o vão visível da porta); reforçar os montantes nas extremidades da cavidade como pilaretes duplos; emitir `V-145 warning: zona de pocket door sem montantes — verificar caminho de carga` |
| **EC-84** | Parede em área molhada (banheiro) com bancada suspensa de $50\text{ kg}$ e espelho pesado de $30\text{ kg}$ | Cargas pontuais de fixação em alturas intermediárias da parede ($900\text{ a }1.200\text{ mm}$) | Montante simples de $38\times 89\text{ mm}$ pode não resistir à flexão da carga excêntrica | Gerar bloqueios horizontais (*nogging*) na altura da bancada e do espelho; se carga pontual $> 25\text{ kg}$: reforçar com montante duplo na posição da fixação |

#### 30.10.2 Reforços em Paredes com Aberturas Múltiplas

| # | Cenário | Critério de Detecção | Ação do Motor |
|---|---|---|---|
| **EC-85** | Duas janelas de $1.200\text{ mm}$ separadas por apenas $300\text{ mm}$ de alvenaria (*pier* estreito) | O *pier* entre as janelas tem apenas 1 montante estrutural de altura total | O único montante recebe toda a carga acumulada acima das duas janelas; fator de utilização potencialmente > 1.0 | Gerar *pier* como pilarete composto (2 ou 3 montantes); se a parede for de contraventamento (shear wall), verificar que o *pier* estreito não anule a capacidade de cisalhamento (*portal frame* ou *perforated shear wall method*) |
| **EC-86** | Porta de garagem de $5.000\times 2.400\text{ mm}$ — abertura gigante em parede portante | Verga de $5.000\text{ mm}$ de vão; reação vertical de $\approx 25\text{ kN}$ em cada extremidade | Verga de madeira sólida não é suficiente; pilaretes laterais sob carga extrema | Especificar verga de madeira laminada colada (MLC/Glulam) ou viga de aço laminado (perfil I ou W); gerar pilaretes de $4\times$ montantes em cada lado; verificar compressão na guia inferior sob o pilarete |
| **EC-87** | Parede de fachada com $80\%$ de área de abertura (vidros do piso ao teto alternados com *piers* de $400\text{ mm}$) | A parede funciona mais como pórtico do que como shear wall | Capacidade de cisalhamento drasticamente reduzida; *piers* estreitos sujeitos a flexão e torção | Calcular capacidade de cisalhamento pelo método de *perforated shear wall* (norma NDS / AS 1684); se insuficiente: emitir `V-146 erro` e exigir contraventamento adicional em outra parede |

#### 30.10.3 Apoios de Caixa d'Água, Reservatórios e Cargas Concentradas no Telhado

| # | Cenário | Critério de Detecção | Ação do Motor |
|---|---|---|---|
| **EC-88** | Caixa d'água de $500\text{ L}$ posicionada sobre 2 treliças que têm vão livre de $4.00\text{ m}$ | Carga concentrada de $500\text{ kg}$ distribuída em $1.00\text{ m}^2$ sobre treliças projetadas para $50\text{ kg/m}^2$ de carga distribuída | Deflexão localizada; possível colapso do banzo inferior da treliça sob carga pontual | Gerar vigas de distribuição (*spreader beams*) perpendiculares às treliças sob a caixa d'água, transferindo a carga para $\ge 4$ treliças; reforçar o banzo inferior das treliças na zona de apoio; emitir `V-090` se o reforço for insuficiente |
| **EC-89** | Caixa d'água de $1.000\text{ L}$ posicionada exatamente sobre uma parede não-portante (parede divisória interna sem função estrutural) | A parede "segura" a caixa mas não tem caminho de carga até a fundação | A parede não-portante esmaga sob $1.000\text{ kg}$; guias inferiores cedem; trincas no piso e forro | Emitir `V-091 erro crítico: caixa d'água sobre parede não-portante W22`; exigir reposicionamento sobre interseção de paredes portantes ou inserção de viga de transferência para paredes portantes adjacentes |
| **EC-90** | Ar-condicionado split condensadora de $80\text{ kg}$ fixada na parede externa a $2.200\text{ mm}$ de altura | Carga excêntrica de $80\text{ kg}$ + vibração + momento de $0.15\text{ kN}\cdot\text{m}$ sobre montante de $38\times 89\text{ mm}$ | Vibração transmitida para a estrutura; possível afrouxamento de fixadores ao longo do tempo | Gerar bloqueio horizontal (*nogging*) duplo na altura de fixação da condensadora; inserir montante reforçado (duplo) na posição exata; quantificar parafusos de fixação e suporte anti-vibratório de borracha no BOM |
| **EC-91** | Aquecedor solar ($200\text{ kg}$ boiler + $60\text{ kg}$ de placas) instalado sobre treliças do telhado | Carga total de $260\text{ kg}$ sobre região de $2.00\text{ m}^2$ do telhado | Treliças projetadas para $\le 100\text{ kg/m}^2$ (telha + forro + carga acidental); carga do aquecedor excede a previsão | Recalcular treliças na zona do aquecedor para carga adicional de $130\text{ kg/m}^2$; se necessário: usar seção maior do banzo superior ou reduzir o espaçamento de treliças de $600\text{ mm}$ para $400\text{ mm}$ na zona carregada |
| **EC-92** | Guarda-corpo metálico pesado ($25\text{ kg/m}$) no beiral de sacada suspensa por balanço de vigas de piso | Carga concentrada de $25\text{ kg/m}$ na extremidade do balanço, gerando momento fletor máximo na raiz | Momento fletor na raiz do balanço é $M = q \times L^2 / 2$; deflexão na ponta do balanço é amplificada | Verificar deflexão na ponta do balanço $\le L/180$; se ultrapassar: reforçar vigas com seção maior ou reduzir espaçamento; quantificar ancoragem de contra-balanço (*hold-back*) na raiz de cada viga |

---

## 31. REGRAS DE OURO INVIOLÁVEIS PARA ENGENHEIROS E AGENTES DE IA

Qualquer intervenção na base de código — por humanos ou por modelos de IA — deve respeitar categoricamente os 12 mandamentos sagrados da plataforma:

1. **A Realidade da Obra Vence a Abstração do CAD**: Se um modelo não puder ser parafusado porque não há espaço físico para a ponteira da parafusadeira ($\varnothing 80\text{ mm}$), o código está errado, mesmo que a matemática teórica pareça bela. Toda folga de ferramenta é sagrada.

2. **Zero Desperdício de Material Não Declarado**: Toda barra e chapa comprada deve ser justificada no plano de corte otimizado. Se houver retalho aproveitável, ele deve ser cadastrado e rastreado. A taxa de perda total do projeto (%) deve ser visível e rastreável no resumo.

3. **Imutabilidade e Determinismo Absoluto**: Para o mesmo arquivo de entrada e mesmo ruleset, o motor deve gerar exatamente os mesmos IDs de peças, mesmos comprimentos de corte e mesmo hash de execução, independentemente da plataforma (Windows/Linux/macOS) ou versão do Python (3.11, 3.12, 3.13).

4. **Isolamento Estrito de Domínio**: O núcleo do motor (`src/vigora_frame/engine/`) jamais importa APIs de terceiros específicas de software de modelagem (como `Autodesk.Revit.DB`, `ifcopenshell.api`, ou `ezdxf`). A inteligência geométrica e de framing deve permanecer 100% pura, testável e executável em servidores Linux headless sem interface gráfica.

5. **Rigor Inegociável com Normas ABNT NBR**: Nenhuma simplificação estética ou otimização de performance deve atropelar as distâncias de fixadores, folgas de dilatação térmica/higroscópica, espessuras mínimas de chapa ou fatores de segurança prescritas pelas normas brasileiras (NBR 14762, NBR 7190, NBR 16970, NBR 15575, NBR 6123). Em caso de dúvida, o motor assume a interpretação mais conservadora (mais segura).

6. **Autocorreção Auditável com Notificação Explícita**: O motor pode tentar corrigir automaticamente pequenos desvios de modelagem arquitetônica (como estender paredes com folgas de $3\text{ mm}$), mas deve obrigatoriamente registrar o evento no log de auditoria com nível `info` ou `warning`, indicando o desvio original e a correção aplicada. Cada autocorreção é transparente e rastreável no resultado JSON.

7. **Falha Segura (Fail-Safe) sem Exceções**: Se um erro estrutural crítico for detectado (como ausência de apoio para caixa d'água, verga ausente sob carga pesada, ou montante com fator de utilização > 1.0), a exportação para máquinas CNC deve ser bloqueada e as pranchas emitidas com a marca d'água de grande formato `RASCUNHO — NÃO LIBERADO PARA FÁBRICA`.

8. **Compatibilidade Retroativa do Esquema de Dados**: Alterações no `model.py` nunca devem apagar ou renomear campos existentes sem uma migração explícita. O campo `schema_version` deve ser incrementado, e o motor deve saber ler arquivos de versões anteriores sem perda de dados.

9. **Rastreabilidade Total (Traceability)**: Toda peça gerada tem um ID estável e determinístico. Toda regra construtiva que posiciona ou dimensiona uma peça é identificada pelo campo `rule` no `Member`. Todo conector ou fixador é vinculado à `Connection` que o originou. A cadeia completa de rastreio — do modelo do arquiteto à peça cortada na máquina — nunca é rompida.

10. **Cobertura de Testes > 90%**: Nenhum merge é aceito sem que a suíte de testes cubra pelo menos 90% das linhas executáveis do motor. Todo novo módulo, classe ou função pública deve ser acompanhado de pelo menos 3 testes unitários (cenário feliz, cenário de contorno e cenário de erro).

11. **Documentação In-Code Obrigatória**: Todo módulo Python de engenharia (em `engine/`, `export/`, `validate.py`) deve possuir docstring de módulo explicando a referência normativa (seção da NBR ou do manual de engenharia), o referencial de coordenadas adotado e os pressupostos simplificadores. Toda função pública deve ter docstring com parâmetros e retorno tipados.

12. **Respeito ao Construtor e ao Operador da Máquina**: O output do motor não é um exercício acadêmico. Ele será lido por carpinteiros, serralheiros, operadores de CNC e engenheiros de campo. Mensagens de erro, etiquetas de peças e instruções de montagem devem ser escritas em português claro e objetivo, com unidades explícitas (mm, kg, un) e sem jargão de programação.

---
*Fim da Especificação Técnica Integral — Vigora Frame Engine 3.0-ENTERPRISE.*
*Documento de ~1.500 linhas técnicas — © Vigora Engenharia & Tecnologia.*

