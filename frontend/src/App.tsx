import { useState } from "react";
import "./App.css";
import logo from "./assets/logo.png";
import { SupportFooter } from "./components/SupportFooter";
import { FutebolTab } from "./tabs/FutebolTab";
import { LotteryTab } from "./tabs/LotteryTab";
import { SportTab } from "./tabs/SportTab";
import { TotobolaTab } from "./tabs/TotobolaTab";

const SANTA_CASA_GAMES = [
  { id: "totobola", label: "Totobola" },
  { id: "totobola_extra", label: "Totobola Extra" },
  { id: "totoloto", label: "Totoloto" },
  { id: "euromilhoes", label: "Euromilhões" },
  { id: "eurodreams", label: "EuroDreams" },
] as const;

const OTHER_SPORTS = [
  { id: "basquetebol", label: "Basquetebol" },
  { id: "nba", label: "NBA" },
  { id: "formula1", label: "Fórmula 1" },
  { id: "mma", label: "MMA" },
  { id: "raguebi", label: "Râguebi" },
  { id: "voleibol", label: "Voleibol" },
  { id: "andebol", label: "Andebol" },
] as const;

const SECTIONS = [
  { id: "santacasa", label: "Jogos Santa Casa" },
  { id: "futebol", label: "Futebol" },
  { id: "desportos", label: "Outros desportos" },
] as const;

type Section = (typeof SECTIONS)[number]["id"];
type GameId = (typeof SANTA_CASA_GAMES)[number]["id"];
type SportId = (typeof OTHER_SPORTS)[number]["id"];

function App() {
  const [section, setSection] = useState<Section>("santacasa");
  // Each section remembers its last choice while the user visits the others.
  const [game, setGame] = useState<GameId>("totobola");
  const [sport, setSport] = useState<SportId>("basquetebol");
  const active = section === "santacasa" ? game : section;

  return (
    <div className="app" data-game={active}>
      <header>
        <h1 className="brand">
          <img src={logo} alt="desdobra1X2" width={360} height={87} />
        </h1>
        <p className="disclaimer">Ferramenta de análise e geração de apostas — não submete apostas automaticamente.</p>
      </header>

      <aside className="warning-banner" role="note" aria-label="Aviso importante">
        <strong>⚠ Aviso:</strong> as previsões do Totobola e do Futebol são meramente estatísticas e os números do
        Totoloto, Euromilhões e EuroDreams são gerados aleatoriamente.{" "}
        <strong>Não há qualquer garantia de acerto.</strong> Joga com responsabilidade — maiores de 18 anos.
      </aside>

      <nav className="sections" aria-label="Secções">
        {SECTIONS.map((t) => (
          <button
            key={t.id}
            className={section === t.id ? "active" : ""}
            aria-pressed={section === t.id}
            onClick={() => setSection(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {section === "santacasa" && (
        <nav className="tabs" aria-label="Jogos Santa Casa">
          {SANTA_CASA_GAMES.map((t) => (
            <button
              key={t.id}
              className={game === t.id ? "active" : ""}
              aria-pressed={game === t.id}
              onClick={() => setGame(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      )}

      {section === "desportos" && (
        <nav className="tabs" aria-label="Outros desportos">
          {OTHER_SPORTS.map((t) => (
            <button
              key={t.id}
              className={sport === t.id ? "active" : ""}
              aria-pressed={sport === t.id}
              onClick={() => setSport(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      )}

      <main>
        {active === "totobola" && <TotobolaTab game="totobola" title="Totobola" />}
        {active === "totobola_extra" && <TotobolaTab game="totobola_extra" title="Totobola Extra" />}
        {active === "futebol" && <FutebolTab />}
        {active === "desportos" && <SportTab name={OTHER_SPORTS.find((t) => t.id === sport)!.label} />}
        {active === "totoloto" && <LotteryTab game="totoloto" title="Totoloto" extraLabel="Nº de sorte" />}
        {active === "euromilhoes" && <LotteryTab game="euromilhoes" title="Euromilhões" extraLabel="Estrelas" />}
        {active === "eurodreams" && <LotteryTab game="eurodreams" title="EuroDreams" extraLabel="Dream number" />}
      </main>

      <SupportFooter />
    </div>
  );
}

export default App;
