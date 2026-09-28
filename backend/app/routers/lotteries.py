from fastapi import APIRouter, HTTPException, Response

from app.cache import cdn_cache
from app.models import Draw, FrequenciaResponse, LotteryGenerateRequest, LotteryGenerateResponse, UltimoSorteio
from app.scrapers import santacasa_calendar, santacasa_results
from app.services import lottery_generator

router = APIRouter(prefix="/api/lotteries", tags=["lotteries"])

VALID_GAMES = {"totoloto", "euromilhoes", "eurodreams"}


@router.get("/{game}/draw", response_model=Draw | None)
def get_draw(game: str, response: Response):
    if game not in VALID_GAMES:
        raise HTTPException(status_code=404, detail=f"Unknown lottery game: {game}")
    try:
        draw = santacasa_calendar.get_lottery_draw(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game} draw: {e}") from e
    cdn_cache(response, 900)
    return draw


@router.get("/{game}/ultimo-sorteio", response_model=UltimoSorteio)
def get_ultimo_sorteio(game: str, response: Response):
    if game not in VALID_GAMES:
        raise HTTPException(status_code=404, detail=f"Unknown lottery game: {game}")
    try:
        result = santacasa_results.get_ultimo_sorteio(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game}'s last draw: {e}") from e
    cdn_cache(response, 12 * 3600)
    return result


@router.get("/{game}/frequencia", response_model=FrequenciaResponse)
def get_frequencia(game: str, response: Response):
    if game not in VALID_GAMES:
        raise HTTPException(status_code=404, detail=f"Unknown lottery game: {game}")
    try:
        result = santacasa_results.get_frequencia(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game}'s number frequency: {e}") from e
    cdn_cache(response, 12 * 3600)
    return result


@router.post("/{game}/generate", response_model=LotteryGenerateResponse)
def generate(game: str, req: LotteryGenerateRequest):
    if game not in VALID_GAMES:
        raise HTTPException(status_code=404, detail=f"Unknown lottery game: {game}")
    if req.count < 1 or req.count > 20:
        raise HTTPException(status_code=400, detail="count must be between 1 and 20")

    tickets = lottery_generator.generate_tickets(game, req.count)
    return LotteryGenerateResponse(tickets=tickets)
