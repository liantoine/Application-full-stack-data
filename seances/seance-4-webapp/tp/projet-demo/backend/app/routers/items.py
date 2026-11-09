from fastapi import APIRouter, Path, Query, Response

from app.api.deps import ItemServiceDep
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[ItemRead])
def list_items(
    service: ItemServiceDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    q: str | None = None,
    disponible: bool | None = None,
) -> list[Item]:
    return service.lister(skip=skip, limit=limit, q=q, disponible=disponible)


@router.post("", response_model=ItemRead, status_code=201)
def create_item(payload: ItemCreate, service: ItemServiceDep) -> Item:
    return service.creer(payload.model_dump())


@router.get("/{item_id}", response_model=ItemRead)
def get_item(service: ItemServiceDep, item_id: int = Path(ge=1)) -> Item:
    return service.obtenir(item_id)


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(payload: ItemUpdate, service: ItemServiceDep, item_id: int = Path(ge=1)) -> Item:
    return service.modifier(item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}", status_code=204, response_class=Response)
def delete_item(service: ItemServiceDep, item_id: int = Path(ge=1)) -> None:
    service.supprimer(item_id)
