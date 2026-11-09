CREATE TABLE users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email         VARCHAR(255) NOT NULL CONSTRAINT users_email_key UNIQUE,
    password_hash TEXT         NOT NULL,
    display_name  VARCHAR(80)  NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE items (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id    BIGINT        NOT NULL
        CONSTRAINT items_owner_id_fkey REFERENCES users (id) ON DELETE CASCADE,
    titre       VARCHAR(120)  NOT NULL,
    description TEXT,
    tarif_jour  NUMERIC(10, 2) NOT NULL CONSTRAINT items_tarif_jour_positif CHECK (tarif_jour > 0),
    disponible  BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE reservations (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    item_id     BIGINT      NOT NULL
        CONSTRAINT reservations_item_id_fkey REFERENCES items (id) ON DELETE CASCADE,
    borrower_id BIGINT      NOT NULL
        CONSTRAINT reservations_borrower_id_fkey REFERENCES users (id),
    date_debut  DATE        NOT NULL,
    date_fin    DATE        NOT NULL,
    statut      VARCHAR(20) NOT NULL DEFAULT 'active'
        CONSTRAINT reservations_statut_check CHECK (statut IN ('active', 'annulee', 'terminee')),
    CONSTRAINT reservations_dates_check CHECK (date_fin > date_debut)
);
