from datetime import date
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, Response

from app.api_client import ApiError, api_client
from app.auth import Token
from app.routers.items import contexte_annonce
from app.templating import templates

router = APIRouter()


@router.post("/items/{item_id}/reservations")
def reserver(
    request: Request,
    item_id: int,
    token: Token,
    date_debut: Annotated[date, Form()],
    date_fin: Annotated[date, Form()],
) -> Response:
    try:
        api_client.create_reservation(token, item_id, date_debut, date_fin)
    except ApiError as exc:
        if exc.status_code not in (409, 422):  # 409 : créneau pris ou item indisponible
            raise
        return templates.TemplateResponse(
            request,
            "items/detail.html",
            {
                **contexte_annonce(item_id, token),
                "erreurs": exc.messages(),
                "saisie": {"date_debut": date_debut, "date_fin": date_fin},
            },
            status_code=exc.status_code,
        )
    return RedirectResponse(f"/items/{item_id}?reservation=ok", status_code=303)


# Un formulaire HTML ne fait pas de PATCH : on reçoit un POST et on appelle PATCH sur l'API
@router.post("/reservations/{reservation_id}")
def changer_statut(
    reservation_id: int,
    token: Token,
    statut: Annotated[str, Form()],
    item_id: Annotated[int, Form()],
) -> Response:
    try:
        api_client.update_reservation(token, reservation_id, statut)
    except ApiError as exc:
        if exc.status_code != 409:  # 409 : réservation déjà annulée ou terminée
            raise
        return RedirectResponse(f"/items/{item_id}?statut=conflit", status_code=303)
    return RedirectResponse(f"/items/{item_id}", status_code=303)


@router.post("/reservations/{reservation_id}/avis")
def laisser_avis(
    request: Request,
    reservation_id: int,
    token: Token,
    item_id: Annotated[int, Form()],
    note: Annotated[str, Form()],
    commentaire: Annotated[str, Form()] = "",
) -> Response:
    # Note transmise telle quelle si ce n'est pas un entier : le backend renvoie le 422
    note_envoyee: int | str = int(note) if note.strip().lstrip("-").isdigit() else note
    try:
        api_client.create_avis(token, reservation_id, note_envoyee, commentaire.strip() or None)
    except ApiError as exc:
        if exc.status_code not in (409, 422):  # 409 : prêt pas terminé ou avis déjà laissé
            raise
        return templates.TemplateResponse(
            request,
            "items/detail.html",
            {
                **contexte_annonce(item_id, token),
                "erreurs_avis": exc.messages(),
                "saisie_avis": {"reservation_id": reservation_id, "note": note, "commentaire": commentaire},
            },
            status_code=exc.status_code,
        )
    return RedirectResponse(f"/items/{item_id}?avis=ok", status_code=303)
