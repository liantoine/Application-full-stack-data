from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    tarif_jour: float = Field(gt=0)
    disponible: bool = True


class ItemUpdate(BaseModel):
    """Schéma du PATCH : tous les champs sont optionnels."""

    model_config = ConfigDict(extra="forbid")

    titre: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    tarif_jour: float | None = Field(default=None, gt=0)
    disponible: bool | None = None

    @field_validator("titre", "tarif_jour", "disponible")
    @classmethod
    def refuser_null(cls, value: Any) -> Any:
        # Un champ absent est ignoré (exclude_unset), mais un `null` explicite
        # écraserait un champ obligatoire et casserait ItemRead (500).
        if value is None:
            raise ValueError("ce champ ne peut pas être null")
        return value


class ItemRead(BaseModel):
    id: int
    titre: str
    description: str | None
    tarif_jour: float
    disponible: bool
