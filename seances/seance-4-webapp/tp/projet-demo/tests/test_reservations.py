from typing import Any
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.routers import reservations
from tests.conftest import Storage


def _reservation(reservation_id: int, item_id: int = 1, statut: str = "active") -> dict[str, Any]:
    """Une réservation complète, telle qu'elle est rangée dans le stockage."""
    return {"id": reservation_id, "item_id": item_id, "date_debut": "2026-09-01",
            "date_fin": "2026-09-05", "statut": statut}


# --- POST /reservations -----------------------------------------------------------


def test_creer_une_reservation_renvoie_201_et_statut_active(
    client: TestClient, item_velo: dict[str, Any]
) -> None:
    response = client.post("/reservations", json={
        "item_id": item_velo["id"], "date_debut": "2026-09-01", "date_fin": "2026-09-05",
    })

    assert response.status_code == 201
    assert response.json() == {"id": 1, "item_id": item_velo["id"], "date_debut": "2026-09-01",
                               "date_fin": "2026-09-05", "statut": "active"}


def test_une_reservation_creee_est_relisible(
    client: TestClient, reservation_active: dict[str, Any]
) -> None:
    response = client.get(f"/reservations/{reservation_active['id']}")

    assert response.status_code == 200
    assert response.json() == reservation_active


@pytest.mark.parametrize(("date_debut", "date_fin"), [
    ("2026-09-05", "2026-09-01"),  # inversées
    ("2026-09-05", "2026-09-05"),  # égales : date_fin doit être strictement postérieure
])
def test_creer_une_reservation_avec_dates_incoherentes_renvoie_422(
    client: TestClient, date_debut: str, date_fin: str
) -> None:
    response = client.post("/reservations", json={
        "item_id": 1, "date_debut": date_debut, "date_fin": date_fin,
    })

    assert response.status_code == 422
    assert client.get("/reservations").json() == []


@pytest.mark.parametrize(("payload", "champ_en_erreur"), [
    ({"item_id": 0, "date_debut": "2026-09-01", "date_fin": "2026-09-05"}, "item_id"),
    ({"date_debut": "2026-09-01", "date_fin": "2026-09-05"}, "item_id"),
    ({"item_id": 1, "date_debut": "01/09/2026", "date_fin": "2026-09-05"}, "date_debut"),
    ({"item_id": 1, "date_debut": "2026-09-01", "date_fn": "2026-09-05"}, "date_fn"),
])
def test_creer_une_reservation_invalide_renvoie_422(
    client: TestClient, payload: dict[str, Any], champ_en_erreur: str
) -> None:
    response = client.post("/reservations", json=payload)

    assert response.status_code == 422
    champs = [erreur["loc"][-1] for erreur in response.json()["detail"]]
    assert champ_en_erreur in champs


# --- GET /reservations ------------------------------------------------------------


def test_lister_sans_reservation_renvoie_une_liste_vide(client: TestClient) -> None:
    response = client.get("/reservations")

    assert response.status_code == 200
    assert response.json() == []


def test_lister_filtre_par_item_id(client: TestClient, storage: Storage) -> None:
    storage.reservations[1] = _reservation(1, item_id=1)
    storage.reservations[2] = _reservation(2, item_id=2)
    storage.reservations[3] = _reservation(3, item_id=1)

    response = client.get("/reservations", params={"item_id": 1})

    assert [r["id"] for r in response.json()] == [1, 3]


def test_lister_renvoie_au_plus_20_reservations_par_defaut(
    client: TestClient, storage: Storage
) -> None:
    for i in range(1, 31):
        storage.reservations[i] = _reservation(i)

    response = client.get("/reservations")

    assert [r["id"] for r in response.json()] == list(range(1, 21))


def test_lister_avec_limit_tronque_la_liste(client: TestClient, storage: Storage) -> None:
    for i in range(1, 6):
        storage.reservations[i] = _reservation(i)

    response = client.get("/reservations", params={"limit": 2})

    assert [r["id"] for r in response.json()] == [1, 2]


@pytest.mark.parametrize("params", [{"limit": 101}, {"limit": 0}, {"item_id": 0}])
def test_lister_avec_parametre_invalide_renvoie_422(
    client: TestClient, params: dict[str, Any]
) -> None:
    response = client.get("/reservations", params=params)

    assert response.status_code == 422


# --- GET /reservations/{reservation_id} -------------------------------------------


def test_lire_une_reservation_absente_renvoie_404(client: TestClient) -> None:
    response = client.get("/reservations/999")

    assert response.status_code == 404


# --- POST /reservations/{reservation_id}/annuler ----------------------------------


def test_annuler_une_reservation_active_passe_son_statut_a_annulee(
    client: TestClient, reservation_active: dict[str, Any]
) -> None:
    response = client.post(f"/reservations/{reservation_active['id']}/annuler")

    assert response.status_code == 200
    assert response.json()["statut"] == "annulee"
    assert client.get(f"/reservations/{reservation_active['id']}").json()["statut"] == "annulee"


def test_annuler_une_reservation_deja_annulee_renvoie_409(
    client: TestClient, reservation_active: dict[str, Any]
) -> None:
    # Given : la réservation a déjà été annulée.
    reservation_id = reservation_active["id"]
    client.post(f"/reservations/{reservation_id}/annuler")

    # When : on demande une seconde annulation.
    response = client.post(f"/reservations/{reservation_id}/annuler")

    # Then : l'API refuse avec un conflit, et la réservation reste annulée.
    assert response.status_code == 409
    assert client.get(f"/reservations/{reservation_id}").json()["statut"] == "annulee"


def test_annuler_une_reservation_absente_renvoie_404(client: TestClient) -> None:
    response = client.post("/reservations/999/annuler")

    assert response.status_code == 404


# --- Notification d'annulation (effet de bord externe, mocké) ---------------------


def test_annulation_envoie_une_notification(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, reservation_active: dict[str, Any]
) -> None:
    notifier = Mock()
    monkeypatch.setattr(reservations, "envoyer_notification_annulation", notifier)

    response = client.post(f"/reservations/{reservation_active['id']}/annuler")

    assert response.status_code == 200
    notifier.assert_called_once_with(reservation_id=reservation_active["id"])


def test_annulation_refusee_n_envoie_pas_de_notification(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, reservation_active: dict[str, Any]
) -> None:
    client.post(f"/reservations/{reservation_active['id']}/annuler")
    notifier = Mock()
    monkeypatch.setattr(reservations, "envoyer_notification_annulation", notifier)

    response = client.post(f"/reservations/{reservation_active['id']}/annuler")

    assert response.status_code == 409
    notifier.assert_not_called()


def test_annulation_reussit_meme_si_la_notification_echoue(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, reservation_active: dict[str, Any]
) -> None:
    notifier = Mock(side_effect=ConnectionError("serveur mail injoignable"))
    monkeypatch.setattr(reservations, "envoyer_notification_annulation", notifier)

    response = client.post(f"/reservations/{reservation_active['id']}/annuler")

    assert response.status_code == 200
    assert client.get(f"/reservations/{reservation_active['id']}").json()["statut"] == "annulee"
