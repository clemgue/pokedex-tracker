"""Étapes de progression de chaque jeu : badges d'Arène (ou équivalents), Conseil 4, Maître.

Sources : Poképédia, pages « Badge », « Conseil 4 », « Maître Pokémon », « Capitaine d'Épreuve »,
« Doyen », « Gardien (Hisui) », « Ligue de Galar », « Royale Z-A ».

Chaque nom de personnage et de lieu est résolu sur Poképédia (redirections comprises) pour
produire un lien ; un nom introuvable est signalé.

Usage : python progression.py   →   static/data/progression.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import sources

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "static" / "data" / "progression.json"


def E(id, nom, personne=None, lieu=None, type=None, versions=None, note=None, page=None, page_lieu=None):
    """Une étape. `page` / `page_lieu` : titre Poképédia s'il diffère du nom affiché."""
    return {k: v for k, v in {
        "id": id, "nom": nom, "personne": personne, "lieu": lieu, "type": type, "versions": versions,
        "note": note, "_page": page or personne, "_page_lieu": page_lieu or lieu,
    }.items() if v is not None}


def G(id, titre, etapes):
    return {"id": id, "titre": titre, "etapes": etapes}


def ligue(c4, maitre, page_maitre=None, versions_maitre=None, titre="Ligue Pokémon", autres=()):
    """Conseil 4 : liste de (personne, type[, page]) ; le Maître clôt l'aventure (id « maitre »)."""
    etapes = []
    for i, m in enumerate(c4, 1):
        personne, type_, *page = m
        if isinstance(personne, list):  # membre différent selon la version : [(nom, versions, page)]
            for nom, versions, pg in personne:
                etapes.append(E(f"c4-{i}", "Conseil 4", nom, type=type_, versions=versions, page=pg))
        else:
            etapes.append(E(f"c4-{i}", "Conseil 4", personne, type=type_, page=page[0] if page else None))
    if isinstance(maitre, list):
        for nom, versions, pg in maitre:
            etapes.append(E("maitre", "Maître", nom, versions=versions, page=pg))
    else:
        etapes.append(E("maitre", "Maître", maitre, page=page_maitre, versions=versions_maitre))
    etapes.extend(autres)
    return G("ligue", titre, etapes)


# --- Kanto -------------------------------------------------------------------------------

def arenes_kanto(johto=False):
    """Badges de Kanto ; `johto=True` : version Or/Argent/Cristal et HGSS (Jeannine, Blue, Îles Écume)."""
    return G("kanto", "Badges de Kanto" if johto else "Arènes", [
        E("roche", "Badge Roche", "Pierre", "Argenta", "Roche", page="Pierre (Kanto)"),
        E("cascade", "Badge Cascade", "Ondine", "Azuria", "Eau"),
        E("foudre", "Badge Foudre", "Major Bob", "Carmin sur Mer", "Électrik"),
        E("prisme", "Badge Prisme", "Erika", "Céladopole", "Plante"),
        E("ame", "Badge Âme", "Jeannine" if johto else "Koga", "Parmanie", "Poison"),
        E("marais", "Badge Marais", "Morgane", "Safrania", "Psy"),
        E("volcan", "Badge Volcan", "Auguste", "Îles Écume" if johto else "Cramois'Île", "Feu"),
        E("terre", "Badge Terre", "Blue" if johto else "Giovanni", "Jadielle", "Sol"),
    ])


C4_KANTO = [("Olga", "Glace", "Olga (Conseil 4)"), ("Aldo", "Combat"), ("Agatha", "Spectre", "Agatha (Conseil 4)"),
            ("Peter", "Dragon")]


# --- Johto -------------------------------------------------------------------------------

