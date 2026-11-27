---
name: fiche-feature
description: Rédige la fiche d'une nouvelle fonctionnalité de GearShare dans
  docs/features/<nom>/fiche.md. À utiliser quand on demande de cadrer, spécifier,
  décrire, rédiger la spec ou la PRD d'une feature, ou quand on dit « on va ajouter … »,
  avant tout plan ou tout code.
---

# Rédiger une fiche feature

1. Ne rédige rien tout de suite. Pose d'abord des questions, une série à la fois (3 à 5
   questions), sur : le problème, les utilisateurs, les cas de refus, ce qui est hors périmètre.
   Attends les réponses avant la série suivante.
2. Lis le code concerné (modèles, services, routers, migrations) pour remplir l'évaluation
   technique. Signale explicitement tout prérequis absent de l'existant (une route, un statut,
   une table qui n'existe pas encore).
3. Remplis docs/templates/fiche-feature.md et écris le résultat dans
   docs/features/<nom>/fiche.md, avec le statut « brouillon ».
4. Dans la section « Options et compromis », propose des options mais laisse la colonne
   « Décision » vide : c'est à moi de trancher.
5. Le problème est formulé sans solution, et l'hypothèse a une métrique mesurable.
6. Chaque user story a au moins un critère de refus (non connecté, pas le droit, ressource
   absente, doublon, donnée invalide, mauvais état).
7. Les critères d'acceptation décrivent ce qu'on observe de l'extérieur : ils ne mentionnent
   ni route, ni code HTTP, ni nom de table ou de classe.
8. Numérote les critères `AC-<story>.<n>` (ex. AC-02.3) : ils serviront à nommer les tests.
9. N'écris aucun code et ne crée aucun autre fichier que la fiche.
10. Termine en listant les questions ouvertes et ce que tu n'as pas pu vérifier dans le code.
