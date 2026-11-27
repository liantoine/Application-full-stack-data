from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.api_client import ApiError, api_client
from app.auth import COOKIE_JETON, COOKIE_SECURE
from app.templating import templates

router = APIRouter()


def chemin_local(cible: str | None) -> str:
    """N'autorise qu'une redirection vers une page de ce site (pas de redirection ouverte)."""
    if cible and cible.startswith("/") and not cible.startswith(("//", "/\\")):
        return cible
    return "/items"


@router.get("/connexion", response_class=HTMLResponse)
def connexion_page(request: Request, suivant: str | None = None) -> HTMLResponse:
    return templates.TemplateResponse(request, "auth/connexion.html", {"suivant": suivant})


@router.post("/connexion")
def connexion(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    suivant: Annotated[str | None, Form()] = None,
) -> Response:
    try:
        jeton = api_client.login(email, password)
    except ApiError as exc:
        if exc.status_code not in (401, 422):
            raise
        # On réaffiche l'email, jamais le mot de passe
        return templates.TemplateResponse(
            request,
            "auth/connexion.html",
            {"erreur": "Email ou mot de passe incorrect.", "saisie": {"email": email}, "suivant": suivant},
            status_code=401,
        )
    response = RedirectResponse(chemin_local(suivant), status_code=303)
    response.set_cookie(
        COOKIE_JETON,
        jeton["access_token"],
        max_age=jeton["expires_in"],
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return response


@router.get("/inscription", response_class=HTMLResponse)
def inscription_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "auth/inscription.html", {})


@router.post("/inscription")
def inscription(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    display_name: Annotated[str, Form()],
) -> Response:
    try:
        api_client.register(email, password, display_name)
    except ApiError as exc:
        if exc.status_code not in (409, 422):
            raise
        erreurs = ["Un compte existe déjà avec cet email."] if exc.status_code == 409 else exc.messages()
        return templates.TemplateResponse(
            request,
            "auth/inscription.html",
            {"erreurs": erreurs, "saisie": {"email": email, "display_name": display_name}},
            status_code=exc.status_code,
        )
    return RedirectResponse("/connexion?inscription=ok", status_code=303)


# POST et pas un lien : une action qui modifie quelque chose ne passe jamais par un GET
@router.post("/deconnexion")
def deconnexion() -> Response:
    response = RedirectResponse("/items", status_code=303)
    response.delete_cookie(COOKIE_JETON)
    return response
