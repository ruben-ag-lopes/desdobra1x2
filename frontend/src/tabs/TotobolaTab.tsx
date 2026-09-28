import { useEffect, useState } from "react";
import { getContestMatches, getResumoDisponivel, getTotobolaDraws, postDesdobramento, postResumo } from "../api/client";
import { CopyButton } from "../components/CopyButton";
import { CriteriaDialog } from "../components/CriteriaDialog";
import { DrawInfo } from "../components/DrawInfo";
import type { Criteria, DesdobramentoResponse, Draw, MatchInput, Outcome, ResultProbabilities } from "../api/types";
import { isCriteriaCustom, loadCriteria, saveCriteria } from "../criteriaProfile";
import { OUTCOMES, pickLabel, togglePick } from "../picks";

interface Props {
  game: "totobola" | "totobola_extra";
  title: string;
}

function newMatch(home = "", away = "", competition = ""): MatchInput {
  return {
    id: crypto.randomUUID(),
    home_team: home,
    away_team: away,
    home_country: "Portugal",
    away_country: "Portugal",
    competition_code: null,
    competition,
    home_is_loaned_venue: null,
    manual_home_stats: null,
    manual_away_stats: null,
    manual_h2h: [],
    fixed_results: [],
  };
}

const MAX_APOSTAS = 500; // same limit as the backend (app/models.py)

function pickClass(picks: Outcome[]): string {
  return picks.length === 1 ? "fixed" : picks.length === 2 ? "double" : "";
}

function bestPick(p: ResultProbabilities): string {
  if (p.fixed_results.length) return pickLabel(p.fixed_results);
  const top = Math.max(p.prob_home, p.prob_draw, p.prob_away);
  return top === p.prob_home ? "1" : top === p.prob_away ? "2" : "X";
}

