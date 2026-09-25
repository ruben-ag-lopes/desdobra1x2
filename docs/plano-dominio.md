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

**Recomendação:** Site.pt (ou quem tiver a renovação mais barata na altura), registado **por 1 ano** para não ficar preso. Antes de pagar, confirma o preço de renovação e se o valor inclui IVA.

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
6. Opcional (opção B): Cloudflare Email Routing `contacto@desdobra1x2.pt` para o teu e-mail pessoal, para usar nas páginas legais, no Buy Me a Coffee e no PayPal.
7. Ativar a renovação automática, ou pôr um lembrete um mês antes do fim do prazo.

## Opcional
- **`desdobra1x2.com`** no Cloudflare Registrar (preço de custo, cerca de 10 US$/ano), só para proteger o nome e redirecionar para o `.pt`. Não é necessário no início.
- Até haver domínio, o endereço gratuito `desdobra1x2.vercel.app` serve para testes com amigos.

## Verificação
- `https://desdobra1x2.pt` abre a app com cadeado válido, e `http://` e `www` redirecionam para `https://desdobra1x2.pt`.
- `https://desdobra1x2.pt/api/health` devolve `{"status":"ok"}`.
- WHOIS mostra o titular correto e a data de expiração.

Fontes: Vercel, lista de domínios suportados (vercel.com/docs/domains/supported-domains); comunidade Cloudflare sobre `.pt`; preços nos sites da Site.pt, PTISP, OVHcloud, Amen e Dominios.pt (consultados a 25/09/2026).
