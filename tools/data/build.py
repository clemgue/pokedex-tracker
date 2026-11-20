"""Génère les données d'un jeu pour Pokédex Tracker.

Usage :  python build.py rouge-bleu-jaune

Sources :
- PokéAPI : liste du Pokédex régional, noms FR/EN, types (de la génération du jeu),
  sprites de la version, chaînes d'évolution.
- Poképédia : localisations (Module:Localisations/Données/<jeu>), URL des pages
  Pokémon et lieux.
- tools/data/jeux/<jeu>.json : configuration, ordre des lieux, corrections manuelles.

Sortie : static/data/jeux/<jeu>.json + static/data/jeux/index.json
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import lua_table
import normalisation as norm
import sources

RACINE = Path(__file__).resolve().parents[2]
CONFIGS = Path(__file__).parent / "jeux"
SORTIE = RACINE / "static" / "data" / "jeux"

avertissements: list[str] = []


def avertir(msg: str) -> None:
    avertissements.append(msg)


def slug(texte: str) -> str:
    t = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    t = t.replace("♀", "f").replace("♂", "m")
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def majuscule(texte: str | None) -> str | None:
    return texte[:1].upper() + texte[1:] if texte else texte


def id_depuis_url(url: str) -> int:
    return int(url.rstrip("/").split("/")[-1])


def num_generation(nom: str) -> int:
    romains = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9}
    return romains[nom.removeprefix("generation-")]


# --- PokéAPI -------------------------------------------------------------------

_cache_types: dict[str, str] = {}


def type_fr(nom_en: str) -> str:
    if nom_en not in _cache_types:
        _cache_types[nom_en] = sources.localized(sources.pokeapi(f"type/{nom_en}")["names"], "fr") or nom_en
    return _cache_types[nom_en]


def types_pour_generation(pokemon: dict, generation: int) -> list[str]:
    """Types du Pokémon tels qu'ils étaient dans la génération du jeu (ex. Mélofée : Normal en Gén. 1)."""
    candidats = [
        (num_generation(p["generation"]["name"]), p["types"])
        for p in pokemon.get("past_types", [])
        if num_generation(p["generation"]["name"]) >= generation
    ]
    types = min(candidats, key=lambda c: c[0])[1] if candidats else pokemon["types"]
    return [type_fr(t["type"]["name"]) for t in sorted(types, key=lambda t: t["slot"])]


def charger_pokemon(config: dict) -> tuple[dict[int, dict], list[dict]]:
    """Renvoie ({id_national: pokémon}, [pokédex])."""
    generation = config["generation"]
    especes: dict[int, dict] = {}
    pokedexes = []
    for pdx in config["pokedex"]:
        donnees = sources.pokeapi(f"pokedex/{pdx['pokeapi']}")
        entrees = []
        for e in sorted(donnees["pokemon_entries"], key=lambda e: e["entry_number"]):
            pid = id_depuis_url(e["pokemon_species"]["url"])
            entrees.append({"numero": e["entry_number"], "pokemon": pid})
            especes[pid] = {}
        pokedexes.append({"id": pdx["id"], "nom": pdx["nom"], "entrees": entrees})

    print(f"PokéAPI : {len(especes)} espèces…", flush=True)
    for pid in sorted(especes):
        espece = sources.pokeapi(f"pokemon-species/{pid}")
        poke = sources.pokeapi(f"pokemon/{pid}")
        sprites_gen = poke["sprites"]["versions"].get(config["generation_pokeapi"], {})
        sprites = {}
        for v in config["versions"]:
            jeu = sprites_gen.get(v["sprites_pokeapi"], {})
            url = jeu.get("front_transparent") or jeu.get("front_default")
            if url:
                sprites[v["id"]] = url
            else:
                avertir(f"Sprite {v['id']} manquant pour #{pid}")
        especes[pid] = {
            "id": pid,
            "nom": sources.localized(espece["names"], "fr"),
            "nom_en": sources.localized(espece["names"], "en"),
            "types": types_pour_generation(poke, generation),
            "sprites": sprites,
            "artwork": poke["sprites"]["other"]["official-artwork"]["front_default"],
            "_chaine": espece["evolution_chain"]["url"],
        }
    return especes, pokedexes


