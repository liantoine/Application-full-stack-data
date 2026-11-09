from typing import Any

from app.core.exceptions import AccesRefuse, RessourceIntrouvable
from app.models.item import Item
from app.repositories.item import ItemRepository


class ItemService:
    def __init__(self, items: ItemRepository) -> None:
        self.items = items

    def lister(self, **filtres: Any) -> list[Item]:
        return self.items.list(**filtres)

    def obtenir(self, item_id: int) -> Item:
        item = self.items.get(item_id)
        if item is None:
            raise RessourceIntrouvable(f"Item {item_id} introuvable")
        return item

    def _obtenir_en_tant_que_proprietaire(self, item_id: int, current_user_id: int) -> Item:
        item = self.obtenir(item_id)
        if item.owner_id != current_user_id:
            raise AccesRefuse("Vous n'êtes pas le propriétaire de ce matériel")
        return item

    def creer(self, data: dict[str, Any], *, owner_id: int) -> Item:
        return self.items.add(Item(**data, owner_id=owner_id))

    def modifier(self, item_id: int, changements: dict[str, Any], *, current_user_id: int) -> Item:
        item = self._obtenir_en_tant_que_proprietaire(item_id, current_user_id)
        for champ, valeur in changements.items():
            setattr(item, champ, valeur)
        return self.items.add(item)

    def supprimer(self, item_id: int, *, current_user_id: int) -> None:
        self.items.delete(self._obtenir_en_tant_que_proprietaire(item_id, current_user_id))
