# Cahier des charges — Pokédex Tracker (application web)

> Version 1.0 — 20/11/2026
> Source d'inspiration : le Google Sheets « Capture Pokemon X/Y » (exemple non terminé, **pas** une source de données à importer).

---

## 1. Contexte

Le suivi de complétion du Pokédex a été esquissé dans un Google Sheets, qui sert de **maquette fonctionnelle** :

- Une ligne par Pokémon : Attrapé, N° (Central/Coastal/Mountain/National #xxx), sprite, nom FR (lien Poképédia), version (X / Y / Both / N/A), lieu, méthode d'obtention, taux de rencontre, niveaux, notes.
- Un Pokémon peut avoir plusieurs lieux de capture, saisis sur des lignes supplémentaires.
- Un second onglet amorce le même principe pour Or/Argent/Cristal.

Ce fichier n'est pas terminé et ses données sont hétérogènes : **toutes les données de l'application sont reconstruites de zéro** à partir de sources de référence (§ 8).

**Limites du tableur que l'application doit corriger**

| Limite | Réponse de l'application |
|---|---|
| Lignes « multi-lieux » empilées à la main | Une entrée par méthode d'obtention dans une base structurée |
| Données mélangées FR / EN | Données générées entièrement en français |
| Pas de vue par lieu | Vue « qu'est-ce qu'il me reste à attraper ici ? » |
| Pas de statistiques | Tableau de bord de progression |
| Un onglet par jeu, saisi à la main | Jeux = fichiers de données générés |
| Ni formes, ni Méga, ni chromatiques | Suivi des variantes (§ 6.7) |

## 2. Objectifs

1. Suivre la capture des Pokémon **jeu par jeu**, par partie.
2. Répondre vite à trois questions :
   - *Où et comment attraper ce Pokémon ?*
   - *Qu'est-ce qu'il me reste à attraper dans cette zone ?*
   - *Où en suis-je dans ma complétion ?*
3. Être **multi-jeux** dès la conception : **Rouge/Bleu/Jaune en premier**, puis tous les jeux de la série principale, génération par génération, dans l'ordre de sortie (§ 9.1). Ajouter un jeu ne demande pas de toucher au code.
4. Utilisable confortablement sur **PC et sur téléphone**, avec la même progression sur les deux.
5. Renvoyer vers **Poképédia** pour chaque Pokémon et chaque lieu.

## 3. Périmètre

### Dans le périmètre (V1)
- Catalogue Pokémon (nom FR, nom EN, n° national, sprite, types, formes).
- Données de capture par jeu (lieux, méthodes, taux, niveaux, exclusivités de version).
- Jeu de lancement : **Pokémon Rouge / Bleu / Jaune**.
- Suivi de progression par **partie** (« Ma partie Rouge », « Ma partie Jaune »).
- Liens vers les pages Poképédia des Pokémon et des lieux.
- Suivi des **formes**, **Méga-évolutions** et **chromatiques**.
- Filtres, recherche, statistiques.
- Sauvegarde / restauration de la progression (fichier JSON).

### Hors périmètre (V1)
- Comptes utilisateurs propres à l'application, serveur dédié.
- Import du Google Sheets existant.
- Combats, statistiques de combat, EV/IV, stratégie.
- Lecture automatique des sauvegardes de jeu.
- Application mobile native (le site web responsive + PWA suffit).

## 4. Utilisateurs

**Décision : application mono-utilisateur, sans compte propre à l'application.**
- La progression est un **fichier JSON stocké dans le Dropbox** de l'utilisateur, partagé entre PC et téléphone (même principe que le fichier KeePass) — voir § 6.6.
- Une copie locale (IndexedDB) permet de travailler hors ligne.
- Plusieurs parties peuvent coexister dans le même fichier (ex. une par membre de la famille).

## 5. Modèle de données

```
Pokemon        (id, num_national, nom_fr, nom_en, types[], sprite_url, sprite_shiny_url, url_pokepedia)
Forme          (id, pokemon_id, nom_fr, est_defaut, sprite_url, sprite_shiny_url)
                 ex. Prismillon « Motif Floraison », Chenisélle « Cape Sol »
Mega           (id, pokemon_id, nom_fr, mega_gemme, jeu_id, lieu_gemme_id?, condition)
Jeu            (id, nom, generation, annee_sortie, ordre, versions[])
                 ex. "Rouge/Bleu/Jaune" → [Rouge, Bleu, Jaune]
Pokedex        (id, jeu_id, nom)                             ex. Kanto ; pour X/Y : Central, Côtier, Montagne
EntreePokedex  (pokedex_id, pokemon_id, numero)              ex. Kanto #025 → Pikachu
Lieu           (id, jeu_id, nom, versions[], ordre_progression, url_pokepedia)
                 ex. Route 1 ; versions[] = versions où le lieu existe
Obtention      (id, jeu_id, pokemon_id, forme_id?, lieu_id?, methode, detail,
                versions[], taux?, niveau_min?, niveau_max?, notes)
                 versions[] ex. [Rouge] (exclusif), [Rouge, Bleu, Jaune] (commun)
                 methode ∈ {hautes_herbes, fleurs, eau, peche, grotte, evolution,
                            echange, don, safari_amis, oeuf, evenement, introuvable, …}
Partie         (id, jeu_id, version, nom, date_creation)
Capture        (partie_id, pokemon_id, forme_id?, attrape: bool, shiny: bool, date?, note?)
MegaObtenue    (partie_id, mega_id, obtenue: bool)
```

Points clés :
- **Une ligne par méthode d'obtention**.
- Une évolution est une `Obtention` de méthode `evolution` qui pointe vers le Pokémon de base + condition (niveau, pierre, bonheur…).
- Un Pokémon absent du jeu → méthode `introuvable` (visible, exclu du % atteignable, marqué « transfert requis »).
- La progression est **par partie** : on peut avoir une partie Rouge et une partie Jaune.
- **Filtrage par version** : une partie est liée à une version précise. Un lieu (ou une obtention) qui n'existe pas dans cette version **n'apparaît pas** pour cette partie (ex. un lieu propre à Cristal n'apparaît pas dans une partie Or).
- Les URL Poképédia sont stockées explicitement (pas déduites du nom), car les titres de pages ne suivent pas toujours le nom affiché (homonymies, lieux qui changent d'une génération à l'autre).
- Chromatique et formes sont suivis **en plus** du Pokémon de base : cocher une forme ou un shiny coche automatiquement le Pokémon de base comme attrapé.

## 6. Fonctionnalités

### 6.1 Pokédex (vue liste) — **priorité haute**
- Liste des Pokémon du jeu de la partie active, avec sprite, numéro, nom, case « Attrapé ».
- Bascule de Pokédex régional / national quand le jeu en a plusieurs (ex. Central / Côtier / Montagne pour X/Y).
- Cocher / décocher en un clic, sans rechargement.
- Filtres combinables :
  - attrapé / non attrapé / shiny
  - exclusivité (exclusifs de ma version, exclusifs d'une autre version)
  - méthode (herbes, pêche, évolution, échange…)
  - lieu
  - type
- Recherche par nom FR ou EN, ou par numéro.
- Tri par numéro régional, numéro national, nom.

### 6.2 Fiche Pokémon — **priorité haute**
- Toutes les méthodes d'obtention dans ce jeu : lieu, méthode, taux, niveaux, version.
- Chaîne d'évolution cliquable avec conditions.
- Formes disponibles (cases à cocher), Méga-évolution et emplacement de la Méga-Gemme.
- Bascule sprite normal / chromatique, case « Shiny obtenu ».
- **Lien vers la page Poképédia du Pokémon** ; chaque lieu cité renvoie vers sa propre page Poképédia.
- Note personnelle.

### 6.3 Vue par lieu — **priorité haute**
- Liste des lieux **de la version de la partie** dans l'ordre de progression, chacun avec un lien vers sa page Poképédia.
- Pour un lieu : Pokémon disponibles, méthode, taux, niveaux, **en mettant en avant ceux non encore attrapés**.
- Compteur « reste X à attraper ici ».

### 6.4 Tableau de bord / statistiques — **priorité moyenne**
- % de complétion global et par Pokédex régional.
- Compteurs séparés : formes, Méga-Gemmes, chromatiques.
- Répartition des manquants par méthode (« 12 nécessitent un échange »).
- Liste des **exclusifs de l'autre version** à obtenir par échange.
- Pokémon « introuvables dans ce jeu » listés à part.

### 6.5 Gestion des parties — **priorité moyenne**
- Créer / renommer / supprimer une partie (jeu + version).
- Changer de partie active.

### 6.6 Sauvegarde et synchronisation Dropbox — **priorité haute**
- La progression (toutes les parties) est un fichier `progression.json` dans le Dropbox de l'utilisateur, dossier `Applications/Pokedex Tracker/`.
- L'application accède à ce fichier via l'**API Dropbox** (connexion OAuth une seule fois par appareil, accès limité à ce dossier d'application, aucun serveur intermédiaire).
- À chaque coche : écriture immédiate dans la copie locale (IndexedDB), puis envoi vers Dropbox (regroupé sur quelques secondes).
- À l'ouverture et au retour au premier plan : lecture de la version Dropbox.
- Hors ligne : on continue en local ; synchronisation au retour du réseau.
- Conflit (fichier modifié sur les deux appareils) : fusion automatique capture par capture (la modification la plus récente l'emporte), grâce à un horodatage par capture.
- Secours : export / import manuel du fichier JSON, et mode « local seul » si on ne connecte pas Dropbox.

### 6.7 Variantes — **priorité moyenne**
- **Formes** : chaque forme d'un Pokémon disponible dans le jeu peut être cochée séparément.
- **Méga-évolutions** (jeux de 6ᵉ génération et plus) : suivi des Méga-Gemmes obtenues, avec leur emplacement.
- **Chromatiques** : case « shiny » par Pokémon (et par forme), sprite chromatique affiché.
- Les variantes non pertinentes pour un jeu sont masquées : pas de chromatique ni de formes dans Rouge/Bleu/Jaune, chromatiques dès la 2ᵉ génération, Méga uniquement dans les jeux qui les proposent.

### 6.8 Ajout de jeux — **priorité basse (V2)**
- Les données d'un jeu sont des fichiers JSON générés par script et versionnés, pas du code.
- Ajouter un jeu = lancer le script de génération pour ce jeu + compléter à la main ce que la source ne couvre pas.

## 7. Exigences non fonctionnelles

| Exigence | Cible |
|---|---|
| Langue | Interface et données en **français** ; noms EN stockés pour la recherche |
| Responsive | Utilisable d'une main sur téléphone (≥ 360 px de large) |
| Performance | Liste de ~730 Pokémon filtrable sans latence perceptible (< 100 ms) |
| Hors ligne | Fonctionne entièrement sans réseau une fois chargée (PWA) |
| Persistance | Sauvegarde immédiate à chaque coche, aucune perte ; même progression sur PC et téléphone via Dropbox |
| Style | **Façon Pokédex** (coque rouge, écran, boutons) via un thème isolé (variables CSS), pour pouvoir le retravailler après la V1 sans toucher aux composants |
| Thème clair / sombre | **Bouton de bascule** clair ↔ sombre toujours visible ; par défaut, suit le réglage de l'appareil ; le choix est mémorisé |
| Accessibilité | Contraste suffisant, navigation clavier, mode sombre |
| Coût | Hébergement gratuit, aucun serveur à maintenir |
| Droits | Sprites et données issus de sources publiques ; projet personnel non commercial ; Poképédia et PokéAPI crédités sur le site, conformément à leurs licences |

## 8. Choix techniques

- **Front** : SvelteKit (ou React + Vite), TypeScript, PWA, rendu entièrement statique.
- **Stockage de la progression** : IndexedDB (copie locale) + fichier JSON dans Dropbox via l'API Dropbox (SDK JavaScript, OAuth PKCE, accès « App folder »).
- **Hébergement** : site statique gratuit — **GitHub Pages** (ou Netlify).
- **Données de jeu**, générées par un script (Node ou Python) à partir de :
  - **PokéAPI** (source principale) : noms FR/EN, numéros, types, formes, sprites (normaux et chromatiques), Pokédex régionaux, rencontres par version (lieu, méthode, taux, niveaux) ;
  - **Poképédia** (source complémentaire) : tout ce que PokéAPI couvre mal ou pas — noms de lieux en français, dons, échanges en jeu, Pokémon obtenus par événement, emplacements des Méga-Gemmes, lieux propres à une version — et l'**URL de la page** de chaque Pokémon et de chaque lieu. Lecture via l'API MediaWiki de Poképédia, avec cache local et un débit limité pour ne pas surcharger le site ;
  - **fichiers de corrections manuelles** pour les cas restants, versionnés avec le reste.
- Les données générées sont commitées dans le dépôt : l'application n'appelle aucune API de données au moment de l'utilisation (seulement Dropbox).

## 9. Planning indicatif

| Lot | Contenu | Livrable |
|---|---|---|
| L0 | Validation du cahier des charges | CDC v1.0 |
| L1 | Script de génération des données Rouge/Bleu/Jaune (PokéAPI + Poképédia + corrections) | Données RBJ |
| L2 | Vue Pokédex + cochage + filtres + sauvegarde IndexedDB, thème Pokédex | V0.1 utilisable |
| L3 | Fiche Pokémon + vue par lieu + liens Poképédia | V0.2 |
| L4 | Synchronisation Dropbox + gestion des parties + tableau de bord | V0.3 |
| L5 | PWA hors ligne, déploiement GitHub Pages | **V1.0 (Rouge/Bleu/Jaune)** |
| L6 | Variantes (formes, Méga, shiny), activées à partir des jeux qui en ont besoin | V1.x |
| L7+ | Un lot par génération, dans l'ordre du § 9.1 | V2, V3… |

### 9.1 Ordre d'ajout des jeux (série principale, par ordre de sortie)

| Gén. | Jeux |
|---|---|
| 1 | Rouge / Bleu / Jaune |
| 2 | Or / Argent / Cristal |
| 3 | Rubis / Saphir / Émeraude ; Rouge Feu / Vert Feuille |
| 4 | Diamant / Perle / Platine ; Or HeartGold / Argent SoulSilver |
| 5 | Noir / Blanc ; Noir 2 / Blanc 2 |
| 6 | X / Y ; Rubis Oméga / Saphir Alpha |
| 7 | Soleil / Lune ; Ultra-Soleil / Ultra-Lune ; Let's Go Pikachu / Let's Go Évoli |
| 8 | Épée / Bouclier ; Diamant Étincelant / Perle Scintillante ; Légendes Pokémon : Arceus |
| 9 | Écarlate / Violet ; Légendes Pokémon : Z-A |

Let's Go et les jeux « Légendes » ont des mécaniques de capture propres (captures visibles sur la carte, combos, Pokémon Baron / Alpha…) : la liste des méthodes d'obtention sera étendue lors de leur lot.

## 10. Décisions et questions ouvertes

### Décisions (20/11/2026)
| Sujet | Décision |
|---|---|
| Utilisateurs | Mono-utilisateur, pas de compte propre à l'application |
| Synchronisation | Fichier JSON dans Dropbox via l'API Dropbox, copie locale hors ligne |
| Hébergement | En ligne, site statique gratuit (GitHub Pages / Netlify) |
| Variantes | Formes, Méga-évolutions et chromatiques suivis |
| Google Sheets | Simple exemple : pas d'import, données reconstruites de zéro |
| Sources | PokéAPI + Poképédia pour les informations manquantes |
| Liens | Chaque Pokémon et chaque lieu renvoie vers sa page Poképédia |
| Premier jeu | Rouge / Bleu / Jaune, puis toute la série principale par génération (§ 9.1) |
| Versions | Lieux et obtentions propres à une version affichés uniquement pour cette version |
| Style | Façon Pokédex, thème isolé et retravaillable après la V1 |
| Jeux inclus | Série principale + Let's Go Pikachu / Évoli + Légendes Arceus et Z-A |
| Thème | Bouton de bascule clair / sombre |

### Questions ouvertes
Aucune — le cahier des charges est prêt à passer en v1.0.
