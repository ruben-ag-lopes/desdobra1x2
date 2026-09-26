# Guia das tuas ações

Só tu podes criar contas, aceitar termos e pagar. Este guia diz o que fazer, pela ordem que desbloqueia mais trabalho, e o que me enviar depois. **Nunca me envies palavras-passe. Chaves de API e tokens também não os colo em ficheiros que vão para o Git**: guardam-se em `backend/.env` (já ignorado pelo Git) e nas variáveis do Vercel.

## 1. GitHub — ✅ feito
Repositório **privado**: https://github.com/ruben-ag-lopes/desdobra1x2 (ramo `master`). Só tu o vês. Para enviar alterações novas: `git push`.

## 2. Vercel (10 min)
1. vercel.com → **Sign Up** → **Continue with GitHub** (plano **Hobby**, gratuito, sem cartão).
2. **Add New → Project** → importa o repositório `desdobra1x2`.
3. Se pedir a "Root Directory", deixa a raiz: o `vercel.json` já define os dois serviços.
4. Em **Settings → Environment Variables**, define `DATA_DIR` = `/tmp/data`. Os links de donativos (passo 4) entram aqui também.
5. **Deploy**. Envia-me o endereço `*.vercel.app` que aparecer; eu testo tudo (o scraping da Santa Casa a partir do Vercel é o maior risco, ver o plano 3).

O plano Hobby só permite uso **não comercial**: donativos são permitidos, anúncios não.

## 3. Domínio `.pt` (15 min + 10 €)
O Vercel e o Cloudflare não vendem `.pt`, por isso registas num registador português e ligas ao Vercel (grátis).
1. Vê se `desdobra1x2.pt` está livre: pt.pt → Ferramentas → WHOIS.
2. Escolhe o registador. Pelos preços que encontrei (confirma antes de pagar, com e sem IVA): **Site.pt** (11,95 € no 1.º ano, 14,95 € a renovar), PTISP (16,50 €). Evita as promoções de 1 € ou grátis cuja renovação seja muito mais cara.
3. Regista **por 1 ano**. Vão pedir o teu nome e um número de identificação (CC ou passaporte); desde 1 de julho de 2026 os dados são validados antes de o registo ficar ativo.
4. No Vercel: **Settings → Domains → Add** `desdobra1x2.pt` e `www.desdobra1x2.pt`. O Vercel mostra os registos DNS (um `A` para a raiz e um `CNAME` para o `www`). Cria-os no painel do registador.
5. Espera a propagação (minutos a horas) e o certificado HTTPS aparece sozinho.
6. Liga a renovação automática ou põe um lembrete.

Detalhes e alternativas (e-mail `contacto@desdobra1x2.pt` grátis com Cloudflare): [plano-dominio.md](plano-dominio.md).

## 4. Donativos (20 min)
- **Buy Me a Coffee:** buymeacoffee.com → Sign up → escolhe o nome da página → liga a conta de pagamentos (Stripe ou PayPal). O link fica `buymeacoffee.com/<nome>`.
- **PayPal.Me:** paypal.com/paypalme → cria o teu link, `paypal.me/<nome>`.
- Depois pões os dois em `frontend/.env.local` (local) e nas variáveis do Vercel: `VITE_BUYMEACOFFEE_URL` e `VITE_PAYPAL_URL`. Envia-me os links e faço eu.

## 5. API-Football (10 min) — desbloqueia Liga 2, Liga 3 e Campeonato de Portugal
1. dashboard.api-football.com/register → cria a conta com o teu e-mail e confirma-o.
2. Escolhe o plano **Free** (100 pedidos/dia, todas as competições). Não pede cartão.
3. No painel, copia a **API Key**.
4. Guarda-a em `backend/.env` numa linha `API_FOOTBALL_KEY=...` (crio o ficheiro se quiseres) e, quando publicarmos, nas variáveis do Vercel.
5. Avisa-me. Eu verifico logo o que o plano gratuito realmente inclui: os ids das ligas portuguesas, as épocas disponíveis e a cobertura da Liga 3 e do Campeonato de Portugal. Se o histórico for curto demais, digo-te antes de gastarmos tempo.

## 6. Base de dados (15 min) — só depois do deploy
Recomendo **Postgres na Neon** (plano gratuito), ligado ao Vercel:
1. No projeto Vercel → **Storage** (ou Marketplace) → **Neon** → **Create**. Aceita o plano gratuito.
2. O Vercel cria a variável `DATABASE_URL` sozinho.
3. Avisa-me e crio as tabelas do [plano 4](plano-base-de-dados.md).

A alternativa é continuar só com o BigQuery, que dá mais trabalho e custos em Google Cloud.

## 7. Decisões (sem contas)
- **Maquete do novo visual:** abre https://claude.ai/artifact/K1C5CQPMKxTyRo3Koe2dD5 (só tu a vês). Diz-me o que mudar; falta o logótipo.
- **Anúncios:** só donativos por agora (recomendado)? Publicidade de casas de apostas exige parecer jurídico ([plano 5](plano-anuncios-e-apoios.md)).
- **Termos de uso e política de privacidade:** antes de abrir ao público. Escrevo os rascunhos, mas convém que um jurista os reveja.

## Resumo
| # | Ação | Tempo | Custo | Desbloqueia |
|---|---|---|---|---|
| 1 | GitHub | feito | 0 € | tudo o resto |
| 2 | Vercel | 10 min | 0 € | app online |
| 3 | Domínio `.pt` | 15 min | ~12–17 €/ano | endereço próprio |
| 4 | Buy Me a Coffee e PayPal.Me | 20 min | 0 € | donativos |
| 5 | API-Football | 10 min | 0 € | ligas portuguesas |
| 6 | Neon (Postgres) | 15 min | 0 € | acerto das previsões |
| 7 | Decisões | — | — | visual e anúncios |
