#!/usr/bin/env python3
"""Luo ehdotussivut sisältöreposta moskeijoille listasta moskeijat.csv (hallinta#51, ADR-0006).

    python3 lisaa_listasta.py --sisalto <sisältörepon kansio> [--tallenna] [--vain nimi1,nimi2] [--tuo-sivut]

Luo ehdotuksen (kansio moskeijat/<nimi>/ ja sivustoluettelon rivi, kuten lisaa_moskeija.py) jokaiselle sisältörepon
moskeijat.csv:n moskeijalle, jonka tila on tyhjä ja jolla ei vielä ole sivua: ei kansiota sisältörepossa eikä vanhan
julkaisun moskeijarepoa. Ehdotus = esimerkkisivu, josta moskeija ei ole vielä päättänyt: palkki "Ehdotus", näkyy vain
luonnoslinkillä. Mukaan tulevat listan tiedot (nimi, osoite, puhelin, sähköposti, linkit); --tuo-sivut tuo lisäksi
moskeijan nettisivulta logon, värit, kuvat ja tekstit. Kaikki ehdotukset tallennetaan yhtenä committina (--tallenna).

Syötteet (vain, tuo_sivut) luetaan työnkulussa käynnistyksen tiedoista. Julkiseen lokiin vain sivujen tunnukset ja määrät.
Vanhan julkaisun moskeijarepon tarkistus: GitHubin rajapinta (GITHUB_API, avain MOSKEIJA_AVAIN tai GITHUB_TOKEN), ORG.
"""
import argparse
import os
import sys
import urllib.error
import urllib.request

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lisaa_moskeija
import sisaltorepo


def repo_olemassa(org, repo, avain):
    """Onko vanhan julkaisun moskeijarepo olemassa (siirtämätön moskeija tai aiemmin luotu ehdotus)."""
    osoite = os.environ.get("GITHUB_API", "https://api.github.com").rstrip("/") + f"/repos/{org}/{repo}"
    req = urllib.request.Request(osoite, headers={"Authorization": f"Bearer {avain}"} if avain else {})
    try:
        urllib.request.urlopen(req, timeout=30)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise sisaltorepo.Virhe(f"Vanhan julkaisun repoa ei voitu tarkistaa (HTTP {e.code})")


def main(argv=None):
    syotteet = lisaa_moskeija.kaynnistyksen_syotteet()
    ap = argparse.ArgumentParser()
    ap.add_argument("--sisalto", required=True, help="sisältörepon kansio (moskeijat.csv, sivustot.yml, moskeijat/)")
    ap.add_argument("--tallenna", action="store_true", help="commit ja push sisältörepoon (muuten kuivaharjoitus)")
    ap.add_argument("--vain", default=syotteet.get("vain", os.environ.get("SYOTE_VAIN", "")), help="pilkulla erotellut sivujen tunnukset")
    ap.add_argument("--tuo-sivut", action="store_true",
                    default=str(syotteet.get("tuo_sivut", os.environ.get("SYOTE_TUO", ""))).lower() == "true",
                    help="tuo moskeijan nettisivulta logo, värit, kuvat ja tekstit (ehdotukseen)")
    a = ap.parse_args(argv)
    vain = {x.strip().lower() for x in a.vain.split(",") if x.strip()}
    org = os.environ.get("ORG", "suomen-moskeijat")
    avain = os.environ.get("MOSKEIJA_AVAIN") or os.environ.get("GITHUB_TOKEN", "")
    _, rivit = sisaltorepo.lue_csv(a.sisalto)
    luotu, ohitettu, virheet = [], [], []
    for r in rivit:
        nimi = lisaa_moskeija.slugiksi(r.get("repo", "").strip() or r.get("nimi", ""))
        if vain and nimi not in vain and r.get("repo", "").strip().lower() not in vain:
            continue
        if not nimi:
            continue
        if (r.get("tila") or "").strip():
            ohitettu.append(f"{nimi} (tila: {r['tila'].strip()})")
            continue
        if os.path.exists(sisaltorepo.kansio(a.sisalto, nimi)) or sisaltorepo.sivu(a.sisalto, nimi):
            ohitettu.append(f"{nimi} (on jo sisältörepossa)")
            continue
        if a.tallenna and repo_olemassa(org, r.get("repo", "").strip() or nimi, avain):
            ohitettu.append(f"{nimi} (vanhan julkaisun sivu on olemassa)")
            continue
        tuo = a.tuo_sivut and (r.get("nettisivu") or "").strip()
        argumentit = ["--sisalto", a.sisalto, "--nimi", r.get("nimi", ""), "--kaupunki", r.get("kaupunki", ""),
                      "--osoite", r.get("osoite", ""), "--repo", nimi, "--puhelin", r.get("puhelin", ""),
                      "--sahkoposti", r.get("sahkoposti", ""), "--nettisivu" if tuo else "--linkki", r.get("nettisivu", ""),
                      "--facebook", r.get("facebook", ""), "--ehdotus"]
        print(f"=== {nimi}", file=sys.stderr, flush=True)
        try:
            m = lisaa_moskeija.argumentit(argumentit)
            nimi_, t, tiedot = lisaa_moskeija.valmistele(m)
            lisaa_moskeija.lisaa_sisaltoon(a.sisalto, nimi_, tiedot)
            lisaa_moskeija.ilmoita(f"{nimi_}: {lisaa_moskeija.kuvaus(t, tiedot)}")
            luotu.append(nimi_)
        except SystemExit as e:  # yhden moskeijan virhe ei estä muita (teksti on julkista lokia varten)
            lisaa_moskeija.ilmoita(f"{nimi}: ei luotu ({e})")
            virheet.append(nimi)
        except Exception as e:
            lisaa_moskeija.ilmoita(f"{nimi}: ei luotu (odottamaton virhe {type(e).__name__})")
            virheet.append(nimi)
    tila = "kuivaharjoitus, mitään ei tallennettu"
    if a.tallenna and luotu:
        commit = sisaltorepo.tallenna(a.sisalto, f"Ehdotussivut listasta: {', '.join(luotu)}",
                                      [*(f"moskeijat/{n}" for n in luotu), sisaltorepo.LUETTELO])
        tila = "tallennettu sisältörepoon" if commit else "ei muutoksia"
    yhteenveto = (f"## Ehdotussivut listasta\n\n**Luotu ({len(luotu)}):** {', '.join(luotu) or '–'} ({tila})"
                  f"\n\n**Ohitettu ({len(ohitettu)}):** {', '.join(ohitettu) or '–'}"
                  f"\n\n**Virheet ({len(virheet)}):** {', '.join(virheet) or '–'}\n\n"
                  "Ehdotukset rakentuvat seuraavassa rakennusajossa ja näkyvät vain luonnoslinkillä (paneeli).\n")
    print(yhteenveto)
    lisaa_moskeija.yhteenvetoon(yhteenveto)
    return 1 if virheet else 0


if __name__ == "__main__":
    sys.exit(main())
