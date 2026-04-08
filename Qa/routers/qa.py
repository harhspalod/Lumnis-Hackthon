# routers/qa.py
from fastapi import APIRouter, HTTPException
from models.schemas import IncomingSignal, SignalReport
from services.signal_router import route_signal

router = APIRouter()


@router.post(
    "/signal",
    response_model = SignalReport,
    summary        = "Receive a signal and auto-run targeted QA checks",
)
def receive_signal(signal: IncomingSignal) -> SignalReport:
    """
    Your review system posts here when it detects an issue.
    The signal router decides which checks to run and returns a full report.
    """
    try:
        return route_signal(signal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))