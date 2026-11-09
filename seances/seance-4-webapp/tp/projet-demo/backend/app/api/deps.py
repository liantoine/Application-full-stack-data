from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.item import ItemRepository
from app.repositories.reservation import ReservationRepository
from app.repositories.user import UserRepository
from app.services.item import ItemService
from app.services.reservation import ReservationService


# Une requête HTTP = une transaction : commit si tout va bien, rollback sinon
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_item_service(db: DbSession) -> ItemService:
    return ItemService(ItemRepository(db), UserRepository(db))


ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


def get_reservation_service(db: DbSession) -> ReservationService:
    return ReservationService(ReservationRepository(db), ItemRepository(db), UserRepository(db))


ReservationServiceDep = Annotated[ReservationService, Depends(get_reservation_service)]
