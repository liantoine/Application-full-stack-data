# Review du schéma v2

Schéma relu : `01-schema.sql` (v1) + `03-schema-v2.sql` (avis, tags, corrections).

| Point de contrôle | OK / KO | Ce que j'ai corrigé |
|---|---|---|
| Chaque table a une clé primaire | OK | — |
| Les clés étrangères sont déclarées avec `REFERENCES` | OK | — |
| Les `ON DELETE` sont explicites et cohérents avec le métier | KO → OK | `reservations.borrower_id` n'avait pas d'`ON DELETE` et `items.owner_id` était en `CASCADE` (efface les prêts des autres) : les deux passent en `ON DELETE RESTRICT`. `avis` et `item_tags` en `CASCADE` (ils n'ont pas de sens sans leur parent). |
| La règle « un seul avis par réservation » est garantie par une contrainte `UNIQUE` | OK | `avis_reservation_id_key` |
| La note est bornée par un `CHECK (note BETWEEN 1 AND 5)` | OK | `avis_note_check` |
| La table de liaison item/tag a une clé primaire composite | OK | `item_tags_pkey (item_id, tag_id)` |
| Le libellé de tag est `UNIQUE` | OK | `tags_libelle_key`, plus `tags_libelle_minuscules` pour les minuscules |
| Les contraintes sont nommées | OK | — |
| Des index existent sur les clés étrangères | KO → OK | Ajout de `items_owner_id_idx`, `reservations_item_id_idx`, `reservations_borrower_id_idx`, `item_tags_tag_id_idx` (`avis.reservation_id` et `item_tags.item_id` sont déjà couverts par l'`UNIQUE` / la PK). |
| Le non-chevauchement est réellement garanti (contrainte) ou explicitement laissé à l'applicatif | OK | Contrainte d'exclusion `reservations_pas_de_chevauchement` (`btree_gist`), sur les réservations `active` uniquement, intervalle `[date_debut, date_fin)`. |
| Aucun type flottant pour un montant, aucun `TIMESTAMP` sans fuseau | OK | `NUMERIC(10, 2)` et `TIMESTAMPTZ` |

Non garanti par la base : « l'avis n'est possible qu'après une réservation `terminee` ». La
condition porte sur une autre table (un `CHECK` ne peut pas la lire) : vérification côté applicatif.

## Suppression d'un utilisateur (question de l'étape 2)

Avec la cascade sur `borrower_id`, supprimer Bob a effacé les 3 réservations : la n°1 (son propre
emprunt, via `reservations_borrower_id_fkey`), et les n°2 et n°3 d'Alice et Chloé (via
`items_owner_id_fkey` puis `reservations_item_id_fkey`, car ses items ont été supprimés).
Décision pour GearShare : supprimer un compte ne doit effacer ni l'historique des prêts faits sur
son matériel, ni ses propres emprunts. La base refuse donc la suppression (`RESTRICT`) et
l'application désactive/anonymise le compte au lieu de le supprimer.
