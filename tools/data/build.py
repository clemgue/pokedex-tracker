"""Génère les données d'un jeu pour Pokédex Tracker.

Usage :  python build.py <jeu>      ex. python build.py rouge-bleu-jaune
         python build.py tous       tous les jeux de tools/data/jeux/

Sources :
- PokéAPI : Pokédex régionaux/national, noms FR/EN, types (de la génération du jeu),
  sprites de la version (normaux et chromatiques), chaînes d'évolution, Méga-évolutions.
- Poképédia : localisations (Module:Localisations/Données/<jeu>), URL des pages Pokémon et lieux.
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

# Dernier numéro national de chaque génération
MAX_ID = {1: 151, 2: 251, 3: 386, 4: 493, 5: 649, 6: 721, 7: 809, 8: 905, 9: 1025}
METHODES_DIRECTES = {"hautes_herbes", "marche", "surf", "peche", "fixe", "don", "echange_pnj", "achat",
                     "fossile", "autre"}

avertissements: list[str] = []


def avertir(msg: str) -> None:
    avertissements.append(msg)


def slug(texte: str) -> str:
    t = texte.replace("♀", "f").replace("♂", "m")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def majuscule(texte: str | None) -> str | None:
    return texte[:1].upper() + texte[1:] if texte else texte


def id_depuis_url(url: str) -> int:
    return int(url.rstrip("/").split("/")[-1])


def num_generation(nom: str) -> int:
    romains = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9}
    return romains[nom.removeprefix("generation-")]


def tri_naturel(texte: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", texte)]


def ecrire_json(chemin: Path, donnees: object, compact: bool) -> None:
    texte = json.dumps(donnees, ensure_ascii=False, separators=(",", ":")) if compact \
        else json.dumps(donnees, ensure_ascii=False, indent=1)
    chemin.write_text(texte + "\n", encoding="utf-8", newline="\n")


# --- PokéAPI : noms, types, sprites ------------------------------------------------

_cache_noms: dict[str, str] = {}


def nom_fr(url: str) -> str:
    """Nom français d'une ressource PokéAPI (type, objet, capacité, lieu…)."""
    if url not in _cache_noms:
        res = sources.pokeapi(url)
        _cache_noms[url] = sources.localized(res.get("names", []), "fr") or res["name"]
    return _cache_noms[url]


def types_pour_generation(pokemon: dict, generation: int) -> list[str]:
    """Types du Pokémon tels qu'ils étaient dans la génération du jeu (ex. Mélofée : Normal en Gén. 1)."""
    candidats = [
        (num_generation(p["generation"]["name"]), p["types"])
        for p in pokemon.get("past_types", [])
        if num_generation(p["generation"]["name"]) >= generation
    ]
    types = min(candidats, key=lambda c: c[0])[1] if candidats else pokemon["types"]
    return [nom_fr(t["type"]["url"]) for t in sorted(types, key=lambda t: t["slot"])]


def noms_especes(generation: int) -> dict[str, int]:
    """Nom français → numéro national, pour toutes les espèces jusqu'à la génération du jeu."""
    resultat = {}
    for pid in range(1, MAX_ID[generation] + 1):
        espece = sources.pokeapi(f"pokemon-species/{pid}")
        for lang in ("fr", "en"):
            nom = sources.localized(espece["names"], lang)
            if nom:
                resultat.setdefault(nom, pid)
    return resultat


def sprites_pokemon(poke: dict, config: dict) -> tuple[dict, dict]:
    """Sprites normaux et chromatiques par version (repli : sprite par défaut)."""
    gen = poke["sprites"]["versions"].get(config.get("generation_pokeapi", ""), {}) or {}
    normaux, chromas = {}, {}
    for v in config["versions"]:
        jeu = gen.get(v.get("sprites_pokeapi") or "", {}) or {}
        normal = jeu.get("front_transparent") or jeu.get("front_default") or poke["sprites"]["front_default"]
        chroma = jeu.get("front_shiny_transparent") or jeu.get("front_shiny") or poke["sprites"]["front_shiny"]
        if normal:
            normaux[v["id"]] = normal
        if chroma and config["generation"] >= 2:
            chromas[v["id"]] = chroma
    # Évite de répéter la même URL pour chaque version
    if len(set(normaux.values())) == 1:
        normaux = {"*": next(iter(normaux.values()))}
    if len(set(chromas.values())) == 1:
        chromas = {"*": next(iter(chromas.values()))}
    return normaux, chromas