ARENES_JOHTO = G("johto", "Badges de Johto", [
    E("zephyr", "Badge Zéphyr", "Albert", "Mauville", "Vol", page="Albert (Johto)"),
    E("essaim", "Badge Essaim", "Hector", "Écorcia", "Insecte", page="Hector (Johto)"),
    E("plaine", "Badge Plaine", "Blanche", "Doublonville", "Normal", page="Blanche (Johto)"),
    E("brume", "Badge Brume", "Mortimer", "Rosalia", "Spectre"),
    E("choc", "Badge Choc", "Chuck", "Irisia", "Combat"),
    E("mineral", "Badge Minéral", "Jasmine", "Oliville", "Acier"),
    E("glacier", "Badge Glacier", "Frédo", "Acajou", "Glace"),
    E("lever", "Badge Lever", "Sandra", "Ébènelle", "Dragon", page="Sandra (Johto)"),
])
C4_JOHTO = [("Clément", "Psy"), ("Koga", "Poison"), ("Aldo", "Combat"), ("Marion", "Ténèbres")]
RED = E("red", "Combat final", "Red", "Mont Argenté", note="Après avoir obtenu les 16 Badges")


# --- Hoenn -------------------------------------------------------------------------------

def arenes_hoenn(emeraude=False):
    pluie = [E("pluie", "Badge Pluie", "Marc", "Atalanopolis", "Eau", page="Marc (Hoenn)")]
    if emeraude:
        pluie = [E("pluie", "Badge Pluie", "Marc", "Atalanopolis", "Eau", versions=["rubis", "saphir"], page="Marc (Hoenn)"),
                 E("pluie", "Badge Pluie", "Juan", "Atalanopolis", "Eau", versions=["emeraude"])]
    return G("arenes", "Arènes", [
        E("roche", "Badge Roche", "Roxanne", "Mérouville", "Roche"),
        E("poing", "Badge Poing", "Bastien", "Myokara", "Combat", page="Bastien (Champion)"),
        E("dynamo", "Badge Dynamo", "Voltère", "Lavandia", "Électrik"),
        E("chaleur", "Badge Chaleur", "Adriane", "Vermilava", "Feu"),
        E("balancier", "Badge Balancier", "Norman", "Clémenti-Ville", "Normal"),
        E("plume", "Badge Plume", "Alizée", "Cimetronelle", "Vol"),
        E("esprit", "Badge Esprit", "Lévy & Tatia", "Algatia", "Psy"),
        *pluie,
    ])


C4_HOENN = [("Damien", "Ténèbres", "Damien (Conseil 4)"), ("Spectra", "Spectre"), ("Glacia", "Glace"),
            ("Aragon", "Dragon")]


# --- Sinnoh ------------------------------------------------------------------------------

def arenes_sinnoh(platine: list[str] | None = None):
    """Platine inverse l'ordre : Kiméra 3e, puis Mélina et Lovis."""
    tete = [
        E("charbon", "Badge Charbon", "Pierrick", "Charbourg", "Roche"),
        E("foret", "Badge Forêt", "Flo", "Vestigion", "Plante"),
    ]
    milieu = [
        E("pave", "Badge Pavé", "Mélina", "Voilaroc", "Combat"),
        E("palustre", "Badge Palustre", "Lovis", "Verchamps", "Eau"),
        E("fantome", "Badge Fantôme", "Kiméra", "Unionpolis", "Spectre"),
    ]
    if platine:
        autres = [v for v in ["diamant", "perle"]]
        milieu = [
            E("fantome", "Badge Fantôme", "Kiméra", "Unionpolis", "Spectre", versions=platine),
            *[{**e, "versions": autres + platine} for e in milieu[:2]],
            E("fantome", "Badge Fantôme", "Kiméra", "Unionpolis", "Spectre", versions=autres),
        ]
    fin = [
        E("mine", "Badge Mine", "Charles", "Joliberges", "Acier", page="Charles (Champion)"),
        E("glacon", "Badge Glaçon", "Gladys", "Frimapic", "Glace"),
        E("phare", "Badge Phare", "Tanguy", "Rivamar", "Électrik"),
    ]
    return G("arenes", "Arènes", tete + milieu + fin)


C4_SINNOH = [("Aaron", "Insecte", "Aaron (Conseil 4)"), ("Terry", "Sol", "Terry (Conseil 4)"), ("Adrien", "Feu"),
             ("Lucio", "Psy")]

# --- Unys --------------------------------------------------------------------------------

