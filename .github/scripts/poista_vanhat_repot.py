#!/usr/bin/env python3
"""Poistaa siirrettyjen moskeijoiden vanhat moskeijarepot (hallinta#56, J16, ADR-0006). Työnkulku: Poista vanhat repot.

    python3 poista_vanhat_repot.py --sisalto <sisältörepon kansio> [--moskeijat "a,b" | --moskeijat siirretyt] [--poista]

Moskeija on siirretty, kun sen sisältö on sisältörepossa (kansio moskeijat/<nimi>/ ja sivustoluettelon rivi). Sen jälkeen vanha
moskeijarepo (oma julkinen repo ja GitHub Pages) on tarpeeton. Tämä poistaa vain vanhan GitHub-repon: sisältörepoon, sivustoluetteloon
ja Cloudflareen ei kosketa. (Poista moskeija -työnkulku poistaisi sisältörepon moskeijalta uuden sisällön, joten sitä ei käytetä tähän.)

Turvarajat (testi: hallinta testi/vanhat-repot.mjs):
- repo poistetaan vain, jos sisältörepossa on kansio moskeijat/<nimi>/ (jossa _moskeijat/*.md) ja sivustoluettelossa rivi samalla
  nimellä, kirjainkoko tarkasti
- ei koskaan SUOJATUT (vertailu kirjainkoosta riippumatta, koska GitHubin repojen nimet eivät erottele kirjainkokoa: esim.
  /repos/<org>/masjid-sunnah osuu repoon Masjid-sunnah)
- vain organisaation moskeijarepo: GitHubin vastauksen nimi on täsmälleen <nimi> (ei uudelleennimettyä eikä eri kirjainkokoa),
  omistaja on organisaatio ja repossa on _moskeijat/*.md
- nimetty lista: jos yksikin nimi hylätään, mitään ei poisteta. siirretyt: hylätyt ohitetaan, muut poistetaan.
- kuivaharjoitus (oletus) tekee tarkistukset ja tulostaa listan, mutta ei poista mitään

Syötteet: käynnistyksen tiedoista (GITHUB_EVENT_PATH: moskeijat, kuiva) tai argumenteista (argumentit voittavat; --poista = ei kuiva).
Ympäristö: MOSKEIJA_AVAIN (repon poisto), ORG, GITHUB_API (oletus https://api.github.com).
Julkiseen lokiin vain nimet ja tulokset.
"""
import argparse, glob, json, os, re, sys, urllib.error, urllib.parse, urllib.request

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sisaltorepo

# Ei koskaan poisteta: sivupohja, paneeli, sisältörepo, organisaation asetukset ja vanhaan julkaisuun jäävät sivut
# (Hyvinkää, Masjid-sunnah siirretään erikseen, vanha testimoskeija odottaa testaajan kuittausta).
SUOJATUT = {"pohja", "hallinta", "sisalto", ".github", "hyvinkaa-islam-keskus", "masjid-sunnah", "testimoskeija"}
NIMI = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
SIIRRETYT = "siirretyt"


class Hylatty(Exception):
    """Repoa ei poisteta: syy on julkista lokia varten (vain nimi ja syy)."""


