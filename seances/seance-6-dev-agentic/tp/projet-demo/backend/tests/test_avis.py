"""US-02 (laisser un avis) et US-03 (voir la réputation d'une annonce).

Alice possède `item_velo`, Bob l'emprunte ; `pret_termine` = sa réservation clôturée par Alice.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier
from app.models import Avis, Reservation, User
from app.repositories.avis import AvisRepository


def _url(reservation: Reservation) -> str:
    return f"/reservations/{reservation.id}/avis"


def _nb_avis(db: Session) -> int:
    return db.query(Avis).count()


# --- US-02 : laisser un avis ---


def test_ac_02_1_l_emprunteur_laisse_un_avis_sur_un_pret_termine(
    client_bob: TestClient, pret_termine: Reservation, bob: User
) -> None:
    response = client_bob.post(_url(pret_termine), json={"note": 4, "commentaire": "Vélo impeccable"})

    assert response.status_code == 201
    avis = response.json()
    assert avis["reservation_id"] == pret_termine.id
    assert avis["note"] == 4
    assert avis["commentaire"] == "Vélo impeccable"
    assert avis["auteur"] == {"id": bob.id, "display_name": "Bob"}


def test_ac_02_2_avis_sans_commentaire_accepte(
    client_bob: TestClient, pret_termine: Reservation
) -> None:
    response = client_bob.post(_url(pret_termine), json={"note": 5})

    assert response.status_code == 201
    assert response.json()["commentaire"] is None


def test_ac_02_3_avis_sans_jeton_refuse(
    client: TestClient, pret_termine: Reservation, db: Session
) -> None:
    response = client.post(_url(pret_termine), json={"note": 4})

    assert response.status_code == 401
    assert _nb_avis(db) == 0


@pytest.mark.parametrize("nom_client", ["client_alice", "client_carol"])
def test_ac_02_4_avis_par_le_preteur_ou_un_tiers_refuse(
    request: pytest.FixtureRequest, nom_client: str, pret_termine: Reservation, db: Session
) -> None:
    client: TestClient = request.getfixturevalue(nom_client)

    response = client.post(_url(pret_termine), json={"note": 5})

    assert response.status_code == 403
    assert _nb_avis(db) == 0


@pytest.mark.parametrize("statut", ["active", "annulee"])
def test_ac_02_5_avis_sur_un_pret_non_termine_refuse(
    client_bob: TestClient, reservation_bob: Reservation, db: Session, statut: str
) -> None:
    reservation_bob.statut = statut
    db.flush()

    response = client_bob.post(_url(reservation_bob), json={"note": 4})

    assert response.status_code == 409
    assert _nb_avis(db) == 0


def test_ac_02_6_un_second_avis_est_refuse(
    client_bob: TestClient, pret_termine: Reservation, db: Session
) -> None:
    premier = client_bob.post(_url(pret_termine), json={"note": 4, "commentaire": "Bien"})

    second = client_bob.post(_url(pret_termine), json={"note": 1, "commentaire": "Finalement non"})

    assert premier.status_code == 201
    assert second.status_code == 409
    avis = db.query(Avis).one()
    assert (avis.note, avis.commentaire) == (4, "Bien")


def test_ac_02_6_doublon_simultane_bloque_par_la_base(
    db: Session, pret_termine: Reservation, bob: User
) -> None:
    # Deux requêtes passent le contrôle du service en même temps : c'est le UNIQUE qui tranche.
    # Simulé en insérant l'avis "concurrent" juste avant l'écriture du repository.
    db.add(Avis(reservation_id=pret_termine.id, note=3))
    db.flush()

    with pytest.raises(ConflitMetier):
        AvisRepository(db).add(Avis(reservation_id=pret_termine.id, note=5))

    assert db.query(Avis).one().note == 3


@pytest.mark.parametrize("note", [0, 6, 3.5, "4", True])
def test_ac_02_7_note_hors_bornes_refusee(
    client_bob: TestClient, pret_termine: Reservation, db: Session, note: object
) -> None:
    response = client_bob.post(_url(pret_termine), json={"note": note})

    assert response.status_code == 422
    assert _nb_avis(db) == 0


def test_ac_02_8_commentaire_trop_long_refuse(
    client_bob: TestClient, pret_termine: Reservation, db: Session
) -> None:
    response = client_bob.post(_url(pret_termine), json={"note": 4, "commentaire": "x" * 1001})

    assert response.status_code == 422
    assert _nb_avis(db) == 0


def test_ac_02_9_avis_sur_une_reservation_inexistante(client_bob: TestClient, db: Session) -> None:
    response = client_bob.post("/reservations/999999/avis", json={"note": 4})

    assert response.status_code == 404
    assert _nb_avis(db) == 0


def test_auteur_dans_le_corps_refuse(
    client_bob: TestClient, pret_termine: Reservation, alice: User, db: Session
) -> None:
    response = client_bob.post(_url(pret_termine), json={"note": 5, "auteur_id": alice.id})

    assert response.status_code == 422
    assert _nb_avis(db) == 0
