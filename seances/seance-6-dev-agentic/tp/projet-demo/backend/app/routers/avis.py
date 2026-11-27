from fastapi import APIRouter, Path

from app.api.deps import AvisServiceDep, CurrentUser
from app.models.avis import Avis
from app.schemas.avis import AvisCreate, AvisRead

router = APIRouter(tags=["avis"])


@router.post("/reservations/{reservation_id}/avis", response_model=AvisRead, status_code=201)
def create_avis(
    payload: AvisCreate,
    current_user: CurrentUser,
    service: AvisServiceDep,
    reservation_id: int = Path(ge=1),
) -> Avis:
    # L'auteur est l'utilisateur du jeton ; le service vérifie qu'il est l'emprunteur
    return service.creer(
        reservation_id,
        current_user_id=current_user.id,
        note=payload.note,
        commentaire=payload.commentaire,
    )
