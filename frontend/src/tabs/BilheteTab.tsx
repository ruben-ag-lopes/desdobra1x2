import { useEffect, useState } from "react";
import { conferirBilhete, getUltimoBilhete, sugerirBilhete, type TicketGame } from "../api/client";
import type { ConferirBilheteResponse, UltimoBilhete } from "../api/types";
import { CopyButton } from "../components/CopyButton";

interface Props {
  game: TicketGame;
  title: string;
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

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-PT");
}

function UltimoBilheteCard({ sorteio }: { sorteio: UltimoBilhete }) {
  return (
    <div className="ultimo-sorteio">
      <h3>
        Último sorteio: extração {sorteio.concurso} — {formatDate(sorteio.data_sorteio)}
      </h3>
      <div className="table-scroll">
        <table className="prize-table">
          <thead>
            <tr>
              <th>Prémio</th>
              <th>Bilhete</th>
              <th>Valores</th>
            </tr>
          </thead>
          <tbody>
            {sorteio.premios.map((p) => (
              <tr key={p.nome}>
                <td>{p.nome}</td>
                <td>
                  <strong>{p.bilhete}</strong>
                </td>
                <td>{p.valores.join(" · ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="hint">
        Sequências de {sorteio.sequencias_digitos} algarismos: {sorteio.sequencias.join(" - ")}
      </p>
    </div>
  );
}

function ResultadoBilhete({ r, sequenciaDigitos }: { r: ConferirBilheteResponse; sequenciaDigitos: number }) {
  if (r.premio) {
    return (
      <h3>
        Tens prémio: {r.premio.nome} — {r.premio.valores.join(" · ")}
      </h3>
    );
  }
  if (r.sequencia) {
    return (
      <h3>
        Tens uma sequência de {sequenciaDigitos} algarismos ({r.sequencia}). Confirma o valor no plano oficial de
        prémios.
      </h3>
    );
  }
  return <h3>Sem prémio nesta extração.</h3>;
}

export function BilheteTab({ game, title }: Props) {
  const [sorteio, setSorteio] = useState<UltimoBilhete | null>(null);
  const [sorteioError, setSorteioError] = useState<string | null>(null);
  const [bilhete, setBilhete] = useState("");
  const [resultado, setResultado] = useState<ConferirBilheteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sugestao, setSugestao] = useState<string | null>(null);

  useEffect(() => {
    setSorteio(null);
    setSorteioError(null);
    setResultado(null);
    setSugestao(null);
    getUltimoBilhete(game)
      .then(setSorteio)
      .catch((e) => setSorteioError(String(e)));
  }, [game]);

  async function handleConferir(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResultado(null);
    try {
      setResultado(await conferirBilhete(game, bilhete));
    } catch (err) {
      setError(mensagemErro(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSugerir() {
    setError(null);
    try {
      setSugestao((await sugerirBilhete(game)).bilhete);
    } catch (err) {
      setError(mensagemErro(err));
    }
  }

  return (
    <div className="tab-content">
      <h2>{title}</h2>
      {sorteioError && <p className="hint">Não foi possível obter o último sorteio ({sorteioError}).</p>}
      {sorteio && <UltimoBilheteCard sorteio={sorteio} />}

      <section className="conferir">
        <h3>Conferir o meu bilhete</h3>
        <form className="controls" onSubmit={handleConferir}>
          <label>
            Bilhete:
            <input
              type="text"
              inputMode="numeric"
              value={bilhete}
              onChange={(e) => setBilhete(e.target.value)}
              placeholder="10138"
              required
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "A verificar..." : "Verificar"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        {resultado && sorteio && <ResultadoBilhete r={resultado} sequenciaDigitos={sorteio.sequencias_digitos} />}
      </section>

      <section className="conferir">
        <h3>Sugestão de bilhete</h3>
        <div className="controls">
          <button onClick={handleSugerir}>Sugerir bilhete</button>
        </div>
        {sugestao && (
          <p>
            <strong>{sugestao}</strong> <CopyButton text={sugestao} label="Copiar" />
          </p>
        )}
        <p className="hint">Um número ao acaso: a probabilidade de ganhar é a mesma para qualquer bilhete.</p>
      </section>
    </div>
  );
}
