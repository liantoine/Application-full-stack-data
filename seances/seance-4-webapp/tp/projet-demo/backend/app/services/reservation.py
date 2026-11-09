from datetime import date

from app.core.exceptions import ConflitMetier, RessourceIntrouvable
from app.models.reservation import Reservation
from app.repositories.item import ItemRepository
from app.repositories.reservation import ReservationRepository
from app.repositories.user import UserRepository


class ReservationService:
    def __init__(
        self, reservations: ReservationRepository, items: ItemRepository, users: UserRepository
    ) -> None:
        self.reservations = reservations
        self.items = items
        self.users = users

    def lister(self, *, item_id: int | None = None, skip: int = 0, limit: int = 20) -> list[Reservation]:
        return self.reservations.list(item_id=item_id, skip=skip, limit=limit)

    def obtenir(self, reservation_id: int) -> Reservation:
        reservation = self.reservations.get(reservation_id)
        if reservation is None:
            raise RessourceIntrouvable(f"Réservation {reservation_id} introuvable")
        return reservation

    def creer(self, *, item_id: int, borrower_id: int, debut: date, fin: date) -> Reservation:
        item = self.items.get(item_id)
        if item is None:
            raise RessourceIntrouvable(f"Item {item_id} introuvable")
        if self.users.get(borrower_id) is None:
            raise RessourceIntrouvable(f"Utilisateur {borrower_id} introuvable")
        if not item.disponible:
            raise ConflitMetier("Ce matériel n'est pas disponible")
        if self.reservations.find_chevauchements(item_id, debut, fin):
            raise ConflitMetier("Ce créneau est déjà réservé")
        return self.reservations.add(
            Reservation(item_id=item_id, borrower_id=borrower_id,
                        date_debut=debut, date_fin=fin, statut="active")
        )

    def annuler(self, reservation_id: int) -> Reservation:
        reservation = self.obtenir(reservation_id)
        if reservation.statut != "active":
            raise ConflitMetier(f"Réservation {reservation_id} déjà {reservation.statut}")
        reservation.statut = "annulee"
        return self.reservations.add(reservation)
