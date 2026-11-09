# Comment appliquer les migrations

## Les quatre questions

**1. Deuxième `docker compose up`, base déjà à jour ?**
`alembic upgrade head` ne trouve rien à appliquer : il se connecte, lit `alembic_version` et
s'arrête. Dans les deux options, ça coûte une seconde au démarrage. Vérifié avec le service
`migrate` : ses logs n'affichent aucune ligne `Running upgrade`, il sort en `Exited (0)` et le
backend démarre.

**2. Une migration qui échoue ?**
Testé avec une migration volontairement cassée (`SELECT * FROM table_inexistante`) :
`docker compose up` affiche `service "migrate" didn't complete successfully: exit 1`,
`docker compose ps -a` montre `migrate Exited (1)`, l'erreur SQL est dans
`docker compose logs migrate`, et **le backend ne démarre pas**. Avec `entrypoint.sh` et
`set -e`, le conteneur backend s'arrêterait aussi, mais l'erreur serait mélangée aux logs de
l'API. Et avec un `restart: always`, il redémarrerait en boucle.

**3. Trois instances du backend en même temps sur une base non migrée ?**
Avec `entrypoint.sh`, les trois lancent `alembic upgrade head` en parallèle. Alembic ne pose pas de
verrou : la première crée les tables, les autres risquent de tomber sur un `relation already exists`
ou un conflit sur `alembic_version` et de planter (pas testé en local, le port 8000 publié empêche
plusieurs instances). Avec un service (ou un job) `migrate` séparé, la migration tourne une seule
fois, avant le démarrage des instances.

**4. Et le `--reload` ?**
Avec `migrate`, rien ne change : le backend garde sa commande `uvicorn ... --reload`. Le reload ne
relance pas les migrations, il faut faire `docker compose up -d` (qui relance `migrate`) après en
avoir ajouté une. Avec `entrypoint.sh`, la `command:` du compose remplace le `CMD` de l'image. Si
le script est lancé par le `CMD`, le mettre en `--reload` dans le compose fait sauter les
migrations. Il faudrait passer par `ENTRYPOINT` et un `exec "$@"` à la fin du script.

## Choix : service `migrate`

On garde le service `migrate` dédié (même image que le backend, `command: alembic upgrade head`,
le backend attend `service_completed_successfully`). La migration est une étape à part : on la lit
dans ses propres logs, on peut la relancer seule (`docker compose run --rm migrate`), un échec
bloque clairement le backend, et elle ne tourne qu'une fois même avec plusieurs instances de l'API.
Le prix à payer est un service de plus dans le `docker-compose.yml`, ce qui reste raisonnable.