def objet_existe(objet: dict, generation: int) -> bool:
    """Un objet existe dans la génération s'il y a un index de jeu dans cette génération ou avant."""
    gens = [num_generation(g["generation"]["name"]) for g in objet.get("game_indices", [])]
    return not gens or min(gens) <= generation


def condition_evolution(details: list[dict], pre_nom: str, generation: int) -> str:
    textes = []
    for d in details:
        if d.get("required_pokemon_form"):
            continue  # évolution propre à une forme régionale (gérée avec les formes, lot V1.x)
        if d.get("version_group"):
            gen_vg = num_generation(sources.pokeapi(d["version_group"]["url"])["generation"]["name"])
            if gen_vg > generation:
                continue  # condition introduite dans un jeu plus récent
        declencheur = d["trigger"]["name"]
        if declencheur == "level-up" and d.get("min_level"):
            textes.append(f"Faire évoluer {pre_nom} au niveau {d['min_level']}")
        elif declencheur == "use-item" and d.get("item"):
            objet = sources.pokeapi(d["item"]["url"])
            if not objet_existe(objet, generation):
                continue  # ex. Fil de Liaison (Gén. 8) pour les jeux plus anciens
            nom = sources.localized(objet["names"], "fr")
            article = "une " if nom.startswith("Pierre") else ""
            textes.append(f"Faire évoluer {pre_nom} avec {article}{nom}")
        elif declencheur == "trade":
            textes.append(f"Faire évoluer {pre_nom} par échange")
        else:
            textes.append(f"Faire évoluer {pre_nom}")
    return " ou ".join(dict.fromkeys(textes)) or f"Faire évoluer {pre_nom}"


def charger_evolutions(especes: dict[int, dict], generation: int) -> list[tuple[int, int, str]]:
    """[(pré-évolution, évolution, condition)] limité aux espèces du jeu."""
    liens = []
    vues = set()
    for p in especes.values():
        url = p["_chaine"]
        if url in vues:
            continue
        vues.add(url)

        def parcourir(noeud: dict) -> None:
            pre = id_depuis_url(noeud["species"]["url"])
            for suivant in noeud["evolves_to"]:
                post = id_depuis_url(suivant["species"]["url"])
                if pre in especes and post in especes:
                    liens.append((pre, post, condition_evolution(suivant["evolution_details"],
                                                                 especes[pre]["nom"], generation)))
                parcourir(suivant)

        parcourir(sources.pokeapi(url)["chain"])
    return liens


# --- Poképédia -----------------------------------------------------------------

def charger_localisations(config: dict, par_nom: dict[str, int]) -> tuple[list[dict], dict[str, dict]]:
    obtentions: list[dict] = []
    lieux: dict[str, dict] = {}
    exclusions = {(e["lieu"], e["pokemon"]) for e in config["corrections"].get("exclure", [])}

    for src in config["sources_pokepedia"]:
        titre = f"Module:Localisations/Données/{src['module']}"
        donnees = lua_table.parse_module(sources.pokepedia_source(titre))
        print(f"Poképédia : {src['module']} — {len(donnees)} lieux", flush=True)
        for cle_lieu, pokemons in donnees.items():
            page, affiche, sous_zone = norm.analyser_lieu(cle_lieu)
            lieu = lieux.setdefault(page, {"id": slug(page), "nom": affiche, "page": page})
            for nom, entrees in pokemons.items():
                if (page, nom) in exclusions:
                    continue
                pid = par_nom.get(nom)
                if pid is None:
                    avertir(f"Pokémon Poképédia inconnu : {nom!r} ({page})")
                    continue
                for entree in entrees:
                    for o in norm.normaliser_entree(entree, src["codes"], src["versions"]):
                        zone = " — ".join(z for z in (sous_zone, majuscule(o["zone"])) if z) or None
                        obtentions.append({"pokemon": pid, "lieu": lieu["id"], **o, "zone": zone,
                                           "detail": majuscule(o["detail"])})
    return obtentions, lieux


# --- Assemblage ------------------------------------------------------------------

