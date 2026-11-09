"""Hachage des mots de passe, sans base ni client HTTP."""

import hashlib
import secrets

from app.core.security import hash_password, verify_password


def test_deux_hachages_du_meme_mot_de_passe_sont_differents() -> None:
    assert hash_password("motdepasse-alice") != hash_password("motdepasse-alice")


def test_le_bon_mot_de_passe_est_accepte() -> None:
    assert verify_password("motdepasse-alice", hash_password("motdepasse-alice")) is True


def test_un_mauvais_mot_de_passe_est_refuse() -> None:
    assert verify_password("mauvais", hash_password("motdepasse-alice")) is False


def test_un_condensat_malforme_est_refuse_sans_erreur() -> None:
    assert verify_password("x", "x") is False
    assert verify_password("x", "pbkdf2_sha256$pas-un-nombre$00$00") is False


def test_un_condensat_avec_un_autre_cout_reste_verifiable() -> None:
    # Le coût est relu dans la chaîne stockée, pas dans la constante ITERATIONS
    sel = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", b"ancien-mot-de-passe", sel, 1_000)
    stocke = f"pbkdf2_sha256$1000${sel.hex()}${dk.hex()}"

    assert verify_password("ancien-mot-de-passe", stocke) is True
    assert verify_password("autre", stocke) is False
