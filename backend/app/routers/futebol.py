from fastapi import APIRouter, HTTPException, Query, Response

from app.cache import cdn_cache
from app.models import Competition, FootballGame
from app.services import futebol

router = APIRouter(prefix="/api/futebol", tags=["futebol"])


@router.get("/competicoes", response_model=list[Competition])
def get_competicoes(response: Response):
    try:
        result = futebol.competitions()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch upcoming games: {e}") from e
    cdn_cache(response, 900)
    return result


@router.get("/jogos", response_model=list[FootballGame])
def get_jogos(
    response: Response,
    competicao: str | None = Query(None, description="league code, e.g. P1"),
    q: str | None = Query(None, max_length=60, description="team or competition name"),
    dias: int | None = Query(None, ge=1, le=14, description="only games in the next N days"),
):
    # Each league needs its model trained: without a filter a request could train all of them at once.
    if not competicao and not (q and q.strip()):
        raise HTTPException(status_code=422, detail="Choose a competition or search for a team")
    try:
        result = futebol.games(competicao, q, dias)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch upcoming games: {e}") from e
    cdn_cache(response, 900)
    return result
