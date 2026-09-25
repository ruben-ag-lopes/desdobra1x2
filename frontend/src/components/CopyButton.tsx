import { useState } from "react";

interface Props {
  text: string;
  label: string;
  disabled?: boolean;
}

async function copyToClipboard(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // Clipboard API unavailable (e.g. non-secure context): fall back to a temporary textarea.
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
}

export function CopyButton({ text, label, disabled }: Props) {
  const [copied, setCopied] = useState(false);

  async function handleClick() {
    await copyToClipboard(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <button onClick={handleClick} disabled={disabled}>
      {copied ? "Copiado ✓" : label}
    </button>
  );
}
