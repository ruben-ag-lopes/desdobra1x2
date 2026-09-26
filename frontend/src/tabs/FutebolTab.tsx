import { useEffect, useRef, useState } from "react";
import { getCompeticoes, getJogos } from "../api/client";
import type { Competition, FootballGame, GoalMarket, Outcome } from "../api/types";
import { CopyButton } from "../components/CopyButton";
import { CriteriaDialog } from "../components/CriteriaDialog";
import { confidence, OUTCOMES, pickLabel, pickProbability, togglePick } from "../picks";

const PERIODS = [
  { dias: 0, label: "Todos" },
  { dias: 3, label: "3 dias" },
  { dias: 7, label: "7 dias" },
];

function pct(p: number): string {
  return `${Math.round(p * 100)}%`;
}

function dayLabel(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-PT", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
  });
}

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleTimeString("pt-PT", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function groupByDay(games: FootballGame[]): [string, FootballGame[]][] {
  const groups = new Map<string, FootballGame[]>();
  for (const g of games) groups.set(dayLabel(g.data), [...(groups.get(dayLabel(g.data)) ?? []), g]);
  return [...groups.entries()];
}

function GoalLine({ label, market, bookmakers }: { label: string; market: GoalMarket; bookmakers?: number | null }) {
  return (
    <li>
      {label}: <strong>{pct(market.probabilidade)}</strong>
      {market.fonte === "media_liga" && <span className="hint"> (média da liga)</span>}
      {bookmakers != null && <span className="hint"> · casas {pct(bookmakers)}</span>}
    </li>
  );
}

function GameCard({
  game,
  picks,
  onPick,
}: {
  game: FootballGame;
  picks: Outcome[];
  onPick: (outcome: Outcome) => void;
}) {
  const conf = game.prob ? confidence(game.prob) : null;
  return (
    <article className={`game-card ${picks.length ? "picked" : ""}`}>
      <div className="game-meta">
        <span>{timeLabel(game.data)}</span>
        <span>{game.competicao_nome}</span>
      </div>
      <h4>
        {game.casa} <span className="hint">vs</span> {game.fora}
      </h4>

      {game.prob ? (
        <>
          <div
            className="outcome-buttons"
            role="group"
            aria-label={`Escolher resultado de ${game.casa} vs ${game.fora}`}
          >
            {OUTCOMES.map((o, k) => (
              <button
                key={o}
                className={picks.includes(o) ? "active" : ""}
                aria-pressed={picks.includes(o)}
                onClick={() => onPick(o)}
              >
                <span className="outcome">{o}</span>
                <span className="outcome-prob">{pct(game.prob![k])}</span>
                {game.casas_de_apostas && <span className="outcome-book">casas {pct(game.casas_de_apostas[k])}</span>}
              </button>
            ))}
          </div>
          {conf && (
            <p className="hint">
              Palpite {conf.suggestion.length === 2 && "dupla "}
              <strong>{pickLabel(conf.suggestion)}</strong> · confiança {conf.level}
              {conf.suggestion.length === 2 && " (jogo equilibrado)"}
            </p>
          )}
          <details>
            <summary>Golos</summary>
            <ul className="goal-list">
              {game.golos_esperados && (
                <li>
                  Golos esperados: <strong>{game.golos_esperados[0].toFixed(1)}</strong> –{" "}
                  <strong>{game.golos_esperados[1].toFixed(1)}</strong>
                </li>
              )}
              {game.mais_2_5 && (
                <GoalLine label="Mais de 2,5 golos" market={game.mais_2_5} bookmakers={game.casas_mais_2_5} />
              )}
              {game.ambas_marcam && <GoalLine label="Ambas marcam" market={game.ambas_marcam} />}
              {game.resultados_provaveis.length > 0 && (
                <li>
                  Resultados mais prováveis:{" "}
                  {game.resultados_provaveis.map((r) => `${r.casa}-${r.fora} (${pct(r.probabilidade)})`).join(" · ")}
                </li>
              )}
            </ul>
          </details>
        </>
      ) : (
        <p className="hint">Sem histórico suficiente destas equipas nesta liga para prever.</p>
      )}
    </article>
  );
}

export function FutebolTab() {
  const [competitions, setCompetitions] = useState<Competition[] | null>(null);
  const [competicao, setCompeticao] = useState("");
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [dias, setDias] = useState(0);
  const [games, setGames] = useState<FootballGame[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [picks, setPicks] = useState<Map<string, { game: FootballGame; outcomes: Outcome[] }>>(new Map());
  const requestId = useRef(0);

  useEffect(() => {
    getCompeticoes()
      .then((list) => {
        setCompetitions(list);
        setCompeticao((list.find((c) => c.jogos > 0) ?? list[0])?.codigo ?? "");
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query.trim()), 300);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    if (!competicao && !debouncedQuery) return;
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    getJogos({
      competicao: competicao || undefined,
      q: debouncedQuery || undefined,
      dias: dias || undefined,
    })
      .then((list) => id === requestId.current && setGames(list))
      .catch((e) => id === requestId.current && setError(String(e)))
      .finally(() => id === requestId.current && setLoading(false));
  }, [competicao, debouncedQuery, dias]);

  function pick(game: FootballGame, outcome: Outcome) {
    setPicks((prev) => {
      const next = new Map(prev);
      const outcomes = togglePick(prev.get(game.id)?.outcomes ?? [], outcome);
      if (outcomes.length) next.set(game.id, { game, outcomes });
      else next.delete(game.id);
      return next;
    });
  }

  const chosen = [...picks.values()];
  const joint = chosen.reduce((p, c) => p * pickProbability(c.game.prob!, c.outcomes), 1);
  const usage = new Map<string, number[]>();
  games?.forEach((g, i) => g.modelo && usage.set(g.modelo, [...(usage.get(g.modelo) ?? []), i + 1]));

  return (
    <div className="tab-content">
      <h2>Futebol</h2>
      <p className="hint">
        Próximos jogos das ligas cobertas, com as nossas probabilidades e as das casas de apostas como referência. As
        casas de apostas acertam mais do que o nosso modelo nos testes: usa-as para comparar, não como garantia.
      </p>

      <div className="controls futebol-filters">
        <label>
          Competição
          <select value={competicao} onChange={(e) => setCompeticao(e.target.value)}>
            <option value="">Todas (pesquisa)</option>
            {competitions?.map((c) => (
              <option key={c.codigo} value={c.codigo}>
                {c.nome} ({c.jogos})
              </option>
            ))}
          </select>
        </label>
        <label>
          Equipa
          <input type="search" placeholder="ex.: Benfica" value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
        <div className="period-toggle" role="group" aria-label="Período">
          {PERIODS.map((p) => (
            <button
              key={p.dias}
              className={dias === p.dias ? "active" : ""}
              aria-pressed={dias === p.dias}
              onClick={() => setDias(p.dias)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {!competicao && !debouncedQuery && <p className="hint">Escolhe uma competição ou pesquisa uma equipa.</p>}
      {error && <p className="error">{error}</p>}
      {loading && <p className="hint">A carregar jogos e previsões...</p>}
      {games && !loading && games.length === 0 && (competicao || debouncedQuery) && (
        <p className="hint">Sem jogos publicados para estes filtros nos próximos dias.</p>
      )}

      {games && games.length > 0 && (
        <div className="result-heading">
          <span className="hint">{games.length} jogo(s)</span>
          {usage.size > 0 && <CriteriaDialog usage={usage} hasDouble={false} />}
        </div>
      )}

      {games &&
        groupByDay(games).map(([day, dayGames]) => (
          <section key={day} className="game-day">
            <h3>{day}</h3>
            <div className="game-list">
              {dayGames.map((g) => (
                <GameCard key={g.id} game={g} picks={picks.get(g.id)?.outcomes ?? []} onPick={(o) => pick(g, o)} />
              ))}
            </div>
          </section>
        ))}

      {chosen.length > 0 && (
        <aside className="boletim" aria-label="Boletim">
          <div className="boletim-head">
            <strong>Boletim · {chosen.length} jogo(s)</strong>
            <span>
              Probabilidade de acertar tudo: <strong>{(joint * 100).toFixed(joint < 0.01 ? 2 : 1)}%</strong>
            </span>
          </div>
          <ul>
            {chosen.map((c) => (
              <li key={c.game.id}>
                {c.game.casa} vs {c.game.fora}: <strong>{pickLabel(c.outcomes)}</strong>{" "}
                <span className="hint">({pct(pickProbability(c.game.prob!, c.outcomes))})</span>
              </li>
            ))}
          </ul>
          <div className="controls">
            <CopyButton
              label="Copiar boletim"
              text={chosen.map((c) => `${c.game.casa} - ${c.game.fora}: ${pickLabel(c.outcomes)}`).join("\n")}
            />
            <button onClick={() => setPicks(new Map())}>Limpar</button>
          </div>
        </aside>
      )}
    </div>
  );
}
