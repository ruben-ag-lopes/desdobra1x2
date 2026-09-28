# Plano — Domínio desdobra1X2.pt (o mais barato possível)

> Só plano: nada foi comprado nem configurado.

## Conclusões da pesquisa (25/09/2026)
- **O Vercel não vende `.pt`** (não está na lista de domínios suportados) e **o Cloudflare Registrar também não** (não suporta `.pt`). O registo tem de ser feito num **registador acreditado pelo .PT** e depois ligado ao Vercel. Isso é gratuito.
- **Os domínios não distinguem maiúsculas:** o endereço será `desdobra1x2.pt`, e a marca pode continuar a escrever-se "desdobra1X2".
- **Qualquer pessoa pode registar `.pt`:** particular ou empresa, com ou sem morada em Portugal. Desde 1 de julho de 2026 os dados do titular são validados antes de o registo ficar concluído. Pede-se nº de identificação: CC ou passaporte, ou NIPC.
- **Disponibilidade:** hoje o nome não existe no DNS, bom sinal mas não prova. Confirmar no WHOIS oficial (pt.pt → Ferramentas → WHOIS) no momento da compra.
- **Regras de nome:** o .PT recusa nomes confundíveis com marcas notórias de terceiros. "desdobra1x2" não usa "Santa Casa" nem "Totobola", o que ajuda.

## Preços encontrados (confirmar no momento da compra; o IVA pode acrescer)
| Registador | 1.º ano | Renovação/ano | Nota |
|---|---|---|---|
| Site.pt | 11,95 € (promoção) | 14,95 € | Renovação "ao preço de tabela" |
| PTISP | 16,50 € | 16,50 € | Preço estável |
| OVHcloud | ~19,40 US$ | ~14,59 US$ | Preços em dólares no site internacional |
| Amen.pt | grátis (promoção) | preço de tabela | A promoção não inclui renovações |
| Dominios.pt | 1 € (promoção) | 32,90 € + IVA | Barato no 1.º ano, caro depois |

**O que conta é o custo em 3 anos**, porque as promoções só valem no 1.º ano:
- Site.pt: ≈ 41,85 € (11,95 + 2 × 14,95);
- OVH: ≈ 48,60 US$;
- PTISP: ≈ 49,50 €;
- Dominios.pt: ≈ 66,80 € + IVA.

**Recomendação (custo total mais baixo em 3 anos):** Site.pt.

**Recomendação (mais barato só no 1.º ano — decisão de 29/09/2026):** confirmado de novo hoje, a Dominios.pt continua a anunciar **1 € + IVA no 1.º ano** (≈ 1,23 € com IVA a 23%), com renovação de **32 € + IVA/ano** (≈ 39,36 €) a partir do 2.º ano. Como preferes o mais barato já e aceitas pagar mais depois, é esta a opção. Página de registo: dominios.pt/registar/dominios-pt/. O 1.º ano inclui 1 GB de alojamento, um site de uma página e 1 conta de e-mail — não precisas de usar isso, o site vai continuar no Vercel.

## Custos totais do 1.º ano
| Item | Custo |
|---|---|
| Domínio `.pt` | ~12–20 € |
| Alojamento Vercel (Hobby, só donativos) | 0 € |
| Certificado HTTPS (automático no Vercel) | 0 € |
| DNS (no registador, no Vercel ou no Cloudflare) | 0 € |
| E-mail de reencaminhamento `contacto@desdobra1x2.pt` (opcional) | 0 € (Cloudflare Email Routing) |
| **Total** | **~12–20 €** |

Com anúncios, o Vercel passa a exigir o plano Pro, que é pago (ver `plano-anuncios-e-apoios.md`).

## Onde fica o DNS
| Opção | Como | Prós | Contras |
|---|---|---|---|
| **A. DNS do registador** (mais simples) | No painel do registador: registo `A` do domínio raiz e `CNAME` do `www` com os valores que o Vercel mostrar | Nada a mudar de sítio | Depende da qualidade do painel do registador |
| **B. DNS no Cloudflare** (recomendado se quiseres e-mail) | Criar conta gratuita no Cloudflare, adicionar o domínio e mudar os *nameservers* no registador para os do Cloudflare. Depois criar os registos do Vercel com o proxy **desligado** (nuvem cinzenta) | E-mail de reencaminhamento grátis, DNS rápido, proteção básica | Mais um serviço. O proxy laranja pode entrar em conflito com o Vercel, por isso deixá-lo desligado |
| C. DNS no Vercel | Mudar os *nameservers* para os do Vercel | Tudo num sítio | Sem e-mail grátis integrado |

O Cloudflare não regista `.pt`, mas pode gerir o DNS de um `.pt` registado noutro sítio.

