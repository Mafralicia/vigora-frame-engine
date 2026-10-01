# Guia de modelagem no Revit para o Vigora Frame Engine (1 página)

**Regra de ouro:** modele a arquitetura normalmente; o framing é gerado. Nunca edite as peças geradas — mude a
arquitetura e clique em *Gerar framing*.

1. **Paredes pela linha de centro** (ou qualquer linha, mas a mesma no projeto — o plugin corrige para o eixo).
2. **Paredes encostando de verdade**: una as pontas e os encontros em T. Folga de 20–50 mm vira erro (V-075).
3. **Ângulos de 90° ou entre 120° e 180°** (use snap). 89,7° desenhado à mão não passa (V-078).
4. **Tipo de parede certo**: função *Exterior/Interior* e *Estrutural* marcado nas portantes
   (ou use o botão *Tipos de parede*). Portante decide apoio do telhado, do entrepiso e da caixa.
5. **Altura da parede**: restrição superior no nível de cima ou altura desconectada — as duas funcionam.
6. **Portas e janelas** como famílias com largura/altura/peitoril; ≥ 150 mm dos cantos e **fora de encontros em T**.
7. **Telhado por perímetro, um por volume, retangular e alinhado aos eixos.** O caimento das bordas define o tipo:
   4 bordas = 4 águas · 2 opostas = 2 águas · 1 borda = meia-água. Asas em L/T/U: um telhado por asa, encostado na
   linha de beiral do principal (rincão automático). Telhado desenhado por dentro das paredes = platibanda.
8. **Entrepiso**: piso no nível superior com o furo da escada (esboço ou abertura). **Escada** em lance reto,
   alinhada aos eixos. O vão do furo precisa de 2,00 m livres sobre a linha dos bocéis.
9. **Caixa d'água**: família com "Caixa" no nome (tipo BR_500L/BR_1000L) ou o botão *Caixa d'água*. Precisa de
   duas paredes estruturais paralelas a até 1,50 m embaixo (hall, banheiro, shaft), perto da cumeeira.

**Dica de custo:** medidas em múltiplos de 600/1200 mm reduzem cortes e perda de placa.
**Antes de gerar:** *Verificar modelo* → corrija o que aparecer (duplo clique = mostra no modelo).
