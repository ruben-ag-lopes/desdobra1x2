# Plano 12 — Critérios editáveis: o que falta

Já existe: no pop-up "Critérios e pesos", um cursor de 0% a 200% por critério, com "Aplicar e recalcular" e "Repor predefinidos". A escolha fica guardada no navegador (aplica-se ao Totobola **e** ao Futebol) e a tabela mostra "critérios personalizados". Como funciona: [criterios.md](criterios.md) e [criterios-antigos.md](criterios-antigos.md).

**Feito (27/09/2026):**
- **Critérios antigos editáveis** (jogos sem histórico): os 5 pesos (`forma`, `ranking_uefa`, `ultimos2`, `confronto_direto`, `classificacao`) têm sliders próprios de 0% a 100%, numa secção separada do pop-up ("Critérios do modelo antigo"). Diferença importante face aos multiplicadores: estes são uma **partilha de 100%** (a soma não pode ultrapassar 100% e cada um também não, `app/models.py`, validado no backend e travado no slider do frontend).
- **Correção do desdobramento:** um resultado com probabilidade só ligeiramente menor do que os outros dois deixou de ficar sempre a zero apostas — a repartição é agora sempre proporcional às probabilidades (`_allocate_counts`, com testes de regressão).
- **Futebol usa o mesmo editor de critérios** do Totobola (multiplicadores 0–200%; os critérios antigos não se aplicam aqui porque o Futebol só lista jogos com modelo treinado).
- **Mais linhas de golos** no Futebol: "mais de 1,5" e "mais de 3,5" golos, mostradas como informação (não validadas no backtest, ao contrário de "mais de 2,5" e "ambas marcam").

Hoje há um único conjunto de critérios (multiplicadores + pesos antigos), guardado uma vez e partilhado por toda a app.

## Falta fazer
1. **Perfis com nome:** além do "Predefinido" (bloqueado), perfis próprios ("Conservador", "O meu", …). Escolher o ativo, duplicar e apagar.
2. **Exportar, importar e partilhar por link** (perfil codificado no URL). Um link corrompido volta ao predefinido, com aviso.
3. **Multiplicadores por modelo:** poder alterar só a Primeira Liga, por exemplo, sem mexer nas seleções.
4. **Ajuste manual por jogo** (−3 a +3 na linha do boletim), para informação que o modelo não tem: lesões, castigos, motivação.
   - Aplica-se em log-odds (×0,15 por passo) às probabilidades finais e renormaliza, antes de fixos e duplas.
   - Opcional: ajuste da tendência para o empate.
5. **"Avaliar o meu perfil":** corre o backtest da última época com o perfil do utilizador e mostra o log loss comparado com o predefinido. Precisa de limite de pedidos e cache.
6. **Comparação:** mostrar as probabilidades do modelo predefinido ao lado das personalizadas.
7. **Registo** das previsões personalizadas com o perfil (plano 4), para comparar o acerto dos perfis com o predefinido.
8. **Cache:** a chave inclui o perfil. O predefinido continua a usar a cache do CDN e os personalizados não.

## Regras de segurança dos predefinidos
- O perfil "Predefinido" não é editável nem apagável. É definido no servidor e versionado com o modelo.
- Quando o modelo muda de versão, os perfis do utilizador continuam a funcionar (os multiplicadores são relativos) e o pop-up avisa que o predefinido foi atualizado.

## Verificação
- Com todos os multiplicadores a 100% as probabilidades são idênticas às predefinidas (já testado).
- "Repor predefinidos" volta ao estado inicial mesmo depois de importar um perfil.
- Pedido com valores fora dos limites ou ids desconhecidos: erro 422 (já testado).