def ajouter_evolutions_et_echanges(config: dict, especes: dict[int, dict], obtentions: list[dict],
                                   evolutions: list[tuple[int, int, str]]) -> list[dict]:
    versions = [v["id"] for v in config["versions"]]
    directes = {v: {o["pokemon"] for o in obtentions if v in o["versions"] and o["methode"] != "bug"}
                for v in versions}

    # Évolutions : disponibles dans une version si la pré-évolution y est obtenable (point fixe)
    # Évolutions impossibles dans certaines versions (ex. Pikachu de Jaune et la Pierre Foudre)
    interdites = {(e["de"], e["vers"], v)
                  for e in config["corrections"].get("evolutions_impossibles", []) for v in e["versions"]}
    noms = {p["nom"]: pid for pid, p in especes.items()}
    interdites = {(noms[a], noms[b], v) for a, b, v in interdites}

    obtenables = {v: set(directes[v]) for v in versions}
    change = True
    while change:
        change = False
        for pre, post, _ in evolutions:
            for v in versions:
                if pre in obtenables[v] and post not in obtenables[v] and (pre, post, v) not in interdites:
                    obtenables[v].add(post)
                    change = True

    ajouts = []
    for pre, post, condition in evolutions:
        vs = [v for v in versions if pre in obtenables[v] and (pre, post, v) not in interdites]
        if vs:
            ajouts.append({"pokemon": post, "lieu": None, "methode": "evolution", "detail": condition,
                           "depuis": pre, "zone": None, "versions": vs, "niveaux": None,
                           "taux": None, "taux_texte": None})

    # Échange depuis une autre version : pour les versions où l'espèce est inobtenable
    for pid in especes:
        manquantes = [v for v in versions if pid not in obtenables[v]]
        autres = [v for v in versions if pid in obtenables[v]]
        if manquantes and autres:
            noms_v = [next(x["nom"] for x in config["versions"] if x["id"] == a) for a in autres]
            noms = ", ".join(noms_v[:-1]) + " ou " + noms_v[-1] if len(noms_v) > 1 else noms_v[0]
            ajouts.append({"pokemon": pid, "lieu": None, "methode": "echange_version",
                           "detail": f"Échanger depuis {noms}", "zone": None, "versions": manquantes,
                           "niveaux": None, "taux": None, "taux_texte": None})
    return ajouts


