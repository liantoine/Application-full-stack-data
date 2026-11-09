class DomainError(Exception):
    """Erreur métier. Ne connaît pas HTTP : la traduction se fait dans main.py."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RessourceIntrouvable(DomainError): ...


class ConflitMetier(DomainError): ...


class AccesRefuse(DomainError): ...


class EmailDejaUtilise(DomainError): ...
