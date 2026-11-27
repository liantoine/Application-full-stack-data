from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models import Base, Item, Reservation, User


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    # Base dédiée (gearshare_test), jamais celle de dev
    engine = create_engine(settings.test_database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """Une session par test, dans une transaction annulée à la fin."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autoflush=False, autocommit=False)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _user(db: Session, email: str, nom: str) -> User:
    # Pas de vrai hachage ici : seuls les tests de register/login en ont besoin
    user = User(email=email, display_name=nom, password_hash="x")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def alice(db: Session) -> User:
    return _user(db, "alice@esiee.fr", "Alice")


@pytest.fixture
def bob(db: Session) -> User:
    return _user(db, "bob@esiee.fr", "Bob")


@pytest.fixture
def carol(db: Session) -> User:
    return _user(db, "carol@esiee.fr", "Carol")


def _bearer(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


# Une instance de TestClient par identité : partager `client` mélangerait les en-têtes.
# Elles dépendent de `client` pour que l'override de get_db soit en place.
@pytest.fixture
def client_alice(client: TestClient, alice: User) -> TestClient:
    return TestClient(app, headers=_bearer(alice))


@pytest.fixture
def client_bob(client: TestClient, bob: User) -> TestClient:
    return TestClient(app, headers=_bearer(bob))


@pytest.fixture
def client_carol(client: TestClient, carol: User) -> TestClient:
    return TestClient(app, headers=_bearer(carol))


@pytest.fixture
def item_velo(db: Session, alice: User) -> Item:
    item = Item(owner_id=alice.id, titre="Vélo de ville", tarif_jour=Decimal("8.50"))
    db.add(item)
    db.flush()
    return item


@pytest.fixture
def reservation_bob(db: Session, item_velo: Item, bob: User) -> Reservation:
    """Bob emprunte le vélo d'Alice du 1er au 5 septembre."""
    reservation = Reservation(
        item_id=item_velo.id, borrower_id=bob.id,
        date_debut=date(2026, 9, 1), date_fin=date(2026, 9, 5), statut="active",
    )
    db.add(reservation)
    db.flush()
    return reservation
