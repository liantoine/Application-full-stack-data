from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflitMetier
from app.models.avis import Avis
from app.models.reservation import Reservation


class AvisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_par_reservation(self, reservation_id: int) -> Avis | None:
        return self.db.scalar(select(Avis).where(Avis.reservation_id == reservation_id))

    def resume(self, item_id: int) -> tuple[int, Decimal | None]:
        # Calculé à la lecture (décision de la fiche) : une seule requête d'agrégat
        stmt = (
            select(func.count(Avis.id), func.avg(Avis.note))
            .join(Avis.reservation)
            .where(Reservation.item_id == item_id)
        )
        nombre, moyenne = self.db.execute(stmt).one()
        return nombre, moyenne

    def list_par_item(self, item_id: int) -> list[Avis]:
        # selectinload : réservations et auteurs chargés en deux requêtes, pas une par avis
        stmt = (
            select(Avis)
            .join(Avis.reservation)
            .where(Reservation.item_id == item_id)
            .options(selectinload(Avis.reservation).selectinload(Reservation.borrower))
            .order_by(Avis.created_at.desc(), Avis.id.desc())
        )
        return list(self.db.scalars(stmt))

    def add(self, avis: Avis) -> Avis:
        # SAVEPOINT : si le UNIQUE refuse (deux envois simultanés), seule cette insertion est annulée
        try:
            with self.db.begin_nested():
                self.db.add(avis)
        except IntegrityError as exc:
            if "avis_reservation_unique" in str(exc.orig):
                raise ConflitMetier("Un avis a déjà été laissé sur ce prêt") from exc
            raise
        self.db.refresh(avis)
        return avis
