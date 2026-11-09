-- Insertions qui doivent échouer. Tout est annulé à la fin (ROLLBACK), le fichier est rejouable :
-- docker compose exec -T db psql -U gearshare -d gearshare < sql/tests-contraintes.sql
\set ON_ERROR_ROLLBACK on
BEGIN;

-- Étape 2
INSERT INTO users (email, password_hash, display_name) VALUES ('alice@esiee.fr', 'x', 'Alice bis');
-- ERROR: duplicate key value violates unique constraint "users_email_key"
INSERT INTO items (owner_id, titre, tarif_jour) VALUES (999, 'Fantôme', 10);
-- ERROR: insert or update on table "items" violates foreign key constraint "items_owner_id_fkey"
INSERT INTO items (owner_id, titre, tarif_jour) VALUES (1, 'Négatif', -5);
-- ERROR: new row for relation "items" violates check constraint "items_tarif_jour_positif"
INSERT INTO reservations (item_id, borrower_id, date_debut, date_fin) VALUES (2, 3, '2026-10-10', '2026-10-05');
-- ERROR: new row for relation "reservations" violates check constraint "reservations_dates_check"
INSERT INTO reservations (item_id, borrower_id, date_debut, date_fin, statut)
VALUES (2, 3, '2026-10-01', '2026-10-05', 'en_attente_peut_etre');
-- ERROR: new row for relation "reservations" violates check constraint "reservations_statut_check"

-- Étape 6 (données valides de départ : un avis sur la réservation terminée 1, un tag)
INSERT INTO avis (reservation_id, note, commentaire) VALUES (1, 5, 'Nickel');
INSERT INTO tags (libelle) VALUES ('velo');

INSERT INTO avis (reservation_id, note) VALUES (1, 6);
-- ERROR: new row for relation "avis" violates check constraint "avis_note_check"
INSERT INTO avis (reservation_id, note) VALUES (1, 4);
-- ERROR: duplicate key value violates unique constraint "avis_reservation_id_key"
INSERT INTO tags (libelle) VALUES ('velo');
-- ERROR: duplicate key value violates unique constraint "tags_libelle_key"
INSERT INTO avis (reservation_id, note) VALUES (999, 3);
-- ERROR: insert or update on table "avis" violates foreign key constraint "avis_reservation_id_fkey"
-- Chevauchement : l'Appareil photo est réservé (actif) du 15 au 20 septembre
INSERT INTO reservations (item_id, borrower_id, date_debut, date_fin) VALUES (4, 1, '2026-09-18', '2026-09-22');
-- ERROR: conflicting key value violates exclusion constraint "reservations_pas_de_chevauchement"

ROLLBACK;
