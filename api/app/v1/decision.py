from fastapi import APIRouter

from app.models.request import DecisionRequest
from ..models.response import DecisionResponse

router = APIRouter()

@router.post("/decision", response_model=DecisionResponse)
def make_decision(payload: DecisionRequest):

    results = []

    return {
        "ranking": results
    }