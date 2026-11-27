# Fiche feature — Avis sur les prêts terminés

**Statut** : validée
**Auteurs** : Antoine Li
**Date** : 2026-11-27

## 1. Le problème

- Les emprunteurs hésitent à emprunter du matériel à quelqu'un qu'ils ne connaissent pas : rien
  sur une annonce ne leur dit si les prêts précédents se sont bien passés.
- Les prêteurs sérieux n'ont aucun moyen de se distinguer des autres.
- Signal : enquête utilisateurs, 6 utilisateurs sur 10 disent hésiter à emprunter à un inconnu ;
  plusieurs prêteurs regrettent de ne pas pouvoir « se faire une réputation ».

## 2. L'hypothèse et la métrique

> *Si les emprunteurs peuvent noter un prêt terminé et que la note moyenne est visible sur
> l'annonce, alors les visiteurs réserveront plus souvent le matériel d'un prêteur qu'ils ne
> connaissent pas.*

- **Métrique** : taux de conversion consultation d'annonce -> réservation, comparé entre les
  annonces avec au moins un avis et celles sans avis, sur un mois.
- **Métrique secondaire** : part des prêts terminés qui reçoivent un avis (si elle est très
  faible, la moyenne affichée n'a pas de sens).

## 3. Les utilisateurs concernés

- Emprunteur : veut savoir à qui il a affaire avant de réserver, et pouvoir dire comment son
  prêt s'est passé.
- Prêteur (propriétaire du matériel) : veut indiquer que le matériel lui a été rendu, et se
  construire une réputation.
- Visiteur non connecté : consulte les annonces, voit la réputation.

## 4. User stories et critères d'acceptation

### US-01 — Clôturer un prêt

En tant que prêteur, je veux indiquer qu'un prêt est terminé (matériel rendu) afin que
l'emprunteur puisse laisser un avis.

```text
AC-01.1  Given une réservation active du vélo d'Alice, empruntée par Bob
         When  Alice clôture la réservation
         Then  la réservation passe au statut « terminée »

AC-01.2  Given une réservation active
         When  un visiteur non connecté tente de la clôturer
         Then  la demande est refusée, il est invité à se connecter, le statut est inchangé

AC-01.3  Given une réservation active du vélo d'Alice, empruntée par Bob
         When  Bob (l'emprunteur) ou Carol (sans lien) tente de la clôturer
         Then  la demande est refusée pour défaut de droits, le statut reste « active »

AC-01.4  Given une réservation annulée ou déjà terminée
         When  Alice tente de la clôturer
         Then  la demande est refusée car la réservation n'est plus active, le statut est inchangé

AC-01.5  Given aucune réservation avec cet identifiant
         When  Alice tente de la clôturer
         Then  la demande est refusée, la réservation est signalée introuvable
```

### US-02 — Laisser un avis

En tant qu'emprunteur, je veux noter un prêt terminé et laisser un commentaire afin d'informer
les futurs emprunteurs.

```text
AC-02.1  Given une réservation terminée empruntée par Bob
         When  Bob laisse une note de 4 avec le commentaire « Vélo impeccable »
         Then  l'avis est enregistré avec sa note, son commentaire et Bob comme auteur

AC-02.2  Given une réservation terminée empruntée par Bob
         When  Bob laisse une note de 5 sans commentaire
         Then  l'avis est enregistré sans commentaire

AC-02.3  Given une réservation terminée
         When  un visiteur non connecté tente de laisser un avis
         Then  la demande est refusée, il est invité à se connecter, aucun avis n'est créé

AC-02.4  Given une réservation terminée empruntée par Bob
         When  Alice (la prêteuse) ou Carol (sans lien) tente de laisser un avis
         Then  la demande est refusée pour défaut de droits, aucun avis n'est créé

AC-02.5  Given une réservation encore active, ou annulée, empruntée par Bob
         When  Bob tente de laisser un avis
         Then  la demande est refusée car le prêt n'est pas terminé, aucun avis n'est créé

AC-02.6  Given Bob a déjà laissé un avis sur cette réservation
         When  il tente d'en laisser un second
         Then  la demande est refusée, le premier avis est inchangé

AC-02.7  Given une réservation terminée empruntée par Bob
         When  Bob envoie une note de 0, de 6 ou de 3,5
         Then  la demande est refusée comme invalide, aucun avis n'est créé

AC-02.8  Given une réservation terminée empruntée par Bob
         When  Bob envoie un commentaire de plus de 1000 caractères
         Then  la demande est refusée comme invalide, aucun avis n'est créé

AC-02.9  Given aucune réservation avec cet identifiant
         When  Bob tente de laisser un avis
         Then  la demande est refusée, la réservation est signalée introuvable
```

### US-03 — Voir la réputation d'une annonce

En tant que visiteur, je veux voir la note moyenne, le nombre d'avis et les commentaires d'une
annonce afin de décider si je réserve.

```text
AC-03.1  Given le vélo d'Alice a reçu deux avis, notés 4 et 5
         When  n'importe qui, même non connecté, consulte la réputation de l'annonce
         Then  il voit une moyenne de 4,5 et 2 avis, avec la note, le commentaire et le nom
               de l'auteur de chacun

AC-03.2  Given une annonce sans aucun avis
         When  on consulte sa réputation
         Then  on voit 0 avis et aucune moyenne (pas de 0/5 trompeur)

AC-03.3  Given aucune annonce avec cet identifiant
         When  on consulte sa réputation
         Then  l'annonce est signalée introuvable

AC-03.4  Given un avis laissé sur le vélo d'Alice et un autre sur la tente de Carol
         When  on consulte la réputation du vélo
         Then  seul l'avis du vélo est compté
```

## 5. Hors périmètre

- Modification ou suppression d'un avis (un avis est définitif).
- Notation de l'emprunteur par le prêteur (V2).
- Modération des commentaires, signalement d'un avis abusif.
- Réponse du prêteur à un avis.
- Réputation agrégée d'un prêteur sur toutes ses annonces.
- Affichage de la moyenne dans la liste des annonces, tri ou filtre par note.
- Clôture automatique d'une réservation à sa date de fin.

## 6. Évaluation technique

### 6.1. Impacts par couche

| Couche | Impact |
|---|---|
| Base de données (tables, contraintes, migration) | Nouvelle table `avis` liée à `reservations` (clé étrangère), une seule ligne par réservation (`UNIQUE`), note entre 1 et 5 (`CHECK`). Le statut `terminee` existe déjà dans le `CHECK` de `reservations` : pas de migration pour la clôture. |
| Modèle métier (règles, où elles sont vérifiées) | Clôture : propriétaire de l'item, réservation active. Avis : emprunteur seulement, réservation terminée, pas de doublon. Dans les services, comme l'annulation. « Réservation terminée » ne peut pas être un `CHECK` (il porte sur une autre table) : vérifié dans le service uniquement. |
| API (routes, codes de statut) | Étendre la modification de statut d'une réservation à « terminée ». Création d'un avis sur une réservation. Lecture publique de la réputation d'un item (moyenne, nombre, liste). |
| Autorisation (qui a le droit de quoi) | Clôturer : propriétaire de l'item seulement (l'annulation reste ouverte aux deux). Avis : emprunteur seulement. Lecture : tout le monde. |
| Frontend (écrans, formulaires) | Page de l'annonce : bouton « Clôturer » pour le prêteur, formulaire d'avis pour l'emprunteur sur ses prêts terminés, bloc réputation. Le frontend doit savoir qui est connecté (appel à `/auth/me`). |
| Prérequis absents de l'existant | **Aucune route ne permet de terminer une réservation** : le statut `terminee` est prévu en base mais la modification n'accepte que l'annulation. Le frontend ne connaît pas l'identifiant de l'utilisateur connecté. |

