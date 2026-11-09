from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import Storage


def _item(item_id: int, **champs: Any) -> dict[str, Any]:
    """Un item complet, tel qu'il est rangé dans le stockage."""
    return {"id": item_id, "titre": f"Item {item_id}", "description": None,
            "tarif_jour": 5.0, "disponible": True, **champs}


# --- POST /items -----------------------------------------------------------------


def test_creer_un_item_renvoie_201_et_l_item_cree(client: TestClient) -> None:
    response = client.post("/items", json={"titre": "Tente 2 places", "tarif_jour": 6})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "titre": "Tente 2 places", "description": None,
                               "tarif_jour": 6.0, "disponible": True}


def test_un_item_cree_est_relisible(client: TestClient, item_velo: dict[str, Any]) -> None:
    response = client.get(f"/items/{item_velo['id']}")

    assert response.status_code == 200
    assert response.json() == item_velo


def test_deux_items_crees_ont_des_ids_differents(client: TestClient) -> None:
    premier = client.post("/items", json={"titre": "Tente", "tarif_jour": 6}).json()
    second = client.post("/items", json={"titre": "Réchaud", "tarif_jour": 2}).json()

    assert premier["id"] != second["id"]


@pytest.mark.parametrize(
    ("payload", "champ_en_erreur"),
    [
        ({"titre": "ab", "tarif_jour": 8.5}, "titre"),                      # trop court
        ({"titre": "x" * 121, "tarif_jour": 8.5}, "titre"),                 # trop long
        ({"tarif_jour": 8.5}, "titre"),                                     # manquant
        ({"titre": "Vélo de ville", "tarif_jour": 0}, "tarif_jour"),        # nul
        ({"titre": "Vélo de ville", "tarif_jour": -3}, "tarif_jour"),       # négatif
        ({"titre": "Vélo de ville"}, "tarif_jour"),                         # manquant
        ({"titre": "Vélo de ville", "tarif_jour": 8.5, "description": "x" * 1001},
         "description"),                                                    # trop longue
        ({"titre": "Vélo de ville", "tarif_jour": 8.5, "couleur": "rouge"}, "couleur"),  # inconnu
    ],
)
def test_creation_item_invalide_renvoie_422(
    client: TestClient, payload: dict[str, Any], champ_en_erreur: str
) -> None:
    response = client.post("/items", json=payload)

    assert response.status_code == 422
    champs = [erreur["loc"][-1] for erreur in response.json()["detail"]]
    assert champ_en_erreur in champs


# --- GET /items -------------------------------------------------------------------


def test_lister_sans_item_renvoie_une_liste_vide(client: TestClient) -> None:
    response = client.get("/items")

    assert response.status_code == 200
    assert response.json() == []


def test_lister_renvoie_au_plus_20_items_par_defaut(client: TestClient, storage: Storage) -> None:
    for i in range(1, 31):
        storage.items[i] = _item(i)

    response = client.get("/items")

    assert [item["id"] for item in response.json()] == list(range(1, 21))


def test_lister_avec_skip_saute_les_premiers(client: TestClient, storage: Storage) -> None:
    # Given : cinquante items, insérés sans passer par cinquante requêtes HTTP.
    for i in range(1, 51):
        storage.items[i] = _item(i)

    response = client.get("/items", params={"skip": 40, "limit": 20})

    assert [item["id"] for item in response.json()] == list(range(41, 51))


def test_lister_avec_limit_tronque_la_liste(client: TestClient, storage: Storage) -> None:
    for i in range(1, 6):
        storage.items[i] = _item(i)

    response = client.get("/items", params={"skip": 0, "limit": 1})

    assert [item["id"] for item in response.json()] == [1]


@pytest.mark.parametrize("q", ["vélo", "VELO", "velo", "ville"])
def test_lister_avec_q_filtre_sur_le_titre_sans_casse_ni_accents(
    client: TestClient, item_velo: dict[str, Any], q: str
) -> None:
    client.post("/items", json={"titre": "Tente 2 places", "tarif_jour": 6})

    response = client.get("/items", params={"q": q})

    assert [item["id"] for item in response.json()] == [item_velo["id"]]


@pytest.mark.parametrize(("disponible", "titres_attendus"), [
    ("true", ["Vélo de ville"]),
    ("false", ["Perceuse"]),
])
def test_lister_avec_disponible_filtre_les_items(
    client: TestClient, item_velo: dict[str, Any], disponible: str, titres_attendus: list[str]
) -> None:
    client.post("/items", json={"titre": "Perceuse", "tarif_jour": 4, "disponible": False})

    response = client.get("/items", params={"disponible": disponible})

    assert [item["titre"] for item in response.json()] == titres_attendus


