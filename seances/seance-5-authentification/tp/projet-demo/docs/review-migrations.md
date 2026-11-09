# Review des migrations et notes du TP 2

## Hôte de la base

`DATABASE_URL` pointe sur `db` et pas sur `localhost` : le backend tourne dans un conteneur, où
`localhost` est le conteneur lui-même. `db` est le nom du service Compose, résolu par le DNS
interne du réseau Docker.

## Point de contrôle de l'étape 1

`get_db` fait `commit()` après la requête et `rollback()` si une exception remonte. Si une route
lève après un `add()`, l'objet n'est donc pas en base.

Vérifié à l'étape 4 : en court-circuitant la vérification du propriétaire dans le service, un
`POST /items` avec `owner_id = 999` fait échouer le `flush()` sur la clé étrangère
(`IntegrityError`). Résultat : **500**, et 0 ligne en base (rollback). Le rollback marche, mais la
500 n'est pas le bon code : c'est une erreur du client, pas du serveur. C'est au service de
détecter ce cas. `ItemService.creer` vérifie donc que l'utilisateur existe et lève
`RessourceIntrouvable`, ce qui donne une **404** « Utilisateur 999 introuvable ».

## Le renommage `tarif_jour` -> `prix_jour` (étape 3bis)

Base de départ : 1 utilisateur et 2 items (Perceuse 5.00, Tente 12.00).

Migration générée par `--autogenerate` :

```python
def upgrade() -> None:
    op.add_column('items', sa.Column('prix_jour', sa.Numeric(precision=8, scale=2), nullable=False))
    op.drop_column('items', 'tarif_jour')
```

Alembic ne voit pas un renommage, il voit une colonne supprimée et une colonne ajoutée.

Prédiction : avec des lignes déjà en base, l'ajout d'une colonne `NOT NULL` sans valeur par défaut
doit échouer. Si la colonne avait été nullable, la migration serait passée et les deux tarifs
auraient été perdus (nouvelle colonne vide, ancienne supprimée).

Observé en l'appliquant quand même :
`psycopg.errors.NotNullViolation: column "prix_jour" of relation "items" contains null values`.
Rien n'a été appliqué (DDL transactionnel sous PostgreSQL), `alembic_version` est resté sur la
migration initiale.

Correction à la main :

```python
def upgrade() -> None:
    op.alter_column('items', 'tarif_jour', new_column_name='prix_jour')


def downgrade() -> None:
    op.alter_column('items', 'prix_jour', new_column_name='tarif_jour')
```

Après `upgrade head`, `SELECT id, titre, prix_jour FROM items` renvoie bien 5.00 et 12.00. La
contrainte `items_tarif_jour_positif` suit la colonne (`CHECK (prix_jour > 0)`), seul son nom
devient trompeur. Ensuite `downgrade -1`, suppression du fichier et retour à `tarif_jour` dans le
modèle : les tarifs sont toujours là.

## Traduction des exceptions métier

Choix : un gestionnaire global `DomainError` dans `main.py`, avec une table exception -> code HTTP.
Une seule correspondance pour toute l'API, donc des codes cohérents, et des routes qui restent
réduites à « schéma en entrée, service, schéma en sortie ».

## N+1 sur `GET /items` (étape 5)

20 items ajoutés en SQL, chacun avec un propriétaire différent (`generate_series` sur `users` puis
`items`). `GET /items?limit=50` avec `SQL_ECHO=true` :

| | Requêtes `SELECT` |
|---|---|
| Avant | 22 (1 pour les items + 1 par propriétaire distinct : 21) |
| Après `selectinload(Item.owner)` | 2 (les items, puis tous les propriétaires en un `WHERE users.id IN (...)`) |

Il n'y a pas de boucle dans le code : le N+1 vient du champ `owner: OwnerRead` de `ItemRead`.
Quand FastAPI sérialise la réponse (`response_model`), il lit `item.owner` sur chaque objet, ce
qui déclenche le chargement paresseux de la relation, une requête à chaque fois.

Remarque : les propriétaires déjà chargés ne sont pas redemandés (identity map de la session). Avec
20 items appartenant tous au même utilisateur, on n'aurait vu que 2 requêtes, et rien d'anormal.
D'où un propriétaire différent par item pour la mesure.

## Modifications imposées au frontend

| Modification dans `frontend/` | Changement de contrat qui l'a provoquée |
|---|---|
| `owner_id` fixé à un utilisateur de démo dans `POST /items` (`DEMO_USER_ID`, `# TODO séance 5`) | `ItemCreate` exige `owner_id` (un item a un propriétaire) : le formulaire affichait « owner_id : Field required » |
| `create_reservation` envoie `borrower_id` (même utilisateur de démo) | `ReservationCreate` exige `borrower_id` : « borrower_id : Field required » |
| Le formulaire de réservation gère aussi le `409` | Nouvelles règles métier : créneau déjà pris ou item indisponible |

Sans modification : la liste et le détail. `tarif_jour` est maintenant un `Numeric`, renvoyé par
l'API comme une chaîne (`"5.00"` au lieu de `5.0`), donc la page affiche « 5.00 € ». C'est même
mieux. Le nouveau champ `owner` de la réponse est simplement ignoré par le frontend.
