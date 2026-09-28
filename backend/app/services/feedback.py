"""User suggestions, appended as one JSON line per message.

Stored in DATA_DIR/sugestoes.jsonl. On Vercel that's /tmp, which is wiped between cold starts —
fine for a first version; move to the database (plano-base-de-dados.md) once that exists.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from app.research.data import CACHE_DIR

_FILE = CACHE_DIR / "sugestoes.jsonl"


def save_suggestion(mensagem: str, contacto: str | None) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "recebido_em": datetime.now(timezone.utc).isoformat(),
        "mensagem": mensagem,
        "contacto": contacto,
    }
    with open(_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_suggestions() -> list[dict]:
    """For your own use (not exposed over the API): read every stored suggestion."""
    if not Path(_FILE).exists():
        return []
    with open(_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
