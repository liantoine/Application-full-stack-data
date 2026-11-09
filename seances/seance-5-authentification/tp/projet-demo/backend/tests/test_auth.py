from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models import User

INSCRIPTION = {"email": "alice@esiee.fr", "password": "motdepasse-alice", "display_name": "Alice"}


def test_inscription_valide(client: TestClient) -> None:
    response = client.post("/auth/register", json=INSCRIPTION)

    assert response.status_code == 201
    assert response.json()["email"] == "alice@esiee.fr"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_inscription_hache_le_mot_de_passe(client: TestClient, db: Session) -> None:
    client.post("/auth/register", json=INSCRIPTION)

    user = db.query(User).filter_by(email="alice@esiee.fr").one()
    assert user.password_hash.startswith("pbkdf2_sha256$600000$")
    assert "motdepasse-alice" not in user.password_hash


def test_inscription_email_deja_utilise(client: TestClient) -> None:
    client.post("/auth/register", json=INSCRIPTION)

    response = client.post("/auth/register", json=INSCRIPTION)

    assert response.status_code == 409


@pytest.mark.parametrize(
    "champs",
    [
        {"email": "pas-un-email"},
        {"password": "abcd"},
        {"password": "a" * 200},
    ],
)
def test_inscription_invalide(client: TestClient, champs: dict[str, str]) -> None:
    response = client.post("/auth/register", json={**INSCRIPTION, **champs})

    assert response.status_code == 422


def test_login_renvoie_un_jeton(client: TestClient) -> None:
    client.post("/auth/register", json=INSCRIPTION)

    response = client.post(
        "/auth/login", data={"username": "alice@esiee.fr", "password": "motdepasse-alice"}
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == settings.jwt_expire_minutes * 60


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("alice@esiee.fr", "mauvais-mot-de-passe"),
        ("inconnu@esiee.fr", "motdepasse-alice"),
    ],
)
def test_login_echoue_toujours_avec_le_meme_401(client: TestClient, email: str, password: str) -> None:
    client.post("/auth/register", json=INSCRIPTION)

    response = client.post("/auth/login", data={"username": email, "password": password})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {"detail": "Email ou mot de passe incorrect"}


def test_login_avec_un_condensat_malforme_renvoie_401(client: TestClient, alice: User) -> None:
    # La fixture alice a password_hash="x" : pas de 500
    response = client.post("/auth/login", data={"username": "alice@esiee.fr", "password": "x"})

    assert response.status_code == 401


def test_me_renvoie_l_utilisateur_du_jeton(client_alice: TestClient, alice: User) -> None:
    response = client_alice.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"id": alice.id, "email": "alice@esiee.fr", "display_name": "Alice"}


def _jeton_expire(user_id: int) -> str:
    passe = datetime.now(timezone.utc) - timedelta(hours=2)
    payload = {"sub": str(user_id), "iat": passe, "exp": passe + timedelta(minutes=1)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _jeton_mauvais_secret(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id)}, "secret", algorithm="HS256")


@pytest.mark.parametrize(
    "fabriquer_en_tete",
    [
        lambda alice: {},
        lambda alice: {"Authorization": "Bearer nimportequoi"},
        lambda alice: {"Authorization": f"Bearer {_jeton_expire(alice.id)}"},
        lambda alice: {"Authorization": f"Bearer {_jeton_mauvais_secret(alice.id)}"},
        lambda alice: {"Authorization": f"Bearer {create_access_token(999_999)}"},  # utilisateur disparu
    ],
    ids=["sans-jeton", "malforme", "expire", "mauvais-secret", "utilisateur-inconnu"],
)
def test_jeton_invalide_donne_toujours_le_meme_401(client: TestClient, alice: User, fabriquer_en_tete) -> None:
    response = client.get("/auth/me", headers=fabriquer_en_tete(alice))

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {"detail": "Identifiants invalides"}
