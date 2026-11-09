# Mesures EXPLAIN ANALYZE (étape 5)

200 000 items générés (`generate_series` + `random()`), `ANALYZE items` après chaque création d'index.
PostgreSQL 16, Docker Desktop, 200 004 lignes dans `items`.

## Titre exact : `WHERE titre = 'Item de test 123456'`

| | Nœud | Temps d'exécution |
|---|---|---|
| Sans index | `Seq Scan` (200 003 lignes filtrées) | 15.948 ms |
| Avec `items_titre_idx` | `Index Scan using items_titre_idx` | 0.086 ms |

Facteur d'accélération : **≈ 185×**.

## (a) Joker en tête : `WHERE titre LIKE '%123456'`

| | Nœud | Temps d'exécution |
|---|---|---|
| Sans index | `Seq Scan` | 23.955 ms |
| Avec `items_titre_idx` | `Seq Scan` (index ignoré) | 22.620 ms |

Le B-tree est trié par le début de la chaîne : sans préfixe connu, il n'y a aucune plage de l'index à
parcourir, donc PostgreSQL lit toute la table.

## (b) Index sur `disponible`

Répartition : 200 004 lignes à `TRUE`, 0 à `FALSE`.

| Filtre | Nœud | Temps d'exécution |
|---|---|---|
| `disponible = TRUE` | `Seq Scan` (index ignoré) | 24.973 ms |
| `disponible = FALSE` | `Index Scan using items_disponible_idx` | 0.191 ms |

L'index n'est utilisé que si la condition est sélective : `TRUE` concerne 100 % des lignes, lire la
table directement coûte moins cher, alors que `FALSE` ne concerne aucune ligne et l'index la trouve
immédiatement.

## Bonus : joker en fin, `WHERE titre LIKE 'Item de test 12345%'`

| | Nœud | Temps d'exécution |
|---|---|---|
| Sans index | `Seq Scan` | 20.870 ms |
| Avec `items_titre_idx` | `Seq Scan` (index ignoré) | 19.438 ms |

Non, l'index n'est pas utilisé : la base est en collation `en_US.utf8`, dont l'ordre de tri n'est
pas l'ordre des octets, donc un B-tree « normal » ne peut pas servir pour un `LIKE 'préfixe%'`. Il
faudrait un index `varchar_pattern_ops` : testé, la même requête passe en `Index Scan` en 0.117 ms.
