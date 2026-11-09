#!/usr/bin/env python3
"""Päivittää pohjan mallitiedostot kaikkiin moskeijarepoihin (oletus: Pages CMS -asetukset).

    python3 paivita_kaikki.py [--tiedosto .pages.yml] [--kuiva]

Käy läpi organisaation repot, joissa on kansio _moskeijat/, ja kirjoittaa tiedoston
malli/<tiedosto> repoon, jos sisältö poikkeaa. Ajetaan työnkulussa "Päivitä muokkausnäkymä
kaikille" automaattisesti, kun malli/.pages.yml muuttuu.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

POHJA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def api(menetelma, polku, avain, data=None, sallitut=()):
    req = urllib.request.Request("https://api.github.com" + polku, method=menetelma,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Authorization": f"Bearer {avain}", "Accept": "application/vnd.github+json",
                                          "User-Agent": "suomen-moskeijat"})
    try:
        with urllib.request.urlopen(req, timeout=30) as v:
            sis = v.read()
            return v.status, json.loads(sis) if sis else {}
    except urllib.error.HTTPError as e:
        if e.code in sallitut:
            return e.code, {}
        raise SystemExit(f"GitHub-virhe {e.code} ({menetelma} {polku}): {e.read()[:300]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiedosto", default=".pages.yml")
    ap.add_argument("--kuiva", action="store_true")
    a = ap.parse_args()
    avain, org = os.environ.get("MOSKEIJA_AVAIN"), os.environ.get("ORG", "suomen-moskeijat")
    if not avain:
        raise SystemExit("MOSKEIJA_AVAIN puuttuu.")
    uusi = open(os.path.join(POHJA, "malli", a.tiedosto), "rb").read()
    repot, sivu = [], 1
    while True:
        _, osa = api("GET", f"/orgs/{org}/repos?per_page=100&page={sivu}", avain)
        repot += osa
        if len(osa) < 100:
            break
        sivu += 1
    paivitetty, ennallaan = [], []
    for r in repot:
        nimi = r["name"]
        if nimi == "pohja" or r.get("archived"):
            continue
        tila, _ = api("GET", f"/repos/{org}/{nimi}/contents/_moskeijat", avain, sallitut=(404,))
        if tila != 200:
            continue
        tila, nyk = api("GET", f"/repos/{org}/{nimi}/contents/{a.tiedosto}", avain, sallitut=(404,))
        if tila == 200 and base64.b64decode(nyk["content"]) == uusi:
            ennallaan.append(nimi)
            continue
        if not a.kuiva:
            data = {"message": f"Muokkausnäkymä päivitetty pohjasta ({a.tiedosto})", "content": base64.b64encode(uusi).decode()}
            if tila == 200:
                data["sha"] = nyk["sha"]
            api("PUT", f"/repos/{org}/{nimi}/contents/{a.tiedosto}", avain, data)
        paivitetty.append(nimi)
        print(f"  päivitetty: {nimi}")
    yht = f"## {a.tiedosto}\n\n**Päivitetty ({len(paivitetty)}):** {', '.join(paivitetty) or '–'}\n\n**Ennallaan ({len(ennallaan)}):** {len(ennallaan)} repoa\n"
    print(yht)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8").write(yht)


if __name__ == "__main__":
    sys.exit(main())
