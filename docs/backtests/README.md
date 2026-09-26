# Resultados dos backtests

Teste cronológico nas duas últimas épocas de cada liga, com os modelos reajustados de 4 em 4 semanas e cada jogo previsto só com dados anteriores. Métrica: **log loss** (quanto mais baixo, melhor). Os ficheiros `<liga>.json` e `<liga>-golos.json` desta pasta têm todas as métricas.

## 1X2
"Frequências" é prever sempre a percentagem histórica de 1, X e 2. "Motor anterior" é a fórmula de Elo antiga da app. "Casas" são as odds de fecho sem margem.

| Liga | Frequências | Motor anterior | Melhor modelo nosso | Casas |
|---|---|---|---|---|
| Primeira Liga (P1) | 1,086 | 0,942 | **0,930** Elo calibrado | 0,918 |
| Premier League (E0) | 1,090 | 1,041 | **1,029** Poisson+H2H+Dixon–Coles | 1,017 |
| LaLiga (SP1) | 1,054 | 0,992 | **0,986** Poisson+H2H | 0,963 |
| Serie A (I1) | 1,083 | 1,022 | **0,991** Elo calibrado | 0,975 |
| Bundesliga (D1) | 1,065 | 0,974 | **0,966** Poisson+H2H+Dixon–Coles | 0,949 |
| Ligue 1 (F1) | 1,069 | 1,014 | **1,006** Elo calibrado | 0,982 |
| Championship (E1) | 1,082 | 1,084 | **1,061** Elo | 1,043 |
| League One (E2) | 1,070 | 1,053 | **1,044** Elo | 1,027 |
| League Two (E3) | 1,078 | 1,062 | **1,046** Elo | 1,027 |
| National League (EC) | 1,068 | 1,030 | **1,006** Elo | 0,994 |
| Premiership escocesa (SC0) | 1,073 | 0,989 | **0,979** Elo | 0,971 |
| Championship escocesa (SC1) | 1,091 | 1,068 | **1,059** Elo | 1,053 |
| League One escocesa (SC2) | 1,082 | 1,068 | **1,052** Elo | 1,008 |
| League Two escocesa (SC3) | 1,081 | 1,089 | **1,069** Poisson | 1,058 |
| 2. Bundesliga (D2) | 1,067 | 1,069 | **1,052** Elo | 1,035 |
| Serie B (I2) | 1,071 | 1,025 | 1,027 Elo | 1,014 |
| LaLiga 2 (SP2) | 1,080 | 1,063 | **1,055** Poisson | 1,029 |
| Ligue 2 (F2) | 1,105 | 1,117 | **1,082** Elo | 1,061 |
| Eredivisie (N1) | 1,081 | 0,995 | **0,982** Elo | 0,970 |
| Liga belga (B1) | 1,078 | 1,040 | **1,014** Elo | 1,000 |
| Liga turca (T1) | 1,085 | 1,022 | **1,011** Poisson | 0,979 |
| Liga grega (G1) | 1,084 | 0,975 | **0,962** Elo | 0,943 |

Conclusões:
- Em 21 das 22 ligas o modelo treinado melhora o método anterior. A exceção é a Serie B, com empate técnico (1,027 contra 1,025).
- As casas de apostas continuam à frente em todas as ligas, por 0,006 a 0,05.
- Entre os nossos modelos a diferença é pequena (≤ 0,004), por isso, quando é mínima, fica o mais simples (Elo calibrado).

## Mercados de golos
Log loss de "mais de 2,5 golos" e de "ambas marcam", comparando com prever sempre a média histórica da liga. Na app, o valor do modelo só aparece onde ganha à média por pelo menos 0,002.

| Liga | +2,5: média → modelo | +2,5: casas | Ambas marcam: média → modelo |
|---|---|---|---|
| Primeira Liga | 0,695 → **0,674** | 0,673 | 0,693 → **0,690** |
| Premier League | **0,688** → 0,692 | 0,683 | 0,687 → 0,686 |
| LaLiga | 0,697 → **0,680** | 0,665 | **0,690** → 0,692 |
| Serie A | 0,697 → 0,696 | 0,698 | 0,704 → **0,695** |
| Bundesliga | 0,649 → **0,636** | 0,634 | **0,666** → 0,667 |
| Ligue 1 | 0,692 → 0,690 | 0,666 | 0,696 → 0,696 |
| Seleções | 0,696 → **0,672** | — | 0,687 → **0,677** |
| Championship | 0,698 → 0,701 | — | 0,693 → 0,694 |
| League One | 0,694 → 0,693 | — | 0,692 → **0,690** |
| National League | 0,688 → **0,678** | — | 0,683 → **0,680** |
| Premiership escocesa | 0,692 → **0,687** | — | 0,694 → **0,683** |
| League One escocesa | 0,698 → **0,695** | — | 0,696 → 0,695 |
| League Two escocesa | 0,690 → **0,683** | — | 0,688 → **0,677** |
| Serie B | 0,697 → **0,693** | — | 0,690 → 0,698 |
| LaLiga 2 | 0,709 → **0,701** | — | 0,697 → 0,700 |
| Eredivisie | 0,658 → **0,648** | — | 0,668 → 0,668 |
| Liga turca | 0,692 → **0,679** | — | 0,691 → 0,694 |
| Liga grega | 0,696 → **0,688** | — | 0,695 → 0,696 |

O confronto direto e o ajuste Dixon–Coles quase não ajudam nos golos. Nas outras ligas testadas (League Two, Championship, 2. Bundesliga, Ligue 2, Liga belga, Championship escocesa) o modelo não bate a média da liga e a app mostra a média.

## Repetir
```
cd backend
python -m app.research.backtest --league <código> --json ../docs/backtests/<código>.json
python -m app.research.backtest --league <código> --goals --json ../docs/backtests/<código>-golos.json
python -m app.research.backtest --international --seasons 10
```
