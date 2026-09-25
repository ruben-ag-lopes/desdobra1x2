import { useRef, useState } from "react";
import { getCriterios } from "../api/client";
import type { ModelCriteria } from "../api/types";

interface Props {
  /** Model ids used in the current result, with the (1-based) numbers of the games each one predicted. */
  usage: Map<string, number[]>;
  hasDouble: boolean;
}

function formatGames(numbers: number[]): string {
  return numbers.length === 1 ? `jogo ${numbers[0]}` : `jogos ${numbers.join(", ")}`;
}

export function CriteriaDialog({ usage, hasDouble }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [models, setModels] = useState<ModelCriteria[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function open() {
    dialogRef.current?.showModal();
    setModels(null);
    setError(null);
    getCriterios([...usage.keys()])
      .then(setModels)
      .catch((e) => setError(String(e)));
  }

  return (
    <>
      <button className="link-button" onClick={open}>
        ⓘ Critérios e pesos
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
