# Plano — Guardas de segurança antes do go-live

> ⚠️ **Isto é um plano, não está implementado.** Nenhum destes itens existe hoje no código. Os itens
> marcados **🔴 Bloqueador** não devem ficar por fazer quando o site for publicado a sério (domínio
> próprio, tráfego real) — os **🟡 Recomendado** podem esperar pela fase seguinte sem grande risco.

## Porque isto importa agora
A app vai deixar de correr só em `localhost` e passa a ter: um domínio público, dois serviços pagos por
uso (API-Football, com limite diário; Anthropic, cobrado por pedido) e endpoints de escrita sem
autenticação (`/desdobramento`, `/resumo`, `/feedback`). Sem guardas, qualquer pessoa (ou um bot) pode:
- esgotar as 100 chamadas/dia da API-Football só com pedidos repetidos a `/api/futebol/jogos`;
- gerar uma fatura na Anthropic repetindo `/api/totobola/resumo` com pequenas variações (o cache de
  `resumo_ia.py` só evita repetir um pedido *idêntico*);
- encher o disco (ou o `/tmp` do Vercel) de `sugestoes.jsonl` com spam;
- ver mensagens de erro internas (caminhos de ficheiros, stack traces) devolvidas tal e qual pelo `HTTPException(detail=f"...{e}")` usado em todos os routers hoje.

## 1. Rate limiting — 🔴 Bloqueador

**Onde falta:** não existe nenhum limite de pedidos em nenhum endpoint. `app/main.py` não tem
*middleware* nenhum além do CORS.

