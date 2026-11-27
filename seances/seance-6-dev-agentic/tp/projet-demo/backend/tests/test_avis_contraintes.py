"""Contraintes de la table avis, vérifiées directement en base (sans passer par l'API).

Si le service oublie un contrôle, la base refuse quand même. begin_nested : l'erreur
n'annule que le SAVEPOINT, pas la transaction du test.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Avis, Item, Reservation


@pytest.mark.parametrize("note", [0, 6])
def test_contrainte_note_hors_bornes_refusee_en_base(
    db: Session, pret_termine: Reservation, note: int
) -> None:
    with pytest.raises(IntegrityError, match="avis_note_bornes"), db.begin_nested():
        db.add(Avis(reservation_id=pret_termine.id, note=note))


def test_contrainte_un_seul_avis_par_reservation_en_base(db: Session, pret_termine: Reservation) -> None:
    db.add(Avis(reservation_id=pret_termine.id, note=4))
    db.flush()

    with pytest.raises(IntegrityError, match="avis_reservation_unique"), db.begin_nested():
        db.add(Avis(reservation_id=pret_termine.id, note=2))

    assert db.query(Avis).one().note == 4


def test_contrainte_commentaire_trop_long_refuse_en_base(db: Session, pret_termine: Reservation) -> None:
    with pytest.raises(IntegrityError, match="avis_commentaire_longueur"), db.begin_nested():
        db.add(Avis(reservation_id=pret_termine.id, note=4, commentaire="x" * 1001))


def test_supprimer_un_item_supprime_ses_avis(
    client_alice: TestClient, db: Session, item_velo: Item, pret_termine: Reservation
) -> None:
    db.add(Avis(reservation_id=pret_termine.id, note=4))
    db.flush()

    response = client_alice.delete(f"/items/{item_velo.id}")

    assert response.status_code == 204
    assert db.query(Avis).count() == 0
