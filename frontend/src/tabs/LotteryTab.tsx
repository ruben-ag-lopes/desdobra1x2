import { useEffect, useState } from "react";
import { generateLotteryTickets, getLotteryDraw } from "../api/client";
import type { Draw, LotteryTicket } from "../api/types";
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

export function LotteryTab({ game, title, extraLabel }: Props) {
  const [count, setCount] = useState(1);
  const [tickets, setTickets] = useState<LotteryTicket[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draw, setDraw] = useState<Draw | null | undefined>(undefined);
  const [drawError, setDrawError] = useState<string | null>(null);

  useEffect(() => {
    getLotteryDraw(game)
      .then(setDraw)
      .catch((e) => setDrawError(String(e)));
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
    </div>
  );
}
