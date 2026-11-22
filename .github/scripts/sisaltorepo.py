#!/usr/bin/env python3
"""Sisältörepon kirjoitus pohjan työnkuluista (hallinta#51, ADR-0006): uusi moskeija, ehdotukset listasta ja poisto.

Sisältörepo on yksityinen repo, jossa on
  sivustot.yml           sivustoluettelo: jokaiselle sivulle nimi, projekti, sivupohjan versio (pohja), salainen osa …
  moskeijat.csv          ylläpitäjän luettelo Suomen moskeijoista (ehdotusten pohja; paneelin Moskeijalista)
  moskeijat/<nimi>/      moskeijan oma sisältö (kuten vanhan moskeijarepon juuri, ilman sivun osoitetta)

Työnkulku hakee sisältörepon kansioon (actions/checkout kirjoitusavaimella), skripti muuttaa tiedostot ja tallenna() tekee
yhden commitin ja pushaa sen. Jos sisältörepo liikkui välissä (paneelin tallennus), commit siirretään tuoreen kärjen päälle ja
yritetään uudelleen; ristiriita tulee vain, jos samaa tiedostoa on muutettu.

Sivustoluettelo muutetaan tekstinä (rivi lisätään tai sivun kohta poistetaan), jotta paneelin ja ihmisten muotoilu ja
kommentit säilyvät, ja tulos tarkistetaan YAML-lukijalla: muut sivut pysyvät täsmälleen ennallaan.
Mikään funktio ei tulosta sisältöä eikä salaista osaa (julkinen loki).
"""
import csv, io, os, re, secrets, subprocess

import yaml

LUETTELO = "sivustot.yml"
MOSKEIJAT_CSV = "moskeijat.csv"
CSV_SARAKKEET = ["nimi", "kaupunki", "osoite", "puhelin", "sahkoposti", "nettisivu", "facebook", "repo", "tila", "lahde", "huom"]
NIMI = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")  # sama kuin rakennusajossa (rakennusajo.py)
PROJEKTI = re.compile(r"[a-z0-9][a-z0-9-]{0,57}")
KIRJOITTAJA = ["-c", "user.name=github-actions[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com"]


class Virhe(SystemExit):
    """Työnkulun virhe: teksti on julkista lokia varten (ei sisältöä eikä salaista osaa)."""


def kansio(sisalto, nimi):
    return os.path.join(sisalto, "moskeijat", nimi)


# ---------------------------------------------------------------- sivustoluettelo
def lue_sivut(sisalto):
    polku = os.path.join(sisalto, LUETTELO)
    if not os.path.exists(polku):
        return []
    try:
        with open(polku, encoding="utf-8") as f:
            sivut = (yaml.safe_load(f) or {}).get("sivut") or []
    except Exception:
        raise Virhe("Sivustoluetteloa (sivustot.yml) ei voitu lukea")
    if not isinstance(sivut, list):
        raise Virhe("Sivustoluettelossa (sivustot.yml) ei ole sivujen listaa")
    return [s for s in sivut if isinstance(s, dict)]


def sivu(sisalto, nimi):
    return next((s for s in lue_sivut(sisalto) if str(s.get("nimi") or "") == nimi), None)


def uusi_salainen_osa():
    """Luonnoslinkin salainen osa samassa muodossa kuin paneelin luonnoslinkin vaihto (hallinta src/sivustoluettelo.js, #49):
    "luonnos-" + 32 merkkiä A-Z, a-z, 0-9, - ja _ (192 bittiä satunnaista, ADR-0008). Etuliite erottaa luonnoslinkin
    julkaistun sivun poluista (esim. Cloudflaren sääntö tekoälyboteille) eikä heikennä satunnaisuutta."""
    return "luonnos-" + secrets.token_urlsafe(24)


def projektin_nimi(nimi, sivut):
    """Pages-projektin nimi: sm-<nimi> (enintään 58 merkkiä), eri kuin luettelon muilla sivuilla."""
    varatut = {str(s.get("projekti") or "") for s in sivut}
    perus = ("sm-" + nimi)[:58].rstrip("-")
    ehdokas, i = perus, 2
    while ehdokas in varatut:
        loppu = f"-{i}"
        ehdokas, i = perus[:58 - len(loppu)].rstrip("-") + loppu, i + 1
    return ehdokas


def _vertaa(ennen, jalkeen, odotettu, toimenpide):
    if jalkeen != odotettu:
        raise Virhe(f"Sivustoluettelon muutos ({toimenpide}) ei onnistunut: luettelon muoto on odottamaton. Tiedostoa ei muutettu.")


def lisaa_sivu(sisalto, uusi):
    """Lisää sivun sivustoluettelon loppuun. uusi: { nimi, projekti, pohja, salainen_osa?, … } (vain yksinkertaisia arvoja)."""
    polku = os.path.join(sisalto, LUETTELO)
    teksti = open(polku, encoding="utf-8").read() if os.path.exists(polku) else "sivut:\n"
    ennen = lue_sivut(sisalto)
    if any(str(s.get("nimi") or "") == uusi["nimi"] for s in ennen):
        raise Virhe(f"{uusi['nimi']} on jo sivustoluettelossa")
    # Luettelon kohtien sisennys (paneelin ja ihmisten kirjoittama muoto säilyy)
    m = re.search(r"^(\s*)-\s", teksti.split("sivut:", 1)[-1], re.M)
    sis = m.group(1) if m else "  "
    rivit = []
    for i, (k, v) in enumerate(uusi.items()):
        arvo = "true" if v is True else "false" if v is False else str(v)
        if not re.fullmatch(r"[A-Za-z0-9_.:/-]+", arvo):
            raise Virhe(f"Sivustoluettelon arvo {k} ei kelpaa")
        if yaml.safe_load(arvo) != v:  # esim. pelkistä numeroista tehty tunnus: lainausmerkit, jotta arvo pysyy tekstinä
            arvo = f'"{arvo}"'
        rivit.append(f"{sis}{'- ' if i == 0 else '  '}{k}: {arvo}")
    teksti = re.sub(r"^sivut:\s*\[\s*\]\s*$", "sivut:", teksti, count=1, flags=re.M)  # tyhjä lista: sivut: []
    uusi_teksti = teksti.rstrip("\n") + "\n" + "\n".join(rivit) + "\n"
    jalkeen = (yaml.safe_load(uusi_teksti) or {}).get("sivut") or []
    _vertaa(ennen, jalkeen, ennen + [uusi], "lisäys")
    with open(polku, "w", encoding="utf-8") as f:
        f.write(uusi_teksti)


