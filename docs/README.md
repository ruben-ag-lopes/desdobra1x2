# Roteiro

| # | Tarefa | Estado |
|---|---|---|
| 1 | Pop-up "Critérios e pesos" em vez do nome do modelo | ✅ Feito |
| 2 | Duplas: escolher 2 resultados e redistribuir as probabilidades | ✅ Feito |
| 3 | Publicação no Vercel | 📝 [Plano](plano-publicacao-vercel.md) · 🔨 `vercel.json`, versões fixas, cache no CDN e limites anti-abuso feitos; repositório Git criado (local, 1.º commit feito); falta GitHub + 1.º deploy |
| 4 | Base de dados de resultados e acerto das previsões | 📝 [Plano](plano-base-de-dados.md) |
| 5 | Anúncios + botão Buy Me a Coffee / PayPal | ✅ Botão feito · 📝 [Plano](plano-anuncios-e-apoios.md) |
| 6 | Jogos das principais competições (separador "Futebol", golos, boletim) | ✅ Separador "Futebol" com 22 ligas, golos e boletim · 📝 [Plano](plano-competicoes.md) (faltam competições europeias e a tarefa diária) |
| 7 | Novo visual: cores, tipo de letra e apresentação | 📝 [Plano](plano-design.md) · 🎨 [Maquete](https://claude.ai/artifact/K1C5CQPMKxTyRo3Koe2dD5) para aprovares |
| 8 | Aviso em destaque: previsões estatísticas, números aleatórios, sem garantia de acerto | ✅ Feito (todas as páginas) |
| 9 | Nome **desdobra1X2** no título; subtítulo sem a referência ao site oficial | ✅ Feito |
| 10 | Domínio `desdobra1x2.pt` o mais barato possível | 📝 [Plano](plano-dominio.md) |
| 11 | README com tutorial e critérios completos de previsão | ✅ [README](../README.md), [tutorial](tutorial.md), [critérios](criterios.md) e [desenvolvimento](desenvolvimento.md) escritos · 📝 [Plano](plano-readme-tutorial.md) (faltam capturas de ecrã, tabelas automáticas e a página "Como funciona") |
| 12 | Critérios editáveis pelo utilizador (predefinidos sempre disponíveis) | ✅ Cursores 0–200% no pop-up, guardados no navegador · 📝 [Plano](plano-criterios-editaveis.md) (faltam perfis, partilha e ajuste por jogo) |
| 13 | Ligas internacionais + todas as ligas portuguesas (até ao Campeonato de Portugal) | 🔨 22 ligas do football-data.co.uk feitas · 📝 [Plano](plano-ligas.md) (faltam Liga 2, Liga 3 e Campeonato de Portugal, que precisam da chave da API-Football) |

## Decisões que dependem de ti
1. **Domínio** (ainda por decidir): que registador (recomendado: o de renovação mais barata; ver o plano 10) e se queres o e-mail `contacto@desdobra1x2.pt` (DNS no Cloudflare).
2. **Links reais** do Buy Me a Coffee e do PayPal (plano 5).
3. **Base de dados:** Postgres (Neon/Supabase, recomendado) ou continuar só com o BigQuery (plano 4).
4. **Anúncios:** avançar só com donativos no início (recomendado), e se no futuro aceitas publicidade de apostas (plano 5).
5. **Alojamento do backend:** Vercel Services (recomendado) ou Render/Railway (plano 3).
6. **Maquete do novo visual:** aprovar ou pedir alterações (plano 7). Falta o logótipo.
7. **Dados das ligas portuguesas:** criar uma chave gratuita da API-Football (plano 13, fase 1).

## Ordem sugerida
3 (GitHub + preview no Vercel) → 10 (domínio) → 7 (visual, depois de aprovares a maquete) → 13 fase 1 (Liga 2, Liga 3 e Campeonato de Portugal, precisa da chave da API-Football) → 4 (base de dados + tarefa diária) → 11 (capturas e página "Como funciona", já com o visual final) → 12 (perfis e partilha) → 5 fases 2/3 (anúncios, quando houver tráfego).
