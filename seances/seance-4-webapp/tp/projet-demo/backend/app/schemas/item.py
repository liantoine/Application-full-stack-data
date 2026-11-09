from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import OwnerRead


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_id: int = Field(ge=1)  # TODO séance 5 : déduit du jeton
    titre: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    tarif_jour: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    disponible: bool = True


class ItemUpdate(BaseModel):
    """Schéma du PATCH : tous les champs sont optionnels."""

    model_config = ConfigDict(extra="forbid")

    titre: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    tarif_jour: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    disponible: bool | None = None

    @field_validator("titre", "tarif_jour", "disponible")
    @classmethod
    def refuser_null(cls, value: Any) -> Any:
        # Un null explicite écraserait une colonne NOT NULL
        if value is None:
            raise ValueError("ce champ ne peut pas être null")
        return value


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    titre: str
    description: str | None
    tarif_jour: Decimal
    disponible: bool
    owner: OwnerRead
