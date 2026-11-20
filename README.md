# Pokédex Tracker

Application web de suivi de captures Pokémon, jeu par jeu, façon Pokédex.
Cahier des charges : [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md).

## Démarrer

Prérequis : Node.js 20+ (LTS), Python 3.11+ (uniquement pour régénérer les données).

```powershell
npm install
npm run dev        # http://localhost:5173
```

## Commandes

| Commande | Rôle |
|---|---|
| `npm run dev` | Serveur de développement |
| `npm run check` | Vérification TypeScript / Svelte |
| `npm run build` | Site statique dans `build/` |
| `npm run donnees` | Régénère les données Rouge/Bleu/Jaune (voir [tools/data](tools/data/README.md)) |

Pour GitHub Pages (site servi depuis `/<dépôt>/`) :

```powershell
$env:BASE_PATH = '/pokedex-tracker'; npm run build
```

## Publier sur GitHub Pages

Le workflow [.github/workflows/deploiement.yml](.github/workflows/deploiement.yml) vérifie, teste,
construit et publie le site à chaque envoi sur `main`.

1. Créer un dépôt GitHub (ex. `pokedex-tracker`) et y envoyer ce dépôt local :
   `git remote add origin https://github.com/<compte>/pokedex-tracker.git` puis `git push -u origin main`.
2. Sur GitHub : **Settings → Pages → Source : GitHub Actions**.
3. Le site est publié à `https://<compte>.github.io/pokedex-tracker/`.
4. (Optionnel) **Settings → Secrets and variables → Actions → Variables** : `DROPBOX_APP_KEY` = clé
   d'application Dropbox, pour qu'elle soit préremplie (sinon, la saisir dans *Réglages*).
5. Ajouter `https://<compte>.github.io/pokedex-tracker/` aux *Redirect URIs* de l'application Dropbox.

## Synchronisation Dropbox

La progression est un fichier `progression.json` dans le dossier d'application Dropbox. Il faut créer
une fois une application Dropbox (*Scoped access*, *App folder*, permissions `files.content.read` et
`files.content.write`, Redirect URIs = adresses du site) : la marche à suivre détaillée est dans
l'écran *Réglages* de l'application. Connexion OAuth 2 PKCE : aucun secret n'est stocké.

## Hors ligne (PWA)

L'application est installable (« Ajouter à l'écran d'accueil ») et fonctionne sans réseau :
le code et l'index sont préchargés, chaque jeu et les sprites sont mis en cache à la première
consultation. Les icônes se régénèrent avec `python tools/icones.py` (Pillow).

## Organisation

```
src/
  lib/
    theme.css          Thème Pokédex (variables CSS clair/sombre) — à retoucher pour changer le style
    types.ts           Types des données de jeu et de la progression
    donnees.ts         Chargement des fichiers de jeu
    db.ts              Stockage local (IndexedDB)
    etat.svelte.ts     État global : parties, partie active, captures
    analyse.ts         Calculs par version (méthodes, lieux, exclusivités)
    composants/        Bouton Poké Ball, badges de type, bascule de thème, nouvelle partie
  routes/
    +page.svelte       Vue Pokédex (liste, filtres, recherche)
    parties/           Gestion des parties
static/data/jeux/      Données générées (une par jeu + index.json)
tools/data/            Script Python de génération des données
```

Navigation par ancre (`#/parties`) : le site fonctionne en pur statique, sans configuration serveur.

## Sources

Données : [Poképédia](https://www.pokepedia.fr/) (CC BY-NC-SA) et [PokéAPI](https://pokeapi.co/).
Projet personnel non commercial ; Pokémon est une marque de Nintendo, Creatures et Game Freak.
