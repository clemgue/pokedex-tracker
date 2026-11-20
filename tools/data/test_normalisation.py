"""Tests de la normalisation des données Poképédia.  Lancer : python -m unittest discover tools/data"""

import unittest

import lua_table
import normalisation as norm

CODES = {"R": "rouge", "B": "bleu"}
VERSIONS = ["rouge", "bleu"]


class TestValeursParVersion(unittest.TestCase):
    def test_valeurs_par_version(self):
        self.assertEqual(norm.valeurs_par_version("3-5, R, 3, B", CODES, VERSIONS), {"rouge": "3-5", "bleu": "3"})

    def test_valeur_commune(self):
        self.assertEqual(norm.valeurs_par_version("10, 15, 20", CODES, VERSIONS),
                         {"rouge": "10, 15, 20", "bleu": "10, 15, 20"})

    def test_exclusivite(self):
        self.assertEqual(norm.valeurs_par_version("35, R", CODES, VERSIONS), {"rouge": "35"})


class TestMilieu(unittest.TestCase):
    def test_zone_interieure(self):
        self.assertEqual(norm.analyser_milieu("Étage,s,, Troisième et quatrième"), ("marche", None, "3e et 4e étages"))
        self.assertEqual(norm.analyser_milieu("Sous-sol,, Premier"), ("marche", None, "1er sous-sol"))

    def test_peche(self):
        self.assertEqual(norm.analyser_milieu("Pêche à la Méga Canne, sur les quais"),
                         ("peche", "Méga Canne", "sur les quais"))

    def test_echange(self):
        self.assertEqual(norm.analyser_milieu("Échange, contre [[Têtarte]]"), ("echange_pnj", "contre Têtarte", None))

    def test_mots_cles(self):
        self.assertEqual(norm.analyser_milieu("Hautes herbes (Kanto)")[0], "hautes_herbes")
        self.assertEqual(norm.analyser_milieu("Pêche dans les remous")[0], "peche")
        self.assertEqual(norm.analyser_milieu("Éclate-Roc")[0], "marche")
        self.assertEqual(norm.analyser_milieu("")[0], "marche")
        self.assertEqual(norm.analyser_milieu("Scanner des Îles"), ("autre", "Scanner des Îles", None))

    def test_fichier_supprime(self):
        methode, detail, _ = norm.analyser_milieu("[[Fichier:Icône Pokémon Baron LPA.png|20px]] Pokémon Barons")
        self.assertEqual((methode, detail), ("fixe", "Pokémon Barons"))


class TestEntree(unittest.TestCase):
    def test_versions_fusionnees(self):
        r = norm.normaliser_entree({"milieu": "Hautes herbes", "niveau": "32-36", "taux": "24, R, 14, B"}, CODES, VERSIONS)
        self.assertEqual([(o["versions"], o["taux"]) for o in r], [(["rouge"], 24.0), (["bleu"], 14.0)])

    def test_unique_devient_fixe(self):
        r = norm.normaliser_entree({"milieu": "Étage,, Premier", "niveau": "50", "taux": "Unique"}, CODES, VERSIONS)
        self.assertEqual(r[0]["methode"], "fixe")

    def test_taux_selon_moment(self):
        r = norm.normaliser_entree({"milieu": "Hautes herbes", "niveau": "3", "taux-matin": "10", "taux-nuit": "30"},
                                   CODES, VERSIONS)
        self.assertEqual(r[0]["taux_texte"], "Matin 10 % · Nuit 30 %")
        self.assertEqual(r[0]["taux"], 30.0)

    def test_sans_taux(self):
        r = norm.normaliser_entree({"niveau": "25"}, CODES, VERSIONS)
        self.assertEqual(r[0]["versions"], VERSIONS)
        self.assertIsNone(r[0]["taux"])

    def test_notes(self):
        r = norm.normaliser_entree({"milieu": "Hautes herbes", "taux": "5", "météo": "Pluie"}, CODES, VERSIONS)
        self.assertEqual(r[0]["notes"], "Météo : Pluie")


class TestDivers(unittest.TestCase):
    def test_nom_forme(self):
        self.assertEqual(norm.analyser_nom("Miaouss forme(Galar)"), ("Miaouss", "Galar"))
        self.assertEqual(norm.analyser_nom("M. Mime"), ("M. Mime", None))

    def test_lieu(self):
        self.assertEqual(norm.analyser_lieu("Parc Safari (Kanto)@zone est"), ("Parc Safari (Kanto)", "Parc Safari", "Zone est"))
        self.assertEqual(norm.analyser_lieu("Casino de Céladopole|Casino Rocket"),
                         ("Casino de Céladopole", "Casino Rocket", None))

    def test_lua(self):
        self.assertEqual(lua_table.parse_module('return { ["a"] = {{["x"] = "1"}}, ["b"] = {} }'),
                         {"a": [{"x": "1"}], "b": []})


if __name__ == "__main__":
    unittest.main()
