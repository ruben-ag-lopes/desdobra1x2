from fastapi import APIRouter, HTTPException

from app.models import SuggestionRequest
from app.services import feedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("")
def submit(req: SuggestionRequest) -> dict:
    try:
        feedback.save_suggestion(req.mensagem, req.contacto)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to save suggestion: {e}") from e
    return {"status": "ok"}
