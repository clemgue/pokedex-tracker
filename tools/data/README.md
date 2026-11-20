# Génération des données de jeu

Script Python (3.11+) qui produit `static/data/jeux/<jeu>.json`, le fichier lu par l'application.

```powershell
python -m pip install --user truststore   # une seule fois
cd tools/data
python build.py rouge-bleu-jaune          # un jeu
python build.py tous                      # tous les jeux de jeux/*.json
```

Le premier passage interroge PokéAPI pour chaque espèce (jusqu'à 1 025) : comptez une quinzaine
de minutes ; les suivants utilisent le cache et prennent quelques secondes.

Les réponses de PokéAPI et de Poképédia sont mises en cache dans `tools/data/.cache/`
(non versionné). Supprimer ce dossier force un rafraîchissement complet. Débit limité :
1 requête/s vers Poképédia, 5/s vers PokéAPI.

## Sources

| Donnée | Source |
|---|---|
| Liste du Pokédex régional, noms FR/EN, types de la génération, sprites de la version, chaînes d'évolution | PokéAPI |
| Lieux, méthodes, niveaux, taux, exclusivités de version, dons, échanges, casino, fossiles, Pokémon fixes | Poképédia — `Module:Localisations/Données/<jeu>` |
| URL des pages Pokémon et lieux | Poképédia (titres vérifiés, redirections suivies) |
| Ordre de progression des lieux, corrections | `jeux/<jeu>.json` (saisi à la main) |

## Ajouter un jeu

1. Créer `jeux/<jeu>.json` sur le modèle des fichiers existants :
   - `versions` : identifiant, nom, couleur, `codes` (suffixes de version utilisés dans les modules
     Poképédia, ex. `R`, `B`, `RuO`), `sprites_pokeapi` (groupe de sprites PokéAPI, ou `null`) ;
   - `pokedex` : Pokédex PokéAPI (`pokeapi`), `max` pour limiter le national à la génération,
     ou sans `pokeapi` pour un Pokédex reconstruit à partir des Pokémon présents ;
   - `megas: true` pour suivre les Méga-évolutions ;
   - `sources_pokepedia` : modules et versions qu'ils couvrent ;
   - `ordre_lieux` (facultatif) : ordre de progression ; sinon tri naturel des noms.
2. Lancer `python build.py <jeu>` et lire le rapport : chaque avertissement signale une donnée à
   vérifier (nom inconnu, page Poképédia introuvable, lieu sans ordre, écart avec la liste
   « Indisponibles » de Poképédia).
3. Traiter les écarts dans `corrections` :
   - `exclure` : retirer une entrée Poképédia (ex. Ossatueur fantôme, non capturable) ;
   - `ajouter` : ajouter une obtention absente des sources (ex. Mew par événement) ;
   - `evolutions_impossibles` : bloquer une évolution dans une version (ex. Pikachu de Jaune) ;
   - `ecarts_pokepedia_connus` : documenter une incohérence connue entre deux pages Poképédia.

## Format de sortie (`format: 1`)

```jsonc
{
  "jeu":      { "id", "nom", "generation", "region", "annee_sortie", "annee_sortie_fr", "ordre",
                "versions": [{ "id", "nom", "couleur" }] },
  "methodes": { "hautes_herbes": "Hautes herbes", … },          // libellés des méthodes
  "pokedex":  [{ "id", "nom", "entrees": [{ "numero", "pokemon" }] }],
  "pokemon":  [{ "id" /* n° national */, "nom", "nom_en", "types",
                 "sprites": { "<version>" | "*": url }, "sprites_chromatiques"?, "artwork",
                 "url_pokepedia", "formes"?: [{ "id", "nom", "type": "forme" | "mega" }] }],
  "lieux":    [{ "id", "nom", "url_pokepedia", "versions", "ordre" }],
  "obtentions": [{ "id", "pokemon", "forme"?, "lieu"?, "methode", "detail"?, "zone"?,
                   "versions", "niveaux"?, "taux"? /* % */, "taux_texte"?, "notes"?,
                   "depuis"? /* évolutions : pré-évolution */, "glitch" }]
}
```

- Les champs vides sont omis (`?`) pour alléger les fichiers.
- `sprites["*"]` : sprite identique pour toutes les versions du jeu.
- Méthode `autre` : milieu Poképédia non classé automatiquement, texte conservé dans `detail`
  (le rapport de génération liste les plus fréquents).

- `versions` d'un lieu = versions où au moins un Pokémon y est obtenable : l'application
  n'affiche un lieu que pour ces versions.
- `echange_version` est calculé : un Pokémon inobtenable dans une version (ni capturable, ni
  par évolution) reçoit une obtention « Échanger depuis <autres versions> ».
- `glitch: true` marque les obtentions par bug (ex. Mew), à masquer par défaut.