### 6.2. Risques

- Sécurité : un utilisateur qui note un prêt qui n'est pas le sien (à bloquer côté service),
  un prêteur qui clôture puis se note lui-même (bloqué : seul l'emprunteur note). Commentaire
  affiché sur l'annonce : échappement HTML (Jinja2 le fait par défaut).
- Données existantes : aucune réservation n'est terminée aujourd'hui, la table `avis` part vide.
  La migration ne touche pas aux tables existantes.
- Performance : moyenne calculée à chaque lecture de l'annonce, une requête d'agrégat sur les
  avis d'un item. Les réservations sont indexées par item, volume négligeable pour le projet.
- Concurrence : deux avis envoyés en même temps sur la même réservation passent le contrôle du
  service ; c'est le `UNIQUE` qui garantit le refus du second.

### 6.3. Taille estimée

M : une table et une migration, deux règles métier, trois routes, un écran à enrichir. Le
prérequis (clôture) ajoute une petite étape mais réutilise le `PATCH` existant.

## 7. Options et compromis

| Question | Option A | Option B | Décision et raison |
|---|---|---|---|
| Quand un prêt est-il terminé ? | Le prêteur le clôture explicitement | Automatiquement à la date de fin | A. Seul le prêteur sait si le matériel est rendu ; une clôture automatique permettrait de noter un prêt qui s'est mal fini avant le retour. |
| Qui peut clôturer ? | Le prêteur seulement | Prêteur ou emprunteur | A. C'est le prêteur qui récupère le matériel ; si l'emprunteur pouvait clôturer, il pourrait se donner le droit de noter tout de suite. |
| Contenu d'un avis | Note de 1 à 5 + commentaire optionnel | Note seule | A. La note seule ne dit pas pourquoi ; le commentaire reste optionnel pour ne pas décourager. |
| Nombre d'avis | Un par réservation | Un par couple emprunteur/item | A. Chaque prêt est une expérience différente, et c'est simple à garantir avec un `UNIQUE`. |
| Avis modifiable ? | Non | Oui, pendant N jours | A pour le MVP : pas de route ni de règle de délai ; on verra si les utilisateurs le demandent. |
| Moyenne | Calculée à la lecture | Stockée sur l'item, mise à jour à chaque avis | A. Pas de risque de désynchronisation ; le volume ne justifie pas une colonne dénormalisée. |
| Où afficher la réputation ? | Sur l'annonce | Sur l'annonce et la liste | A. Suffit pour tester l'hypothèse (le visiteur décide sur la page de l'annonce). |
| Afficher les commentaires ? | Moyenne et nombre seulement | Moyenne, nombre et liste des avis | B. Sinon le commentaire est collecté pour rien ; c'est une lecture simple. |
| Clôture avant la date de fin ? | Autorisée | Interdite | A. Un retour anticipé arrive ; le prêteur est seul juge. |

## 8. MVP et itérations suivantes

- **MVP** : US-01 (clôturer), US-02 (laisser un avis), US-03 (voir la réputation sur l'annonce).
- **V2** : notation de l'emprunteur par le prêteur ; moyenne dans la liste des annonces.
- **Plus tard / backlog** : modération et signalement, réponse du prêteur, réputation agrégée
  par prêteur, clôture automatique avec délai de contestation.

## 9. Questions ouvertes

- Faut-il afficher un avis anonymisé (prénom seulement) ? Pour le MVP on affiche le
  `display_name`, déjà public sur les annonces.
- Que faire si un utilisateur est supprimé ? Aujourd'hui un emprunteur ne peut pas être
  supprimé (pas de `ON DELETE` sur `reservations.borrower_id`), la question ne se pose pas.