def megas(espece: dict) -> list[dict]:
    """Méga-évolutions d'une espèce (variétés PokéAPI « -mega… »)."""
    resultat = []
    for var in espece["varieties"]:
        nom = var["pokemon"]["name"]
        if "-mega" not in nom:
            continue
        poke = sources.pokeapi(var["pokemon"]["url"])
        forme = sources.pokeapi(poke["forms"][0]["url"])
        libelle = sources.localized(forme.get("names", []), "fr") or sources.localized(forme.get("form_names", []), "fr")
        suffixe = nom.split("-mega", 1)[1].strip("-")
        resultat.append({"id": "mega" + (f"-{suffixe}" if suffixe else ""), "nom": libelle or f"Méga ({nom})",
                         "type": "mega"})
    return resultat


# --- PokéAPI : évolutions ------------------------------------------------------------

def objet_existe(objet: dict, generation: int) -> bool:
    gens = [num_generation(g["generation"]["name"]) for g in objet.get("game_indices", [])]
    return not gens or min(gens) <= generation


_DECLENCHEURS = {
    "shed": "(apparaît avec une Poké Ball libre et une place dans l'équipe)",
    "spin": "en faisant tourner le personnage",
    "tower-of-darkness": "en réussissant la Tour des Ténèbres",
    "tower-of-waters": "en réussissant la Tour des Eaux",
    "three-critical-hits": "après trois coups critiques en un combat",
    "take-damage": "après avoir perdu au moins 49 PV",
    "agile-style-move": "en utilisant une capacité en style Rapide",
    "strong-style-move": "en utilisant une capacité en style Puissant",
    "recoil-damage": "après avoir subi des dégâts de contrecoup",
    "use-move": "en utilisant une capacité",
    "gimmighoul-coins": "en réunissant 999 pièces",
}


