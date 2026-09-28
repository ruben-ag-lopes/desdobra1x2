import os

FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"

# AI-written summary of a desdobramento (docs/plano-resumo-ia.md). Optional: the feature is
# simply unavailable (not an error) when this is unset.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_BASKETBALL_KEY = os.environ.get("API_BASKETBALL", "") or API_FOOTBALL_KEY
API_HANDBALL_KEY = os.environ.get("API_HANDBALL", "") or API_FOOTBALL_KEY
