import { SuggestionForm } from "./SuggestionForm";

// Set in frontend/.env.local (see .env.example). Until then it points to the service's home page.
const BUY_ME_A_COFFEE_URL = import.meta.env.VITE_BUYMEACOFFEE_URL ?? "https://www.buymeacoffee.com/";

export function SupportFooter() {
  return (
    <footer className="site-footer">
      <p className="hint">
        Ferramenta gratuita e independente. Joga com responsabilidade — maiores de 18 anos. ·{" "}
        <a href="/termos.html">Termos</a> · <a href="/privacidade.html">Privacidade</a> · <SuggestionForm />
      </p>
      <a className="support-button" href={BUY_ME_A_COFFEE_URL} target="_blank" rel="noopener noreferrer">
        ☕ Apoiar o projeto
      </a>
    </footer>
  );
}
