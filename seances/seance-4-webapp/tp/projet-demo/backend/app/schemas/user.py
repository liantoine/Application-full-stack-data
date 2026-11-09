from pydantic import BaseModel, ConfigDict


class OwnerRead(BaseModel):
    """Vue publique d'un utilisateur dans une autre ressource : ni email ni password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