def construire(jeu_id: str) -> None:
    config = json.loads((CONFIGS / f"{jeu_id}.json").read_text(encoding="utf-8"))
    versions = [v["id"] for v in config["versions"]]

    especes, pokedexes = charger_pokemon(config)
    par_nom = {p["nom"]: pid for pid, p in especes.items()}
    evolutions = charger_evolutions(especes, config["generation"])
    obtentions, lieux = charger_localisations(config, par_nom)

    for a in config["corrections"].get("ajouter", []):
        obtentions.append({"pokemon": par_nom[a["pokemon"]], "lieu": a.get("lieu"), "methode": a["methode"],
                           "detail": a.get("detail"), "zone": a.get("zone"), "versions": a["versions"],
                           "niveaux": a.get("niveaux"), "taux": a.get("taux"), "taux_texte": a.get("taux_texte")})

    obtentions += ajouter_evolutions_et_echanges(config, especes, obtentions, evolutions)

    # Liens Poképédia (titres vérifiés, redirections suivies)
    print("Poképédia : vérification des pages…", flush=True)
    titres = [p["nom"] for p in especes.values()] + [l["page"] for l in lieux.values()]
    resolus = sources.pokepedia_resolve(titres)
    for p in especes.values():
        titre = resolus.get(p["nom"])
        p["url_pokepedia"] = sources.pokepedia_url(titre) if titre else None
        if not titre:
            avertir(f"Page Poképédia introuvable pour le Pokémon {p['nom']}")
    ordre = {page: i for i, page in enumerate(config["ordre_lieux"], start=1)}
    for l in lieux.values():
        titre = resolus.get(l["page"])
        l["url_pokepedia"] = sources.pokepedia_url(titre) if titre else None
        if not titre:
            avertir(f"Page Poképédia introuvable pour le lieu {l['page']}")
        l["ordre"] = ordre.get(l["page"])
        if l["ordre"] is None:
            avertir(f"Lieu absent de ordre_lieux : {l['page']}")
        l["versions"] = [v for v in versions
                         if any(o["lieu"] == l["id"] and v in o["versions"] for o in obtentions)]
    for page in ordre:
        if page not in lieux:
            avertir(f"ordre_lieux cite un lieu sans données : {page}")

    # Sortie
    ordre_par_id = {l["id"]: l["ordre"] or 999 for l in lieux.values()}
    obtentions.sort(key=lambda o: (o["pokemon"], o["lieu"] is None, ordre_par_id.get(o["lieu"], 999), o["methode"]))
    for i, o in enumerate(obtentions, start=1):
        o["id"] = i
        o["glitch"] = o["methode"] == "bug"
    for p in especes.values():
        del p["_chaine"]

    sortie = {
        "format": 1,
        "jeu": {k: config[k] for k in ("id", "nom", "generation", "region", "annee_sortie", "annee_sortie_fr", "ordre")}
               | {"versions": [{k: v[k] for k in ("id", "nom", "couleur")} for v in config["versions"]]},
        "methodes": norm.METHODES,
        "pokedex": pokedexes,
        "pokemon": [especes[pid] for pid in sorted(especes)],
        "lieux": sorted(({k: l[k] for k in ("id", "nom", "url_pokepedia", "versions", "ordre")} for l in lieux.values()),
                        key=lambda l: (l["ordre"] or 999, l["nom"])),
        "obtentions": [{"id": o["id"], **{k: v for k, v in o.items() if k != "id"}} for o in obtentions],
        "sources": [
            {"nom": "Poképédia", "url": "https://www.pokepedia.fr/",
             "licence": "Contenu sous licence Creative Commons BY-NC-SA"},
            {"nom": "PokéAPI", "url": "https://pokeapi.co/"},
        ],
    }
    SORTIE.mkdir(parents=True, exist_ok=True)
    # JSON compact : ces fichiers sont téléchargés par l'application
    (SORTIE / f"{jeu_id}.json").write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")),
                                           encoding="utf-8")

    index_path = SORTIE / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"jeux": []}
    index["jeux"] = [j for j in index["jeux"] if j["id"] != jeu_id] + [
        {**sortie["jeu"], "fichier": f"{jeu_id}.json"}]
    index["jeux"].sort(key=lambda j: j["ordre"])
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

    # Contrôle croisé avec les listes « Indisponibles » de Poképédia
    for src in config["sources_pokepedia"]:
        try:
            indispo = lua_table.parse_module(
                sources.pokepedia_source(f"Module:Localisations/Données/{src['module']}/Indisponibles"))
        except KeyError:
            continue
        # La liste Indisponibles d'un module couvre les Pokémon absents de TOUTES ses versions
        # (les exclusivités d'une version n'y figurent pas).
        connus = {e["pokemon"] for e in config["corrections"].get("ecarts_pokepedia_connus", [])
                  if e["module"] == src["module"]}
        echange_partout = {o["pokemon"] for o in obtentions if o["methode"] == "echange_version"
                           and set(src["versions"]) <= set(o["versions"])}
        attendus = {par_nom[n] for n, texte in indispo.items()
                    if "change" in texte and n in par_nom and n not in connus}
        for pid in sorted(attendus - echange_partout):
            avertir(f"[{src['module']}] Poképédia indique {especes[pid]['nom']} obtenable seulement par échange, "
                    f"le script le trouve obtenable en jeu")
        for pid in sorted(echange_partout - attendus):
            avertir(f"[{src['module']}] Le script met {especes[pid]['nom']} en échange inter-versions, "
                    f"absent de la liste Indisponibles de Poképédia")

    # Rapport
    print(f"\n=== {config['nom']} ===")
    print(f"{len(especes)} Pokémon, {len(lieux)} lieux, {len(obtentions)} obtentions")
    for v in versions:
        def a(methodes):
            return {o["pokemon"] for o in obtentions if v in o["versions"] and o["methode"] in methodes}
        sauvages = a({"hautes_herbes", "marche", "surf", "peche", "fixe", "don", "echange_pnj", "achat", "fossile"})
        evol = a({"evolution"}) - sauvages
        echange = a({"echange_version"})
        autres = set(especes) - sauvages - evol - echange
        print(f"  {v:6} : {len(sauvages)} en jeu, +{len(evol)} par évolution, {len(echange)} par échange inter-versions,"
              f" reste {len(autres)} : {sorted(especes[x]['nom'] for x in autres)}")
    if avertissements:
        print(f"\n{len(avertissements)} avertissement(s) :")
        for a_ in avertissements:
            print("  -", a_)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    construire(sys.argv[1])
