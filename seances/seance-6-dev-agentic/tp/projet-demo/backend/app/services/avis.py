from app.core.exceptions import AccesRefuse, ConflitMetier, RessourceIntrouvable
from app.models.avis import Avis
from app.repositories.avis import AvisRepository
from app.repositories.reservation import ReservationRepository


class AvisService:
    def __init__(self, avis: AvisRepository, reservations: ReservationRepository) -> None:
        self.avis = avis
        self.reservations = reservations

    def creer(
        self, reservation_id: int, *, current_user_id: int, note: int, commentaire: str | None
    ) -> Avis:
        reservation = self.reservations.get(reservation_id)
        if reservation is None:
            raise RessourceIntrouvable(f"Réservation {reservation_id} introuvable")
        # Le prêteur ne peut pas se noter lui-même : seul l'emprunteur donne un avis
        if reservation.borrower_id != current_user_id:
            raise AccesRefuse("Seul l'emprunteur peut laisser un avis sur ce prêt")
        if reservation.statut != "terminee":
            raise ConflitMetier("Ce prêt n'est pas terminé : l'avis n'est possible qu'après la clôture")
        # Contrôle pour le message ; le UNIQUE en base couvre les envois simultanés
        if self.avis.get_par_reservation(reservation_id) is not None:
            raise ConflitMetier("Un avis a déjà été laissé sur ce prêt")
        return self.avis.add(Avis(reservation_id=reservation_id, note=note, commentaire=commentaire))
