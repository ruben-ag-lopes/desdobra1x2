import { useEffect, useState } from "react";
import { conferirCodigo, getUltimoCodigo, sugerirCodigo, type CodeGame } from "../api/client";
import type { ConferirCodigoResponse, UltimoCodigo } from "../api/types";
import { CopyButton } from "../components/CopyButton";

interface Props {
  game: CodeGame;
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

function UltimoCodigoCard({ sorteio }: { sorteio: UltimoCodigo }) {
  return (
    <div className="ultimo-sorteio">
      <h3>
        Último sorteio: {sorteio.concurso} — {formatDate(sorteio.data_sorteio)}
      </h3>
      <div className="table-scroll">
        <table className="prize-table">
          <thead>
            <tr>
              <th>Prémio</th>
              <th>Vencedores</th>
              <th>Valor</th>
            </tr>
          </thead>
          <tbody>
            {sorteio.premios.map((p) => (
              <tr key={p.nome}>
                <td>{p.nome}</td>
                <td>{p.vencedores_portugal != null ? `${p.vencedores_portugal} (PT) / ${p.vencedores_total}` : p.vencedores_total}</td>
                <td>{p.valor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details>
        <summary>Códigos premiados ({sorteio.codigos.length})</summary>
        <p>{sorteio.codigos.join(" · ")}</p>
      </details>
    </div>
  );
}

function ResultadoCodigo({ r }: { r: ConferirCodigoResponse }) {
  return r.premio ? (
    <h3>
      Tens prémio: {r.premio.nome} — {r.premio.valor}
    </h3>
  ) : (
    <h3>Sem prémio neste sorteio.</h3>
  );
}

export function CodigoTab({ game, title }: Props) {
  const [sorteio, setSorteio] = useState<UltimoCodigo | null>(null);
  const [sorteioError, setSorteioError] = useState<string | null>(null);
  const [codigo, setCodigo] = useState("");
  const [resultado, setResultado] = useState<ConferirCodigoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sugestao, setSugestao] = useState<string | null>(null);

  useEffect(() => {
    setSorteio(null);
    setSorteioError(null);
    setResultado(null);
    setSugestao(null);
    getUltimoCodigo(game)
      .then(setSorteio)
      .catch((e) => setSorteioError(String(e)));
  }, [game]);

  async function handleConferir(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResultado(null);
    try {
      setResultado(await conferirCodigo(game, codigo));
    } catch (err) {
      setError(mensagemErro(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSugerir() {
    setError(null);
    try {
      setSugestao((await sugerirCodigo(game)).codigo);
    } catch (err) {
      setError(mensagemErro(err));
    }
  }

  return (
    <div className="tab-content">
      <h2>{title}</h2>
      {sorteioError && <p className="hint">Não foi possível obter o último sorteio ({sorteioError}).</p>}
      {sorteio && <UltimoCodigoCard sorteio={sorteio} />}

      <section className="conferir">
        <h3>Conferir o meu código</h3>
        <form className="controls" onSubmit={handleConferir}>
          <label>
            Código:
            <input type="text" value={codigo} onChange={(e) => setCodigo(e.target.value)} placeholder="QRX13538" required />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "A verificar..." : "Verificar"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        {resultado && <ResultadoCodigo r={resultado} />}
      </section>

      <section className="conferir">
        <h3>Sugestão de código</h3>
        <div className="controls">
          <button onClick={handleSugerir}>Sugerir código</button>
        </div>
        {sugestao && (
          <p>
            <strong>{sugestao}</strong> <CopyButton text={sugestao} label="Copiar" />
          </p>
        )}
        <p className="hint">Um código ao acaso: a probabilidade de ganhar é a mesma para qualquer código.</p>
      </section>
    </div>
  );
}
