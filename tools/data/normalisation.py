"""Normalisation des entrées des modules `Module:Localisations/Données/<jeu>` de Poképédia.

Une entrée Poképédia ressemble à :
    {"milieu": "Étage,, Deuxième", "niveau": "32-36", "taux": "24, R, 14, B"}

- `milieu` : méthode + précisions. Les virgules ont un sens :
  "Mot,suffixe-pluriel,, Préfixe"  (ex. "Étage,s,, Troisième et quatrième" → « 3e et 4e étages »)
  "Mot, précision"                 (ex. "Donné, après le Badge Foudre")
- `niveau` / `taux` : listes séparées par ", " ; un code de version (R, B…) placé après des
  valeurs les rattache à cette version, les valeurs non suivies d'un code valent pour toutes.
"""

from __future__ import annotations

import re

# --- Méthodes -----------------------------------------------------------------

METHODES = {
    "hautes_herbes": "Hautes herbes",
    "marche": "En marchant",
    "surf": "Sur l'eau",
    "peche": "Pêche",
    "don": "Don",
    "echange_pnj": "Échange en jeu",
    "achat": "Achat",
    "fossile": "Fossile",
    "fixe": "Pokémon fixe",
    "evolution": "Évolution",
    "echange_version": "Échange depuis une autre version",
    "evenement": "Événement",
    "bug": "Bug",
    "autre": "Autre méthode",
}

_ZONES_INTERIEURES = {"Rez-de-chaussée", "Étage", "Sous-sol"}
_ORDINAUX = {
    "Premier": "1er", "Première": "1re", "Deuxième": "2e", "Second": "2e", "Seconde": "2e",
    "Troisième": "3e", "Quatrième": "4e", "Cinquième": "5e", "Sixième": "6e",
    "Septième": "7e", "Huitième": "8e", "Neuvième": "9e", "Dixième": "10e",
}
_MOTS_TAUX = {"Un": 1, "Deux": 2, "Trois": 3, "Quatre": 4, "Cinq": 5, "Six": 6, "Sept": 7, "Huit": 8}


def wiki_vers_texte(texte: str) -> str:
    """Retire la syntaxe wiki : [[Page|Texte]] → Texte, {{Objet|Nautile|...}} → Nautile, {{P}} → ₽."""
    texte = texte.replace("{{P}}", "₽")
    texte = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", texte)
    texte = re.sub(r"\{\{Objet\|([^|}]*)[^}]*\}\}", r"\1", texte)
    texte = re.sub(r"\{\{[^|}]*\|([^|}]*)[^}]*\}\}", r"\1", texte)
    return texte.strip()


def _ordinaux(texte: str) -> str:
    for mot, abr in _ORDINAUX.items():
        texte = re.sub(rf"\b{mot}\b", abr, texte)
        texte = re.sub(rf"\b{mot.lower()}\b", abr, texte)
    return texte


def zone_interieure(milieu: str) -> str:
    """"Étage,, Premier" → "1er étage" ; "Étage,s,, Troisième et quatrième" → "3e et 4e étages"."""
    tete, _, prefixe = milieu.partition(",, ")
    mot, _, pluriel = tete.partition(",")
    if not prefixe:
        return mot
    return f"{_ordinaux(prefixe)} {mot.lower()}{pluriel}"


def analyser_milieu(milieu: str) -> tuple[str, str | None, str | None]:
    """Renvoie (méthode, détail, zone)."""
    tete = milieu.split(",")[0].strip()
    precision = milieu[len(tete):].lstrip(",").strip() or None
    if precision:
        precision = wiki_vers_texte(precision.strip("() "))

    if tete in _ZONES_INTERIEURES:
        return "marche", None, zone_interieure(milieu)
    if tete == "Hautes herbes":
        return "hautes_herbes", None, precision
    if tete == "En marchant":
        return "marche", None, precision
    if tete == "Sur l'eau":
        return "surf", None, precision
    if tete.startswith("Pêche à la "):
        return "peche", tete.removeprefix("Pêche à la "), precision
    if tete == "Donné":
        return "don", precision, None
    if tete == "Dans une Poké Ball":
        return "don", f"Dans une Poké Ball, {precision}" if precision else "Dans une Poké Ball", None
    if tete == "Échange":
        return "echange_pnj", precision, None
    if tete == "À acheter":
        return "achat", precision, None
    if tete == "Fossiles":
        return "fossile", None, None
    if tete == "Fausses Balls au sol":
        return "fixe", "Fausses Poké Balls au sol", None
    if tete == "Rencontre":
        return "fixe", None, precision
    if tete == "Spécial":
        return "fixe", None, precision
    if tete == "Pokéflûte":
        return "fixe", "Réveiller avec la Pokéflûte", None
    if tete == "Bug":
        return "bug", f"Bug {precision}" if precision else None, None
    return classer_par_mots_cles(milieu)


