"""Génère les icônes PNG de l'application (PWA) : Poké Ball sur fond rouge Pokédex.

Usage : python tools/icones.py   (nécessite Pillow)
"""

from pathlib import Path

from PIL import Image, ImageDraw

SORTIE = Path(__file__).resolve().parents[1] / "static" / "icones"
ROUGE = (200, 16, 46)
ROUGE_FONCE = (143, 12, 34)
BLANC = (255, 255, 255)
NOIR = (29, 29, 29)


def icone(taille: int, masquable: bool) -> Image.Image:
    f = 4  # suréchantillonnage pour l'anticrénelage
    t = taille * f
    img = Image.new("RGBA", (t, t), ROUGE_FONCE if masquable else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if not masquable:
        d.rounded_rectangle((0, 0, t - 1, t - 1), radius=t // 5, fill=ROUGE_FONCE)
    # Zone sûre des icônes masquables : cercle de 80 % du diamètre
    r = int(t * (0.30 if masquable else 0.36))
    c = t // 2
    trait = max(f, t // 28)
    d.ellipse((c - r, c - r, c + r, c + r), fill=BLANC, outline=NOIR, width=trait)
    d.pieslice((c - r, c - r, c + r, c + r), 180, 360, fill=ROUGE, outline=NOIR, width=trait)
    d.rectangle((c - r, c - trait // 2, c + r, c + trait // 2), fill=NOIR)
    rc = r // 3
    d.ellipse((c - rc, c - rc, c + rc, c + rc), fill=BLANC, outline=NOIR, width=trait)
    rc2 = r // 6
    d.ellipse((c - rc2, c - rc2, c + rc2, c + rc2), outline=NOIR, width=max(f, trait // 2))
    return img.resize((taille, taille), Image.LANCZOS)


def main() -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)
    for taille in (192, 512):
        icone(taille, False).save(SORTIE / f"icone-{taille}.png", optimize=True)
        icone(taille, True).save(SORTIE / f"icone-masquable-{taille}.png", optimize=True)
    icone(180, True).convert("RGB").save(SORTIE / "apple-touch-icon.png", optimize=True)
    print("Icônes écrites dans", SORTIE)


if __name__ == "__main__":
    main()
