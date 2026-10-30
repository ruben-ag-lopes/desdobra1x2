from fastapi import APIRouter, HTTPException, Response

from app.cache import cdn_cache
from app.models import (
    ConferirBilheteRequest,
    ConferirBilheteResponse,
    ConferirCodigoRequest,
    ConferirCodigoResponse,
    ConferirRequest,
    ConferirResponse,
    Draw,
    FrequenciaResponse,
    LotteryGenerateRequest,
    LotteryGenerateResponse,
    SugestaoBilheteResponse,
    UltimoBilhete,
    UltimoCodigo,
    UltimoSorteio,
)
from app.scrapers import santacasa_calendar, santacasa_results
from app.services import bilhete, codigo, conferencia, lottery_generator

router = APIRouter(prefix="/api/lotteries", tags=["lotteries"])

VALID_GAMES = {"totoloto", "euromilhoes", "eurodreams"}


def _check_game(game: str, allowed: set[str]) -> None:
    if game not in allowed:
        raise HTTPException(status_code=404, detail=f"Unknown lottery game: {game}")


def _fetch(fetch, game: str, what: str = "last draw"):
    """Run a scraper call; a failure of the Santa Casa site becomes a 502."""
    try:
        return fetch(game)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {game}'s {what}: {e}") from e


def _parse(parse, *args):
    """Run an input parser; a bad value from the visitor becomes a 400."""
    try:
        return parse(*args)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{game}/draw", response_model=Draw | None)
def get_draw(game: str, response: Response):
    _check_game(game, VALID_GAMES)
    draw = _fetch(santacasa_calendar.get_lottery_draw, game, "draw")
    cdn_cache(response, 900)
    return draw


@router.get("/{game}/ultimo-sorteio", response_model=UltimoSorteio)
def get_ultimo_sorteio(game: str, response: Response):
    _check_game(game, VALID_GAMES)
    result = _fetch(santacasa_results.get_ultimo_sorteio, game)
    cdn_cache(response, 12 * 3600)
    return result


@router.get("/{game}/frequencia", response_model=FrequenciaResponse)
def get_frequencia(game: str, response: Response):
    _check_game(game, VALID_GAMES)
    result = _fetch(santacasa_results.get_frequencia, game, "number frequency")
    cdn_cache(response, 12 * 3600)
    return result


@router.post("/{game}/generate", response_model=LotteryGenerateResponse)
def generate(game: str, req: LotteryGenerateRequest):
    _check_game(game, VALID_GAMES)
    if req.count < 1 or req.count > 20:
        raise HTTPException(status_code=400, detail="count must be between 1 and 20")

    tickets = lottery_generator.generate_tickets(game, req.count)
    return LotteryGenerateResponse(tickets=tickets)


@router.post("/{game}/conferir", response_model=ConferirResponse)
def conferir(game: str, req: ConferirRequest):
    _check_game(game, VALID_GAMES)
    numeros, numeros_extra = _parse(conferencia.parse_aposta, game, req.aposta)
    sorteio = _fetch(santacasa_results.get_ultimo_sorteio, game)
    return conferencia.conferir(game, sorteio, numeros, numeros_extra)


@router.get("/{game}/ultimo-bilhete", response_model=UltimoBilhete)
def get_ultimo_bilhete(game: str, response: Response):
    _check_game(game, bilhete.BILHETE_GAMES)
    result = _fetch(santacasa_results.get_ultimo_bilhete, game)
    cdn_cache(response, 12 * 3600)
    return result


@router.post("/{game}/conferir-bilhete", response_model=ConferirBilheteResponse)
def conferir_bilhete(game: str, req: ConferirBilheteRequest):
    _check_game(game, bilhete.BILHETE_GAMES)
    numero = _parse(bilhete.parse_bilhete, req.bilhete)
    sorteio = _fetch(santacasa_results.get_ultimo_bilhete, game)
    return bilhete.conferir_bilhete(sorteio, numero)


@router.post("/{game}/sugerir-bilhete", response_model=SugestaoBilheteResponse)
def sugerir_bilhete(game: str):
    _check_game(game, bilhete.BILHETE_GAMES)
    return bilhete.sugerir_bilhete()


@router.get("/{game}/ultimo-codigo", response_model=UltimoCodigo)
def get_ultimo_codigo(game: str, response: Response):
    _check_game(game, codigo.CODIGO_GAMES)
    result = _fetch(santacasa_results.get_ultimo_codigo, game)
    cdn_cache(response, 12 * 3600)
    return result


@router.post("/{game}/conferir-codigo", response_model=ConferirCodigoResponse)
def conferir_codigo(game: str, req: ConferirCodigoRequest):
    _check_game(game, codigo.CODIGO_GAMES)
    valor = _parse(codigo.parse_codigo, req.codigo)
    sorteio = _fetch(santacasa_results.get_ultimo_codigo, game)
    return codigo.conferir_codigo(sorteio, valor)
