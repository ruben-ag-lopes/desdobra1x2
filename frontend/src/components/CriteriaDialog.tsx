import { useRef, useState } from "react";
import { getCriterios } from "../api/client";
import type { Criteria, CriterionId, LegacyCriterionId, ModelCriteria } from "../api/types";
import {
  customOnly,
  emptyCriteria,
  isCriteriaCustom,
  LEGACY_SHARE_MAX,
  legacyCustomOnly,
  legacySum,
  MULTIPLIER_MAX,
} from "../criteriaProfile";

interface Props {
  /** Model ids used in the current result, with the (1-based) numbers of the games each one predicted. */
  usage: Map<string, number[]>;
  hasDouble: boolean;
  /** The user's criteria; together with onApply, shows the editor. */
  criteria?: Criteria;
  /** Called with the user's criteria when they press "Aplicar e recalcular". */
  onApply?: (criteria: Criteria) => void;
}

const TRAINED_IDS = new Set<string>(["elo", "casa", "ataque", "defesa", "h2h"]);
const LEGACY_IDS = new Set<string>(["forma", "ranking_uefa", "ultimos2", "confronto_direto", "classificacao"]);

function formatGames(numbers: number[]): string {
  return numbers.length === 1 ? `jogo ${numbers[0]}` : `jogos ${numbers.join(", ")}`;
}

/** Criteria the user can scale, restricted to one id set, once each, most influential first. */
function pickEditable(models: ModelCriteria[], ids: Set<string>): { id: string; nome: string }[] {
  const best = new Map<string, { nome: string; peso: number }>();
  for (const c of models.flatMap((m) => m.criterios)) {
    if (!c.id || !ids.has(c.id)) continue;
    const peso = c.peso ?? 0;
    if (peso > (best.get(c.id)?.peso ?? -1)) best.set(c.id, { nome: c.nome, peso });
  }
  return [...best.entries()].sort((a, b) => b[1].peso - a[1].peso).map(([id, { nome }]) => ({ id, nome }));
}

function multiplierLabel(m: number): string {
  if (m === 0) return "ignorado";
  if (m === 1) return "100% (predefinido)";
  return `${Math.round(m * 100)}%`;
}

