from typing import Any

from app.core.exceptions import RessourceIntrouvable
from app.models.item import Item
from app.repositories.item import ItemRepository
from app.repositories.user import UserRepository


class ItemService:
    def __init__(self, items: ItemRepository, users: UserRepository) -> None:
        self.items = items
        self.users = users

    def lister(self, **filtres: Any) -> list[Item]:
        return self.items.list(**filtres)

    def obtenir(self, item_id: int) -> Item:
        item = self.items.get(item_id)
        if item is None:
            raise RessourceIntrouvable(f"Item {item_id} introuvable")
        return item

    def creer(self, data: dict[str, Any]) -> Item:
        # Vérifié ici plutôt que de laisser la FK lever une IntegrityError (500)
        if self.users.get(data["owner_id"]) is None:
            raise RessourceIntrouvable(f"Utilisateur {data['owner_id']} introuvable")
        return self.items.add(Item(**data))

    def modifier(self, item_id: int, changements: dict[str, Any]) -> Item:
        item = self.obtenir(item_id)
        for champ, valeur in changements.items():
            setattr(item, champ, valeur)
        return self.items.add(item)

    def supprimer(self, item_id: int) -> None:
        self.items.delete(self.obtenir(item_id))
