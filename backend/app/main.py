# ---------------------------------------------------------------------------
# Workaround: platform.machine() hangs on Windows when WMI is unresponsive.
# SQLAlchemy calls it at import time (util/compat.py:51). Cache the result
# eagerly using os.environ so the WMI code-path is never reached.
# ---------------------------------------------------------------------------
import os
import platform

if not os.environ.get("PROCESSOR_ARCHITECTURE"):
    # Fallback: if the env var is somehow missing, try the slow path once
    pass
else:
    _cached_machine = os.environ.get("PROCESSOR_ARCHITECTURE", "AMD64")
    platform.machine = lambda: _cached_machine  # type: ignore[assignment]

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import auth, friends, game_edits, game_invitations, games, history, ledger, notifications, settlement, social, users, ws
from app.core.config import settings
from app.services.game_lifecycle_service import MissingFinalStacksError

app = FastAPI(
    title="Poker Night Ledger",
    version="0.1.0",
    debug=settings.debug,
)

_allowed_origins = [
    o.strip() for o in settings.allowed_origins.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(friends.router)
app.include_router(games.router)
app.include_router(game_edits.router)
app.include_router(game_invitations.router)
app.include_router(ledger.router)
app.include_router(settlement.router)
app.include_router(history.router)
app.include_router(notifications.router)
app.include_router(social.router)
app.include_router(ws.router)


@app.exception_handler(MissingFinalStacksError)
async def _missing_final_stacks_handler(
    request: Request, exc: MissingFinalStacksError
) -> JSONResponse:
    """Produce a structured 400 response for missing final stacks.

    Response shape (matches original JSONResponse contract):
        {
            "detail": "Cannot close game: missing final chip counts",
            "missing_final_stacks": [
                {"participant_id": "uuid", "display_name": "Alice"}, ...
            ]
        }
    """
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Cannot close game: missing final chip counts",
            "missing_final_stacks": [
                {
                    "participant_id": str(m.participant_id),
                    "display_name": m.display_name,
                }
                for m in exc.missing
            ],
        },
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
