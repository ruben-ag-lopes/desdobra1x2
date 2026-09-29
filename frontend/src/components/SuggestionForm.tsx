import { useRef, useState } from "react";
import { postFeedback } from "../api/client";

export function SuggestionForm() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [mensagem, setMensagem] = useState("");
  const [contacto, setContacto] = useState("");
  const [empresa, setEmpresa] = useState(""); // honeypot: hidden from people, bots tend to fill it in
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function open() {
    setSent(false);
    setError(null);
    dialogRef.current?.showModal();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!mensagem.trim()) return;
    setSending(true);
    setError(null);
    try {
      await postFeedback(mensagem, contacto, empresa);
      setSent(true);
      setMensagem("");
      setContacto("");
      setEmpresa("");
    } catch (e) {
      setError(String(e));
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <button className="link-button suggestion-link" onClick={open}>
        💬 Sugestões
      </button>
      <dialog
        ref={dialogRef}
        className="suggestion-dialog"
        onClick={(e) => e.target === dialogRef.current && dialogRef.current?.close()}
      >
        <header>
          <h3>Tens uma sugestão?</h3>
          <button aria-label="Fechar" onClick={() => dialogRef.current?.close()}>
            ✕
          </button>
        </header>

        {sent ? (
          <p>Obrigado! A tua sugestão foi enviada.</p>
        ) : (
          <form onSubmit={handleSubmit}>
            {/* Honeypot: invisible to people, tabIndex -1 keeps keyboard users away from it too. */}
            <input
              type="text"
              name="empresa"
              value={empresa}
              onChange={(e) => setEmpresa(e.target.value)}
              className="honeypot"
              tabIndex={-1}
              autoComplete="off"
              aria-hidden="true"
            />
            <label htmlFor="suggestion-mensagem">A tua ideia, crítica ou problema encontrado</label>
            <textarea
              id="suggestion-mensagem"
              rows={5}
              maxLength={2000}
              value={mensagem}
              onChange={(e) => setMensagem(e.target.value)}
              required
            />
            <label htmlFor="suggestion-contacto">O teu e-mail (opcional, para te responder)</label>
            <input
              id="suggestion-contacto"
              type="email"
              value={contacto}
              onChange={(e) => setContacto(e.target.value)}
            />
            {error && <p className="error">{error}</p>}
            <div className="controls">
              <button type="submit" disabled={sending || !mensagem.trim()}>
                {sending ? "A enviar..." : "Enviar"}
              </button>
            </div>
          </form>
        )}
      </dialog>
    </>
  );
}
