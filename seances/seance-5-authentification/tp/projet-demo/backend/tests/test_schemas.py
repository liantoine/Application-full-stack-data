"""Tests unitaires des schémas Pydantic, sans HTTP ni stockage."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.item import ItemCreate, ItemUpdate
from app.schemas.reservation import ReservationCreate


def test_reservation_valide_est_acceptee() -> None:
    reservation = ReservationCreate(item_id=1, date_debut=date(2026, 9, 1), date_fin=date(2026, 9, 5))

    assert reservation.date_fin > reservation.date_debut


def test_reservation_d_une_seule_nuit_est_acceptee() -> None:
    reservation = ReservationCreate(item_id=1, date_debut=date(2026, 9, 1), date_fin=date(2026, 9, 2))

    assert reservation.date_fin == date(2026, 9, 2)


def test_dates_inversees_sont_refusees_par_le_schema() -> None:
    with pytest.raises(ValidationError, match="date_fin"):
        ReservationCreate(item_id=1, date_debut=date(2026, 9, 5), date_fin=date(2026, 9, 1))


def test_dates_egales_sont_refusees_par_le_schema() -> None:
    with pytest.raises(ValidationError, match="date_fin"):
        ReservationCreate(item_id=1, date_debut=date(2026, 9, 5), date_fin=date(2026, 9, 5))


def test_item_create_refuse_un_champ_inconnu() -> None:
    with pytest.raises(ValidationError, match="couleur"):
        ItemCreate(titre="Vélo de ville", tarif_jour=8.5, couleur="rouge")


def test_item_create_est_disponible_par_defaut() -> None:
    assert ItemCreate(titre="Vélo de ville", tarif_jour=8.5).disponible is True


def test_item_update_sans_champ_est_vide() -> None:
    assert ItemUpdate().model_dump(exclude_unset=True) == {}


def test_item_update_ne_garde_que_les_champs_transmis() -> None:
    assert ItemUpdate(titre="Vélo pliant").model_dump(exclude_unset=True) == {"titre": "Vélo pliant"}


@pytest.mark.parametrize("champ", ["titre", "tarif_jour", "disponible"])
def test_item_update_refuse_null_sur_un_champ_obligatoire(champ: str) -> None:
    with pytest.raises(ValidationError, match=champ):
        ItemUpdate(**{champ: None})


def test_item_update_accepte_null_sur_la_description() -> None:
    assert ItemUpdate(description=None).model_dump(exclude_unset=True) == {"description": None}