C4_UNYS = [("Anis", "Spectre"), ("Pieris", "Ténèbres"), ("Percila", "Psy", "Percila (Conseil 4)"), ("Kunz", "Combat")]

ARENES_NB = G("arenes", "Arènes", [
    E("triple", "Badge Triple", "Rachid, Armando ou Noa", "Ogoesse", note="Le Champion dépend du Pokémon de départ choisi",
      page="Rachid"),
    E("basique", "Badge Basique", "Aloé", "Maillard", "Normal"),
    E("elytre", "Badge Élytre", "Artie", "Volucité", "Insecte"),
    E("volt", "Badge Volt", "Inezia", "Méanville", "Électrik"),
    E("sismique", "Badge Sismique", "Bardane", "Port Yoneuve", "Sol"),
    E("jet", "Badge Jet", "Carolina", "Parsemille", "Vol", page="Carolina (Unys)"),
    E("stalactite", "Badge Stalactite", "Zhu", "Flocombe", "Glace"),
    E("mythe", "Badge Mythe", "Watson", "Janusia", "Dragon", versions=["noir"]),
    E("mythe", "Badge Mythe", "Iris", "Janusia", "Dragon", versions=["blanc"], page="Iris (Unys)"),
])

ARENES_N2B2 = G("arenes", "Arènes", [
    E("basique", "Badge Basique", "Tcheren", "Pavonnay", "Normal"),
    E("toxique", "Badge Toxique", "Strykna", "Ondes-sur-Mer", "Poison"),
    E("elytre", "Badge Élytre", "Artie", "Volucité", "Insecte"),
    E("volt", "Badge Volt", "Inezia", "Méanville", "Électrik"),
    E("sismique", "Badge Sismique", "Bardane", "Port Yoneuve", "Sol"),
    E("jet", "Badge Jet", "Carolina", "Parsemille", "Vol", page="Carolina (Unys)"),
    E("mythe", "Badge Mythe", "Watson", "Janusia", "Dragon"),
    E("vague", "Badge Vague", "Amana", "Papeloa", "Eau"),
])

# --- Kalos -------------------------------------------------------------------------------

ARENES_KALOS = G("arenes", "Arènes", [
    E("coleoptere", "Badge Coléoptère", "Violette", "Neuvartault", "Insecte", page="Violette (Kalos)"),
    E("mur", "Badge Mur", "Lino", "Relifac-le-Haut", "Roche"),
    E("lutte", "Badge Lutte", "Cornélia", "Yantreizh", "Combat"),
    E("vegetal", "Badge Végétal", "Amaro", "Port Tempères", "Plante"),
    E("tension", "Badge Tension", "Lem", "Illumis", "Électrik"),
    E("nymphe", "Badge Nymphe", "Valériane", "Romant-sous-Bois", "Fée"),
    E("psychisme", "Badge Psychisme", "Astera", "Flusselles", "Psy"),
    E("iceberg", "Badge Iceberg", "Urup", "Auffrac-les-Congères", "Glace"),
])
C4_KALOS = [("Thyméo", "Acier"), ("Dracéna", "Dragon"), ("Malva", "Feu"), ("Narcisse", "Eau")]

# --- Alola -------------------------------------------------------------------------------


def tour_des_iles(ultra: bool):
    epreuves = [
        E("altheo", "Épreuve", "Althéo", "Grotte Verdoyante", "Normal"),
        E("pectorius", "Grande Épreuve de Mele-Mele", "Pectorius", "Mele-Mele", "Combat"),
        E("nephie", "Épreuve", "Néphie", "Colline Clapotis", "Eau"),
        E("kiawe", "Épreuve", "Kiawe", "Parc Volcanique", "Feu"),
        E("barbara", "Épreuve", "Barbara", "Jungle Sombrefeuille", "Plante"),
        E("alyxia", "Grande Épreuve d'Akala", "Alyxia", "Akala", "Roche"),
        E("chrys", "Épreuve", "Chrys", "Observatoire", "Électrik"),
        E("margie", "Épreuve", "Margie", "Ancien site Bradley Prix", "Spectre"),
        E("danh", "Grande Épreuve d'Ula-Ula", "Danh", "Ula-Ula", "Ténèbres"),
    ]
    if ultra:
        epreuves.append(E("olea", "Épreuve", "Oléa", "Village Flottant", "Fée"))
    epreuves.append(E("paulie", "Grande Épreuve de Poni", "Paulie", "Poni", "Sol"))
    return G("epreuves", "Tour des Îles", epreuves)


