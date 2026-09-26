# Plano 13 — Ligas: o que falta

Já estão cobertas 22 ligas (Primeira Liga, as cinco grandes, as segundas divisões europeias, Escócia, Holanda, Bélgica, Turquia e Grécia) e as seleções, com modelo e backtest por liga ([backtests/README.md](backtests/README.md)). No Totobola, a competição indicada pela Santa Casa decide o modelo.

## Prioridade: ligas portuguesas abaixo da 1.ª Liga
Os concursos do Totobola incluem muitas vezes jogos da **Liga 2, Liga 3 e Campeonato de Portugal**, que hoje caem no método "pouco fiável" (probabilidades perto de 1/3).

| Divisão | Equipas | Fonte de dados proposta |
|---|---|---|
| Liga Portugal 2 | 18 | API-Football |
| Liga 3 | 24 (2 séries + fases finais) | API-Football; confirmar com o portal da FPF |
| Campeonato de Portugal | 56 (4 séries) | API-Football; confirmar com o portal da FPF |
| Taça de Portugal, Taça da Liga | todas as divisões | API-Football |

- **API-Football:** plano gratuito com 100 pedidos/dia. Chega para uma sincronização diária incremental e para carregar o histórico ao longo de alguns dias. Antes de começar, confirmar no endpoint `/leagues` os ids, as épocas disponíveis no plano gratuito e a cobertura real da Liga 3 e do Campeonato de Portugal.
- **Portal de resultados da FPF:** fonte oficial para validar. Só usar se os termos permitirem a recolha automática.
- **zerozero.pt e Transfermarkt:** não usar (os termos proíbem, em regra, a recolha automática).

### Como modelar
1. **Um Elo português único, das 4 divisões:** as subidas e descidas levam o rating da equipa consigo, e os jogos da Taça de Portugal entre divisões diferentes calibram a diferença de nível.
2. **Equipas novas** (vindas dos distritais) entram com o rating médio das equipas que desceram para essa divisão.
3. **Vantagem de casa e taxa de empates por divisão**, porque o empate é mais frequente nas divisões baixas.
4. **Sem odds:** não há comparação com casas de apostas. Validar contra as frequências históricas e o método anterior.
5. **Equipas B e sub-23** são equipas diferentes da principal.
6. **Sinónimos** dos nomes usados pela Santa Casa ("Vitória SC", "Belenenses", …), numa tabela editável (`team_aliases`, plano 4).

## Outras ligas
| Grupo | Ligas | Fonte | Nota |
|---|---|---|---|
| Europa, 2.ª fase | Suécia, Noruega, Dinamarca, Áustria, Suíça, Polónia | football-data.co.uk, ficheiros "new" | Existem, com odds de fecho. Formato diferente das ligas atuais e épocas por ano civil. |
| Fora da Europa | Brasil, Argentina, EUA (MLS), México, Japão | football-data.co.uk, ficheiros "new" | Mesmo formato e a mesma nota. |
| Competições europeias e taças | Liga dos Campeões, Liga Europa, Conference League | API-Football ou football-data.org | Ver o plano 6. |

## Página de análise de cada jogo
Já mostramos 1X2, golos e resultados prováveis. Faltam:
- forma: últimos 5 resultados de cada equipa (V/E/D) e golos marcados e sofridos;
- Elo das duas equipas e a sua evolução na época;
- confrontos diretos (últimos 5);
- classificação atual (API-Football);
- API `GET /api/futebol/jogos/{id}`.

## Fases
| Fase | Entrega |
|---|---|
| 1 | Liga 2, Liga 3, Campeonato de Portugal: sincronização, Elo português, backtest por divisão, sinónimos |
| 2 | Europa 2.ª fase e fora da Europa |
| 3 | Página de análise de cada jogo |
| 4 | Competições europeias e taças (Elo entre ligas) |
| 5 | Tudo na base de dados (plano 4) + tarefa diária |

## Medida de sucesso
- **Cobertura do Totobola:** % de jogos dos concursos que usam modelo treinado, medida nos últimos concursos. Objetivo ≥ 95%.
- **Por liga:** log loss do modelo escolhido menor do que o das frequências históricas e menor ou igual ao do método anterior.

## Riscos
- O plano gratuito da API-Football pode limitar as épocas antigas. Se não chegar, há planos pagos (preço a confirmar).
- Confirmar os termos de uso das fontes para um site público com donativos ou anúncios.
- Menos jogos por equipa e mais mudanças de plantel: previsões menos precisas. O pop-up deve dizê-lo ("Campeonato de Portugal: histórico curto").
