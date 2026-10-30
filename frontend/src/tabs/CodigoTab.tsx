import { useEffect, useState } from "react";
import { conferirCodigo, getUltimoCodigo, type CodeGame } from "../api/client";
import type { ConferirCodigoResponse, UltimoCodigo } from "../api/types";
import { formatDate, mensagemErro } from "../format";

interface Props {
  game: CodeGame;
  title: string;
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

  useEffect(() => {
    setSorteio(null);
    setSorteioError(null);
    setResultado(null);
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

    </div>
  );
}