def condition_evolution(details: list[dict], pre_nom: str, generation: int, especes_noms: dict[int, str]) -> str:
    textes = []
    for d in details:
        if d.get("required_pokemon_form"):
            continue  # évolution d'une forme régionale : non gérée par espèce
        if d.get("version_group"):
            gen_vg = num_generation(sources.pokeapi(d["version_group"]["url"])["generation"]["name"])
            if gen_vg > generation:
                continue  # condition introduite dans un jeu plus récent
        declencheur = d["trigger"]["name"]
        parts: list[str] = []
        if declencheur == "use-item" and d.get("item"):
            objet = sources.pokeapi(d["item"]["url"])
            if not objet_existe(objet, generation):
                continue
            nom = nom_fr(d["item"]["url"])
            parts.append(f"avec {'une ' if nom.startswith('Pierre') else ''}{nom}")
        elif declencheur == "trade":
            parts.append("par échange")
            if d.get("trade_species"):
                parts.append(f"contre {especes_noms.get(id_depuis_url(d['trade_species']['url']), 'un Pokémon précis')}")
        elif declencheur in _DECLENCHEURS:
            parts.append(_DECLENCHEURS[declencheur])
        if d.get("min_level"):
            parts.append(f"au niveau {d['min_level']}")
        elif declencheur == "level-up" and len(d) > 0:
            parts.append("en montant d'un niveau")
        if d.get("held_item"):
            parts.append(f"en tenant {nom_fr(d['held_item']['url'])}")
        if d.get("min_happiness"):
            parts.append("avec un bonheur élevé")
        if d.get("min_affection"):
            parts.append("avec une forte affection")
        if d.get("min_beauty"):
            parts.append("avec une Beauté élevée")
        if d.get("known_move"):
            parts.append(f"en connaissant {nom_fr(d['known_move']['url'])}")
        if d.get("known_move_type"):
            parts.append(f"en connaissant une capacité de type {nom_fr(d['known_move_type']['url'])}")
        if d.get("location"):
            parts.append(f"à {nom_fr(d['location']['url'])}")
        moment = {"day": "le jour", "night": "la nuit", "dusk": "au crépuscule"}.get(d.get("time_of_day") or "")
        if moment:
            parts.append(moment)
        if d.get("needs_overworld_rain"):
            parts.append("sous la pluie")
        if d.get("party_species"):
            parts.append(f"avec {especes_noms.get(id_depuis_url(d['party_species']['url']), 'un Pokémon précis')}"
                         " dans l'équipe")
        if d.get("party_type"):
            parts.append(f"avec un Pokémon de type {nom_fr(d['party_type']['url'])} dans l'équipe")
        stats = d.get("relative_physical_stats")
        if stats is not None:
            parts.append({1: "si Attaque > Défense", -1: "si Attaque < Défense", 0: "si Attaque = Défense"}[stats])
        if d.get("gender"):
            parts.append("(femelle)" if d["gender"] == 1 else "(mâle)")
        if d.get("turn_upside_down"):
            parts.append("en retournant la console")
        if declencheur == "other" and not parts:
            parts.append("(condition spéciale)")
        textes.append(f"Faire évoluer {pre_nom} " + " ".join(parts) if parts else f"Faire évoluer {pre_nom}")
    return " ou ".join(dict.fromkeys(t.strip() for t in textes)) or f"Faire évoluer {pre_nom}"


def charger_evolutions(especes: dict[int, dict], generation: int) -> list[tuple[int, int, str]]:
    """[(pré-évolution, évolution, condition)] limité aux espèces du jeu."""
    liens = []
    vues = set()
    noms = {pid: p["nom"] for pid, p in especes.items()}
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
                    liens.append((pre, post, condition_evolution(suivant["evolution_details"], noms[pre],
                                                                 generation, noms)))
                parcourir(suivant)

        parcourir(sources.pokeapi(url)["chain"])
    return liens


# --- Poképédia ---------------------------------------------------------------------

def codes_module(config: dict, src: dict) -> dict[str, str]:
    codes = {}
    for v in config["versions"]:
        if v["id"] in src["versions"]:
            for c in v.get("codes", []):
                codes[c] = v["id"]
    return codes


def charger_localisations(config: dict, par_nom: dict[str, int]):
    obtentions: list[dict] = []
    lieux: dict[str, dict] = {}
    formes: dict[int, dict[str, str]] = {}
    inconnus: dict[str, int] = {}
    exclusions = {(e["lieu"], e["pokemon"]) for e in config["corrections"].get("exclure", [])}

    for src in config["sources_pokepedia"]:
        titre = f"Module:Localisations/Données/{src['module']}"
        donnees = lua_table.parse_module(sources.pokepedia_source(titre))
        codes = codes_module(config, src)
        print(f"Poképédia : {src['module']} — {len(donnees)} lieux", flush=True)
        for cle_lieu, pokemons in donnees.items():
            page, affiche, sous_zone = norm.analyser_lieu(cle_lieu)
            lieu = lieux.setdefault(page, {"id": slug(page), "nom": affiche, "page": page})
            for nom_brut, entrees in pokemons.items():
                nom, forme = norm.analyser_nom(nom_brut)
                if (page, nom) in exclusions or (page, nom_brut) in exclusions:
                    continue
                pid = par_nom.get(nom)
                if pid is None:
                    inconnus[nom] = inconnus.get(nom, 0) + 1
                    continue
                forme_id = None
                if forme:
                    forme_id = slug(forme)
                    formes.setdefault(pid, {})[forme_id] = forme
                for entree in entrees:
                    for o in norm.normaliser_entree(entree, codes, src["versions"]):
                        zone = " — ".join(z for z in (sous_zone, majuscule(o["zone"])) if z) or None
                        obtentions.append({"pokemon": pid, "forme": forme_id, "lieu": lieu["id"], **o,
                                           "zone": zone, "detail": majuscule(o["detail"])})
    for nom, n in sorted(inconnus.items()):
        avertir(f"Pokémon Poképédia inconnu : {nom!r} ({n} entrée(s))")
    return obtentions, lieux, formes


