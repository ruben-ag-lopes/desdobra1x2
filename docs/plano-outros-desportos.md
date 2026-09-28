# Plano — Mercados de previsão para basquetebol, andebol, ténis e voleibol

> **Investigado (27/09/2026): bloqueio real, não de código.** A tua chave API-Sports está confirmada a funcionar
> (`plan: Free`, ativa) para basquetebol, andebol e voleibol, mas o **plano gratuito destes desportos só dá
> acesso a jogos de hoje, ontem e amanhã** (`GET /games?date=...`) — qualquer data fora dessa janela de 3 dias
> devolve erro `"Free plans do not have access to this date"`. O mesmo acontece ao pedir por época
> (`season=2025-2026` → erro, só aceita 2022–2024, mas os jogos de hoje já não pertencem a essas épocas) ou por
> "últimos N jogos de uma equipa" (`last=10` → bloqueado de propósito). **Não há forma de obter histórico**, e
> sem histórico não há como calcular a força das equipas (Elo, médias de pontos, nada). Isto é diferente do
> futebol: a tua chave de futebol (`v3.football.api-sports.io`) tem acesso normal a 8 épocas de histórico.

## O que isto significa
Não é possível construir qualquer modelo de previsão real para basquetebol, andebol ou voleibol com o plano
gratuito atual. Os separadores destes desportos continuam com a página "em preparação".

## Opções
1. **Upgrade a um plano pago da API-Sports** (não consegui obter os preços automaticamente — `api-sports.io/pricing` bloqueou o pedido; confirma manualmente no teu painel em dashboard.api-football.com, secção do desporto em causa). Depois disso, o plano técnico abaixo aplica-se sem alterações.
2. **Outra fonte de dados histórica e gratuita** para pelo menos um destes desportos (ex.: um ficheiro de resultados históricos como os que usamos para futebol, football-data.co.uk). Não encontrei nenhuma equivalente óbvia para basquetebol/andebol/voleibol; precisaria de pesquisa dedicada.
3. **Ficar só com "jogos de hoje" sem previsão própria**, mostrando quando muito o calendário do dia (sem 1X2 nem pontos), o que tem pouco valor por si só.

**Recomendação:** não avançar com nenhum destes desportos até teres decidido entre 1 e 2. Não vale a pena escrever código de um modelo que não tem dados para treinar.

## Mercados (mantido para quando houver dados)
| Desporto | Mercado principal (equivalente ao 1X2) | Linhas de pontos/sets |
|---|---|---|
| Basquetebol / NBA | Vencedor (sem empate: 1/2, ou spread) | Total de pontos (over/under, ex.: 215,5); diferença de pontos (spread) |
| Andebol | Vencedor (1X2, o empate existe) | Total de golos (over/under, ex.: 55,5) |
| Voleibol | Vencedor do encontro (sem empate) | Total de sets (melhor de 3 ou de 5); total de pontos por set |
| Ténis | Vencedor do encontro | Total de sets; hándicap de sets; total de jogos (games) — **não está nos separadores da app nem coberto pela tua chave API-Sports**; ficaria para um fornecedor à parte |

## Modelo estatístico (proposta, sem alterações face à ideia original)
- **Vencedor sem empate** (basquetebol, voleibol): Elo calibrado, igual ao futebol, sem a componente de empate.
- **Totais de pontos/golos** (basquetebol, andebol): Poisson, trocando "golos" por "pontos"/"golos de andebol" — a `PoissonModel` já é genérica à escala, só muda o `MAX_GOALS` por desporto.
- **Sets de voleibol:** modelo de "melhor de N", não reaproveita o Poisson diretamente.

## F1 e MMA
Já confirmámos (sessão anterior) que a tua chave cobre F1 e MMA, mas são corrida/combate, sem "1X2" nem "linhas de pontos" — precisam de um modelo próprio (pódio, vitória por nocaute vs. decisão) e ficam fora do âmbito deste plano.

## Passos (só depois de resolvido o acesso a histórico)
1. Confirmar o histórico disponível no plano escolhido (quantas épocas, que competições).
2. Escolher um desporto para começar (Basquetebol ou Andebol, por reaproveitarem mais código do futebol).
3. Backtest do vencedor e das linhas de pontos, com a mesma disciplina do futebol (docs/backtests/).
4. Trocar a página "em preparação" pelo separador real, reaproveitando `FutebolTab.tsx` como modelo.

## Verificação
- Antes de mostrar qualquer previsão: log loss do modelo escolhido menor do que as frequências históricas, no backtest desse desporto.
- Mesma regra do futebol: nunca anunciar "aposta de valor" sem bater as casas de apostas num backtest com amostra suficiente.