function formatProb(p: ResultProbabilities, outcome: Outcome, value: number): string {
  if (p.fixed_results.length === 2 && !p.fixed_results.includes(outcome)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

/** Model id -> numbers (1-based) of the games it predicted; fixed games are left out. */
function modelUsage(probabilities: ResultProbabilities[]): Map<string, number[]> {
  const usage = new Map<string, number[]>();
  probabilities.forEach((p, i) => {
    if (p.fixed_results.length === 1) return;
    usage.set(p.modelo, [...(usage.get(p.modelo) ?? []), i + 1]);
  });
  return usage;
}

export function TotobolaTab({ game, title }: Props) {
  const [draws, setDraws] = useState<Draw[] | null>(null);
  const [drawsError, setDrawsError] = useState<string | null>(null);
  const [matches, setMatches] = useState<MatchInput[]>([]);
  const [matchesStatus, setMatchesStatus] = useState<string | null>(null);
  const [nApostas, setNApostas] = useState(4);
  const [result, setResult] = useState<DesdobramentoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [criteria, setCriteria] = useState<Criteria>(loadCriteria);
  const [resumoDisponivel, setResumoDisponivel] = useState(false);
  const [resumo, setResumo] = useState<string | null>(null);
  const [resumoLoading, setResumoLoading] = useState(false);
  const [resumoError, setResumoError] = useState<string | null>(null);

  useEffect(() => {
    getTotobolaDraws()
      .then(setDraws)
      .catch((e) => setDrawsError(String(e)));
    getResumoDisponivel()
      .then((r) => setResumoDisponivel(r.disponivel))
      .catch(() => setResumoDisponivel(false));
  }, []);

  const activeDraw = draws?.find((d) => d.game === game);
  const contestId = activeDraw?.contest_id ?? null;

  function loadOfficialMatches() {
    if (!contestId) return;
    setMatchesStatus("A obter jogos do concurso...");
    getContestMatches(contestId)
      .then((fixtures) => {
        setMatches(fixtures.map((f) => newMatch(f.home_team, f.away_team, f.competition)));
        setResult(null);
        setMatchesStatus(fixtures.length ? null : "O concurso ainda não tem jogos publicados.");
      })
      .catch((e) => setMatchesStatus(`Não foi possível obter os jogos automaticamente (${e}). Adiciona-os com "+ Adicionar jogo".`));
  }

  // Fetch the official fixtures whenever the active contest changes (i.e. on app load/refresh).
  useEffect(loadOfficialMatches, [contestId]); // eslint-disable-line react-hooks/exhaustive-deps

  function updateMatch(id: string, patch: Partial<MatchInput>) {
    setMatches((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)));
  }

  function addMatch() {
    setMatches((prev) => [...prev, newMatch()]);
  }

  function removeMatch(id: string) {
    setMatches((prev) => prev.filter((m) => m.id !== id));
  }

  function toggleFixed(id: string, outcome: Outcome) {
    setMatches((prev) =>
      prev.map((m) => (m.id === id ? { ...m, fixed_results: togglePick(m.fixed_results, outcome) } : m)),
    );
  }

  function applyCriteria(next: Criteria) {
    setCriteria(next);
    saveCriteria(next);
    handleCalcular(next);
  }

  const nFixed = matches.filter((m) => m.fixed_results.length === 1).length;
  const nDouble = matches.filter((m) => m.fixed_results.length === 2).length;
  const nFree = matches.length - nFixed - nDouble;

  async function handleCalcular(criteriaOverride: Criteria = criteria) {
    setLoading(true);
    setError(null);
    setResumo(null);
    setResumoError(null);
    try {
      const res = await postDesdobramento(matches, nApostas, activeDraw, criteriaOverride);
      setResult(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleExplicar() {
    if (!result) return;
    setResumoLoading(true);
    setResumoError(null);
    try {
      const res = await postResumo(result.probabilities, nApostas);
      setResumo(res.resumo);
    } catch (e) {
      setResumoError(String(e));
    } finally {
      setResumoLoading(false);
    }
  }

  return (
    <div className="tab-content">
      <h2>{title}</h2>

      <DrawInfo draw={draws ? (activeDraw ?? null) : undefined} error={drawsError} />

      {matchesStatus && <p className="hint">{matchesStatus}</p>}
      <div className="controls">
        <button onClick={loadOfficialMatches} disabled={!contestId}>
          Recarregar jogos do concurso
        </button>
      </div>
      {matches.length > 0 && (
        <p className="hint">
          Um resultado escolhido fica fixo em todas as apostas. Dois resultados formam uma dupla: as apostas só usam
          esses dois. Clica outra vez para desfazer.{" "}
          {nFixed + nDouble > 0 && `${nFixed} fixo(s) · ${nDouble} dupla(s) · ${nFree} livre(s).`}
        </p>
      )}

      {matches.map((m, i) => (
        <div key={m.id} className={`match-row ${pickClass(m.fixed_results)}`}>
          <span className="match-number">{i + 1}</span>
          <input
            placeholder="Equipa da casa"
            value={m.home_team}
            onChange={(e) => updateMatch(m.id, { home_team: e.target.value })}
          />
          <span>vs</span>
          <input
            placeholder="Equipa visitante"
            value={m.away_team}
            onChange={(e) => updateMatch(m.id, { away_team: e.target.value })}
          />
          <div className="fix-toggle" role="group" aria-label="Escolher resultado (fixo ou dupla)">
            {OUTCOMES.map((o) => (
              <button
                key={o}
                className={m.fixed_results.includes(o) ? "active" : ""}
                aria-pressed={m.fixed_results.includes(o)}
                onClick={() => toggleFixed(m.id, o)}
              >
                {o}
              </button>
            ))}
          </div>
          <button onClick={() => removeMatch(m.id)}>Remover</button>
        </div>
      ))}

      <div className="controls">
        <button onClick={addMatch}>+ Adicionar jogo</button>
        <label>
          Nº de apostas no desdobramento:
          <input
            type="number"
            min={1}
            max={MAX_APOSTAS}
            value={nApostas}
            onChange={(e) => setNApostas(Math.min(MAX_APOSTAS, Math.max(1, Number(e.target.value) || 1)))}
          />
        </label>
        <button onClick={() => handleCalcular()} disabled={loading || matches.length === 0}>
          {loading ? "A calcular..." : "Calcular"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result">
          <div className="result-heading">
            <h3>
              Probabilidades calculadas
              {isCriteriaCustom(criteria) && <span className="custom-tag">critérios personalizados</span>}
            </h3>
            <CriteriaDialog
              usage={modelUsage(result.probabilities)}
              hasDouble={result.probabilities.some((p) => p.fixed_results.length === 2)}
              criteria={criteria}
              onApply={applyCriteria}
            />
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Jogo</th>
                  <th>1</th>
                  <th>X</th>
                  <th>2</th>
                  <th>Palpite</th>
                </tr>
              </thead>
              <tbody>
                {result.probabilities.map((p, i) =>
                  p.fixed_results.length === 1 ? (
                    <tr key={p.match_id} className="fixed">
                      <td>
                        {i + 1}. {p.home_team} vs {p.away_team}
                      </td>
                      <td colSpan={3}>fixo pelo utilizador</td>
                      <td>
                        <strong>{bestPick(p)}</strong>
                      </td>
                    </tr>
                  ) : (
                    <tr
                      key={p.match_id}
                      className={pickClass(p.fixed_results)}
                      title={
                        p.probs_modelo
                          ? `Modelo antes da dupla: 1 ${(p.probs_modelo[0] * 100).toFixed(0)}% · X ${(p.probs_modelo[1] * 100).toFixed(0)}% · 2 ${(p.probs_modelo[2] * 100).toFixed(0)}%`
                          : undefined
                      }
                    >
                      <td>
                        {i + 1}. {p.home_team} vs {p.away_team}
                        {p.low_confidence && <span className="low-confidence"> *</span>}
                      </td>
                      <td>{formatProb(p, "1", p.prob_home)}</td>
                      <td>{formatProb(p, "X", p.prob_draw)}</td>
                      <td>{formatProb(p, "2", p.prob_away)}</td>
                      <td>
                        <strong>{bestPick(p)}</strong>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
          {result.probabilities.some((p) => p.low_confidence) && (
            <p className="hint">
              <span className="low-confidence">*</span> Sem histórico destas equipas: estimativa pouco fiável.
            </p>
          )}

          {resumoDisponivel && (
            <div className="resumo-ia">
              <button onClick={handleExplicar} disabled={resumoLoading}>
                {resumoLoading ? "A gerar resumo..." : "Explicar este desdobramento"}
              </button>
              {resumoError && <p className="error">{resumoError}</p>}
              {resumo && (
                <>
                  <p>{resumo}</p>
                  <p className="hint">Resumo gerado por IA, pode conter imprecisões.</p>
                </>
              )}
            </div>
          )}

          <h3>Desdobramento ({result.apostas.length} apostas)</h3>
          <div className="controls">
            <CopyButton text={result.apostas.map((a) => a.join(" ")).join("\n")} label="Copiar apostas (1 por linha)" />
            <CopyButton
              text={result.apostas.map((a) => a.join("\t")).join("\n")}
              label="Copiar para folha de cálculo"
            />
            <CopyButton
              text={result.probabilities
                .map((p, j) => `${j + 1}. ${p.home_team}-${p.away_team}: ${result.apostas.map((a) => a[j]).join(" ")}`)
                .join("\n")}
              label="Copiar jogo a jogo"
            />
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  {result.probabilities.map((p, j) => (
                    <th key={p.match_id} className={pickClass(p.fixed_results)} title={`${p.home_team}-${p.away_team}`}>
                      {j + 1}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.apostas.map((aposta, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    {aposta.map((o, j) => (
                      <td key={j} className={pickClass(result.probabilities[j].fixed_results)}>
                        {o}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
