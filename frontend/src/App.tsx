import { useState } from "react";
import "./App.css";
import { SupportFooter } from "./components/SupportFooter";
import { LotteryTab } from "./tabs/LotteryTab";
import { TotobolaTab } from "./tabs/TotobolaTab";

const TABS = [
  { id: "totobola", label: "Totobola" },
  { id: "totobola_extra", label: "Totobola Extra" },
  { id: "totoloto", label: "Totoloto" },
  { id: "euromilhoes", label: "Euromilhões" },
  { id: "eurodreams", label: "EuroDreams" },
] as const;

type TabId = (typeof TABS)[number]["id"];

function App() {
  const [active, setActive] = useState<TabId>("totobola");

  return (
    <div className="app" data-game={active}>
      <header>
        <h1>desdobra1X2</h1>
        <p className="disclaimer">Ferramenta de análise e geração de apostas — não submete apostas automaticamente.</p>
      </header>

      <aside className="warning-banner" role="note" aria-label="Aviso importante">
        <strong>⚠ Aviso:</strong> as previsões do Totobola são meramente estatísticas e os números do Totoloto,
        Euromilhões e EuroDreams são gerados aleatoriamente. <strong>Não há qualquer garantia de acerto.</strong>{" "}
        Joga com responsabilidade — maiores de 18 anos.
      </aside>

      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t.id} className={active === t.id ? "active" : ""} onClick={() => setActive(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>

      <main>
        {active === "totobola" && <TotobolaTab game="totobola" title="Totobola" />}
        {active === "totobola_extra" && <TotobolaTab game="totobola_extra" title="Totobola Extra" />}
        {active === "totoloto" && <LotteryTab game="totoloto" title="Totoloto" extraLabel="Nº de sorte" />}
        {active === "euromilhoes" && <LotteryTab game="euromilhoes" title="Euromilhões" extraLabel="Estrelas" />}
        {active === "eurodreams" && <LotteryTab game="eurodreams" title="EuroDreams" extraLabel="Dream number" />}
      </main>

      <SupportFooter />
    </div>
  );
}

export default App;
