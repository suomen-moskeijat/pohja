#!/usr/bin/env python3
"""Pienennetyt kuvat gallerioihin: tiedostot/**/kuva.jpg → tiedostot/**/pienet/kuva.jpg (enintään 560 px leveä).

Sivut näyttävät galleriassa pienen version ja avaavat täysikokoisen klikattaessa, jolloin etusivu
latautuu puhelimella nopeasti (Googlen Core Web Vitals). Jos pienentäminen ei onnistu, alkuperäinen
kopioidaan pienen tilalle, ettei sivulle jää rikkinäisiä kuvia. Lopuksi _config.yml:ään lisätään
`pienet: true`, jonka nähdessään sivupohja käyttää pieniä kuvia.
Käyttö: python3 pienet.py <sivun kansio>
"""
import os, shutil, sys

LEVEYS = 560
juuri = sys.argv[1] if len(sys.argv) > 1 else "."
try:
    from PIL import Image, ImageOps
except ImportError:  # ilman Pillowia kopioidaan alkuperäiset
    Image = None

tehty = kopioitu = 0
for kansio, alikansiot, tiedostot in os.walk(os.path.join(juuri, "tiedostot")):
    alikansiot[:] = [a for a in alikansiot if a != "pienet"]
    for nimi in tiedostot:
        if not nimi.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        lahde = os.path.join(kansio, nimi)
        kohde_kansio = os.path.join(kansio, "pienet")
        os.makedirs(kohde_kansio, exist_ok=True)
        kohde = os.path.join(kohde_kansio, nimi)
        try:
            if Image is None:
                raise RuntimeError("ei Pillowia")
            with Image.open(lahde) as kuva:
                kuva = ImageOps.exif_transpose(kuva)
                if kuva.width <= LEVEYS:
                    shutil.copyfile(lahde, kohde); kopioitu += 1; continue
                kuva.thumbnail((LEVEYS, LEVEYS * 4))
                muoto = {".png": "PNG", ".webp": "WEBP"}.get(os.path.splitext(nimi)[1].lower(), "JPEG")
                if muoto == "JPEG" and kuva.mode not in ("RGB", "L"):
                    kuva = kuva.convert("RGB")
                kuva.save(kohde, muoto, **({"quality": 80, "optimize": True, "progressive": True} if muoto == "JPEG" else {"quality": 80} if muoto == "WEBP" else {"optimize": True}))
                tehty += 1
        except Exception as e:  # rikkinäinen tai outo kuva: kopioidaan sellaisenaan
            print(f"  {lahde}: {e} – kopioidaan alkuperäinen")
            shutil.copyfile(lahde, kohde); kopioitu += 1

with open(os.path.join(juuri, "_config.yml"), "a", encoding="utf-8") as f:
    f.write("\npienet: true\n")
print(f"Pienet kuvat: {tehty} pienennetty, {kopioitu} kopioitu sellaisenaan")
