from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier
from app.models.avis import Avis


class AvisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_par_reservation(self, reservation_id: int) -> Avis | None:
        return self.db.scalar(select(Avis).where(Avis.reservation_id == reservation_id))

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
