-- 1. Items disponibles à moins de 10 €/jour, par tarif croissant
SELECT id, titre, tarif_jour FROM items
WHERE disponible AND tarif_jour < 10
ORDER BY tarif_jour;
--  id |     titre     | tarif_jour
--   2 | Perceuse      |       5.00
--   1 | Vélo de ville |       8.50

-- 2. Titre contenant « velo », insensible à la casse
SELECT id, titre FROM items WHERE titre ILIKE '%velo%';
-- (0 rows) : ILIKE ignore la casse mais pas les accents, « Vélo » ne matche pas « velo ».
-- Il faudrait l'extension unaccent : WHERE unaccent(titre) ILIKE '%velo%'

-- 3. Chaque item avec le nom de son propriétaire
SELECT i.id, i.titre, u.display_name AS proprietaire
FROM items i JOIN users u ON u.id = i.owner_id
ORDER BY i.id;
--  id |     titre      | proprietaire
--   1 | Vélo de ville  | Alice
--   2 | Perceuse       | Alice
--   3 | Tente 2 places | Bob
--   4 | Appareil photo | Bob

-- 4. Nombre de réservations par item, y compris jamais réservés
-- LEFT JOIN + COUNT(r.id) (et pas COUNT(*), qui compterait 1 pour la Perceuse)
SELECT i.id, i.titre, COUNT(r.id) AS nb_reservations
FROM items i LEFT JOIN reservations r ON r.item_id = i.id
GROUP BY i.id, i.titre
ORDER BY i.id;
--  id |     titre      | nb_reservations
--   1 | Vélo de ville  |               1
--   2 | Perceuse       |               0
--   3 | Tente 2 places |               1
--   4 | Appareil photo |               1

-- 5. Par utilisateur ayant publié au moins un item : nb d'items et tarif moyen
SELECT u.display_name, COUNT(i.id) AS nb_items, ROUND(AVG(i.tarif_jour), 2) AS tarif_moyen
FROM users u JOIN items i ON i.owner_id = u.id
GROUP BY u.id, u.display_name
ORDER BY u.id;
--  display_name | nb_items | tarif_moyen
--  Alice        |        2 |        6.75
--  Bob          |        2 |       16.00

-- 6. Réservations actives commençant après le 1er septembre 2026
SELECT r.id, i.titre, u.display_name AS emprunteur, r.date_debut, r.date_fin
FROM reservations r
JOIN items i ON i.id = r.item_id
JOIN users u ON u.id = r.borrower_id
WHERE r.statut = 'active' AND r.date_debut > '2026-09-01'
ORDER BY r.date_debut;
--  id |     titre      | emprunteur | date_debut |  date_fin
--   2 | Tente 2 places | Alice      | 2026-09-10 | 2026-09-12
--   3 | Appareil photo | Chloé      | 2026-09-15 | 2026-09-20

-- 7. Les 2 items les plus chers, en sautant le premier
SELECT id, titre, tarif_jour FROM items
ORDER BY tarif_jour DESC
LIMIT 2 OFFSET 1;
--  id |     titre      | tarif_jour
--   3 | Tente 2 places |      12.00
--   1 | Vélo de ville  |       8.50

-- 8. Chiffre d'affaires potentiel de chaque réservation active
SELECT r.id, i.titre, r.date_fin - r.date_debut AS nb_jours,
       i.tarif_jour * (r.date_fin - r.date_debut) AS ca_potentiel
FROM reservations r JOIN items i ON i.id = r.item_id
WHERE r.statut = 'active'
ORDER BY r.id;
--  id |     titre      | nb_jours | ca_potentiel
--   2 | Tente 2 places |        2 |        24.00
--   3 | Appareil photo |        5 |       100.00
