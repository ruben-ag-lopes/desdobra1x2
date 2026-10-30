interface Props {
  numeros: number[];
  extra?: number[];
  neutra?: boolean; // grey instead of the game colour, to tell your own bet apart from the prizes
}

// One number per circle. The extra numbers (stars, lucky number...) take the game colour.
export function Caixas({ numeros, extra = [], neutra = false }: Props) {
  return (
    <div className={neutra ? "caixas neutra" : "caixas"}>
      {numeros.map((n, i) => (
        <span key={`n${i}`} className="caixa">
          {n}
        </span>
      ))}
      {extra.map((n, i) => (
        <span key={`e${i}`} className="caixa extra">
          {n}
        </span>
      ))}
    </div>
  );
}
