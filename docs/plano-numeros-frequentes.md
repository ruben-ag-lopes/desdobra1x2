# Plano — Último sorteio, tabela de prémios e números mais frequentes

> **Feito (27/09/2026):** último sorteio (chave + tabela de prémios) e frequência de números para Totoloto,
> Euromilhões e EuroDreams — `app/scrapers/santacasa_results.py`, `GET /api/lotteries/{game}/ultimo-sorteio` e
> `/frequencia`, cartões no `LotteryTab.tsx`. Testado com dados reais do site.
>
> **Frequência: calculada por nós, sobre os sorteios recentes que o site lista** (a dropdown "Consultar
> Sorteios" da própria página, ~30 sorteios: uns 7 meses para Euromilhões/EuroDreams, ~3,5 meses para o Totoloto,
> que sorteia 2x por semana). Tentámos recuar mais (ids de concurso mais antigos, fora da dropdown) mas os ids
> são partilhados por todos os jogos da Santa Casa e não avançam de forma constante por jogo — saltar para trás
> além da dropdown dá resultados que já não pertencem a este jogo, silenciosamente errados. Ficou por isso pela
> janela que o site garante ser fiável, em vez de "desde sempre" (2011/2004/2023) ou de "últimos 365 dias"
> exatos. Só se aplica às lotarias (Totoloto, Euromilhões, EuroDreams); Totobola/Totobola Extra e os outros
> desportos não têm esta funcionalidade, por indicação do utilizador.

## Aviso a manter sempre visível
Mostrar a frequência de números **não aumenta a probabilidade de ganhar**: cada sorteio é independente dos
anteriores. É informação de curiosidade, não uma sugestão de jogo — o aviso já existente na app deve dizê-lo
explicitamente também nesta secção.

## Onde estão os dados (confirmado por scraping de teste, 27/09/2026)

O site da Santa Casa tem duas famílias de páginas: um sistema mais recente para o EuroDreams e um mais antigo
(`SCCartazResult`/`SCEstatisticas`) para os outros jogos. As páginas são **servidas já com os dados no HTML**
(não são só JavaScript/API), por isso dá para usar o mesmo método dos scrapers atuais (`httpx` + BeautifulSoup),
sem precisar de Playwright em produção.

| Jogo | Último sorteio (chave + prémios) | Estatísticas por número |
|---|---|---|
| Totoloto | `/web/SCCartazResult/totolotoNew` | `/web/SCEstatisticas/totolotoN` |
| Euromilhões | `/web/SCCartazResult/` | `/web/SCEstatisticas/` |
| EuroDreams | `/web/ResultsBoard/EuroDreams` | `/web/Statistics/EuroDreams` |
| Totobola | `/web/SCCartazResult/bolaNormal` | — (não é jogo de números) |
| Totobola Extra | `/web/SCCartazResult/bolaExtra1` | — |
| Lotaria Clássica | `/web/SCCartazResult/lotClass` | — |
| Lotaria Popular | `/web/SCCartazResult/lotPop` | — |
| M1lhão | `/web/SCCartazResult/m1lhao` | — |
| Euromilhões — Chuva de Milionários | `/web/SCCartazResult/cmil` | — |

### Última chave vencedora + tabela de prémios (exemplo real, Euromilhões 077/2026)
A página tem, em texto simples:
```
SORTEIO: 077/2026 - SEXTA-FEIRA
DATA DO SORTEIO - 25/09/2026
CHAVE          11 12 15 38 49 + 10 12
ORDEM DE SAÍDA 12 11 38 15 49 + 10 12
1.º Prémio 5 Números + 2 Estrelas   0 vencedores PT   1 total   € 130.000.000,00
2.º Prémio 5 Números + 1 Estrela    0 vencedores PT   3 total   € 361.615,47
... (13 escalões no Euromilhões, 6 no EuroDreams, 5 + nº da sorte no Totoloto)
Receita ilíquida apostas, Montante para prémios, Nº de registos/apostas
```
Cada jogo tem um número de escalões de prémio diferente — o modelo de dados tem de ser uma lista, não campos fixos.