# --- Galar -------------------------------------------------------------------------------

ARENES_GALAR = G("arenes", "Défi des Arènes", [
    E("plante", "Badge Plante", "Percy", "Greenbury", "Plante"),
    E("eau", "Badge Eau", "Donna", "Skifford", "Eau"),
    E("feu", "Badge Feu", "Kabu", "Motorby", "Feu"),
    E("old-chister", "Badge Combat", "Faïza", "Old Chister", "Combat", versions=["epee"]),
    E("old-chister", "Badge Spectre", "Alistair", "Old Chister", "Spectre", versions=["bouclier"]),
    E("fee", "Badge Fée", "Sally", "Corrifey", "Fée"),
    E("ludester", "Badge Roche", "Chaz", "Ludester", "Roche", versions=["epee"], page="Chaz (Galar)"),
    E("ludester", "Badge Glace", "Lona", "Ludester", "Glace", versions=["bouclier"]),
    E("tenebres", "Badge Ténèbres", "Peterson", "Smashings", "Ténèbres"),
    E("dragon", "Badge Dragon", "Roy", "Kickenham", "Dragon"),
])
POKE_MASTERS = G("ligue", "Poké Masters", [
    E("medailles", "Tournoi des Médaillés", note="Demi-finale et finale contre les autres Challengers",
      page="Ligue de Galar", personne=None),
    E("champions", "Tournoi des Champions", note="Contre les Champions d'Arène", page="Ligue de Galar"),
    E("maitre", "Maître", "Tarak"),
])

# --- Paldea ------------------------------------------------------------------------------

ARENES_PALDEA = G("arenes", "Voie de la Victoire — Arènes", [
    E("insecte", "Badge d'Arène Insecte", "Éra", "Sevaro", "Insecte"),
    E("plante", "Badge d'Arène Plante", "Colza", "Cuencia", "Plante"),
    E("electrik", "Badge d'Arène Électrik", "Mashynn", "Levalendura", "Électrik"),
    E("eau", "Badge d'Arène Eau", "Kombu", "Jarramanca", "Eau"),
    E("normal", "Badge d'Arène Normal", "Okuba", "Mezclamora", "Normal"),
    E("spectre", "Badge d'Arène Spectre", "Laïm", "Frigao", "Spectre"),
    E("psy", "Badge d'Arène Psy", "Tully", "Alforneira", "Psy"),
    E("glace", "Badge d'Arène Glace", "Grusha", "Mont Nappé", "Glace"),
])
DOMINANTS = G("dominants", "Route des Légendes — Pokémon Dominants", [
    E("roche", "Badge Dominant Roche", "Craparoi", "Zone Sud n° 3", "Roche"),
    E("vol", "Badge Dominant Vol", "Lestombaile", "Zone Ouest n° 1", "Vol"),
    E("acier", "Badge Dominant Acier", "Ferdeter", "Zone Est n° 3", "Acier"),
    E("sol", "Badge Dominant Sol", "Fort-Ivoire", "Désert Rôtissable", "Sol", versions=["ecarlate"]),
    E("sol", "Badge Dominant Sol", "Roue-de-Fer", "Désert Rôtissable", "Sol", versions=["violet"]),
    E("dragon", "Badge Dominant Dragon", "Oyacata", "Lac Asrol", "Dragon"),
])
TEAM_STAR = G("team-star", "Opération Stardust — Team Star", [
    E("tenebres", "Badge Team Ténèbres", "Brome", "Zone Ouest n° 1", "Ténèbres", page_lieu="Zone Ouest n° 1"),
    E("feu", "Badge Team Feu", "Meloco", "Zone Est n° 1", "Feu"),
    E("poison", "Badge Team Poison", "Erio", "Zone Est n° 3", "Poison"),
    E("fee", "Badge Team Fée", "Ortiga", "Zone Nord n° 3", "Fée"),
    E("combat", "Badge Team Combat", "Nèflie", "Zone Nord n° 2", "Combat"),
])

