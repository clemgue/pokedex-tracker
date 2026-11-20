"""Passe finale sur l'ensemble des jeux générés : indique d'où transférer les Pokémon
inobtenables dans un jeu (ex. starters de Kanto dans Or/Argent).

Pour chaque jeu, un Pokémon sans aucune obtention (hors bug) reçoit une obtention
« transfert » listant les jeux précédents où il est obtenable. Idempotent.

Usage : python transferts.py   (lancé automatiquement par « build.py tous »)
"""

from __future__ import annotations

import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
DOSSIER = RACINE / "static" / "data" / "jeux"
OBTENABLE = {"hautes_herbes", "marche", "surf", "peche", "fixe", "don", "echange_pnj", "achat", "fossile",
             "autre", "evolution", "echange_version", "evenement"}
MAX_CITES = 3


def nom_court(jeu: dict) -> str:
    return jeu["nom"].removeprefix("Pokémon ").removeprefix("Légendes Pokémon : ")


def lier_transferts() -> None:
    index = json.loads((DOSSIER / "index.json").read_text(encoding="utf-8"))["jeux"]
    jeux = [(j, json.loads((DOSSIER / j["fichier"]).read_text(encoding="utf-8"))) for j in index]

    obtenables = {}
    for j, d in jeux:
        d["obtentions"] = [o for o in d["obtentions"] if o["methode"] != "transfert"]
        obtenables[j["id"]] = {o["pokemon"] for o in d["obtentions"] if o["methode"] in OBTENABLE}

    for j, d in jeux:
        precedents = [x for x, _ in jeux if x["ordre"] < j["ordre"]]
        versions = [v["id"] for v in d["jeu"]["versions"]]
        prochain_id = max((o["id"] for o in d["obtentions"]), default=0) + 1
        ajouts = 0
        for p in d["pokemon"]:
            pid = p["id"]
            if pid in obtenables[j["id"]]:
                continue
            sources = [nom_court(x) for x in reversed(precedents) if pid in obtenables[x["id"]]][:MAX_CITES]
            detail = ("Transférer depuis un autre jeu (ex. : " + ", ".join(sources) + ")") if sources \
                else "Transférer depuis un jeu plus récent ou distribution événementielle"
            d["obtentions"].append({"id": prochain_id, "pokemon": pid, "methode": "transfert", "detail": detail,
                                    "versions": versions, "glitch": False})
            prochain_id += 1
            ajouts += 1
        d["obtentions"].sort(key=lambda o: (o["pokemon"], "lieu" not in o, o["id"]))
        d["methodes"]["transfert"] = "Transfert depuis un autre jeu"
        (DOSSIER / j["fichier"]).write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "\n",
                                            encoding="utf-8", newline="\n")
        print(f"{j['nom']} : {ajouts} Pokémon à transférer")


if __name__ == "__main__":
    lier_transferts()
