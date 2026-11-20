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