def poista_sivu(sisalto, nimi):
    """Poistaa sivun kohdan sivustoluettelosta. Palauttaa poistetun kohdan tai None, jos sivua ei ollut."""
    polku = os.path.join(sisalto, LUETTELO)
    ennen = lue_sivut(sisalto)
    poistettava = next((s for s in ennen if str(s.get("nimi") or "") == nimi), None)
    if not poistettava:
        return None
    rivit = open(polku, encoding="utf-8").read().split("\n")
    # Kohta alkaa rivistä "<sis>- " ja jatkuu, kunnes tulee seuraava samalla sisennyksellä alkava kohta tai sisentämätön rivi
    alku = next((i for i, r in enumerate(rivit) if re.fullmatch(rf"\s*-\s+nimi:\s*[\"']?{re.escape(nimi)}[\"']?\s*(#.*)?", r)), None)
    if alku is None:
        _vertaa(ennen, None, ennen, "poisto")
    sis = len(rivit[alku]) - len(rivit[alku].lstrip())
    loppu = alku + 1
    # Kohtaan kuuluvat sitä syvemmälle sisennetyt rivit (ja tyhjät rivit niiden välissä)
    while loppu < len(rivit) and (not rivit[loppu].strip() or len(rivit[loppu]) - len(rivit[loppu].lstrip()) > sis):
        loppu += 1
    uusi_teksti = "\n".join(rivit[:alku] + rivit[loppu:])
    jalkeen = (yaml.safe_load(uusi_teksti) or {}).get("sivut") or []
    _vertaa(ennen, [s for s in jalkeen if isinstance(s, dict)], [s for s in ennen if s is not poistettava], "poisto")
    with open(polku, "w", encoding="utf-8") as f:
        f.write(uusi_teksti)
    return poistettava


# ---------------------------------------------------------------- moskeijat.csv
def lue_csv(sisalto):
    """(sarakkeet, rivit) sisältörepon moskeijat.csv:stä."""
    polku = os.path.join(sisalto, MOSKEIJAT_CSV)
    if not os.path.exists(polku):
        raise Virhe("moskeijat.csv puuttuu sisältörepon juuresta")
    with open(polku, encoding="utf-8", newline="") as f:
        lukija = csv.DictReader(f)
        rivit = list(lukija)
        return list(lukija.fieldnames or CSV_SARAKKEET), rivit


def kirjoita_csv(sisalto, sarakkeet, rivit):
    ulos = io.StringIO()
    w = csv.DictWriter(ulos, fieldnames=sarakkeet, lineterminator="\n")
    w.writeheader()
    w.writerows(rivit)
    with open(os.path.join(sisalto, MOSKEIJAT_CSV), "w", encoding="utf-8") as f:
        f.write(ulos.getvalue())


# ---------------------------------------------------------------- tallennus (git)
def _git(sisalto, *argumentit, tarkista=True):
    t = subprocess.run(["git", "-C", sisalto, *argumentit], capture_output=True, text=True, timeout=300)
    if tarkista and t.returncode != 0:
        raise Virhe(f"git {argumentit[0]} epäonnistui (koodi {t.returncode})")
    return t


def tallenna(sisalto, viesti, polut, yrityksia=5):
    """Yksi commit muutetuista poluista (moskeijan kansio, sivustot.yml, moskeijat.csv) ja push sisältörepoon.

    Jos sisältörepo liikkui välissä, commit siirretään tuoreen kärjen päälle (rebase) ja push yritetään uudelleen.
    Palauttaa commitin tunnisteen tai None, jos mikään ei muuttunut."""
    _git(sisalto, "add", "-A", "--", *polut)
    if _git(sisalto, "diff", "--cached", "--quiet", tarkista=False).returncode == 0:
        return None
    _git(sisalto, *KIRJOITTAJA, "commit", "-q", "-m", viesti)
    haara = _git(sisalto, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"
    for _ in range(yrityksia):
        if _git(sisalto, "push", "-q", "origin", f"HEAD:{haara}", tarkista=False).returncode == 0:
            return _git(sisalto, "rev-parse", "HEAD").stdout.strip()
        # Joku muu ehti väliin: tuore kärki ja oma commit sen päälle
        if _git(sisalto, *KIRJOITTAJA, "pull", "-q", "--rebase", "origin", haara, tarkista=False).returncode != 0:
            _git(sisalto, "rebase", "--abort", tarkista=False)
            raise Virhe("Sisältörepoa muutettiin samaan aikaan samasta kohdasta (ristiriita). Mitään ei tallennettu: aja työnkulku uudelleen.")
    raise Virhe(f"Sisältörepoon ei saatu tallennettua {yrityksia} yrityksellä. Mitään ei tallennettu: aja työnkulku uudelleen.")
