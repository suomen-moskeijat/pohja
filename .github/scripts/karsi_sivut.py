#!/usr/bin/env python3
"""Poistaa rakennetulta sivulta sivut, joita moskeijalla ei ole (Jekyllin jälkeen, ennen kieliversioita ja kalentereita).

GitHub Pages ei aja omia Jekyll-laajennuksia, joten sivupohja ei voi jättää sivua rakentamatta ehdon mukaan. Sivu, jota ei
pidä olla, merkitään sisällössä merkinnällä data-ei-sivua, ja tämä skripti poistaa sen: osoite antaa 404, eikä sivusta
tule kieliversioita (/en/, /ar/ …). Sääntö pysyy sivupohjassa (esim. ramadan.html: Ramadan vain testimoskeijassa,
osat/ramadan-tiedot.html _rm_kaytossa); tämä vain poistaa merkityt.
Käyttö: python3 karsi_sivut.py <_site-kansio>
"""
import os, sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "_site"
MERKKI = "data-ei-sivua"

poistetut = []
for kansio, _, tiedostot in os.walk(SITE):
    for nimi in tiedostot:
        if not nimi.endswith(".html"):
            continue
        tiedosto = os.path.join(kansio, nimi)
        with open(tiedosto, encoding="utf-8", errors="replace") as f:
            if MERKKI not in f.read():
                continue
        os.remove(tiedosto)
        poistetut.append("/" + os.path.relpath(tiedosto, SITE).replace(os.sep, "/"))
        if not os.listdir(kansio) and os.path.abspath(kansio) != os.path.abspath(SITE):
            os.rmdir(kansio)
print("Karsitut sivut: " + (", ".join(sorted(poistetut)) if poistetut else "ei yhtään"))
