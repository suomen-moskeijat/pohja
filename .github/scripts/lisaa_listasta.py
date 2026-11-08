#!/usr/bin/env python3
"""Luo ehdotussivut moskeijoille listasta moskeijat.csv.

    python3 lisaa_listasta.py [--vain repo1,repo2] [--kuiva KANSIO]

Luo sivun jokaiselle listan moskeijalle, jolla ei vielä ole repoa ja jonka tila on tyhjä.
Sivut ovat ehdotuksia: keltainen palkki "Ehdotus – tämä ei ole moskeijan virallinen sivu",
eivät näy Googlessa. Mukaan tulevat vain listan julkiset tiedot (nimi, osoite, puhelin,
sähköposti, linkit). Moskeijan omaa sivustoa (logo, kuvat, tekstit) EI tuoda ennen kuin
moskeija on lähtenyt mukaan – silloin ajetaan Lisää moskeija nettisivu-kentän kanssa.
"""
import argparse
import csv
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

POHJA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def repo_olemassa(org, repo, avain):
    req = urllib.request.Request(f"https://api.github.com/repos/{org}/{repo}",
                                 headers={"Authorization": f"Bearer {avain}"} if avain else {})
    try:
        urllib.request.urlopen(req, timeout=30)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vain", default=os.environ.get("SYOTE_VAIN", ""), help="pilkulla erotellut repojen nimet")
    ap.add_argument("--kuiva", help="kirjoita tiedostot kansioon, älä luo mitään")
    a = ap.parse_args()
    vain = {x.strip() for x in a.vain.split(",") if x.strip()}
    org, avain = os.environ.get("ORG", "suomen-moskeijat"), os.environ.get("MOSKEIJA_AVAIN", "")
    rivit = list(csv.DictReader(open(os.path.join(POHJA, "moskeijat.csv"), encoding="utf-8")))
    luotu, ohitettu, virheet = [], [], []
    for r in rivit:
        repo = r["repo"].strip()
        if vain and repo not in vain:
            continue
        if r["tila"].strip():
            ohitettu.append(f"{repo} (tila: {r['tila']})")
            continue
        if not a.kuiva and repo_olemassa(org, repo, avain):
            ohitettu.append(f"{repo} (repo on jo olemassa)")
            continue
        komento = [sys.executable, os.path.join(POHJA, ".github/scripts/lisaa_moskeija.py"),
                   "--nimi", r["nimi"], "--kaupunki", r["kaupunki"], "--osoite", r["osoite"], "--repo", repo,
                   "--puhelin", r["puhelin"], "--sahkoposti", r["sahkoposti"], "--linkki", r["nettisivu"],
                   "--facebook", r["facebook"], "--ehdotus"]
        if a.kuiva:
            komento += ["--kuiva", os.path.join(a.kuiva, repo)]
        print(f"\n=== {r['nimi']} ({r['kaupunki']}) → {repo}", flush=True)
        tulos = subprocess.run(komento, env={**os.environ, "GITHUB_STEP_SUMMARY": ""})
        (luotu if tulos.returncode == 0 else virheet).append(repo)
        time.sleep(2)
    yhteenveto = (f"## Ehdotussivut listasta\n\n**Luotu ({len(luotu)}):** "
                  + (", ".join(f"[{x}](https://{org.lower()}.github.io/{x}/)" for x in luotu) or "–")
                  + f"\n\n**Ohitettu ({len(ohitettu)}):** {', '.join(ohitettu) or '–'}"
                  + f"\n\n**Virheet ({len(virheet)}):** {', '.join(virheet) or '–'}\n\n"
                  "Sivut ovat ehdotuksia (palkki ylhäällä, ei Googlessa). Kaikki moskeijat: "
                  f"https://{org.lower()}.github.io/pohja/\n")
    print(yhteenveto)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8").write(yhteenveto)
    return 1 if virheet else 0


if __name__ == "__main__":
    sys.exit(main())
