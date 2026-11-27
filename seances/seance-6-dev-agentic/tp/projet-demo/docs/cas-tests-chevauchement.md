# Cas de tests du chevauchement

Créneau existant (réservation active sur l'item 1) : du **2026-12-10** au **2026-12-15**.

Décision : un créneau est `[date_debut, date_fin)`. Deux réservations jointives (l'une finit le
jour où l'autre commence) ne sont **pas** en conflit : l'objet est rendu puis repris le même jour.
C'est cohérent avec le nombre de jours facturés (`date_fin - date_debut`).

Condition de conflit : il n'y a pas de conflit si l'existante finit avant le début demandé ou
commence après la fin demandée. On prend la négation :
`existante.date_debut < fin_demandee AND existante.date_fin > debut_demande`.

| Cas | Créneau demandé | Code attendu | Code obtenu |
|---|---|---|---|
| Avant | 2026-12-01 -> 2026-12-05 | 201 | 201 |
| Après | 2026-12-20 -> 2026-12-25 | 201 | 201 |
| Chevauchement partiel au début | 2026-12-08 -> 2026-12-12 | 409 | 409 |
| Chevauchement partiel à la fin | 2026-12-13 -> 2026-12-18 | 409 | 409 |
| Englobant | 2026-12-05 -> 2026-12-20 | 409 | 409 |
| Inclus dans l'existante | 2026-12-11 -> 2026-12-13 | 409 | 409 |
| Jointif avant | 2026-12-05 -> 2026-12-10 | 201 | 201 |
| Jointif après | 2026-12-15 -> 2026-12-18 | 201 | 201 |

Rejoués un par un avec `curl` sur `POST /reservations`. Chaque réservation acceptée était annulée
juste après, pour ne pas fausser le cas suivant. Les 409 renvoient
`{"detail": "Ce créneau est déjà réservé"}`.

Autres codes vérifiés au passage :

| Cas | Code obtenu |
|---|---|
| Item inexistant | 404 |
| Emprunteur inexistant | 404 |
| Item indisponible | 409 |
| `date_fin` avant `date_debut` | 422 |
| Annuler une réservation active | 200 |
| L'annuler une deuxième fois | 409 |
| `PATCH` avec `{"statut": "active"}` | 422 |
| `GET /reservations/999` | 404 |
