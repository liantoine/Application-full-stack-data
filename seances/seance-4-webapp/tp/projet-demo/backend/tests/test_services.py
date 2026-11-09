"""Règles de propriété testées directement sur les services, sans HTTP."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse
from app.models import Item, Reservation, User
from app.repositories.item import ItemRepository
from app.repositories.reservation import ReservationRepository
from app.services.item import ItemService
from app.services.reservation import ReservationService


@pytest.fixture
def item_service(db: Session) -> ItemService:
    return ItemService(ItemRepository(db))


@pytest.fixture
def reservation_service(db: Session) -> ReservationService:
    return ReservationService(ReservationRepository(db), ItemRepository(db))


def test_supprimer_l_item_d_un_autre_leve_acces_refuse(
    item_service: ItemService, item_velo: Item, bob: User, db: Session
) -> None:
    with pytest.raises(AccesRefuse):
        item_service.supprimer(item_velo.id, current_user_id=bob.id)

    assert db.get(Item, item_velo.id) is not None


def test_annuler_la_reservation_d_un_autre_leve_acces_refuse(
    reservation_service: ReservationService, reservation_bob: Reservation, carol: User
) -> None:
    with pytest.raises(AccesRefuse):
        reservation_service.annuler(reservation_bob.id, current_user_id=carol.id)

    assert reservation_bob.statut == "active"
