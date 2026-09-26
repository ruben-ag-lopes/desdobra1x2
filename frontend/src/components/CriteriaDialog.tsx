import { useRef, useState } from "react";
import { getCriterios } from "../api/client";
import type { CriterionId, ModelCriteria, Multipliers } from "../api/types";
import { customOnly, isCustom, MULTIPLIER_MAX } from "../criteriaProfile";

interface Props {
  /** Model ids used in the current result, with the (1-based) numbers of the games each one predicted. */
  usage: Map<string, number[]>;
  hasDouble: boolean;
  /** The user's criteria; together with onApply, shows the editor. */
  multipliers?: Multipliers;
  /** Called with the user's criteria when they press "Aplicar e recalcular". */
  onApply?: (multipliers: Multipliers) => void;
}

function formatGames(numbers: number[]): string {
  return numbers.length === 1 ? `jogo ${numbers[0]}` : `jogos ${numbers.join(", ")}`;
}

/** Criteria the user can scale in these models, once each, most influential first. */
function editableCriteria(models: ModelCriteria[]): { id: CriterionId; nome: string }[] {
  const best = new Map<CriterionId, { nome: string; peso: number }>();
  for (const c of models.flatMap((m) => m.criterios)) {
    if (!c.id) continue;
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

export function CriteriaDialog({ usage, hasDouble, multipliers = {}, onApply }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [models, setModels] = useState<ModelCriteria[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Multipliers>(multipliers);

  function open() {
    dialogRef.current?.showModal();
    setModels(null);
    setError(null);
    setDraft(multipliers);
    getCriterios([...usage.keys()])
      .then(setModels)
      .catch((e) => setError(String(e)));
  }

  function apply(next: Multipliers) {
    onApply?.(customOnly(next));
    dialogRef.current?.close();
  }

  const editable = models && onApply ? editableCriteria(models) : [];
  const changed = JSON.stringify(customOnly(draft)) !== JSON.stringify(customOnly(multipliers));

  return (
    <>
      <button className="link-button" onClick={open}>
        ⓘ Critérios e pesos{isCustom(multipliers) && " (personalizados)"}
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

        {editable.length > 0 && (
          <section className="criteria-editor">
            <h4>Os teus critérios</h4>
            <p className="hint">
              Dá mais ou menos importância a cada critério: 100% é o modelo predefinido, 0% ignora o critério e 200%
              duplica o seu efeito. Aplica-se a todos os jogos com modelo treinado.
            </p>
            <datalist id="criteria-default-tick">
              <option value={100} />
            </datalist>
            {editable.map(({ id, nome }) => {
              const value = draft[id] ?? 1;
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
                    onChange={(e) => setDraft({ ...draft, [id]: Number(e.target.value) / 100 })}
                  />
                  <output htmlFor={`mult-${id}`} className={value === 1 ? "hint" : ""}>
                    {multiplierLabel(value)}
                  </output>
                </div>
              );
            })}
            {isCustom(draft) && (
              <p className="criteria-warning" role="note">
                Critérios alterados não foram validados. Os predefinidos são os que tiveram o menor erro nos testes com
                jogos passados.
              </p>
            )}
            <div className="controls">
              <button onClick={() => apply(draft)} disabled={!changed}>
                Aplicar e recalcular
              </button>
              <button onClick={() => apply({})} disabled={!isCustom(draft) && !isCustom(multipliers)}>
                Repor predefinidos
              </button>
            </div>
          </section>
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

        {models && isCustom(multipliers) && (
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