### Números mais frequentes
A página de Estatísticas do site (`SCEstatisticas`/`Statistics`) mostra a frequência **desde sempre** (2011 no
Totoloto, 2023 no EuroDreams) e só filtra por número individual, não por período — por isso não a usamos.
Implementámos antes o cálculo nós próprios, a partir dos ~30 sorteios recentes que a própria página de
resultados lista em "Consultar Sorteios" (ver a nota no topo do documento).

## Modelo de dados (proposta)
```python
class PrizeTier(BaseModel):
    nome: str  # "1.º Prémio 5 Números + 2 Estrelas"
    vencedores_portugal: int | None  # None quando o jogo não distingue (ex.: Totoloto)
    vencedores_total: int
    valor: str  # texto livre: "€ 130.000.000,00" ou "20.000/mês x 30 anos" (jackpots com renda)

class UltimoSorteio(BaseModel):
    game: str
    concurso: str
    data_sorteio: date
    chave: list[int]
    chave_extra: list[int] = []  # estrelas, nº de sonho, nº da sorte...
    ordem_saida: list[int]
    premios: list[PrizeTier]

class NumberFrequency(BaseModel):
    numero: int
    saidas: int
    percentagem: float
    ultimo_sorteio: str | None  # None se não saiu na janela contada
    data_ultimo_sorteio: date | None
    ausencias: int  # sorteios, dentro da janela contada, desde a última vez que saiu

class FrequenciaResponse(BaseModel):
    game: str
    desde: date  # data do sorteio mais antigo contado
    n_sorteios: int
    numeros: list[NumberFrequency]
```

## API (implementado)
| Endpoint | Descrição |
|---|---|
| `GET /api/lotteries/{game}/ultimo-sorteio` | Chave vencedora + tabela de prémios do último sorteio. |
| `GET /api/lotteries/{game}/frequencia` | Frequência por número, sobre os ~30 sorteios recentes listados pelo site (`desde`/`n_sorteios` na resposta dizem qual é a janela real). |

Cache: os dados só mudam depois de cada sorteio (uma ou duas vezes por semana, conforme o jogo) — TTL de 12h chega, igual aos scrapers atuais (`app/cache.py`, `TTLCache`).

## Scraper (novo módulo `app/scrapers/santacasa_results.py`)
1. `_fetch_ultimo_sorteio(game)`: GET à página de resultados, parse com BeautifulSoup (`SORTEIO:`, `CHAVE`, `ORDEM DE SAÍDA`, tabela de prémios — cada jogo tem o próprio número de colunas, ver exemplos acima).
2. `_fetch_frequencia(game)`: GET à página de estatísticas, parse da tabela `NÚMERO | Nº SAÍDAS | % | ÚLTIMO SORTEIO | DATA | AUSÊNCIAS`.
3. Testar se existe filtro de datas na página de estatísticas (inspecionar o HTML do formulário "Consultar Números", não só o texto renderizado).
4. Reutilizar `_cache` e o padrão `_decode`/`httpx` já usados em `santacasa_calendar.py`.

## Frontend (`LotteryTab.tsx`)
- Cartão "Último sorteio": chave vencedora + tabela de prémios (reaproveitar o estilo de `.draw-info`).
- Secção "Números mais frequentes": lista ou gráfico de barras simples com os números mais e menos saídos, e a nota "não aumenta a probabilidade de ganhar" bem visível ao lado.
- Mostrar a data "dados desde XX/XX/XXXX" tal como o site.

## Fases
1. Confirmar o filtro de datas nas Estatísticas (ou decidir calcular localmente) — passo de investigação, ~1h.
2. Scraper do último sorteio (chave + prémios), os 3 jogos de números primeiro (Totoloto, Euromilhões, EuroDreams).
3. Scraper da frequência de números.
4. Endpoints + frontend.
5. Totobola/Totobola Extra: só "último sorteio" faz sentido (não têm números de frequência).

## Verificação
- A chave e os prémios mostrados batem com o que aparece no site em `Últimos Resultados`.
- A frequência soma corretamente (percentagens somam ~100% entre os números possíveis do jogo).
- Falha do scraper (site em baixo ou HTML mudou) não impede o resto da app de funcionar — mesmo padrão dos outros scrapers (falha silenciosa, mensagem "não disponível").
