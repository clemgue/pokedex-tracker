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
    raise ValueError(f"Milieu Poképédia non reconnu : {milieu!r}")


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


def normaliser_entree(entree: dict, codes: dict[str, str], versions: list[str]) -> list[dict]:
    """Une entrée Poképédia → une obtention par jeu de valeurs distinct (versions fusionnées)."""
    methode, detail, zone = analyser_milieu(entree["milieu"])
    taux = valeurs_par_version(entree.get("taux", ""), codes, versions)
    niveaux = valeurs_par_version(entree.get("niveau", ""), codes, versions)

    par_valeurs: dict[tuple, list[str]] = {}
    for v in versions:
        if v not in taux:
            continue  # absent de cette version
        cle = (taux[v], niveaux.get(v))
        par_valeurs.setdefault(cle, []).append(v)

    resultat = []
    for (taux_brut, niveau), vs in par_valeurs.items():
        taux_pct, taux_texte = analyser_taux(taux_brut)
        if methode == "fossile":
            detail, taux_texte = f"Ressusciter le {taux_texte}", None
        if niveau == "Identique":
            niveau = None
        if taux_texte == "Unique" and methode in ("marche", "hautes_herbes", "surf"):
            methode = "fixe"
        resultat.append({
            "methode": methode,
            "detail": detail,
            "zone": zone,
            "versions": vs,
            "niveaux": niveau or None,
            "taux": taux_pct,
            "taux_texte": taux_texte,
        })
    return resultat


def analyser_lieu(cle: str) -> tuple[str, str, str | None]:
    """"Parc Safari (Kanto)@zone est" → (page, nom affiché, sous-zone)."""
    page_aff, _, sous_zone = cle.partition("@")
    page, _, affiche = page_aff.partition("|")
    if not affiche:
        affiche = re.sub(r" \((Kanto|Johto|Hoenn|Sinnoh|Unys|Kalos|Alola|Galar|Paldea)\)$", "", page)
    return page, affiche, (sous_zone[:1].upper() + sous_zone[1:]) if sous_zone else None
