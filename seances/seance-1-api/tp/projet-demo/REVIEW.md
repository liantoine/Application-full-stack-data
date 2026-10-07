# Review — ressource `reservations`

Auteur : Antoine LI

## Ce que j'ai demandé à l'agent

Agent : **GitHub Copilot CLI** (1.0.91), sur le projet dans son état d'avant les réservations
(`items` terminé, [SPEC-reservations.md](SPEC-reservations.md) écrite, aucun test).

1. Plan d'abord, sans modification :
   > Lis SPEC-reservations.md et app/routers/items.py. Propose un plan d'implémentation de la
   > ressource reservations conforme à la spec, en reprenant le style de app/routers/items.py.
   > Ne modifie aucun fichier pour l'instant : donne seulement le plan.
2. Après lecture du plan :
   > Le plan me convient. Implémente-le.

**Le plan** était conforme à la spec (schémas, `extra="forbid"`, `model_validator`, 4 routes avec
leurs codes, helper `_get_or_404`). Un point flou : « confirmer que le nouveau router est bien
inclus dans l'application, *si son enregistrement n'est pas automatique* » — il ne l'est jamais,
il faut l'`include_router` dans `main.py`. Copilot l'a bien fait à l'implémentation.

**Le code produit** : `app/schemas/reservation.py`, `app/routers/reservations.py` et deux lignes
dans `app/main.py`. Je l'ai relu, puis passé à la suite de tests des réservations : 31 tests sur
31 passent une fois le nom du stockage corrigé (voir ligne 4 de la grille).

## Grille de review

| Point de contrôle | OK / KO | Ce que j'ai corrigé |
|---|---|---|
| Les codes de statut correspondent à la spec (201, 404, 409) | OK | Vérifié : `POST` → 201, `GET /reservations/999` → 404, 2ᵉ annulation → 409, `POST /reservations/999/annuler` → 404. |
| `response_model` présent sur les 4 routes | OK | `ReservationRead` sur `POST ""`, `GET "/{id}"`, `POST "/{id}/annuler"` ; `list[ReservationRead]` sur `GET ""`. |
| La validation `date_fin > date_debut` est bien dans le schéma Pydantic | KO (partiel) | Le `model_validator` est bien dans `ReservationCreate` → 422, aucun `if` dans le router. **Mais** la règle n'apparaît pas dans `/openapi.json` : un `model_validator` n'est pas traduit en JSON Schema, un client qui lit `/docs` ne la voit pas. Corrigé : `Field(description="Strictement postérieure à date_debut.")` sur `date_fin`. |
| Le router n'accède pas au stockage de `items` | KO (partiel) | Aucun accès à `items`, c'est bon. Mais Copilot a nommé son stockage `RESERVATIONS_DB` alors que la spec dit « comme `items` » (`FAKE_DB`). Incohérent entre les deux routers, et la fixture `storage` des tests (`reservations.FAKE_DB`) plantait avec `AttributeError`. Renommé `FAKE_DB`. |
| Pas d'`async def` sans `await` | OK | Toutes les routes sont en `def`. |
| Aucune dépendance ajoutée dans `requirements.txt` (ou justifiée) | KO (partiel) | Le fichier n'a pas été modifié. **Mais** pour « vérifier » son code, Copilot a lancé de lui-même `pip install -r requirements.txt` puis `pip install httpx` dans le Python global de ma machine, hors du conteneur, sans demander. Rien à corriger dans le projet ; à l'avenir, lui interdire d'installer des paquets et lui faire lancer les vérifications dans Docker. |
| Les routes littérales sont déclarées avant les routes paramétrées | OK | Pas de route littérale concurrente sous `/reservations/…` ; `"/{reservation_id}/annuler"` a deux segments et ne peut pas être capturée par `"/{reservation_id}"`. |
| Le code renvoie une réponse cohérente pour `POST /reservations/999/annuler` | OK | 404 `{"detail": "Réservation 999 introuvable"}`, via le même `_get_or_404` que `GET`. |

## Constats hors grille

1. **Bon point** : Copilot a typé `statut` en `Literal["active", "annulee"]` et non en `str`
   libre, sans que la spec le précise.
2. **Il ne s'est pas vérifié comme il l'annonçait** : le plan prévoyait de « tester les cas de la
   spec », il a fait des appels manuels dans un script jetable, sans test conservé. Rien ne
   protégeait donc ces cas avant le TP 2.
3. **Trou dans la spec, non corrigé volontairement** : « aucun accès à `FAKE_DB` de items »
   empêche de vérifier que l'item réservé existe → `POST /reservations` avec `item_id=999`
   renvoie 201. Rien n'empêche non plus deux réservations actives qui se chevauchent sur le même
   item (ce devrait être un 409). À traiter avec la base de données dans les séances suivantes.

## Même exercice sur mon CRUD `items`

- **Bug trouvé : `PATCH {"titre": null}` → 500.** `ItemUpdate.titre` est `str | None` pour être
  optionnel, donc `null` passe la validation d'entrée ; `exclude_unset=True` le garde (il a été
  envoyé) ; `titre` devient `None` et `ItemRead` (`titre: str`) lève une erreur de validation de
  **réponse** → 500. Corrigé par un `field_validator` qui refuse `null` sur `titre`,
  `tarif_jour` et `disponible` → 422. `description: null` reste accepté (champ nullable).
- **Recherche `q` sensible aux accents** : `GET /items?q=velo` (l'exemple du TP) ne trouvait pas
  « Vélo de ville ». Corrigé : comparaison en minuscules sans accents (`unicodedata`).