**O que fazer:**
- Adicionar [`slowapi`](https://pypi.org/project/slowapi/) (wrapper do `limits` para FastAPI/Starlette) ao `requirements.txt`.
- Limites propostos, por IP:

| Endpoint | Limite sugerido | Porquê |
|---|---|---|
| `POST /api/totobola/resumo` | 5/min, 30/dia | Cada pedido custa dinheiro (Anthropic). |
| `GET /api/futebol/jogos` (com `criterios`) | 20/min | Cada combinação de critérios nova gasta 1 pedido de treino; sem `criterios` já tem cache de CDN. |
| `POST /api/feedback` | 5/min, 20/dia | Anti-spam; não custa dinheiro mas enche o ficheiro. |
| `POST /api/totobola/desdobramento` | 20/min | Não custa dinheiro (modelos já treinados em cache), mas evita abuso de CPU. |
| Todos os outros `GET` | 60/min | Rede de segurança geral. |

- **Limitação séria a documentar:** o Vercel corre cada função *serverless* isolada — um limitador em
  memória (`slowapi` por omissão) **não é partilhado entre instâncias**. Funciona bem localmente e
  reduz abuso básico em produção, mas um atacante distribuído pode contornar isto. Para um limite a
  sério é preciso um armazém partilhado (Redis/Upstash — o Vercel tem integração directa com o Upstash
  Redis, incluído no plano gratuito até um certo volume). **Fase 1 (já ajuda muito): `slowapi` em
  memória. Fase 2 (antes de tráfego a sério): Upstash Redis como backend do limitador.**
- Devolver `429 Too Many Requests` com uma mensagem em português, sem detalhes internos.

## 2. Não expor erros internos ao cliente — 🔴 Bloqueador

**Onde falta:** todos os routers (`totobola.py`, `lotteries.py`, `futebol.py`, `feedback.py`) fazem
`raise HTTPException(status_code=502, detail=f"Failed to fetch X: {e}")`, o que devolve a mensagem de
exceção do Python (pode incluir caminhos de ficheiros, nomes de bibliotecas, às vezes fragmentos de
HTML de terceiros) diretamente ao browser de quem estiver a usar a app.

**O que fazer:**
- Criar um `exception_handler` global em `app/main.py`: regista o erro completo no log do servidor
  (`logging`, que o Vercel já capta) e devolve ao cliente só uma mensagem genérica + um código de
  referência (ex.: `{"detail": "Não foi possível obter os dados agora. (ref: 8f3a2c)"}`), para conseguires
  cruzar com os logs se o utilizador reportar o problema.
- Manter mensagens específicas só para erros de validação do próprio pedido (422 do Pydantic), que já
  não expõem nada interno — esses podem continuar como estão.

## 3. Limites de tamanho do pedido — 🔴 Bloqueador

**Já parcialmente feito:** `MAX_MATCHES=20`, `MAX_APOSTAS=500` (`app/models.py`) e `mensagem` limitada a
2000 caracteres em `SuggestionRequest` — mas isso só é validado **depois** de o corpo do pedido já ter
sido lido e desserializado. Um pedido de várias dezenas de MB ainda consome memória e CPU antes de ser
rejeitado.

**O que fazer:**
- *Middleware* que rejeita, antes de ler o corpo, qualquer pedido com `Content-Length` acima de um
  limite (ex.: 200 KB chega perfeitamente para qualquer uso legítimo desta app).
- O Vercel já limita o tamanho do pedido a nível da plataforma (alguns MB), o que ajuda como rede de
  segurança adicional, mas não deve ser o único limite.

## 4. Cabeçalhos de segurança HTTP — 🟡 Recomendado

**Onde falta:** nenhum cabeçalho de segurança é definido (nem no FastAPI nem no `vercel.json`).

**O que fazer**, em `vercel.json` (aplica-se ao serviço `web`, não precisa de código):
```json
"headers": [
  {
    "source": "/(.*)",
    "headers": [
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "X-Frame-Options", "value": "DENY" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
      { "key": "Permissions-Policy", "value": "geolocation=(), microphone=(), camera=()" }
    ]
  }
]
```
HTTPS e HSTS já são automáticos no Vercel.

## 5. CORS — 🟡 Recomendado (confirmar antes do go-live)
`CORS_ORIGINS` já é configurável (`app/main.py`) e por omissão só aceita `localhost`. **Antes de
publicar:** confirmar que a variável de ambiente no Vercel está definida como o domínio real
(`https://desdobra1x2.pt`, sem `*`) — hoje em desenvolvimento é fácil esquecer isto.

## 6. Anti-spam simples no formulário de sugestões — 🟡 Recomendado
Além do rate limiting (ponto 1), o formulário (`SuggestionForm.tsx`) não tem nenhuma barreira contra
bots simples. Sem orçamento para CAPTCHA:
- **Honeypot:** um campo escondido por CSS (`nome_da_empresa`, por exemplo) que só um bot preenche;
  se vier preenchido, aceitar o pedido silenciosamente (responder 200) mas não guardar nada — não dar
  pistas ao bot de que foi apanhado.
- Rejeitar mensagens que sejam só URLs ou tenham mais de N links.

## 7. Segredos e variáveis de ambiente — 🔴 Bloqueador (checklist antes de publicar)
- [ ] `API_FOOTBALL_KEY`, `ANTHROPIC_API_KEY` (se ativada) e `GCP_PROJECT`/`BQ_DATASET` (se usado) postos
      como variáveis de ambiente do Vercel, nunca no código nem no `vercel.json`.
- [ ] Confirmar que `.env` e `.env.local` continuam fora do Git (já estão, `.gitignore`).
- [ ] Rodar (gerar de novo) qualquer chave que alguma vez tenha aparecido num commit, print de ecrã ou mensagem partilhada.
- [ ] `CORS_ORIGINS` definido para o domínio de produção (ponto 5).

## 8. Dependências desatualizadas / vulneráveis — 🟡 Recomendado
Não há nenhuma verificação automática hoje.
- Backend: `pip install pip-audit && pip-audit -r requirements.txt` antes de cada publicação; considerar
  o Dependabot do GitHub (grátis, só precisa de um ficheiro de configuração) para alertas automáticos.
- Frontend: `npm audit` (já correndo o `npm install`); o Dependabot também cobre `package.json`.

## 9. Limites e custos dos serviços externos — 🟡 Recomendado
- **API-Football:** 100 pedidos/dia no plano gratuito. Sem rate limiting (ponto 1), um pico de tráfego
  esgota a quota e a app fica sem previsões de Futebol até ao dia seguinte — não é um risco de
  segurança, mas é uma falha de disponibilidade fácil de evitar com o mesmo rate limiting.
- **Anthropic (resumo por IA):** cobrado por pedido. Considerar um limite mensal de gasto configurado
  na própria consola da Anthropic (não é código, é uma definição da conta) como rede de segurança
  final, independente do rate limiting da app.

## 10. Scraping do site da Santa Casa e de outros sites — 🟡 Recomendado
Os scrapers (`santacasa_calendar.py`, `santacasa_results.py`) já têm cache (12–24h) que reduz a carga
nesses sites, mas vale a pena:
- Confirmar um `User-Agent` identificável (não fingir ser um browser comum) — boa prática de scraping,
  reduz o risco de bloqueio por deteção de bot.
- Se o site começar a bloquear pedidos do Vercel (já referido no `plano-publicacao-vercel.md`), isso
  é uma falha funcional, não de segurança, mas o rate limiting do ponto 1 ajuda a não acelerar esse
  bloqueio.

## O que NÃO é necessário agora
- **Autenticação de utilizadores:** não há contas nem dados pessoais além do e-mail opcional no
  formulário de sugestões (já é o mínimo). Só passa a ser relevante com o plano de contas pagas
  (`plano-utilizadores-pagamento.md`).
- **WAF dedicado / proteção anti-DDoS avançada:** o Vercel já filtra tráfego malicioso óbvio a nível de
  rede; um WAF configurável (Vercel Firewall com regras) só compensa com tráfego real a justificar.
- **Banner de consentimento de cookies:** só é preciso se/quando houver anúncios ou analytics com
  cookies (ver `plano-anuncios-e-apoios.md`); hoje a app não usa cookies.

## Ordem de implementação sugerida (antes do go-live)
1. **Erros sem detalhe interno** (ponto 2) — mudança pequena e localizada, sem dependências novas.
2. **Rate limiting em memória** (ponto 1, fase 1) — `slowapi`, cobre os endpoints da tabela.
3. **Limite de tamanho do pedido** (ponto 3).
4. **Checklist de segredos** (ponto 7) — antes do primeiro deploy real, não é código.
5. **Cabeçalhos de segurança + CORS de produção** (pontos 4 e 5) — no `vercel.json`, sem código Python.
6. Depois do go-live, com tráfego a sério: Upstash Redis (ponto 1, fase 2), honeypot no formulário (ponto 6), Dependabot (ponto 8).

## Verificação
- Pedir 10 pedidos seguidos a `/api/totobola/resumo` num segundo: a partir do 6.º, resposta `429`.
- Forçar um erro (ex.: desligar a rede) e confirmar que a resposta ao cliente não contém nenhum caminho de ficheiro nem nome de módulo Python.
- Enviar um pedido de 5 MB a `/api/feedback`: rejeitado antes de processar o corpo.
- `pip-audit` e `npm audit` sem vulnerabilidades críticas por resolver.
