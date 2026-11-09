import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query

from app.schemas.reservation import ReservationCreate, ReservationRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reservations", tags=["reservations"])

FAKE_DB: dict[int, dict[str, Any]] = {}


def _next_id() -> int:
    return max(FAKE_DB, default=0) + 1


def envoyer_notification_annulation(reservation_id: int) -> None:
    """Prévient l'emprunteur de l'annulation.

    Effet de bord externe (e-mail, plus tard) : simulé par un log pour l'instant,
    et remplacé par un `Mock` dans les tests.
    """
    logger.info("Notification d'annulation pour la réservation %s", reservation_id)


def _get_or_404(reservation_id: int) -> dict[str, Any]:
    reservation = FAKE_DB.get(reservation_id)
    if reservation is None:
        raise HTTPException(
            status_code=404, detail=f"Réservation {reservation_id} introuvable"
        )
    return reservation


@router.post("", response_model=ReservationRead, status_code=201)
def create_reservation(payload: ReservationCreate) -> dict[str, Any]:
    reservation = {"id": _next_id(), **payload.model_dump(), "statut": "active"}
    FAKE_DB[reservation["id"]] = reservation
    return reservation


@router.get("", response_model=list[ReservationRead])
def list_reservations(
    item_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, Any]]:
    reservations = list(FAKE_DB.values())
    if item_id is not None:
        reservations = [r for r in reservations if r["item_id"] == item_id]
    return reservations[:limit]


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_reservation(reservation_id: int = Path(ge=1)) -> dict[str, Any]:
    return _get_or_404(reservation_id)


@router.post("/{reservation_id}/annuler", response_model=ReservationRead)
def cancel_reservation(reservation_id: int = Path(ge=1)) -> dict[str, Any]:
    reservation = _get_or_404(reservation_id)
    if reservation["statut"] == "annulee":
        raise HTTPException(
            status_code=409, detail=f"Réservation {reservation_id} déjà annulée"
        )
    reservation["statut"] = "annulee"
    # Décision : l'annulation est acquise même si la notification ne part pas.
    try:
        envoyer_notification_annulation(reservation_id=reservation_id)
    except Exception:
        logger.exception("Échec de la notification d'annulation %s", reservation_id)
    return reservation
