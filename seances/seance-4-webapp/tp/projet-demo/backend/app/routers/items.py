import unicodedata
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query, Response

from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

FAKE_DB: dict[int, dict[str, Any]] = {}


def _next_id() -> int:
    return max(FAKE_DB, default=0) + 1


def _normaliser(texte: str) -> str:
    """Minuscules sans accents : `q=velo` doit trouver « Vélo de ville »."""
    decompose = unicodedata.normalize("NFKD", texte.casefold())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def _get_or_404(item_id: int) -> dict[str, Any]:
    item = FAKE_DB.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} introuvable")
    return item


@router.get("", response_model=list[ItemRead])
def list_items(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    q: str | None = None,
    disponible: bool | None = None,
) -> list[dict[str, Any]]:
    items = list(FAKE_DB.values())
    if q is not None:
        recherche = _normaliser(q)
        items = [item for item in items if recherche in _normaliser(item["titre"])]
    if disponible is not None:
        items = [item for item in items if item["disponible"] == disponible]
    return items[skip : skip + limit]


@router.post("", response_model=ItemRead, status_code=201)
def create_item(payload: ItemCreate) -> dict[str, Any]:
    item = {"id": _next_id(), **payload.model_dump()}
    FAKE_DB[item["id"]] = item
    return item


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int = Path(ge=1)) -> dict[str, Any]:
    return _get_or_404(item_id)


@router.put("/{item_id}", response_model=ItemRead)
def replace_item(payload: ItemCreate, item_id: int = Path(ge=1)) -> dict[str, Any]:
    _get_or_404(item_id)
    item = {"id": item_id, **payload.model_dump()}
    FAKE_DB[item_id] = item
    return item


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(payload: ItemUpdate, item_id: int = Path(ge=1)) -> dict[str, Any]:
    item = _get_or_404(item_id)
    item.update(payload.model_dump(exclude_unset=True))
    return item


@router.delete("/{item_id}", status_code=204, response_class=Response)
def delete_item(item_id: int = Path(ge=1)) -> None:
    _get_or_404(item_id)
    del FAKE_DB[item_id]
