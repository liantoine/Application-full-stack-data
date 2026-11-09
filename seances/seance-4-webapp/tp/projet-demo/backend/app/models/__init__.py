# Alembic ne voit que les tables dont le modèle est importé : ne pas retirer ces imports
from app.models.base import Base
from app.models.item import Item
from app.models.reservation import Reservation
from app.models.user import User

__all__ = ["Base", "Item", "Reservation", "User"]
