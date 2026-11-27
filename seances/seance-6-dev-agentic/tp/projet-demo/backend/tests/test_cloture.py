"""US-01 : le prêteur clôture un prêt (prérequis des avis).

Alice possède `item_velo`, Bob l'emprunte (`reservation_bob`), Carol n'a rien à voir.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Reservation

TERMINER = {"statut": "terminee"}


def test_ac_01_1_le_proprietaire_cloture_une_reservation_active(
    client_alice: TestClient, reservation_bob: Reservation, db: Session
) -> None:
    response = client_alice.patch(f"/reservations/{reservation_bob.id}", json=TERMINER)

    assert response.status_code == 200
    assert response.json()["statut"] == "terminee"
    db.refresh(reservation_bob)
    assert reservation_bob.statut == "terminee"


def test_ac_01_2_cloture_sans_jeton_refusee(
    client: TestClient, reservation_bob: Reservation, db: Session
) -> None:
    response = client.patch(f"/reservations/{reservation_bob.id}", json=TERMINER)

    assert response.status_code == 401
    db.refresh(reservation_bob)
    assert reservation_bob.statut == "active"


@pytest.mark.parametrize("nom_client", ["client_bob", "client_carol"])
def test_ac_01_3_cloture_par_l_emprunteur_ou_un_tiers_refusee(
    request: pytest.FixtureRequest, nom_client: str, reservation_bob: Reservation, db: Session
) -> None:
    client: TestClient = request.getfixturevalue(nom_client)

    response = client.patch(f"/reservations/{reservation_bob.id}", json=TERMINER)

    assert response.status_code == 403
    db.refresh(reservation_bob)
    assert reservation_bob.statut == "active"


@pytest.mark.parametrize("statut", ["annulee", "terminee"])
def test_ac_01_4_cloture_d_une_reservation_pas_active_refusee(
    client_alice: TestClient, reservation_bob: Reservation, db: Session, statut: str
) -> None:
    reservation_bob.statut = statut
    db.flush()

    response = client_alice.patch(f"/reservations/{reservation_bob.id}", json=TERMINER)

    assert response.status_code == 409
    db.refresh(reservation_bob)
    assert reservation_bob.statut == statut


def test_ac_01_5_cloture_d_une_reservation_inexistante(client_alice: TestClient) -> None:
    response = client_alice.patch("/reservations/999999", json=TERMINER)

    assert response.status_code == 404


def test_statut_inconnu_refuse(client_alice: TestClient, reservation_bob: Reservation) -> None:
    response = client_alice.patch(f"/reservations/{reservation_bob.id}", json={"statut": "active"})

    assert response.status_code == 422