def api(polku, metodi="GET"):
    perus = os.environ.get("GITHUB_API", "https://api.github.com").rstrip("/")
    pyynto = urllib.request.Request(perus + polku, method=metodi, headers={
        "Authorization": f"Bearer {os.environ.get('MOSKEIJA_AVAIN', '')}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "suomen-moskeijat"})
    with urllib.request.urlopen(pyynto, timeout=30) as v:
        teksti = v.read()
        return json.loads(teksti) if teksti else {}


def kaynnistyksen_syotteet():
    """workflow_dispatch-syötteet tapahtumatiedostosta (ei ympäristömuuttujina: julkinen loki näyttää vaiheen ympäristön)."""
    polku = os.environ.get("GITHUB_EVENT_PATH")
    if not polku or not os.path.exists(polku):
        return {}
    try:
        with open(polku, encoding="utf-8") as f:
            return (json.load(f) or {}).get("inputs") or {}
    except Exception:
        return {}


def siirretyt(sisalto):
    """Sivustoluettelon sivut, joilla on kansio moskeijat/<nimi>/ (nimi täsmälleen)."""
    kansiot = set(os.listdir(os.path.join(sisalto, "moskeijat"))) if os.path.isdir(os.path.join(sisalto, "moskeijat")) else set()
    return [n for n in (str(s.get("nimi") or "") for s in sisaltorepo.lue_sivut(sisalto)) if n in kansiot]


def tarkista_paikallisesti(sisalto, nimi, luettelo):
    """Nimi, suojatut, sisältörepon kansio ja sivustoluettelon rivi. Hylatty, jos repoa ei saa poistaa."""
    if nimi.lower() in SUOJATUT:
        raise Hylatty("suojattu: ei poisteta koskaan")
    if not NIMI.fullmatch(nimi) or ".." in nimi:
        raise Hylatty("nimi ei kelpaa")
    kansiot = set(os.listdir(os.path.join(sisalto, "moskeijat"))) if os.path.isdir(os.path.join(sisalto, "moskeijat")) else set()
    if nimi not in kansiot:  # os.listdir: kirjainkoko tarkasti myös kirjainkoosta riippumattomassa tiedostojärjestelmässä
        raise Hylatty(f"sisältörepossa ei ole kansiota moskeijat/{nimi}/ (kirjainkoko tarkasti): ei siirretty")
    if not glob.glob(os.path.join(sisaltorepo.kansio(sisalto, nimi), "_moskeijat", "*.md")):
        raise Hylatty(f"sisältörepon kansiossa moskeijat/{nimi}/ ei ole moskeijaa (_moskeijat/*.md)")
    if nimi not in luettelo:
        raise Hylatty("ei sivustoluettelossa samalla nimellä (kirjainkoko tarkasti): ei siirretty")


def tarkista_githubissa(org, nimi):
    """Vanha repo: None, jos sitä ei ole; muuten True, kun se on organisaation moskeijarepo täsmälleen tällä nimellä."""
    polku = f"/repos/{urllib.parse.quote(org)}/{urllib.parse.quote(nimi)}"
    try:
        repo = api(polku)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise Hylatty(f"tarkistus epäonnistui (HTTP {e.code})")
    except (urllib.error.URLError, TimeoutError):
        raise Hylatty("tarkistus epäonnistui (yhteys)")
    if str(repo.get("name") or "") != nimi:
        raise Hylatty(f"GitHubin repon nimi on {repo.get('name')!r} (uudelleennimetty tai eri kirjainkoko)")
    omistaja = str((repo.get("owner") or {}).get("login") or "")
    if omistaja.lower() != org.lower() or str(repo.get("full_name") or "").lower() != f"{org}/{nimi}".lower():
        raise Hylatty(f"ei organisaation {org} repo")
    try:
        tiedostot = api(polku + "/contents/_moskeijat")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise Hylatty(f"tarkistus epäonnistui (HTTP {e.code})")
        raise Hylatty("ei moskeijarepo (_moskeijat puuttuu)")
    except (urllib.error.URLError, TimeoutError):
        raise Hylatty("tarkistus epäonnistui (yhteys)")
    if not isinstance(tiedostot, list) or not any(str(t.get("name", "")).endswith(".md") for t in tiedostot):
        raise Hylatty("ei moskeijarepo (_moskeijat/*.md puuttuu)")
    return True


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--sisalto", required=True)
    p.add_argument("--moskeijat", default=None, help='nimet pilkuin tai "siirretyt"')
    p.add_argument("--poista", action="store_true", help="poista oikeasti (muuten kuiva-syöte, oletus kuivaharjoitus)")
    a = p.parse_args(argv)
    syotteet = kaynnistyksen_syotteet()
    pyydetyt = (a.moskeijat if a.moskeijat is not None else str(syotteet.get("moskeijat") or "")).strip()
    kuiva_syote = syotteet.get("kuiva", True)
    kuiva = not a.poista and not (kuiva_syote is False or str(kuiva_syote).strip().lower() == "false")
    org = os.environ.get("ORG", "suomen-moskeijat")
    if not os.environ.get("MOSKEIJA_AVAIN"):
        raise SystemExit("MOSKEIJA_AVAIN puuttuu (vanhan moskeijarepon tarkistus ja poisto)")
    if not pyydetyt:
        raise SystemExit('Anna moskeijat (nimet pilkuin) tai "siirretyt"')

    luettelo = {str(s.get("nimi") or "") for s in sisaltorepo.lue_sivut(a.sisalto)}
    kaikki = pyydetyt.lower() == SIIRRETYT
    nimet = siirretyt(a.sisalto) if kaikki else [n.strip() for n in pyydetyt.split(",") if n.strip()]
    nimet = list(dict.fromkeys(nimet))
    print(f"{'Kuivaharjoitus: mitään ei poisteta. ' if kuiva else ''}"
          f"{'Siirretyt moskeijat sivustoluettelosta' if kaikki else 'Nimetyt moskeijat'}: {len(nimet)}", flush=True)

    # 1) Tarkistukset kaikille ensin
    poistettavat, hylatyt, virheet = [], [], []
    for nimi in nimet:
        try:
            tarkista_paikallisesti(a.sisalto, nimi, luettelo)
            if tarkista_githubissa(org, nimi) is None:
                print(f"  {nimi}: ei vanhaa repoa (jo poistettu tai ei ollut)", flush=True)
                continue
            poistettavat.append(nimi)
        except Hylatty as e:
            hylatyt.append(nimi)
            if str(e).startswith("tarkistus epäonnistui"):
                virheet.append(nimi)
            print(f"  {nimi}: ei poisteta – {e}", flush=True)

    if hylatyt and not kaikki:
        raise SystemExit(f"Listassa on {len(hylatyt)} nimeä, joita ei saa poistaa: mitään ei poistettu.")

    # 2) Poisto (tai kuivana lista)
    poistetut = []
    for nimi in poistettavat:
        if kuiva:
            print(f"  {nimi}: vanha repo {org}/{nimi} poistettaisiin", flush=True)
            continue
        try:
            api(f"/repos/{urllib.parse.quote(org)}/{urllib.parse.quote(nimi)}", "DELETE")
            poistetut.append(nimi)
            print(f"  {nimi}: vanha repo poistettu", flush=True)
        except urllib.error.HTTPError as e:
            virheet.append(nimi)
            print(f"  {nimi}: poisto epäonnistui (HTTP {e.code})", flush=True)
        except (urllib.error.URLError, TimeoutError):
            virheet.append(nimi)
            print(f"  {nimi}: poisto epäonnistui (yhteys)", flush=True)

    tulos = f"{'Poistettaisiin' if kuiva else 'Poistettu'} {len(poistettavat if kuiva else poistetut)}, ohitettu {len(hylatyt)}, virheitä {len(virheet)}"
    print(tulos, flush=True)
    yhteenveto = os.environ.get("GITHUB_STEP_SUMMARY")
    if yhteenveto:
        with open(yhteenveto, "a", encoding="utf-8") as f:
            f.write(f"{'Kuivaharjoitus. ' if kuiva else ''}{tulos}\n")
    if virheet:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
