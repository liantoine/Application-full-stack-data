from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, SmallInteger, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Avis(Base):
    __tablename__ = "avis"
    __table_args__ = (
        # Un seul avis par réservation : garanti ici même si deux requêtes arrivent ensemble
        UniqueConstraint("reservation_id", name="avis_reservation_unique"),
        CheckConstraint("note BETWEEN 1 AND 5", name="avis_note_bornes"),
        CheckConstraint("char_length(commentaire) <= 1000", name="avis_commentaire_longueur"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Ni auteur ni item ici : on les retrouve par la réservation, pas de copie qui pourrait diverger.
    # "Réservation terminée" ne peut pas être un CHECK (autre table) : vérifié dans AvisService.
    reservation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("reservations.id", ondelete="CASCADE"), nullable=False
    )
    note: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    commentaire: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    reservation: Mapped["Reservation"] = relationship(back_populates="avis")
