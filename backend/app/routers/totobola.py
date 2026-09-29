from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response

from app.cache import cdn_cache
from app.models import (
    DesdobramentoRequest,
    DesdobramentoResponse,
    Draw,
    FixtureInfo,
    ModelCriteria,
    ResumoRequest,
    ResumoResponse,
)
from app.rate_limit import limiter
from app.scrapers import santacasa_calendar
from app.services import criteria, resumo_ia, totobola_engine
from app.storage import bigquery

router = APIRouter(prefix="/api/totobola", tags=["totobola"])


@router.get("/draws", response_model=list[Draw])
def get_draws(response: Response):
    try:
        draws = santacasa_calendar.get_totobola_draws()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Totobola calendar: {e}") from e
    cdn_cache(response, 900)
    return draws


@router.get("/draws/{contest_id}/matches", response_model=list[FixtureInfo])
def get_matches(contest_id: str, response: Response):
    try:
        fixtures = santacasa_calendar.get_contest_matches(contest_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch contest matches: {e}") from e
    cdn_cache(response, 900)
    return fixtures


@router.post("/desdobramento", response_model=DesdobramentoResponse)
@limiter.limit("20/minute")
def desdobramento(request: Request, req: DesdobramentoRequest, background: BackgroundTasks):
    if not req.matches:
        raise HTTPException(status_code=400, detail="No matches provided")

    probabilities, apostas = totobola_engine.gerar_desdobramento(
        req.matches, req.n_apostas, req.multiplicadores, req.pesos_antigos, req.bonus_casa
    )
    background.add_task(bigquery.log_predictions, probabilities, req.concurso, req.data_sorteio)
    return DesdobramentoResponse(probabilities=probabilities, apostas=apostas)


@router.get("/resumo-disponivel")
def resumo_disponivel() -> dict:
    return {"disponivel": resumo_ia.enabled()}


@router.post("/resumo", response_model=ResumoResponse)
@limiter.limit("5/minute")
def resumo(request: Request, req: ResumoRequest):
    """AI-written explanation of an already-computed desdobramento (docs/plano-resumo-ia.md)."""
    if not resumo_ia.enabled():
        return ResumoResponse(disponivel=False)
    try:
        texto = resumo_ia.summarize(req.probabilities, req.n_apostas)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to generate summary: {e}") from e
    return ResumoResponse(disponivel=True, resumo=texto)


@router.get("/criterios", response_model=list[ModelCriteria])
def get_criterios(
    response: Response,
    modelos: str | None = Query(None, description="comma-separated model ids; default: all"),
):
    """Criteria and weights of the prediction models (for the app's pop-up)."""
    versions = [m.strip() for m in modelos.split(",") if m.strip()] if modelos else criteria.ALL_MODELS
    described = criteria.describe(versions)
    cdn_cache(response, 3600)
    return described
