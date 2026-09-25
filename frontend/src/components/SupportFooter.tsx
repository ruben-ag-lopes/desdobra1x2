import { useState } from "react";

// Set in frontend/.env.local (see .env.example). Until then they point to the services' home pages.
const BUY_ME_A_COFFEE_URL = import.meta.env.VITE_BUYMEACOFFEE_URL ?? "https://www.buymeacoffee.com/";
const PAYPAL_URL = import.meta.env.VITE_PAYPAL_URL ?? "https://www.paypal.com/donate/";

export function SupportFooter() {
  const [open, setOpen] = useState(false);

  return (
    <footer className="site-footer">
      <p className="hint">Ferramenta gratuita e independente. Joga com responsabilidade — maiores de 18 anos.</p>
      <div className="support">
        <button className="support-button" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
          ☕ Apoiar o projeto
        </button>
        {open && (
          <div className="support-options">
            <a href={BUY_ME_A_COFFEE_URL} target="_blank" rel="noopener noreferrer">
              Buy Me a Coffee
            </a>
            <a href={PAYPAL_URL} target="_blank" rel="noopener noreferrer">
              PayPal
            </a>
          </div>
        )}
      </div>
    </footer>
  );
}
