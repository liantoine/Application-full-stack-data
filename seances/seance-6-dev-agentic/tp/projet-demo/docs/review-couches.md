# Review de la verticale `reservations`

Relue à froid, avec la grille du TP.

| Point de contrôle | OK / KO | Ce que j'ai corrigé |
|---|---|---|
| Aucun SQL ni requête SQLAlchemy dans le router | OK | |
| Aucune `HTTPException` dans le service (uniquement les exceptions métier) | OK | |
| Aucun `commit()` dans le repository | OK | `flush()` seulement, le commit est fait par `get_db` |
| `response_model` sur les 4 routes | OK | |
| Schéma de lecture construit depuis l'objet SQLAlchemy, sans champ interne | OK | `ReservationRead` en `from_attributes`, pas de relation ni de données d'utilisateur |
| La requête de chevauchement couvre les cinq cas, y compris l'englobant | OK | Les cinq cas, plus l'inclusion et les jointifs, testés (`cas-tests-chevauchement.md`) |
| Pas de f-string dans une requête SQL | OK | |
| Pas de N+1 sur `GET /reservations` (si la relation `item` est chargée) | OK | `ReservationRead` ne lit aucune relation, donc rien à charger |
| Migration relue, `downgrade()` testé | OK | Modèle inchangé depuis le schéma initial : `alembic check` ne détecte rien. Aller-retour `upgrade` / `downgrade base` / `upgrade` testé sur la migration initiale |
| Aucune dépendance ajoutée sans justification | OK | Aucune pour cette verticale |

Correction faite au premier lancement :

- **Import cassé** : `ReservationRepository` a une méthode `list()`. Dans le corps de la classe, elle
  masque le type `list`, et l'annotation `-> list[Reservation]` de `find_chevauchements` plantait au
  démarrage (`'function' object is not subscriptable`). Corrigé avec
  `from __future__ import annotations`.

Choix fait en écrivant le service :

- **Emprunteur inexistant** : sans vérification, la clé étrangère `borrower_id` ferait remonter
  une `IntegrityError`, donc une 500. Le service vérifie donc l'utilisateur et renvoie une 404,
  comme pour `owner_id` sur les items.