export function CriteriaDialog({ usage, hasDouble, criteria, onApply }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [models, setModels] = useState<ModelCriteria[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Criteria>(criteria ?? emptyCriteria());

  function open() {
    dialogRef.current?.showModal();
    setModels(null);
    setError(null);
    setDraft(criteria ?? emptyCriteria());
    getCriterios([...usage.keys()])
      .then(setModels)
      .catch((e) => setError(String(e)));
  }

  function apply(next: Criteria) {
    onApply?.({ multiplicadores: customOnly(next.multiplicadores), pesosAntigos: legacyCustomOnly(next.pesosAntigos) });
    dialogRef.current?.close();
  }

  const editableTrained = models && onApply ? pickEditable(models, TRAINED_IDS) : [];
  const editableLegacy = models && onApply ? pickEditable(models, LEGACY_IDS) : [];
  const currentCriteria = criteria ?? emptyCriteria();
  const changed = JSON.stringify(draft) !== JSON.stringify(currentCriteria);
  const legacyTotal = legacySum(draft.pesosAntigos);
  const legacyOverLimit = legacyTotal > 1 + 1e-9;

  return (
    <>
      <button className="link-button" onClick={open}>
        ⓘ Critérios e pesos{isCriteriaCustom(currentCriteria) && " (personalizados)"}
      </button>
      <dialog
        ref={dialogRef}
        className="criteria-dialog"
        onClick={(e) => e.target === dialogRef.current && dialogRef.current?.close()}
      >
        <header>
          <h3>Como são calculadas as probabilidades</h3>
          <button aria-label="Fechar" onClick={() => dialogRef.current?.close()}>
            ✕
          </button>
        </header>

        {error && <p className="error">{error}</p>}
        {!models && !error && <p className="hint">A carregar...</p>}

        {editableTrained.length > 0 && (
          <section className="criteria-editor">
            <h4>Os teus critérios</h4>
            <p className="hint">
              Dá mais ou menos importância a cada critério: 100% é o modelo predefinido, 0% ignora o critério e 200%
              duplica o seu efeito. Aplica-se aos jogos com modelo treinado.
            </p>
            <datalist id="criteria-default-tick">
              <option value={100} />
            </datalist>
            {editableTrained.map(({ id, nome }) => {
              const value = draft.multiplicadores[id as CriterionId] ?? 1;
              return (
                <div key={id} className="criterion-slider">
                  <label htmlFor={`mult-${id}`}>{nome}</label>
                  <input
                    id={`mult-${id}`}
                    type="range"
                    min={0}
                    max={MULTIPLIER_MAX * 100}
                    step={10}
                    list="criteria-default-tick"
                    value={Math.round(value * 100)}
                    aria-valuetext={multiplierLabel(value)}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        multiplicadores: { ...draft.multiplicadores, [id]: Number(e.target.value) / 100 },
                      })
                    }
                  />
                  <output htmlFor={`mult-${id}`} className={value === 1 ? "hint" : ""}>
                    {multiplierLabel(value)}
                  </output>
                </div>
              );
            })}
          </section>
        )}

        {editableLegacy.length > 0 && (
          <section className="criteria-editor">
            <h4>Critérios do modelo antigo (sem histórico das equipas)</h4>
            <p className="hint">
              Estes 5 pesos são uma partilha de 100%: a soma não pode ultrapassar 100% e nenhum pode sozinho
              ultrapassar 100%. Só afeta jogos sem modelo treinado.
            </p>
            {editableLegacy.map(({ id, nome }) => {
              const value = draft.pesosAntigos[id as LegacyCriterionId] ?? 0;
              return (
                <div key={id} className="criterion-slider">
                  <label htmlFor={`legado-${id}`}>{nome}</label>
                  <input
                    id={`legado-${id}`}
                    type="range"
                    min={0}
                    max={LEGACY_SHARE_MAX * 100}
                    step={5}
                    value={Math.round(value * 100)}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        pesosAntigos: { ...draft.pesosAntigos, [id]: Number(e.target.value) / 100 },
                      })
                    }
                  />
                  <output htmlFor={`legado-${id}`}>{Math.round(value * 100)}%</output>
                </div>
              );
            })}
            <p className={legacyOverLimit ? "criteria-warning" : "hint"} role={legacyOverLimit ? "alert" : undefined}>
              Total: {Math.round(legacyTotal * 100)}%{legacyOverLimit && " — não pode ultrapassar 100%"}
            </p>
          </section>
        )}

        {(editableTrained.length > 0 || editableLegacy.length > 0) && (
          <>
            {isCriteriaCustom(draft) && (
              <p className="criteria-warning" role="note">
                Critérios alterados não foram validados. Os predefinidos são os que tiveram o menor erro nos testes
                com jogos passados.
              </p>
            )}
            <div className="controls">
              <button onClick={() => apply(draft)} disabled={!changed || legacyOverLimit}>
                Aplicar e recalcular
              </button>
              <button
                onClick={() => apply(emptyCriteria())}
                disabled={!isCriteriaCustom(draft) && !isCriteriaCustom(currentCriteria)}
              >
                Repor predefinidos
              </button>
            </div>
          </>
        )}

        {models?.map((m) => (
          <section key={m.modelo}>
            <h4>
              {m.titulo} <span className="hint">({formatGames(usage.get(m.modelo) ?? [])})</span>
            </h4>
            <p>{m.descricao}</p>
            <ul className="criteria-list">
              {m.criterios.map((c) => (
                <li key={c.nome}>
                  <div className="criterion-head">
                    <span>{c.nome}</span>
                    {c.peso !== null && <strong>{Math.round(c.peso * 100)}%</strong>}
                  </div>
                  {c.peso !== null && (
                    <div className="weight-bar" aria-hidden="true">
                      <span style={{ width: `${c.peso * 100}%` }} />
                    </div>
                  )}
                  {c.detalhe && <p className="hint">{c.detalhe}</p>}
                </li>
              ))}
            </ul>
            {m.notas.map((n) => (
              <p key={n} className="hint">
                {n}
              </p>
            ))}
            {m.dados && <p className="hint">Dados: {m.dados}</p>}
          </section>
        ))}

        {models && isCriteriaCustom(currentCriteria) && (
          <p className="hint">Os pesos acima são os do modelo predefinido, antes das tuas alterações.</p>
        )}

        {hasDouble && (
          <section>
            <h4>Duplas</h4>
            <p>
              Nos jogos com dois resultados escolhidos, o modelo calcula 1, X e 2 normalmente e depois reparte a
              probabilidade do resultado excluído pelos dois escolhidos, na proporção de cada um. Exemplo: 33% / 28% /
              38% com dupla 1X fica 54% / 46%.
            </p>
          </section>
        )}
      </dialog>
    </>
  );
}
