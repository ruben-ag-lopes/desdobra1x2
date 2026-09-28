# Roteiro

#api apoio
https://dashboard.api-football.com/soccer/widgets

O que já funciona em http://localhost:5173: Totobola e Totobola Extra (com fixos, duplas e critérios editáveis), separador Futebol com 22 ligas, Totoloto, Euromilhões e EuroDreams, aviso em destaque e botão de apoio. Como usar: [tutorial](tutorial.md). Método: [critérios](criterios.md).

## O que falta

| # | Tarefa | Depende de | Plano |
|---|---|---|---|
| 3 | Publicar no Vercel | conta Vercel (o GitHub já está) | [plano-publicacao-vercel.md](plano-publicacao-vercel.md) |
| 4 | Base de dados de resultados e acerto das previsões | escolha da base de dados | [plano-base-de-dados.md](plano-base-de-dados.md) |
| 5 | Donativos ✅ feito (Buy Me a Coffee); anúncios (fases 2 e 3) | — | [plano-anuncios-e-apoios.md](plano-anuncios-e-apoios.md) |
| 6 | Futebol: competições europeias, seleções, previsões pré-calculadas | tarefa diária (plano 4) | [plano-competicoes.md](plano-competicoes.md) |
| 7 | Novo visual | a tua aprovação da [maquete](https://claude.ai/artifact/K1C5CQPMKxTyRo3Koe2dD5) | [plano-design.md](plano-design.md) |
| 10 | Domínio `desdobra1x2.pt` | registador | [plano-dominio.md](plano-dominio.md) |
| 11 | Documentação: capturas, tabelas automáticas, página "Como funciona" | novo visual (plano 7) | [plano-readme-tutorial.md](plano-readme-tutorial.md) |
| 12 | Critérios: perfis com nome, partilha por link, ajuste manual por jogo | — | [plano-criterios-editaveis.md](plano-criterios-editaveis.md) |
| 13 | Ligas portuguesas abaixo da 1.ª Liga e mais ligas | chave da API-Football | [plano-ligas.md](plano-ligas.md) |
| 14 | Último sorteio, tabela de prémios e números mais frequentes nas lotarias | — | 📝 [plano-numeros-frequentes.md](plano-numeros-frequentes.md) |
| 15 | Contas de utilizador e acesso pago | decisão de preço/modelo | 📝 [plano-utilizadores-pagamento.md](plano-utilizadores-pagamento.md) |
| 16 | Resumo do desdobramento gerado por IA | chave Claude/OpenAI | 📝 [plano-resumo-ia.md](plano-resumo-ia.md) |
| 17 | Mercados de basquetebol, andebol, ténis, voleibol | ⛔ **bloqueado:** o plano gratuito da API-Sports não dá histórico nestes desportos (só jogos de hoje±1) | 📝 [plano-outros-desportos.md](plano-outros-desportos.md) |
| 18 | Guardas de segurança (rate limiting, erros sem detalhe interno, etc.) | — | 🔴 **implementar antes do go-live** — [plano-seguranca.md](plano-seguranca.md) |

**As tuas ações** (contas, chaves, decisões), pela ordem sugerida: [guia-acoes.md](guia-acoes.md).

## Ordem sugerida
Vercel (3) → domínio (10) → visual (7) → ligas portuguesas (13, fase 1) → base de dados e tarefa diária (4) → documentação final (11) → critérios (12) → Futebol europeu (6) → números frequentes (14) → anúncios (5, quando houver tráfego) → contas pagas (15) e resumo por IA (16), se decidires monetizar → outros desportos (17), quando ligares as APIs.
