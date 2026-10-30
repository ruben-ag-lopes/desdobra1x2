import { useState } from "react";
import { conferirAposta } from "../api/client";
import type { ConferirResponse } from "../api/types";
import { formatDate, mensagemErro } from "../format";
import { montarAposta } from "./aposta";
import { Caixas } from "./Caixas";

interface Props {
  game: "totoloto" | "euromilhoes" | "eurodreams";
}

// How many numbers and extra numbers each game has (the API checks them again).
const CONTAGEM = {
  totoloto: { numeros: 5, extra: 1 },
  euromilhoes: { numeros: 5, extra: 2 },
  eurodreams: { numeros: 6, extra: 1 },
};

function Resultado({ r }: { r: ConferirResponse }) {
  const dataSorteio = formatDate(r.data_sorteio);
  const acertos = r.acertos.length > 0 ? r.acertos.join(" ") : "nenhum";
  const acertosExtra = r.acertos_extra.length > 0 ? ` + ${r.acertos_extra.join(" ")}` : "";

  if (!r.tabela_disponivel) {
    return (
      <p className="hint">
        A tabela de prémios do concurso {r.concurso} ({dataSorteio}) ainda não está disponível. Volta a verificar
        mais tarde.
      </p>
    );
  }

  return (
    <div className="ultimo-sorteio">
      <Caixas numeros={r.numeros} extra={r.numeros_extra} neutra />
      {r.premio ? (
        <h3>
          Tens prémio: {r.premio.nome} — {r.premio.valor}
        </h3>
      ) : (
        <h3>Sem prémio neste concurso.</h3>
      )}
      <p>
        Concurso {r.concurso} ({dataSorteio}). Acertaste nos números: {acertos}
        {acertosExtra}.
      </p>
    </div>
  );
}

export function ConferirAposta({ game }: Props) {
  const { numeros, extra } = CONTAGEM[game];
  // One box per number: the main numbers first, then the extra ones.
  const [valores, setValores] = useState<string[]>(Array(numeros + extra).fill(""));
  const [resultado, setResultado] = useState<ConferirResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function mudar(i: number, valor: string) {
    setValores(valores.map((v, j) => (j === i ? valor.replace(/\D/g, "").slice(0, 2) : v)));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const aposta = montarAposta(valores, numeros);
    setLoading(true);
    setError(null);
    setResultado(null);
    try {
      setResultado(await conferirAposta(game, aposta));
    } catch (err) {
      setError(mensagemErro(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="conferir">
      <h3>Conferir a minha aposta</h3>
      <form onSubmit={handleSubmit}>
        <div className="caixas entrada">
          {valores.map((v, i) => (
            <input
              key={i}
              className={i >= numeros ? "caixa extra" : "caixa"}
              inputMode="numeric"
              value={v}
              onChange={(e) => mudar(i, e.target.value)}
              aria-label={i >= numeros ? `Extra ${i - numeros + 1}` : `Número ${i + 1}`}
              required
            />
          ))}
        </div>
        <div className="controls">
          <button type="submit" disabled={loading}>
            {loading ? "A verificar..." : "Verificar"}
          </button>
        </div>
      </form>
      {error && <p className="error">{error}</p>}
      {resultado && <Resultado r={resultado} />}
    </section>
  );
}
