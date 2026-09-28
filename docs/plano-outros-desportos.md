# Plano — Mercados de previsão para basquetebol, andebol, ténis e voleibol

> Estado: separadores criados ("Outros desportos": Basquetebol, NBA, Fórmula 1, MMA, Râguebi, Voleibol,
> Andebol), todos com uma página "em preparação" — **sem dados nem modelo ligados ainda**. Confirmámos
> (26/09/2026) que a tua chave da API-Football dá acesso gratuito (100 pedidos/dia cada) a todos estes
> desportos, mas ainda não foi escrita nenhuma integração: combinaste que ligas tu próprio as APIs.

Este plano define os mercados a mostrar assim que cada desporto tiver dados ligados, para o trabalho de integração já saber o alvo.

## Mercados por desporto
| Desporto | Mercado principal (equivalente ao 1X2) | Linhas de pontos/sets |
|---|---|---|
| Basquetebol / NBA | Vencedor (sem empate: 1/2, ou spread) | Total de pontos (over/under, ex.: 215,5); diferença de pontos (spread) |
| Andebol | Vencedor (1X2, o empate existe) | Total de golos (over/under, ex.: 55,5) |
| Ténis | Vencedor do encontro | Total de sets; hándicap de sets; total de jogos (games) |
| Voleibol | Vencedor do encontro (sem empate) | Total de sets (melhor de 3 ou de 5); total de pontos por set |

Mesma lógica dos golos no futebol: um mercado só aparece na app **depois de validado num backtest** (log loss menor do que prever sempre a média histórica), com a mesma regra de mostrar "média da categoria" quando o modelo não ganha.

## Modelo estatístico (reaproveitar o que já existe)
- **Vencedor sem empate** (basquetebol, voleibol, ténis): o mesmo Elo calibrado já usado no futebol serve, trocando só a fórmula final por uma probabilidade de vencedor único (sem a componente de empate).
- **Totais de pontos/golos** (basquetebol, andebol): o mesmo modelo de Poisson do futebol, trocando "golos" por "pontos" ou "golos de andebol" — a machinery (`app/research/models.py`, `PoissonModel`) já é genérica a qualquer contagem de eventos, só muda a escala (pontos de basquetebol chegam a 100+, por isso `MAX_GOALS` teria de ser paramétrico por desporto).
- **Sets de ténis/voleibol:** mais parecido a uma série "melhor de N" do que a golos — precisa de um modelo próprio (probabilidade de ganhar um set, depois combinar em "melhor de 3/5"), não reaproveita diretamente o Poisson.

## Dados
A tua chave da API-Football (API-Sports) cobre:
- `v1.basketball.api-sports.io` — jogos, resultados, classificações.
- `v2.nba.api-sports.io` — específico da NBA.
- `v1.handball.api-sports.io`
- `v1.volleyball.api-sports.io`
- Ténis e Fórmula 1/MMA **não têm cobertura no mesmo fornecedor** (API-Sports não tem `tennis`/`mma`/`formula-1` no plano gratuito verificado) — confirmar se há um plano/fornecedor alternativo antes de prometer estes dois.

## Passos (quando a integração das APIs estiver feita)
1. Confirmar quais destes desportos a tua chave realmente cobre com dados suficientes (histórico + próximos jogos).
2. Escolher **um desporto para começar** (sugestão: Basquetebol ou Andebol, por reaproveitarem mais código do futebol).
3. Backtest do vencedor e das linhas de pontos, com a mesma disciplina do futebol (docs/backtests/).
4. Trocar a página "em preparação" pelo separador real, reaproveitando `FutebolTab.tsx` como modelo (pesquisa, cartão de jogo, boletim, pop-up de critérios).
5. Repetir por desporto.

## Nota sobre F1 e MMA
Fórmula 1 e MMA não têm um "1X2" nem "linhas de pontos" — são eventos de corrida/combate. Precisam de um modelo diferente (ex.: probabilidade de pódio, de vitória por nocaute vs. decisão) e ficam fora do âmbito deste plano; merecem um plano próprio quando chegar a vez.

## Verificação
- Antes de mostrar qualquer previsão de um novo desporto: log loss do modelo escolhido menor do que as frequências históricas, no backtest desse desporto.
- Mesma regra do futebol: nunca anunciar "aposta de valor" sem bater as casas de apostas num backtest com amostra suficiente.