# --- Assemblage ------------------------------------------------------------------------

def obtention(**champs) -> dict:
    base = {"pokemon": None, "forme": None, "lieu": None, "methode": None, "detail": None, "zone": None,
            "versions": [], "niveaux": None, "taux": None, "taux_texte": None, "notes": None}
    return base | champs


def ajouter_evolutions_et_echanges(config, especes, obtentions, evolutions) -> list[dict]:
    versions = [v["id"] for v in config["versions"]]
    directes = {v: {o["pokemon"] for o in obtentions if v in o["versions"] and o["methode"] in METHODES_DIRECTES}
                for v in versions}
    noms = {p["nom"]: pid for pid, p in especes.items()}
    interdites = {(noms[e["de"]], noms[e["vers"]], v)
                  for e in config["corrections"].get("evolutions_impossibles", []) for v in e["versions"]}

    # Point fixe : une évolution est obtenable si sa pré-évolution l'est
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
            ajouts.append(obtention(pokemon=post, methode="evolution", detail=condition, depuis=pre, versions=vs))

    for pid in especes:
        manquantes = [v for v in versions if pid not in obtenables[v]]
        autres = [v for v in versions if pid in obtenables[v]]
        if manquantes and autres:
            noms_v = [next(x["nom"] for x in config["versions"] if x["id"] == a) for a in autres]
            liste = ", ".join(noms_v[:-1]) + " ou " + noms_v[-1] if len(noms_v) > 1 else noms_v[0]
            ajouts.append(obtention(pokemon=pid, methode="echange_version", detail=f"Échanger depuis {liste}",
                                    versions=manquantes))
    return ajouts


def charger_pokedex(config: dict, par_nom_global: dict[str, int]) -> list[dict]:
    pokedexes = []
    for pdx in config["pokedex"]:
        if not pdx.get("pokeapi"):
            pokedexes.append({"id": pdx["id"], "nom": pdx["nom"], "entrees": None})  # rempli plus tard
            continue
        donnees = sources.pokeapi(f"pokedex/{pdx['pokeapi']}")
        entrees = []
        for e in sorted(donnees["pokemon_entries"], key=lambda e: e["entry_number"]):
            pid = id_depuis_url(e["pokemon_species"]["url"])
            if pid <= pdx.get("max", MAX_ID[config["generation"]]):
                entrees.append({"numero": e["entry_number"], "pokemon": pid})
        pokedexes.append({"id": pdx["id"], "nom": pdx["nom"], "entrees": entrees})
    return pokedexes