# Règles génériques (jeux récents) : premier motif trouvé dans le milieu, en minuscules.
_REGLES = [
    ("bug", ("bug",)),
    ("fossile", ("fossile",)),
    ("echange_pnj", ("échange",)),
    ("don", ("donné", "dans une poké ball", "cadeau", "œuf")),
    ("achat", ("acheter", "achat")),
    ("peche", ("pêche",)),
    ("surf", ("sur l'eau", "surf", "dans l'eau", "remous", "plongée", "algues", "sous l'eau")),
    ("fixe", ("rencontre", "spécial", "fixe", "baron", "fausses balls", "faux objet", "flûte", "pokéflûte")),
    ("hautes_herbes", ("herbe", "fleurs", "hordes", "troupeaux", "essaim", "poké radar", "navi-dex")),
    ("marche", ("rez-de-chaussée", "étage", "sous-sol", "en marchant", "au sol", "sable", "poussière",
                "sol accidenté", "toits", "marécage", "dans les airs", "arbre", "coup d'boule", "éclate-roc",
                "ombre", "canal", "volants", "vols d'oiseaux", "embuscade", "tas de baies")),
]


def classer_par_mots_cles(milieu: str) -> tuple[str, str | None, str | None]:
    """Classe un milieu quelconque ; « autre » (texte conservé) si rien ne correspond."""
    texte = wiki_vers_texte(re.sub(r"\[\[Fichier:[^\]]*\]\]", "", milieu)).replace(",,", ",").strip(" ,")
    texte = re.sub(r"\s*,\s*", ", ", texte)
    if not texte:
        return "marche", None, None  # jeux en monde ouvert : Pokémon visibles, sans milieu précisé
    bas = texte.lower()
    for methode, motifs in _REGLES:
        if any(m in bas for m in motifs):
            return methode, texte, None
    return "autre", texte, None


# --- Valeurs par version --------------------------------------------------------

def valeurs_par_version(texte: str, codes: dict[str, str], versions: list[str]) -> dict[str, str]:
    """"3-5, R, 3, B" → {"rouge": "3-5", "bleu": "3"} ; "10, 15, 20" → toutes versions : "10, 15, 20"."""
    resultat: dict[str, str] = {}
    groupe: list[str] = []
    for jeton in [j.strip() for j in str(texte).split(", ")]:
        if jeton in codes:
            if groupe:
                resultat[codes[jeton]] = ", ".join(groupe)
                groupe = []
        else:
            groupe.append(jeton)
    if groupe:
        commun = ", ".join(groupe)
        for v in versions:
            resultat.setdefault(v, commun)
    return resultat


def analyser_taux(texte: str) -> tuple[float | None, str | None]:
    """Renvoie (taux en %, texte) : "35" → (35, None) ; "500 jetons" → (None, "500 jetons")."""
    texte = wiki_vers_texte(texte)
    try:
        return float(texte.replace(",", ".")), None
    except ValueError:
        pass
    if texte in _MOTS_TAUX:
        n = _MOTS_TAUX[texte]
        return None, f"{n} exemplaire{'s' if n > 1 else ''}"
    return None, texte


_LIBELLES_TAUX = {"taux-matin": "Matin", "taux-jour": "Jour", "taux-jou": "Jour", "taux-nuit": "Nuit",
                  "taux-printemps": "Printemps", "taux-été": "Été", "taux-automne": "Automne",
                  "taux-hiver": "Hiver", "taux-renfort": "Renfort"}
_CHAMPS_NOTES = {"horaire": "Horaire", "météo": "Météo", "emplacement": "Emplacement",
                 "précision-taux": "Précision", "renfort": "Renfort", "blocs": "Blocs", "attente": "Attente"}


