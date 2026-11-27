from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("date_fin > date_debut", name="reservations_dates_check"),
        CheckConstraint(
            "statut IN ('active', 'annulee', 'terminee')", name="reservations_statut_check"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Pas de ondelete, comme en séance 3 : on ne supprime pas un user qui a emprunté
    borrower_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    date_debut: Mapped[date] = mapped_column(Date, nullable=False)
    date_fin: Mapped[date] = mapped_column(Date, nullable=False)
    statut: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )

    item: Mapped["Item"] = relationship(back_populates="reservations")
    borrower: Mapped["User"] = relationship(back_populates="reservations")
