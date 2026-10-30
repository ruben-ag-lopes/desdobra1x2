export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-PT");
}

// The API errors look like "400: {"detail":"..."}": show only the message.
export function mensagemErro(e: unknown): string {
  const texto = String(e).replace(/^\d+: /, "");
  try {
    return JSON.parse(texto).detail ?? texto;
  } catch {
    return texto;
  }
}