@pytest.mark.parametrize(("params", "parametre_en_erreur"), [
    ({"limit": 500}, "limit"),
    ({"limit": 0}, "limit"),
    ({"skip": -1}, "skip"),
    ({"disponible": "peut-etre"}, "disponible"),
])
def test_lister_avec_parametre_invalide_renvoie_422(
    client: TestClient, params: dict[str, Any], parametre_en_erreur: str
) -> None:
    response = client.get("/items", params=params)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", parametre_en_erreur]


# --- GET /items/{item_id} ---------------------------------------------------------


def test_lire_un_item_absent_renvoie_404(client: TestClient) -> None:
    response = client.get("/items/999")

    assert response.status_code == 404


@pytest.mark.parametrize("item_id", ["0", "-1", "abc"])
def test_lire_un_item_avec_id_invalide_renvoie_422(client: TestClient, item_id: str) -> None:
    response = client.get(f"/items/{item_id}")

    assert response.status_code == 422


# --- PUT /items/{item_id} ---------------------------------------------------------


def test_remplacer_un_item_remplace_tous_les_champs(
    client: TestClient, item_velo: dict[str, Any]
) -> None:
    response = client.put(f"/items/{item_velo['id']}", json={
        "titre": "Vélo pliant", "tarif_jour": 9, "disponible": False,
    })

    assert response.status_code == 200
    # description n'est pas transmise : un PUT remplace tout, elle revient à sa valeur par défaut.
    assert response.json() == {"id": item_velo["id"], "titre": "Vélo pliant", "description": None,
                               "tarif_jour": 9.0, "disponible": False}
    assert client.get(f"/items/{item_velo['id']}").json() == response.json()


def test_remplacer_un_item_absent_renvoie_404(client: TestClient) -> None:
    response = client.put("/items/999", json={"titre": "Vélo pliant", "tarif_jour": 9})

    assert response.status_code == 404


def test_remplacer_un_item_avec_un_corps_invalide_renvoie_422(
    client: TestClient, item_velo: dict[str, Any]
) -> None:
    response = client.put(f"/items/{item_velo['id']}", json={"titre": "ab", "tarif_jour": 9})

    assert response.status_code == 422
    assert client.get(f"/items/{item_velo['id']}").json() == item_velo


# --- PATCH /items/{item_id} -------------------------------------------------------


def test_modifier_un_seul_champ_laisse_les_autres_inchanges(
    client: TestClient, item_velo: dict[str, Any]
) -> None:
    response = client.patch(f"/items/{item_velo['id']}", json={"titre": "Vélo pliant"})

    assert response.status_code == 200
    assert response.json() == {**item_velo, "titre": "Vélo pliant"}


def test_modifier_la_description_a_null_l_efface(
    client: TestClient, item_velo: dict[str, Any]
) -> None:
    response = client.patch(f"/items/{item_velo['id']}", json={"description": None})

    assert response.status_code == 200
    assert response.json()["description"] is None


@pytest.mark.parametrize("champ", ["titre", "tarif_jour", "disponible"])
def test_modifier_un_champ_obligatoire_a_null_renvoie_422(
    client: TestClient, item_velo: dict[str, Any], champ: str
) -> None:
    response = client.patch(f"/items/{item_velo['id']}", json={champ: None})

    assert response.status_code == 422
    assert client.get(f"/items/{item_velo['id']}").json() == item_velo


@pytest.mark.parametrize("payload", [{"tarif_jour": 0}, {"couleur": "rouge"}])
def test_modifier_avec_un_corps_invalide_renvoie_422(
    client: TestClient, item_velo: dict[str, Any], payload: dict[str, Any]
) -> None:
    response = client.patch(f"/items/{item_velo['id']}", json=payload)

    assert response.status_code == 422


def test_modifier_un_item_absent_renvoie_404(client: TestClient) -> None:
    response = client.patch("/items/999", json={"titre": "Vélo pliant"})

    assert response.status_code == 404


# --- DELETE /items/{item_id} ------------------------------------------------------


def test_supprimer_un_item_renvoie_204_sans_corps(
    client: TestClient, item_velo: dict[str, Any]
) -> None:
    response = client.delete(f"/items/{item_velo['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_un_item_supprime_n_est_plus_lisible(
    client: TestClient, item_velo: dict[str, Any]
) -> None:
    client.delete(f"/items/{item_velo['id']}")

    response = client.get(f"/items/{item_velo['id']}")

    assert response.status_code == 404


def test_supprimer_un_item_absent_renvoie_404(client: TestClient) -> None:
    response = client.delete("/items/999")

    assert response.status_code == 404
