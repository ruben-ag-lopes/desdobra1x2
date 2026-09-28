# Plano 6 — Futebol: o que falta

O separador "Futebol" já existe: pesquisa por equipa e competição, 1X2 nosso e das casas, golos, resultados prováveis e boletim, para 22 ligas. Tem também o mesmo editor de critérios (multiplicadores) do Totobola, e mostra "mais de 1,5"/"mais de 3,5" golos como informação (não validadas no backtest, só "mais de 2,5" e "ambas marcam" o são). Os resultados dos backtests estão em [backtests/README.md](backtests/README.md).

## Falta fazer
1. **Competições europeias** (Liga dos Campeões, Liga Europa, Conference League), com calendário e horários.
   - Calendário: API football-data.org (chave gratuita, 10 pedidos/min) ou API-Football.
   - Força comparável entre ligas: um Elo único para todos os clubes, ligado pelos jogos europeus, para o Benfica e o Inter ficarem na mesma escala. O clubelo.com serve de referência quando estiver em funcionamento.
   - Validar num backtest só com jogos europeus antes de mostrar.
2. **Seleções no separador Futebol:** o modelo já existe (usado no Totobola), falta o calendário (Liga das Nações, qualificações).
3. **Previsões pré-calculadas:** uma tarefa diária calcula as previsões de todos os próximos jogos e guarda o resultado (ver plano 4). A pesquisa passa a ser uma leitura rápida, sem treinar nada no momento.
4. **API:**
   - `GET /api/futebol/jogos/{id}`: um jogo com todos os detalhes (para ligação direta e partilha);
   - `POST /api/futebol/boletim`: probabilidade conjunta calculada no servidor (hoje é feita no navegador).
5. **Melhoria a testar:** usar as odds de abertura como variável adicional ("combinar com o mercado") e medir se o log loss desce.
6. **Registo de previsões e resultados** na base de dados (plano 4), para medir o acerto por liga e por mercado.

## Regras que se mantêm
- **Não anunciar "apostas de valor"** enquanto o modelo não bater as odds de fecho num backtest com amostra suficiente e retorno positivo. Hoje as casas ganham em todas as ligas.
- **Sem links para casas de apostas**, salvo decisão do plano 5. Aviso de jogo responsável (+18) sempre visível.
- **Um mercado novo só aparece** depois de validado no backtest com log loss próprio.

## Verificação
- **Competições europeias:** o modelo escolhido tem log loss menor do que as frequências históricas nos jogos europeus do teste.
- **Boletim no servidor:** a probabilidade conjunta é igual ao produto das probabilidades, confirmado com um teste.
- **Tarefa diária:** o 1.º pedido a frio fica abaixo de 2 s.
