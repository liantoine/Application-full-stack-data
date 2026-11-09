-- Schéma v2 : avis, tags, non-chevauchement des réservations (version corrigée après review)

CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ON DELETE explicites : supprimer un compte ne doit effacer ni ses emprunts ni l'historique
-- des prêts faits sur son matériel (cf. REVIEW-schema.md)
ALTER TABLE items DROP CONSTRAINT items_owner_id_fkey;
ALTER TABLE items ADD CONSTRAINT items_owner_id_fkey
    FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE RESTRICT;

ALTER TABLE reservations DROP CONSTRAINT reservations_borrower_id_fkey;
ALTER TABLE reservations ADD CONSTRAINT reservations_borrower_id_fkey
    FOREIGN KEY (borrower_id) REFERENCES users (id) ON DELETE RESTRICT;

-- Index sur les clés étrangères existantes
CREATE INDEX items_owner_id_idx ON items (owner_id);
CREATE INDEX reservations_item_id_idx ON reservations (item_id);
CREATE INDEX reservations_borrower_id_idx ON reservations (borrower_id);

-- Règle 4 : pas deux réservations actives qui se chevauchent sur un même item.
-- Intervalle [debut, fin) : rendu le 5, repris le 5 est autorisé (cohérent avec date_fin - date_debut jours)
ALTER TABLE reservations ADD CONSTRAINT reservations_pas_de_chevauchement
    EXCLUDE USING gist (item_id WITH =, daterange(date_debut, date_fin, '[)') WITH &&)
    WHERE (statut = 'active');

-- Règles 1 et 2 : un avis par réservation, note de 1 à 5.
-- L'auteur est l'emprunteur de la réservation (pas de colonne en double).
-- "Uniquement après une réservation terminee" : vérifié côté applicatif.
CREATE TABLE avis (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reservation_id BIGINT      NOT NULL
        CONSTRAINT avis_reservation_id_fkey REFERENCES reservations (id) ON DELETE CASCADE,
    note           SMALLINT    NOT NULL CONSTRAINT avis_note_check CHECK (note BETWEEN 1 AND 5),
    commentaire    TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT avis_reservation_id_key UNIQUE (reservation_id)  -- sert aussi d'index sur la FK
);

-- Règle 3 : tags en n-n avec les items, libellé unique en minuscules
CREATE TABLE tags (
    id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    libelle VARCHAR(50) NOT NULL
        CONSTRAINT tags_libelle_key UNIQUE
        CONSTRAINT tags_libelle_minuscules CHECK (libelle = lower(libelle))
);

CREATE TABLE item_tags (
    item_id BIGINT NOT NULL CONSTRAINT item_tags_item_id_fkey REFERENCES items (id) ON DELETE CASCADE,
    tag_id  BIGINT NOT NULL CONSTRAINT item_tags_tag_id_fkey REFERENCES tags (id) ON DELETE CASCADE,
    CONSTRAINT item_tags_pkey PRIMARY KEY (item_id, tag_id)  -- couvre aussi l'index sur item_id
);
CREATE INDEX item_tags_tag_id_idx ON item_tags (tag_id);
