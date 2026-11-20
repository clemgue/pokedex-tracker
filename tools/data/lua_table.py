"""Parseur minimal de tables Lua littérales (format des modules de données Poképédia).

Gère : tables `{...}` (tableau et/ou dictionnaire), clés `["texte"]`, `[n]` ou identifiant,
chaînes "..." / '...', nombres, true/false/nil, commentaires `--`.
Une table sans aucune clé explicite devient une liste Python, sinon un dict.
"""

from __future__ import annotations

import re

_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}


class LuaParseError(ValueError):
    pass


class _Parser:
    def __init__(self, text: str):
        self.s = text
        self.i = 0

    def error(self, msg: str) -> LuaParseError:
        line = self.s.count("\n", 0, self.i) + 1
        return LuaParseError(f"{msg} (ligne {line})")

    def skip(self) -> None:
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c.isspace():
                self.i += 1
            elif s.startswith("--[[", self.i):
                end = s.find("]]", self.i)
                self.i = len(s) if end < 0 else end + 2
            elif s.startswith("--", self.i):
                end = s.find("\n", self.i)
                self.i = len(s) if end < 0 else end + 1
            else:
                break

    def peek(self) -> str:
        self.skip()
        return self.s[self.i] if self.i < len(self.s) else ""

    def expect(self, ch: str) -> None:
        if self.peek() != ch:
            raise self.error(f"'{ch}' attendu, trouvé {self.s[self.i:self.i + 20]!r}")
        self.i += 1

    def string(self) -> str:
        quote = self.s[self.i]
        self.i += 1
        out = []
        while True:
            if self.i >= len(self.s):
                raise self.error("chaîne non terminée")
            c = self.s[self.i]
            if c == quote:
                self.i += 1
                return "".join(out)
            if c == "\\":
                nxt = self.s[self.i + 1]
                out.append(_ESCAPES.get(nxt, nxt))
                self.i += 2
            else:
                out.append(c)
                self.i += 1

    def value(self):
        c = self.peek()
        if c == "{":
            return self.table()
        if c in "\"'":
            return self.string()
        m = _NUM.match(self.s, self.i)
        if m:
            self.i = m.end()
            txt = m.group()
            return float(txt) if "." in txt else int(txt)
        m = _IDENT.match(self.s, self.i)
        if m and m.group() in ("true", "false", "nil"):
            self.i = m.end()
            return {"true": True, "false": False, "nil": None}[m.group()]
        raise self.error(f"valeur inattendue {self.s[self.i:self.i + 20]!r}")

    def table(self):
        self.expect("{")
        items: list = []
        keyed: dict = {}
        while True:
            c = self.peek()
            if c == "}":
                self.i += 1
                break
            key = None
            if c == "[":
                self.i += 1
                key = self.value()
                self.expect("]")
                self.expect("=")
            else:
                m = _IDENT.match(self.s, self.i)
                if m and m.group() not in ("true", "false", "nil"):
                    save = self.i
                    self.i = m.end()
                    if self.peek() == "=":
                        self.i += 1
                        key = m.group()
                    else:
                        self.i = save
            val = self.value()
            if key is None:
                items.append(val)
            else:
                keyed[key] = val
            if self.peek() in ",;":
                self.i += 1
        if keyed:
            for n, v in enumerate(items, start=1):
                keyed.setdefault(n, v)
            return keyed
        return items


def parse_module(text: str):
    """Parse le contenu d'un module Lua de la forme `return { ... }`."""
    p = _Parser(text)
    p.skip()
    if not p.s.startswith("return", p.i):
        raise p.error("'return' attendu en début de module")
    p.i += len("return")
    result = p.value()
    if p.peek():
        raise p.error("contenu inattendu après la table")
    return result