def _taux_composes(entree: dict, codes: dict[str, str], versions: list[str]) -> dict[str, str]:
    """Taux par moment/saison (« taux-matin »…) → texte par version : « Matin 10 % · Nuit 5 % »."""
    parts: dict[str, list[str]] = {v: [] for v in versions}
    for cle, libelle in _LIBELLES_TAUX.items():
        if cle not in entree:
            continue
        for v, val in valeurs_par_version(entree[cle], codes, versions).items():
            if val and val not in ("-", "—", "0"):
                pct, txt = analyser_taux(val)
                parts[v].append(f"{libelle} {str(pct).removesuffix('.0').replace('.', ',')} %" if pct is not None
                                else f"{libelle} {txt}")
    return {v: " · ".join(p) for v, p in parts.items() if p}


def notes_entree(entree: dict) -> str | None:
    notes = [f"{lib} : {wiki_vers_texte(str(entree[c]))}" for c, lib in _CHAMPS_NOTES.items()
             if entree.get(c) not in (None, "")]
    return " ; ".join(notes) or None


def normaliser_entree(entree: dict, codes: dict[str, str], versions: list[str]) -> list[dict]:
    """Une entrée Poképédia → une obtention par jeu de valeurs distinct (versions fusionnées)."""
    methode, detail, zone = analyser_milieu(entree.get("milieu", ""))
    if "taux" in entree:
        taux = valeurs_par_version(entree["taux"], codes, versions)
    else:
        composes = _taux_composes(entree, codes, versions)
        # Sans aucun taux (jeux en monde ouvert) : présent dans toutes les versions du module
        taux = composes if composes else {v: "" for v in versions}
    niveaux = valeurs_par_version(entree.get("niveau", ""), codes, versions)
    notes = notes_entree(entree)

    par_valeurs: dict[tuple, list[str]] = {}
    for v in versions:
        if v not in taux:
            continue  # absent de cette version
        cle = (taux[v], niveaux.get(v))
        par_valeurs.setdefault(cle, []).append(v)

    resultat = []
    for (taux_brut, niveau), vs in par_valeurs.items():
        if " · " in taux_brut:  # texte déjà composé (taux selon le moment)
            nombres = [float(n.replace(",", ".")) for n in re.findall(r"(\d+(?:,\d+)?) %", taux_brut)]
            taux_pct, taux_texte = (max(nombres) if nombres else None), taux_brut
        elif taux_brut in ("", "-", "—", "?"):
            taux_pct, taux_texte = None, None
        else:
            taux_pct, taux_texte = analyser_taux(taux_brut)
        if methode == "fossile":
            detail, taux_texte = f"Ressusciter le {taux_texte}", None
        if niveau in ("Identique", "-", "—", "?"):
            niveau = None
        m = methode
        if taux_texte == "Unique" and m in ("marche", "hautes_herbes", "surf", "autre"):
            m = "fixe"
        resultat.append({
            "methode": m,
            "detail": detail,
            "zone": zone,
            "versions": vs,
            "niveaux": niveau or None,
            "taux": taux_pct,
            "taux_texte": taux_texte,
            "notes": notes,
        })
    return resultat


def analyser_nom(nom: str) -> tuple[str, str | None]:
    """« Miaouss forme(Galar) » → (« Miaouss », « Galar ») ; « Pikachu » → (« Pikachu », None)."""
    m = re.match(r"^(.*?)\s+forme\((.*)\)\s*$", nom)
    return (m.group(1).strip(), m.group(2).strip()) if m else (nom.strip(), None)


def analyser_lieu(cle: str) -> tuple[str, str, str | None]:
    """"Parc Safari (Kanto)@zone est" → (page, nom affiché, sous-zone)."""
    page_aff, _, sous_zone = cle.partition("@")
    page, _, affiche = page_aff.partition("|")
    if not affiche:
        affiche = re.sub(r" \((Kanto|Johto|Hoenn|Sinnoh|Unys|Kalos|Alola|Galar|Hisui|Paldea)\)$", "", page)
    return page, affiche, (sous_zone[:1].upper() + sous_zone[1:]) if sous_zone else None
