import type { Draw } from "../api/types";

interface Props {
  draw: Draw | null | undefined;
  error: string | null;
}

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString("pt-PT") : "?";
}

export function DrawInfo({ draw, error }: Props) {
  if (error) return <p className="error">Erro a obter concurso ativo: {error}</p>;
  if (draw === undefined) return <p>A carregar concurso ativo...</p>;
  if (draw === null) return <p className="hint">Sem concurso ativo de momento.</p>;
  return (
    <p className="draw-info">
      Concurso <strong>{draw.concurso}</strong> — fecho de apostas:{" "}
      {draw.fecha_apostas ? new Date(draw.fecha_apostas).toLocaleString("pt-PT") : "?"} — sorteio:{" "}
      {formatDate(draw.data_sorteio)}
    </p>
  );
}
