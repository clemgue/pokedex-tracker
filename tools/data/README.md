# Génération des données de jeu

Script Python (3.11+) qui produit `static/data/jeux/<jeu>.json`, le fichier lu par l'application.

```powershell
python -m pip install --user truststore   # une seule fois
cd tools/data
python build.py rouge-bleu-jaune
```

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

1. Créer `jeux/<jeu>.json` sur le modèle de `rouge-bleu-jaune.json` :
   versions (avec le groupe de sprites PokéAPI), Pokédex PokéAPI, modules Poképédia et codes de
   version utilisés dans ces modules (`R`, `B`…), ordre des lieux.
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
  "pokemon":  [{ "id" /* n° national */, "nom", "nom_en", "types", "sprites": { "<version>": url },
                 "artwork", "url_pokepedia" }],
  "lieux":    [{ "id", "nom", "url_pokepedia", "versions", "ordre" }],
  "obtentions": [{ "id", "pokemon", "lieu" /* ou null */, "methode", "detail", "zone",
                   "versions", "niveaux", "taux" /* % ou null */, "taux_texte",
                   "depuis" /* évolutions : pré-évolution */, "glitch" }]
}
```

- `versions` d'un lieu = versions où au moins un Pokémon y est obtenable : l'application
  n'affiche un lieu que pour ces versions.
- `echange_version` est calculé : un Pokémon inobtenable dans une version (ni capturable, ni
  par évolution) reçoit une obtention « Échanger depuis <autres versions> ».
- `glitch: true` marque les obtentions par bug (ex. Mew), à masquer par défaut.
