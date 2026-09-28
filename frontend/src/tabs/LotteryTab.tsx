import { useEffect, useState } from "react";
import { generateLotteryTickets, getFrequencia, getLotteryDraw, getUltimoSorteio } from "../api/client";
import type { Draw, FrequenciaResponse, LotteryTicket, UltimoSorteio } from "../api/types";
import { CopyButton } from "../components/CopyButton";
import { DrawInfo } from "../components/DrawInfo";

interface Props {
  game: "totoloto" | "euromilhoes" | "eurodreams";
  title: string;
  extraLabel: string;
}

function ticketText(t: LotteryTicket): string {
  return `${t.numbers.join(" ")} + ${t.extra_numbers.join(" ")}`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-PT");
}

function formatNumber(n: number): string {
  return n.toLocaleString("pt-PT");
}

function UltimoSorteioCard({ sorteio }: { sorteio: UltimoSorteio }) {
  return (
    <div className="ultimo-sorteio">
      <h3>
        Último sorteio: concurso {sorteio.concurso} — {formatDate(sorteio.data_sorteio)}
      </h3>
      <p className="chave">
        <strong>Chave:</strong> {sorteio.chave.join(" ")}
        {sorteio.chave_extra.length > 0 && <> + {sorteio.chave_extra.join(" ")}</>}
      </p>
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
                <td>
                  {p.vencedores_portugal != null
                    ? `${formatNumber(p.vencedores_portugal)} (PT) / ${formatNumber(p.vencedores_total)}`
                    : formatNumber(p.vencedores_total)}
                </td>
                <td>{p.valor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FrequenciaCard({ frequencia }: { frequencia: FrequenciaResponse }) {
  const ordenados = [...frequencia.numeros].sort((a, b) => b.percentagem - a.percentagem);
  const maisFrequentes = ordenados.slice(0, 6);
  const menosFrequentes = ordenados.slice(-6).reverse();

  return (
    <details className="frequencia">
      <summary>
        Números mais frequentes (últimos {frequencia.n_sorteios} sorteios, desde {formatDate(frequencia.desde)})
      </summary>
      <p className="hint">
        A frequência passada <strong>não aumenta a probabilidade</strong> de um número sair no próximo sorteio: cada
        sorteio é independente dos anteriores. Isto é só curiosidade, calculada apenas com os sorteios recentes
        disponíveis no site — não é o histórico completo do jogo.
      </p>
      <div className="frequencia-grid">
        <div>
          <h4>Mais saídos</h4>
          <ul className="frequencia-list">
            {maisFrequentes.map((n) => (
              <li key={n.numero}>
                <strong>{n.numero}</strong> — {n.percentagem.toFixed(1)}% ({n.saidas}x)
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4>Menos saídos</h4>
          <ul className="frequencia-list">
            {menosFrequentes.map((n) => (
              <li key={n.numero}>
                <strong>{n.numero}</strong> — {n.percentagem.toFixed(1)}% ({n.saidas}x, {n.ausencias} sorteios sem sair)
              </li>
            ))}
          </ul>
        </div>
      </div>
    </details>
  );
}

export function LotteryTab({ game, title, extraLabel }: Props) {
  const [count, setCount] = useState(1);
  const [tickets, setTickets] = useState<LotteryTicket[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draw, setDraw] = useState<Draw | null | undefined>(undefined);
  const [drawError, setDrawError] = useState<string | null>(null);
  const [sorteio, setSorteio] = useState<UltimoSorteio | null>(null);
  const [sorteioError, setSorteioError] = useState<string | null>(null);
  const [frequencia, setFrequencia] = useState<FrequenciaResponse | null>(null);

  useEffect(() => {
    setSorteio(null);
    setSorteioError(null);
    setFrequencia(null);
    getLotteryDraw(game)
      .then(setDraw)
      .catch((e) => setDrawError(String(e)));
    getUltimoSorteio(game)
      .then(setSorteio)
      .catch((e) => setSorteioError(String(e)));
    getFrequencia(game).then(setFrequencia).catch(() => setFrequencia(null));
  }, [game]);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await generateLotteryTickets(game, count);
      setTickets(res.tickets);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="tab-content">
      <h2>{title}</h2>
      <DrawInfo draw={draw} error={drawError} />
      <div className="controls">
        <label>
          Nº de apostas:
          <input
            type="number"
            min={1}
            max={20}
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
          />
        </label>
        <button onClick={handleGenerate} disabled={loading}>
          {loading ? "A gerar..." : "Gerar aposta(s)"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      <ul className="tickets">
        {tickets.map((t, i) => (
          <li key={i}>
            <strong>Números:</strong> {t.numbers.join(", ")} &nbsp;|&nbsp;
            <strong>{extraLabel}:</strong> {t.extra_numbers.join(", ")}
            <CopyButton text={ticketText(t)} label="Copiar" />
          </li>
        ))}
      </ul>
      {tickets.length > 0 && <CopyButton text={tickets.map(ticketText).join("\n")} label="Copiar todas" />}

      {sorteioError && <p className="hint">Não foi possível obter o último sorteio ({sorteioError}).</p>}
      {sorteio && <UltimoSorteioCard sorteio={sorteio} />}
      {frequencia && <FrequenciaCard frequencia={frequencia} />}
    </div>
  );
}
