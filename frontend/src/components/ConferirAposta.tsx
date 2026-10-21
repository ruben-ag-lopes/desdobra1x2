import { useState } from "react";
import { conferirAposta } from "../api/client";
import type { ConferirResponse } from "../api/types";

interface Props {
  game: "totoloto" | "euromilhoes" | "eurodreams";
}

// The API errors look like "400: {"detail":"..."}": show only the message.
function mensagemErro(e: unknown): string {
  const texto = String(e).replace(/^\d+: /, "");
  try {
    return JSON.parse(texto).detail ?? texto;
  } catch {
    return texto;
  }
}

function Resultado({ r }: { r: ConferirResponse }) {
  const dataSorteio = new Date(r.data_sorteio).toLocaleDateString("pt-PT");
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
  const [aposta, setAposta] = useState("");
  const [resultado, setResultado] = useState<ConferirResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
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
      <form className="controls" onSubmit={handleSubmit}>
        <label>
          Aposta:
          <input
            type="text"
            value={aposta}
            onChange={(e) => setAposta(e.target.value)}
            placeholder="3 4 6 7 8 + 1"
            required
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "A verificar..." : "Verificar"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {resultado && <Resultado r={resultado} />}
    </section>
  );
}
