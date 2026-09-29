from fastapi import APIRouter, HTTPException, Request

from app.models import SuggestionRequest
from app.rate_limit import limiter
from app.services import feedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("")
@limiter.limit("5/minute")
def submit(request: Request, req: SuggestionRequest) -> dict:
    if req.empresa:
        # Honeypot tripped: pretend success so the bot doesn't learn it was caught, but save nothing.
        return {"status": "ok"}
    try:
        feedback.save_suggestion(req.mensagem, req.contacto)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to save suggestion: {e}") from e
    return {"status": "ok"}