# --- Hisui et Illumis --------------------------------------------------------------------

MONARQUES = G("monarques", "Pokémon monarques", [
    E("hachecateur", "Pokémon monarque", "Hachécateur", "Plaines Obsidiennes", "Insecte"),
    E("fragilady", "Pokémon monarque", "Fragilady de Hisui", "Marais Carmin", "Plante"),
    E("arcanin", "Pokémon monarque", "Arcanin de Hisui", "Côte Lazuli", "Feu"),
    E("electrode", "Pokémon monarque", "Électrode de Hisui", "Contrefort Couronné", "Électrik"),
    E("seracrawl", "Pokémon monarque", "Séracrawl de Hisui", "Terres Immaculées", "Glace"),
])
FIN_HISUI = G("histoire", "Fin de l'aventure", [
    E("origine", "Combat final", "Dialga ou Palkia (Forme Originelle)", "Colonnes Lances", page="Dialga",
      note="Selon le clan rejoint"),
    E("maitre", "Rencontre avec Arceus", "Arceus", "Colonnes Lances", "Normal",
      note="Après l'histoire, une fois le Pokédex complété"),
])

ROYALE_ZA = G("royale", "Royale Z-A — matchs qualificatifs", [
    *[E(f"rang-{r}", f"Promotion au rang {s}", p, type=None, note=n, page=pg)
      for r, s, p, pg, n in [
          ("z", "Y", "Zachary", "Royale Z-A", "Chauffeur"),
          ("y", "X", "Yvonne", "Royale Z-A", "Employée"),
          ("x", "W", "Xavi", "Royale Z-A", "Jeune Élève"),
          ("w", "V", "Willem", "Royale Z-A", "Serveur"),
          ("v", "F", "Musquat", "Musquat", "Quazar"),
          ("f", "E", "Narica", "Narica", "Digi-Z4P"),
          ("e", "D", "Nivis", "Nivis", "Poings de la Justice"),
          ("d", "C", "Corvault", "Corvault", "Clan Dérouillard"),
          ("c", "B", "Violine", "Violine", "FRIM"),
          ("b", "A", "Cendro", "Cendro", "Néo Team Flare"),
      ]],
    E("maitre", "Match du rang A", "Boro ou Cety", page="Boro", note="Team MZ"),
])

# --- Jeux --------------------------------------------------------------------------------

JEUX = {
    "rouge-bleu-jaune": [arenes_kanto(), ligue(C4_KANTO, "Blue")],
    "or-argent-cristal": [ARENES_JOHTO, ligue(C4_JOHTO, "Peter"), arenes_kanto(johto=True),
                          G("apres", "Après la Ligue", [RED])],
    "rubis-saphir-emeraude": [arenes_hoenn(emeraude=True),
                              ligue(C4_HOENN, [("Pierre Rochard", ["rubis", "saphir"], None),
                                               ("Marc", ["emeraude"], "Marc (Hoenn)")])],
    "rouge-feu-vert-feuille": [arenes_kanto(), ligue(C4_KANTO, "Blue")],
    "diamant-perle-platine": [arenes_sinnoh(platine=["platine"]), ligue(C4_SINNOH, "Cynthia")],
    "heartgold-soulsilver": [ARENES_JOHTO, ligue(C4_JOHTO, "Peter"), arenes_kanto(johto=True),
                             G("apres", "Après la Ligue", [RED])],
    # L'histoire se termine contre N puis Ghetis ; Goyah, le Maître, s'affronte après
    "noir-blanc": [ARENES_NB, G("ligue", "Ligue Pokémon", [
        *ligue(C4_UNYS, "Goyah")["etapes"][:4],
        E("n", "Château de la Team Plasma", "N"),
        E("ghetis", "Château de la Team Plasma", "Ghetis"),
        E("maitre", "Maître", "Goyah", note="Après l'histoire"),
    ])],
    "noir2-blanc2": [ARENES_N2B2, ligue(C4_UNYS, "Iris", page_maitre="Iris (Unys)")],
    "x-y": [ARENES_KALOS, ligue(C4_KALOS, "Dianthéa")],
    "rubis-omega-saphir-alpha": [arenes_hoenn(), ligue(C4_HOENN, "Pierre Rochard")],
    "soleil-lune": [tour_des_iles(ultra=False), ligue(
        [("Pectorius", "Combat"), ("Alyxia", "Roche"), ("Margie", "Spectre"), ("Kahili", "Vol")],
        "Professeur Euphorbe", titre="Ligue d'Alola")],
    "ultra-soleil-ultra-lune": [tour_des_iles(ultra=True), ligue(
        [("Molène", "Acier"), ("Alyxia", "Roche"), ("Margie", "Spectre"), ("Kahili", "Vol")],
        "Tili", titre="Ligue d'Alola")],
    "lets-go": [arenes_kanto(), ligue(C4_KANTO, "Trace")],
    "epee-bouclier": [ARENES_GALAR, POKE_MASTERS],
    "diamant-etincelant-perle-scintillante": [arenes_sinnoh(), ligue(C4_SINNOH, "Cynthia")],
    "legendes-arceus": [MONARQUES, FIN_HISUI],
    "ecarlate-violet": [ARENES_PALDEA, DOMINANTS, TEAM_STAR,
                        ligue([("Cayenn", "Sol"), ("Popi", "Acier"), ("Okuba", "Vol"), ("Hassa", "Dragon")], "Alisma")],
    "legendes-za": [ROYALE_ZA],
}