## Passos (quando decidires avançar)
1. Confirmar a disponibilidade de `desdobra1x2.pt` no WHOIS do .PT.
2. Registar no registador escolhido (1 ano) com os teus dados (serão validados).
3. Publicar a app no Vercel (`plano-publicacao-vercel.md`) e, no projeto, **Settings → Domains → Add** `desdobra1x2.pt` e `www.desdobra1x2.pt`, com o `www` a redirecionar para o domínio raiz.
4. Criar os registos DNS indicados pelo Vercel (opção A) ou mudar os *nameservers* (opção B/C).
5. Esperar a propagação (minutos a algumas horas). O Vercel emite o certificado HTTPS sozinho.
6. Opcional (opção B): Cloudflare Email Routing `contacto@desdobra1x2.pt` para o teu e-mail pessoal, para usar nas páginas legais e no Buy Me a Coffee.
7. Ativar a renovação automática, ou pôr um lembrete um mês antes do fim do prazo.

## Alternativa: `desdobra1x2.com` (pesquisa de 29/09/2026)

Se preferires um `.com` em vez do (ou a par do) `.pt`, aqui estão todas as opções verificadas, incluindo o Vercel e o Netlify — nenhum dos dois vende domínios por preços fixos publicados, o preço só aparece no motor de pesquisa/checkout de cada um.

| Opção | 1.º ano | Renovação | Notas |
|---|---|---|---|
| **Vercel Domains** (vercel.com/domains) | preço de mercado, sem valor fixo publicado (só via `vercel domains search` ou o site) | igual | Sem promoção de arranque. Vantagem: fica tudo integrado, sem configurar DNS. **O domínio grátis do plano Pro não inclui `.com`** (só `.app`, `.dev`, `.online`, `.site`, `.space`, `.store`, `.tech`, `.website`). |
| **Netlify** (regista domínios diretamente, não é só DNS) | preço de mercado, sem valor fixo publicado | igual | Mesma lógica do Vercel: conveniência, não é o mais barato. |
| **Cloudflare Registrar** | **~9–10 US$** (preço de custo, sem margem — a própria Cloudflare garante não cobrar acima do que a registry e a ICANN cobram) | igual ao 1.º ano | O mais previsível a longo prazo: nunca sobe. Sem promoção de arranque. |
| **Porkbun** | **~11,08 US$** (preço fixo, "everyday low price") | igual | Sem truques, mas sem promoção agressiva. |
| **Namecheap / GoDaddy** | costumam ter promoções agressivas de registo novo no 1.º ano (por vezes abaixo de 2 US$, ocasionalmente perto de 0) | tipicamente 15–20 US$/ano | Valor exato não confirmado (muda com frequência e com códigos promocionais); é normalmente onde aparece o preço mais baixo do 1.º ano, ao estilo da Dominios.pt para o `.pt`. Verificar no checkout se há extras obrigatórios (privacidade WHOIS, etc.) que sobem o total. |

**Se o critério for só "mais barato no 1.º ano"** (o mesmo que escolheste para o `.pt`): confirmar agora o preço de registo novo na Namecheap ou GoDaddy para `desdobra1x2.com` — é onde costuma estar o valor mais baixo, mas precisa de confirmação no checkout no momento da compra.

**Se preferires previsibilidade** (mesmo preço todos os anos, sem promoções que depois disparam): Cloudflare Registrar, ~10 US$/ano.

**Disponibilidade:** ainda não confirmada — verificar no motor de pesquisa de qualquer um destes sites.

**Uso sugerido, mesmo escolhendo o `.pt` como principal:** registar o `.com` (no Cloudflare Registrar, mais barato a manter) só para proteger o nome e redirecionar para o `.pt`. Não é necessário no início.

## Até haver domínio
O endereço gratuito `desdobra1x2.vercel.app` serve para testes com amigos.

## Verificação
- `https://desdobra1x2.pt` abre a app com cadeado válido, e `http://` e `www` redirecionam para `https://desdobra1x2.pt`.
- `https://desdobra1x2.pt/api/health` devolve `{"status":"ok"}`.
- WHOIS mostra o titular correto e a data de expiração.

Fontes: Vercel, lista de domínios suportados (vercel.com/docs/domains/supported-domains); comunidade Cloudflare sobre `.pt`; preços nos sites da Site.pt, PTISP, OVHcloud, Amen e Dominios.pt (consultados a 25/09/2026 e a 29/09/2026). Opções `.com`: vercel.com/docs/domains/working-with-domains, docs.netlify.com (registo e compra de domínio), cloudflare.com/products/registrar, porkbun.com/tld/com (consultados a 29/09/2026).
