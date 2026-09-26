interface Props {
  name: string;
}

/** Placeholder for a sport whose predictions are not available yet. */
export function SportTab({ name }: Props) {
  return (
    <div className="tab-content">
      <h2>{name}</h2>
      <p className="coming-soon">
        As previsões de {name} estão em preparação. Por agora podes usar o <strong>Futebol</strong> e os{" "}
        <strong>Jogos Santa Casa</strong>.
      </p>
    </div>
  );
}
