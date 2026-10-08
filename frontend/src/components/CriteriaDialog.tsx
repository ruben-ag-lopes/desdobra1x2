import { useRef, useState } from "react";
import { getCriterios } from "../api/client";
import type { Criteria, CriterionId, ModelCriteria, Shares } from "../api/types";
import { customOnly, emptyCriteria, isCriteriaCustom } from "../criteriaProfile";
import {
  ALL_IDS,
  defaultShares,
  fullWeights,
  sameShares,
  setShare,
  sharesFromMultipliers,
  sharesToMultipliers,
  TRAINED_IDS,
} from "../shares";

interface Props {
  /** Model ids used in the current result, with the (1-based) numbers of the games each one predicted. */
  usage: Map<string, number[]>;
  hasDouble: boolean;
  /** The user's criteria; together with onApply, shows the personalisable column. */
  criteria?: Criteria;
  /** Called with the user's criteria when they apply or reset; the caller recalculates. */
  onApply?: (criteria: Criteria) => void;
}

const LABEL: Record<CriterionId, string> = {
  elo: "Força das equipas (Elo)",
  casa: "Fator casa",
  ataque: "Ataque recente",
  defesa: "Defesa recente",
  h2h: "Confronto direto",
};

const INFO: Record<CriterionId, string> = {
  elo: "Pontuação que mede a força de cada equipa e se atualiza depois de cada jogo (ganhar a um adversário forte vale mais). A diferença entre as duas equipas é, em regra, o fator mais importante da previsão.",
  casa: "A vantagem de jogar em casa: as equipas costumam marcar mais e perder menos no seu estádio.",
  ataque: "Golos marcados por cada equipa nos últimos 8 jogos.",
  defesa: "Golos sofridos por cada equipa nos últimos 8 jogos. Quantos menos, mais forte a defesa.",
  h2h: "Resultados dos últimos 5 jogos entre as duas equipas.",
};

const WEIGHT_NOTE = "O peso de cada critério é a parte da variação das probabilidades que se deve a ele, medida nos jogos mais recentes.";

/** What the dialog shows when opened: the user's saved shares, else the predefined ones. */
function initialDraft(criteria: Criteria, defaults: Shares, full: Record<CriterionId, number>): Shares {
  const saved = criteria.partilhas;
  const total = ALL_IDS.reduce((sum, i) => sum + (saved[i] ?? 0), 0);
  if (Object.keys(saved).length === ALL_IDS.length && total === 100) return saved;
  if (Object.keys(customOnly(criteria.multiplicadores)).length > 0) {
    return sharesFromMultipliers(criteria.multiplicadores, full);
  }
  return defaults;
}

