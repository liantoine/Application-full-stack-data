"""Matrice d'autorisation : pour chaque route, anonyme / propriétaire / autre utilisateur.

Alice possède `item_velo`, Bob l'emprunte (`reservation_bob`), Carol n'a rien à voir.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Item, Reservation, User

NOUVEL_ITEM = {"titre": "Tente 2 places", "tarif_jour": 12}
NOUVELLE_RESA = {"date_debut": "2026-10-01", "date_fin": "2026-10-03"}  # ne chevauche pas reservation_bob

MATRICE = [
    # (méthode, chemin, corps, client, code attendu)
    ("GET", "/items", None, "client", 200),
    ("GET", "/items", None, "client_alice", 200),
    ("GET", "/items", None, "client_bob", 200),
    ("GET", "/items/{item}", None, "client", 200),
    ("GET", "/items/{item}", None, "client_alice", 200),
    ("GET", "/items/{item}", None, "client_bob", 200),
    ("POST", "/items", NOUVEL_ITEM, "client", 401),
    ("POST", "/items", NOUVEL_ITEM, "client_alice", 201),
    ("POST", "/items", NOUVEL_ITEM, "client_bob", 201),
    ("PATCH", "/items/{item}", {"titre": "Vélo pliant"}, "client", 401),
    ("PATCH", "/items/{item}", {"titre": "Vélo pliant"}, "client_alice", 200),
    ("PATCH", "/items/{item}", {"titre": "Vélo pliant"}, "client_bob", 403),
    ("DELETE", "/items/{item}", None, "client", 401),
    ("DELETE", "/items/{item}", None, "client_alice", 204),
    ("DELETE", "/items/{item}", None, "client_bob", 403),
    ("POST", "/reservations", NOUVELLE_RESA, "client", 401),
    ("POST", "/reservations", NOUVELLE_RESA, "client_bob", 201),
    ("POST", "/reservations", NOUVELLE_RESA, "client_carol", 201),
    ("GET", "/reservations", None, "client", 401),
    ("GET", "/reservations", None, "client_bob", 200),
    ("GET", "/reservations", None, "client_carol", 200),
    ("GET", "/reservations/{resa}", None, "client", 401),
    ("GET", "/reservations/{resa}", None, "client_bob", 200),
    ("GET", "/reservations/{resa}", None, "client_carol", 200),
    # Annulation : emprunteur ou propriétaire de l'item, pas les autres
    ("PATCH", "/reservations/{resa}", {"statut": "annulee"}, "client", 401),
    ("PATCH", "/reservations/{resa}", {"statut": "annulee"}, "client_bob", 200),
    ("PATCH", "/reservations/{resa}", {"statut": "annulee"}, "client_alice", 200),
    ("PATCH", "/reservations/{resa}", {"statut": "annulee"}, "client_carol", 403),
    ("GET", "/auth/me", None, "client", 401),
    ("GET", "/auth/me", None, "client_alice", 200),
    ("GET", "/auth/me", None, "client_bob", 200),
]


@pytest.mark.parametrize(
    ("methode", "chemin", "corps", "nom_client", "attendu"),
    MATRICE,
    ids=[f"{m} {c} {n}" for m, c, _, n, _ in MATRICE],
)
def test_matrice_autorisation(
    request: pytest.FixtureRequest,
    item_velo: Item,
    reservation_bob: Reservation,
    client_carol: TestClient,
    methode: str,
    chemin: str,
    corps: dict | None,
    nom_client: str,
    attendu: int,
) -> None:
    client: TestClient = request.getfixturevalue(nom_client)
    url = chemin.format(item=item_velo.id, resa=reservation_bob.id)
    if corps is not None and chemin == "/reservations":
        corps = {**corps, "item_id": item_velo.id}

    response = client.request(methode, url, json=corps)

    assert response.status_code == attendu
    if attendu == 401:
        assert response.headers["WWW-Authenticate"] == "Bearer"


def test_le_proprietaire_d_un_item_vient_du_jeton(client_bob: TestClient, bob: User) -> None:
    response = client_bob.post("/items", json=NOUVEL_ITEM)

    assert response.json()["owner_id"] == bob.id


def test_owner_id_dans_le_corps_ne_permet_pas_d_usurper(
    client_alice: TestClient, bob: User, db: Session
) -> None:
    response = client_alice.post("/items", json={**NOUVEL_ITEM, "owner_id": bob.id})

    # ItemCreate refuse les champs inconnus (extra="forbid" depuis la séance 1) : 422,
    # et surtout aucun item n'est créé au nom de Bob
    assert response.status_code == 422
    assert db.query(Item).filter_by(owner_id=bob.id).count() == 0


def test_l_emprunteur_vient_du_jeton(client_carol: TestClient, carol: User, item_velo: Item) -> None:
    response = client_carol.post("/reservations", json={**NOUVELLE_RESA, "item_id": item_velo.id})

    assert response.json()["borrower_id"] == carol.id