# Étape qui marque la fin de l'histoire principale (« groupe/étape ») ; par défaut le Maître
FINAL = {
    "noir-blanc": "ligue/ghetis",
    "legendes-arceus": "histoire/origine",
    "legendes-za": "royale/maitre",
}

# Titre du dernier défi de Ligue (Maître) : pour Alola, le joueur défend son titre
NOTES_MAITRE = {
    "soleil-lune": "Défense du titre de Maître",
    "ultra-soleil-ultra-lune": "Défense du titre de Maître",
    "rouge-bleu-jaune": "Ton rival",
    "rouge-feu-vert-feuille": "Ton rival",
    "lets-go": "Ton rival",
}


def construire() -> dict:
    titres: list[str] = []
    for groupes in JEUX.values():
        for g in groupes:
            for e in g["etapes"]:
                titres += [t for t in (e.get("_page"), e.get("_page_lieu")) if t]
    pages = sources.pokepedia_resolve(titres)
    manquants = sorted({t for t, p in pages.items() if p is None})

    sortie = {}
    for jeu, groupes in JEUX.items():
        resultat = []
        for g in groupes:
            etapes = []
            for e in g["etapes"]:
                e = dict(e)
                p, pl = e.pop("_page", None), e.pop("_page_lieu", None)
                if p and pages.get(p):
                    e["url_personne"] = sources.pokepedia_url(pages[p])
                if pl and pages.get(pl):
                    e["url_lieu"] = sources.pokepedia_url(pages[pl])
                if e["id"] == "maitre" and jeu in NOTES_MAITRE and "note" not in e:
                    e["note"] = NOTES_MAITRE[jeu]
                etapes.append(e)
            resultat.append({**g, "etapes": etapes})
        final = FINAL.get(jeu, "ligue/maitre")
        g_final, _, e_final = final.partition("/")
        assert any(g["id"] == g_final and any(e["id"] == e_final for e in g["etapes"]) for g in resultat), final
        sortie[jeu] = {"final": final, "groupes": resultat}
    return {"format": 1, "jeux": sortie, "_manquants": manquants}


if __name__ == "__main__":
    donnees = construire()
    manquants = donnees.pop("_manquants")
    for t in manquants:
        print(f"Page Poképédia introuvable : {t}", file=sys.stderr)
    SORTIE.write_text(json.dumps(donnees, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8",
                      newline="\n")
    nb = sum(len(g["etapes"]) for j in donnees["jeux"].values() for g in j["groupes"])
    print(f"{SORTIE.relative_to(RACINE)} : {len(donnees['jeux'])} jeux, {nb} étapes")
