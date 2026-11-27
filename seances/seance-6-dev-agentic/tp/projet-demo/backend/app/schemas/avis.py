from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import OwnerRead


class AvisCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # strict : refuse 3.5, "4" et true, pas seulement les valeurs hors bornes
    note: int = Field(ge=1, le=5, strict=True)
    commentaire: str | None = Field(default=None, max_length=1000)


class AvisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reservation_id: int
    note: int
    commentaire: str | None
    auteur: OwnerRead
    created_at: datetime


class ReputationRead(BaseModel):
    item_id: int
    nombre_avis: int
    note_moyenne: float | None  # None sans avis : pas de 0/5 trompeur
    avis: list[AvisRead]
