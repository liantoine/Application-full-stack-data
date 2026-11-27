from fastapi import APIRouter, Path, Query

from app.api.deps import CurrentUser, ReservationServiceDep
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreate, ReservationRead, ReservationUpdate

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=ReservationRead, status_code=201)
def create_reservation(
    payload: ReservationCreate, current_user: CurrentUser, service: ReservationServiceDep
) -> Reservation:
    # L'emprunteur vient du jeton, jamais du corps
    return service.creer(
        item_id=payload.item_id,
        borrower_id=current_user.id,
        debut=payload.date_debut,
        fin=payload.date_fin,
    )


@router.get("", response_model=list[ReservationRead])
def list_reservations(
    current_user: CurrentUser,
    service: ReservationServiceDep,
    item_id: int | None = Query(default=None, ge=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Reservation]:
    return service.lister(item_id=item_id, skip=skip, limit=limit)


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_reservation(
    current_user: CurrentUser, service: ReservationServiceDep, reservation_id: int = Path(ge=1)
) -> Reservation:
    return service.obtenir(reservation_id)


# Seul changement possible pour l'instant : statut -> "annulee"
@router.patch("/{reservation_id}", response_model=ReservationRead)
def update_reservation(
    payload: ReservationUpdate,
    current_user: CurrentUser,
    service: ReservationServiceDep,
    reservation_id: int = Path(ge=1),
) -> Reservation:
    return service.annuler(reservation_id, current_user_id=current_user.id)
