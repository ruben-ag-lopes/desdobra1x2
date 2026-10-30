from fastapi import APIRouter, HTTPException, Response

from app.cache import cdn_cache
from app.models import (
    ConferirBilheteRequest,
    ConferirCodigoRequest,
    ConferirCodigoResponse,
    SugestaoCodigoResponse,
    UltimoCodigo,
    ConferirBilheteResponse,
    ConferirRequest,
    ConferirResponse,
    Draw,
    FrequenciaResponse,
    LotteryGenerateRequest,
    LotteryGenerateResponse,
    SugestaoBilheteResponse,
    UltimoBilhete,
    UltimoSorteio,
)
from app.scrapers import santacasa_calendar, santacasa_results
from app.services import bilhete, codigo, conferencia, lottery_generator

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


@router.post("/{game}/conferir", response_model=ConferirResponse)
def conferir(game: str, req: ConferirRequest):
    if game not in VALID_GAMES:
        raise HTTPException(status_code=404, detail=f"Unknown lottery game: {game}")
    try:
        numeros, numeros_extra = conferencia.parse_aposta(game, req.aposta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        sorteio = santacasa_results.get_ultimo_sorteio(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game}'s last draw: {e}") from e
    return conferencia.conferir(game, sorteio, numeros, numeros_extra)


def _check_bilhete_game(game: str) -> None:
    if game not in bilhete.BILHETE_GAMES:
        raise HTTPException(status_code=404, detail=f"Unknown ticket game: {game}")


@router.get("/{game}/ultimo-bilhete", response_model=UltimoBilhete)
def get_ultimo_bilhete(game: str, response: Response):
    _check_bilhete_game(game)
    try:
        result = santacasa_results.get_ultimo_bilhete(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game}'s last draw: {e}") from e
    cdn_cache(response, 12 * 3600)
    return result


@router.post("/{game}/conferir-bilhete", response_model=ConferirBilheteResponse)
def conferir_bilhete(game: str, req: ConferirBilheteRequest):
    _check_bilhete_game(game)
    try:
        numero = bilhete.parse_bilhete(req.bilhete)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        sorteio = santacasa_results.get_ultimo_bilhete(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game}'s last draw: {e}") from e
    return bilhete.conferir_bilhete(sorteio, numero)


@router.post("/{game}/sugerir-bilhete", response_model=SugestaoBilheteResponse)
def sugerir_bilhete(game: str):
    _check_bilhete_game(game)
    return bilhete.sugerir_bilhete()


def _check_codigo_game(game: str) -> None:
    if game not in codigo.CODIGO_GAMES:
        raise HTTPException(status_code=404, detail=f"Unknown code game: {game}")


@router.get("/{game}/ultimo-codigo", response_model=UltimoCodigo)
def get_ultimo_codigo(game: str, response: Response):
    _check_codigo_game(game)
    try:
        result = santacasa_results.get_ultimo_codigo(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game}'s last draw: {e}") from e
    cdn_cache(response, 12 * 3600)
    return result


@router.post("/{game}/conferir-codigo", response_model=ConferirCodigoResponse)
def conferir_codigo(game: str, req: ConferirCodigoRequest):
    _check_codigo_game(game)
    try:
        valor = codigo.parse_codigo(req.codigo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        sorteio = santacasa_results.get_ultimo_codigo(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game}'s last draw: {e}") from e
    return codigo.conferir_codigo(sorteio, valor)


@router.post("/{game}/sugerir-codigo", response_model=SugestaoCodigoResponse)
def sugerir_codigo(game: str):
    _check_codigo_game(game)
    return codigo.sugerir_codigo()