export function CriteriaDialog({ usage, hasDouble, criteria, onApply }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [models, setModels] = useState<ModelCriteria[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Shares>({});
  const [showInfo, setShowInfo] = useState(false);

  const current = criteria ?? emptyCriteria();
  const trained = (models ?? []).filter((m) => m.criterios.some((c) => c.id && TRAINED_IDS.has(c.id)));
  const defaults = defaultShares(trained, usage);
  const full = fullWeights(trained, usage);
  const rows = trained.length > 0 ? ALL_IDS : [];
  const applied = initialDraft(current, defaults, full);
  const changed = !sameShares(draft, applied);
  const canReset = isCriteriaCustom(current) || !sameShares(draft, defaults);

  function open() {
    dialogRef.current?.showModal();
    setModels(null);
    setError(null);
    setShowInfo(false);
    getCriterios([...usage.keys()])
      .then((list) => {
        const used = list.filter((m) => m.criterios.some((c) => c.id && TRAINED_IDS.has(c.id)));
        setDraft(initialDraft(current, defaultShares(used, usage), fullWeights(used, usage)));
        setModels(list);
      })
      .catch((e) => setError(String(e)));
  }

  function apply(next: Shares | null) {
    // Choosing the predefined shares again is the same as resetting: back to the validated models.
    const reset = next === null || sameShares(next, defaults);
    const multiplicadores = reset ? {} : sharesToMultipliers(next, full);
    onApply?.({
      multiplicadores,
      pesosAntigos: reset ? {} : current.pesosAntigos,
      partilhas: reset || Object.keys(multiplicadores).length === 0 ? {} : next,
    });
    dialogRef.current?.close();
  }

  // One line per distinct data source (the text already names the league).
  const sources = [...new Set(trained.map((m) => m.dados).filter(Boolean))];

  return (
    <>
      <button className="link-button" onClick={open}>
        ⓘ Critérios{isCriteriaCustom(current) && " (personalizados)"}
      </button>
      <dialog
        ref={dialogRef}
        className="criteria-dialog"
        onClick={(e) => e.target === dialogRef.current && dialogRef.current?.close()}
      >
        <header>
          <h3>Critérios das previsões</h3>
          <button aria-label="Fechar" onClick={() => dialogRef.current?.close()}>
            ✕
          </button>
        </header>

        {error && <p className="error">{error}</p>}
        {!models && !error && <p className="hint">A carregar...</p>}
        {models && rows.length === 0 && <p className="hint">Estas previsões não usam critérios personalizáveis.</p>}

        {models && rows.length > 0 && (
          <>
            <div className="criteria-grid">
              <div className="criteria-grid-row head">
                <span>Critério</span>
                <span>Predefinido</span>
                <span>{onApply ? "Personalizado" : ""}</span>
              </div>
              {rows.map((id) => (
                <div className="criteria-grid-row" key={id}>
                  <label htmlFor={`share-${id}`}>{LABEL[id]}</label>
                  <span className="default-share">{defaults[id]}%</span>
                  {onApply && (
                    <div className="custom-share">
                      <input
                        id={`share-${id}`}
                        type="range"
                        min={0}
                        max={100}
                        step={1}
                        value={draft[id] ?? 0}
                        onChange={(e) => setDraft(setShare(draft, id, Number(e.target.value)))}
                      />
                      <output htmlFor={`share-${id}`}>{draft[id] ?? 0}%</output>
                    </div>
                  )}
                </div>
              ))}
              <div className="criteria-grid-row total">
                <span>Total</span>
                <span>100%</span>
                <span>{onApply ? "100%" : ""}</span>
              </div>
            </div>

            {onApply && (
              <div className="controls">
                <button onClick={() => apply(draft)} disabled={!changed}>
                  Aplicar e recalcular
                </button>
                <button onClick={() => apply(null)} disabled={!canReset}>
                  Repor predefinidos
                </button>
                <button className="link-button" aria-expanded={showInfo} onClick={() => setShowInfo((v) => !v)}>
                  ⓘ Mais informações
                </button>
              </div>
            )}

            {showInfo && (
              <dl className="criteria-info">
                {rows.map((id) => (
                  <div key={id}>
                    <dt>{LABEL[id]}</dt>
                    <dd>{INFO[id]}</dd>
                  </div>
                ))}
                {hasDouble && (
                  <div>
                    <dt>Duplas</dt>
                    <dd>
                      Nos jogos com dois resultados escolhidos, a probabilidade do resultado excluído é repartida pelos
                      dois escolhidos, na proporção de cada um.
                    </dd>
                  </div>
                )}
                <div>
                  <dt>Personalizar</dt>
                  <dd>
                    Um critério a 0% nas previsões predefinidas (por exemplo, o ataque nas ligas de clubes) só passa a
                    contar quando lhe dás peso. O efeito de cada alteração é medido num modelo que usa os cinco
                    critérios e somado à previsão predefinida.
                  </dd>
                </div>
              </dl>
            )}

            <footer className="criteria-footer">
              {sources.map((dados) => (
                <p key={dados}>Dados: {dados}</p>
              ))}
              <p>{WEIGHT_NOTE}</p>
            </footer>
          </>
        )}
      </dialog>
    </>
  );
}
