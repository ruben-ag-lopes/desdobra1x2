from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import TypeAdapter, ValidationError

from app.cache import cdn_cache
from app.models import Competition, CriterionId, FootballGame, Multiplier
from app.rate_limit import limiter
from app.services import futebol

router = APIRouter(prefix="/api/futebol", tags=["futebol"])

_MultiplicadoresAdapter = TypeAdapter(dict[CriterionId, Multiplier])


@router.get("/competicoes", response_model=list[Competition])
def get_competicoes(response: Response):
    try:
        result = futebol.competitions()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch upcoming games: {e}") from e
    cdn_cache(response, 900)
    return result


@router.get("/jogos", response_model=list[FootballGame])
@limiter.limit("20/minute")
def get_jogos(
    request: Request,
    response: Response,
    competicao: str | None = Query(None, description="league code, e.g. P1"),
    q: str | None = Query(None, max_length=60, description="team or competition name"),
    dias: int | None = Query(None, ge=1, le=14, description="only games in the next N days"),
    criterios: str | None = Query(None, description='JSON dict of criterion id -> multiplier, e.g. {"elo":1.5}'),
):
    # Each league needs its model trained: without a filter a request could train all of them at once.
    if not competicao and not (q and q.strip()):
        raise HTTPException(status_code=422, detail="Choose a competition or search for a team")
    multiplicadores = {}
    if criterios:
        try:
            multiplicadores = _MultiplicadoresAdapter.validate_json(criterios)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
    try:
        result = futebol.games(competicao, q, dias, multiplicadores)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch upcoming games: {e}") from e
    cdn_cache(response, 900)
    return result
