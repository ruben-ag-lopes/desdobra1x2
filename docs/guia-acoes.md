# Guia das tuas ações

Só tu podes criar contas, aceitar termos e pagar. Este guia diz o que fazer, pela ordem que desbloqueia mais trabalho, e o que me enviar depois. **Nunca me envies palavras-passe. Chaves de API e tokens também não os colo em ficheiros que vão para o Git**: guardam-se em `backend/.env` (já ignorado pelo Git) e nas variáveis do Vercel.

## 1. GitHub — ✅ feito
Repositório **privado**: https://github.com/ruben-ag-lopes/desdobra1x2 (ramo `master`). Só tu o vês. Para enviar alterações novas: `git push`.

## 2. Vercel + domínio (15 min) — próximo passo
O domínio `desdobra1x2.pt` já está comprado (Dominios.pt) e as guardas de segurança do
[plano-seguranca.md](plano-seguranca.md) já estão todas aplicadas no código. Falta só publicar.

1. vercel.com → **Sign Up** → **Continue with GitHub** (plano **Hobby**, gratuito, sem cartão).
2. **Add New → Project** → importa o repositório `desdobra1x2`.
3. Se pedir a "Root Directory", deixa a raiz: o `vercel.json` já define os dois serviços (`web` e `api`).
4. **Antes do 1.º deploy**, em **Settings → Environment Variables**, cria estas (todos os ambientes: Production, Preview, Development):

   | Nome | Valor |
   |---|---|
   | `DATA_DIR` | `/tmp/data` |
   | `CORS_ORIGINS` | `https://desdobra1x2.pt,https://www.desdobra1x2.pt` |
   | `API_FOOTBALL_KEY` | a tua chave (está em `backend/.env`) |
   | `VITE_BUYMEACOFFEE_URL` | `https://www.buymeacoffee.com/desdobra1x2` |

   Não copies `API_BASKETBALL`, `API_FORMULA_1`, etc. — não têm código a usá-las ainda (plano 17, bloqueado). Também não precisas de `ANTHROPIC_API_KEY` nem das variáveis do `GCP_PROJECT`: ficam desligadas sem elas, sem problema.
5. **Deploy**. Espera terminar e abre o endereço `*.vercel.app` que aparecer.
6. **Ligar o domínio:** no projeto → **Settings → Domains → Add** → escreve `desdobra1x2.pt`, depois `www.desdobra1x2.pt` (define o `www` a redirecionar para o domínio raiz, o Vercel pergunta isto). Ele mostra os registos DNS a criar (um `A` na raiz, um `CNAME` no `www`).
7. No painel da **Dominios.pt**, na gestão de DNS do domínio, cria esses dois registos com os valores exatos que o Vercel mostrou.
8. Espera a propagação (minutos a algumas horas) — o Vercel emite o certificado HTTPS sozinho, não precisas de fazer nada.
9. **Ativar o Web Analytics:** no projeto → **Settings → Analytics → Enable** (grátis, sem cookies).
10. Confirma: `https://desdobra1x2.pt/api/health` devolve `{"status":"ok"}`, e o site abre com cadeado.

Envia-me quando estiver feito (ou o link `*.vercel.app`, se quiseres que eu veja antes de ligar o domínio) — testo o scraping da Santa Casa a partir do Vercel, que é o maior risco (pode bloquear pedidos de IPs de datacenter, ver o plano 3).

O plano Hobby só permite uso **não comercial**: donativos são permitidos, anúncios não (ver o plano 5 para as alternativas).

## 3. Donativos — ✅ feito
Buy Me a Coffee ativo: buymeacoffee.com/desdobra1x2. O link está em `frontend/.env.local` (local); vai também para as variáveis de ambiente do Vercel no passo 2. Só este método de apoio — sem PayPal.

## 4. API-Football — ✅ conta criada
A chave está em `backend/.env` (`API_FOOTBALL_KEY`, fora do Git). Confirmei que a mesma chave dá acesso gratuito (100 pedidos/dia cada) a futebol, basquetebol, NBA, Fórmula 1, MMA, râguebi, voleibol e andebol. Falta o código que a usa, com uma única atualização por dia (plano 13, e o 17 está bloqueado para os outros desportos — ver [plano-outros-desportos.md](plano-outros-desportos.md)). Quando publicares, a chave vai também para as variáveis do Vercel (já no passo 2).

## 5. Segurança — ✅ feito
Todos os itens bloqueadores e recomendados do [plano-seguranca.md](plano-seguranca.md) estão aplicados: rate limiting, erros sem detalhe interno, limite de tamanho do pedido, cabeçalhos de segurança, honeypot no formulário de sugestões, e as dependências desatualizadas (FastAPI/Starlette, tinham 14 vulnerabilidades conhecidas) foram atualizadas. Só falta, no momento do deploy: pôr `CORS_ORIGINS` com o domínio real (já no passo 2) e confirmar que nenhuma chave foi exposta nalgum sítio (também já cobertas no passo 2).

## 6. Base de dados (15 min) — só depois do deploy
Recomendo **Postgres na Neon** (plano gratuito), ligado ao Vercel:
1. No projeto Vercel → **Storage** (ou Marketplace) → **Neon** → **Create**. Aceita o plano gratuito.
2. O Vercel cria a variável `DATABASE_URL` sozinho.
3. Avisa-me e crio as tabelas do [plano 4](plano-base-de-dados.md).

A alternativa é continuar só com o BigQuery, que dá mais trabalho e custos em Google Cloud.

## 7. Decisões (sem contas)
- **Maquete do novo visual:** abre https://claude.ai/artifact/K1C5CQPMKxTyRo3Koe2dD5 (só tu a vês). Diz-me o que mudar; falta o logótipo.
- **Anúncios:** só donativos por agora (recomendado, ver o plano 5). Publicidade de casas de apostas exige parecer jurídico.
- **Termos de uso e política de privacidade:** ✅ rascunhos escritos (`frontend/public/termos.html` e `privacidade.html`), ligados no rodapé do site. Convém um jurista rever antes de dependeres deles a sério, especialmente antes de anúncios.

## Resumo
| # | Ação | Tempo | Custo | Desbloqueia |
|---|---|---|---|---|
| 1 | GitHub | feito | 0 € | tudo o resto |
| 2 | Vercel + domínio `.pt` | 15 min | ~1,23 € (domínio, já pago) | site online |
| 3 | Buy Me a Coffee | feito | 0 € | donativos |
| 4 | API-Football | feito | 0 € | ligas portuguesas |
| 5 | Segurança | feito | 0 € | — |
| 6 | Neon (Postgres) | 15 min | 0 € | acerto das previsões |
| 7 | Decisões | — | — | visual e anúncios |