def construire(jeu_id: str) -> None:
    avertissements.clear()
    config = json.loads((CONFIGS / f"{jeu_id}.json").read_text(encoding="utf-8"))
    config.setdefault("corrections", {})
    generation = config["generation"]
    versions = [v["id"] for v in config["versions"]]
    print(f"\n##### {config['nom']} #####", flush=True)

    print("PokéAPI : noms des espèces…", flush=True)
    par_nom = noms_especes(generation)
    pokedexes = charger_pokedex(config, par_nom)
    obtentions, lieux, formes = charger_localisations(config, par_nom)

    for a in config["corrections"].get("ajouter", []):
        champs = {k: v for k, v in a.items() if k != "pokemon"}
        obtentions.append(obtention(pokemon=par_nom[a["pokemon"]], **champs))

    # Espèces du jeu : Pokédex + Pokémon présents dans les localisations
    ids = {e["pokemon"] for p in pokedexes if p["entrees"] for e in p["entrees"]}
    ids |= {o["pokemon"] for o in obtentions}
    for p in pokedexes:
        if p["entrees"] is None:  # Pokédex reconstruit depuis les données (absent de PokéAPI)
            p["entrees"] = [{"numero": pid, "pokemon": pid} for pid in sorted(ids)]

    print(f"PokéAPI : {len(ids)} espèces…", flush=True)
    especes: dict[int, dict] = {}
    for pid in sorted(ids):
        espece = sources.pokeapi(f"pokemon-species/{pid}")
        poke = sources.pokeapi(f"pokemon/{pid}")
        normaux, chromas = sprites_pokemon(poke, config)
        liste_formes = [{"id": fid, "nom": nom, "type": "forme"} for fid, nom in sorted(formes.get(pid, {}).items())]
        if config.get("megas"):
            liste_formes += megas(espece)
        especes[pid] = {
            "id": pid,
            "nom": sources.localized(espece["names"], "fr"),
            "nom_en": sources.localized(espece["names"], "en"),
            "types": types_pour_generation(poke, generation),
            "sprites": normaux,
            **({"sprites_chromatiques": chromas} if chromas else {}),
            "artwork": poke["sprites"]["other"]["official-artwork"]["front_default"],
            **({"formes": liste_formes} if liste_formes else {}),
            "_chaine": espece["evolution_chain"]["url"],
        }

    evolutions = charger_evolutions(especes, generation)
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

    ordre_manuel = {page: i for i, page in enumerate(config.get("ordre_lieux", []), start=1)}
    restants = sorted((l for l in lieux.values() if l["page"] not in ordre_manuel), key=lambda l: tri_naturel(l["nom"]))
    for i, l in enumerate(restants, start=len(ordre_manuel) + 1):
        if ordre_manuel:
            avertir(f"Lieu absent de ordre_lieux : {l['page']}")
        ordre_manuel[l["page"]] = i
    for page in config.get("ordre_lieux", []):
        if page not in lieux:
            avertir(f"ordre_lieux cite un lieu sans données : {page}")
    for l in lieux.values():
        titre = resolus.get(l["page"])
        l["url_pokepedia"] = sources.pokepedia_url(titre) if titre else None
        if not titre:
            avertir(f"Page Poképédia introuvable pour le lieu {l['page']}")
        l["ordre"] = ordre_manuel[l["page"]]
        l["versions"] = [v for v in versions if any(o["lieu"] == l["id"] and v in o["versions"] for o in obtentions)]

    # Sortie
    ordre_par_id = {l["id"]: l["ordre"] for l in lieux.values()}
    obtentions.sort(key=lambda o: (o["pokemon"], o["lieu"] is None, ordre_par_id.get(o["lieu"], 9999), o["methode"]))
    sortie_obtentions = []
    for i, o in enumerate(obtentions, start=1):
        o["glitch"] = o["methode"] == "bug"
        # Champs vides omis (fichier plus léger)
        sortie_obtentions.append({"id": i} | {k: v for k, v in o.items() if v is not None and k != "id"})
    for p in especes.values():
        del p["_chaine"]

    jeu = {k: config[k] for k in ("id", "nom", "generation", "region", "annee_sortie", "annee_sortie_fr", "ordre")}
    jeu["versions"] = [{k: v[k] for k in ("id", "nom", "couleur")} for v in config["versions"]]
    sortie = {
        "format": 1,
        "jeu": jeu,
        "methodes": norm.METHODES,
        "pokedex": pokedexes,
        "pokemon": [especes[pid] for pid in sorted(especes)],
        "lieux": sorted(({k: l[k] for k in ("id", "nom", "url_pokepedia", "versions", "ordre")} for l in lieux.values()),
                        key=lambda l: l["ordre"]),
        "obtentions": sortie_obtentions,
        "sources": [
            {"nom": "Poképédia", "url": "https://www.pokepedia.fr/",
             "licence": "Contenu sous licence Creative Commons BY-NC-SA"},
            {"nom": "PokéAPI", "url": "https://pokeapi.co/"},
        ],
    }
    SORTIE.mkdir(parents=True, exist_ok=True)
    ecrire_json(SORTIE / f"{jeu_id}.json", sortie, compact=True)

    index_path = SORTIE / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"jeux": []}
    index["jeux"] = [j for j in index["jeux"] if j["id"] != jeu_id] + [{**jeu, "fichier": f"{jeu_id}.json"}]
    index["jeux"].sort(key=lambda j: j["ordre"])
    ecrire_json(index_path, index, compact=False)

    controler_indisponibles(config, especes, obtentions, par_nom)
    rapport(config, especes, lieux, obtentions)


