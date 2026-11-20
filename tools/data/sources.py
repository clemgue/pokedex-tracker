"""Accès aux sources (PokéAPI, Poképédia) avec cache disque et débit limité.

Le cache (`tools/data/.cache/`) évite de re-solliciter les sites à chaque génération :
supprimer le dossier pour forcer un rafraîchissement.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:  # Vérification des certificats par le magasin du système (chaîne Let's Encrypt récente)
    import truststore

    truststore.inject_into_ssl()
except ImportError:  # pragma: no cover
    pass

USER_AGENT = "pokedex-tracker-data/0.1 (projet personnel non commercial)"
CACHE_DIR = Path(__file__).parent / ".cache"
POKEAPI = "https://pokeapi.co/api/v2"
POKEPEDIA_API = "https://www.pokepedia.fr/api.php"
POKEPEDIA_WIKI = "https://www.pokepedia.fr/"

# Délai minimal entre deux requêtes réseau vers un même hôte (secondes)
_MIN_DELAY = {"pokeapi.co": 0.2, "www.pokepedia.fr": 1.0}
_last_call: dict[str, float] = {}


def _get_json(url: str) -> object:
    CACHE_DIR.mkdir(exist_ok=True)
    key = hashlib.sha1(url.encode("utf-8")).hexdigest()
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    host = urllib.parse.urlparse(url).hostname or ""
    wait = _MIN_DELAY.get(host, 0.5) - (time.monotonic() - _last_call.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    _last_call[host] = time.monotonic()
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


# --- PokéAPI -----------------------------------------------------------------

def pokeapi(path: str) -> dict:
    """`pokeapi("pokemon-species/25")` ou URL complète."""
    url = path if path.startswith("http") else f"{POKEAPI}/{path.strip('/')}/"
    return _get_json(url)  # type: ignore[return-value]


def localized(names: list[dict], lang: str) -> str | None:
    for n in names:
        if n["language"]["name"] == lang:
            return n["name"]
    return None


# --- Poképédia ---------------------------------------------------------------

def pokepedia_url(title: str) -> str:
    return POKEPEDIA_WIKI + urllib.parse.quote(title.replace(" ", "_"), safe="/:'(),!")


def pokepedia_query(**params: str) -> dict:
    params = {"format": "json", "formatversion": "2", **params}
    return _get_json(POKEPEDIA_API + "?" + urllib.parse.urlencode(params))  # type: ignore[return-value]


def pokepedia_source(title: str) -> str:
    """Contenu brut (wikitexte / Lua) d'une page Poképédia."""
    data = pokepedia_query(action="query", prop="revisions", rvprop="content", rvslots="main", titles=title)
    page = data["query"]["pages"][0]
    if page.get("missing"):
        raise KeyError(f"Page Poképédia introuvable : {title}")
    return page["revisions"][0]["slots"]["main"]["content"]


def pokepedia_resolve(titles: list[str]) -> dict[str, str | None]:
    """Résout des titres (redirections comprises) → titre réel de la page, ou None si absente."""
    result: dict[str, str | None] = {}
    unique = sorted(set(titles))
    for start in range(0, len(unique), 50):
        batch = unique[start:start + 50]
        data = pokepedia_query(action="query", redirects="1", titles="|".join(batch))
        q = data["query"]
        mapping = {t: t for t in batch}
        for step in ("normalized", "redirects"):
            for r in q.get(step, []):
                for orig, cur in mapping.items():
                    if cur == r["from"]:
                        mapping[orig] = r["to"]
        existing = {p["title"] for p in q["pages"] if not p.get("missing") and not p.get("invalid")}
        for orig, cur in mapping.items():
            result[orig] = cur if cur in existing else None
    return result