def controler_indisponibles(config, especes, obtentions, par_nom) -> None:
    """Contrôle croisé avec les listes « Indisponibles » de Poképédia."""
    for src in config["sources_pokepedia"]:
        try:
            indispo = lua_table.parse_module(
                sources.pokepedia_source(f"Module:Localisations/Données/{src['module']}/Indisponibles"))
        except KeyError:
            continue
        if not isinstance(indispo, dict):
            continue
        connus = {e["pokemon"] for e in config["corrections"].get("ecarts_pokepedia_connus", [])
                  if e["module"] == src["module"]}
        echange_partout = {o["pokemon"] for o in obtentions if o["methode"] == "echange_version"
                           and set(src["versions"]) <= set(o["versions"])}
        attendus = {par_nom[n] for n, texte in indispo.items()
                    if isinstance(texte, str) and "change" in texte and n in par_nom and n not in connus
                    and par_nom[n] in especes}
        for pid in sorted(attendus - echange_partout):
            avertir(f"[{src['module']}] Poképédia indique {especes[pid]['nom']} obtenable seulement par échange, "
                    f"le script le trouve obtenable en jeu")
        for pid in sorted(echange_partout - attendus):
            avertir(f"[{src['module']}] Le script met {especes[pid]['nom']} en échange inter-versions, "
                    f"absent de la liste Indisponibles de Poképédia")


def rapport(config, especes, lieux, obtentions) -> None:
    print(f"\n=== {config['nom']} ===")
    print(f"{len(especes)} Pokémon, {len(lieux)} lieux, {len(obtentions)} obtentions")
    autres = {}
    for o in obtentions:
        if o["methode"] == "autre":
            autres[o["detail"]] = autres.get(o["detail"], 0) + 1
    for v in [v["id"] for v in config["versions"]]:
        def a(methodes):
            return {o["pokemon"] for o in obtentions if v in o["versions"] and o["methode"] in methodes}
        en_jeu = a(METHODES_DIRECTES)
        evol = a({"evolution"}) - en_jeu
        echange = a({"echange_version"})
        reste = set(especes) - en_jeu - evol - echange
        noms = sorted(especes[x]["nom"] for x in reste)
        print(f"  {v:10} : {len(en_jeu)} en jeu, +{len(evol)} par évolution, {len(echange)} par échange,"
              f" reste {len(reste)}{' : ' + ', '.join(noms[:15]) + ('…' if len(noms) > 15 else '') if noms else ''}")
    if autres:
        print(f"  Méthodes « autre » : {dict(sorted(autres.items(), key=lambda x: -x[1])[:12])}")
    if avertissements:
        print(f"\n{len(avertissements)} avertissement(s) :")
        for a_ in avertissements[:40]:
            print("  -", a_)
        if len(avertissements) > 40:
            print(f"  … et {len(avertissements) - 40} autres")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    if sys.argv[1] == "tous":
        for chemin in sorted(CONFIGS.glob("*.json"), key=lambda c: json.loads(c.read_text(encoding="utf-8"))["ordre"]):
            construire(chemin.stem)
    else:
        construire(sys.argv[1])
