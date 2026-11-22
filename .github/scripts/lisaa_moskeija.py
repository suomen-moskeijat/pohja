#!/usr/bin/env python3
"""Lisää uuden moskeijan sisältörepoon (hallinta#51, ADR-0006): kansio moskeijat/<nimi>/ ja sivustoluettelon rivi.

Lopputulos on sama kuin ennen moskeijalle luotu oma repo (kokoelmat, _moskeijat/<nimi>.md, tiedostot/<nimi>/), mutta ilman
sivun osoitetta (url/baseurl): rakennusajo päättää osoitteen sivustoluettelosta. Uusi sivu on luonnos (tai ehdotus), joten
sivustoluetteloon tulee luonnoslinkin salainen osa (ADR-0008), ja sivu rakentuu seuraavassa rakennusajossa omaan
Pages-projektiinsa (julkaisukohde luo projektin). Uusia moskeijarepoja ei luoda.

Käyttö GitHubissa: pohja → Actions → "Lisää moskeija" (paneeli: Ylläpito → Uusi moskeija käynnistää sen).
    python3 .github/scripts/lisaa_moskeija.py --sisalto <sisältörepon kansio> [--tallenna] --nimi "..." --kaupunki "..." [--mawaqit ...]
      --sisalto   kirjoittaa moskeijan kansion ja sivustoluettelon rivin sisältörepon kansioon
      --tallenna  lisäksi commit ja push sisältörepoon (ilman: kuivaharjoitus, mitään ei tallenneta)
    python3 .github/scripts/lisaa_moskeija.py --kuiva <kansio> --nimi "..." --kaupunki "..."
      --kuiva     vain moskeijan kansio tähän kansioon (testit), ei sisältörepoa

Työnkulussa syötteet luetaan käynnistyksen tiedoista (GITHUB_EVENT_PATH), eivät ympäristömuuttujista: julkinen loki näyttää
vaiheen ympäristömuuttujat. Loki ei tulosta tuotua sisältöä (nimi, osoite, yhteystiedot, tekstit) eikä salaista osaa: vain
sivun tunnuksen ja määrät.

Tiedot täydennetään automaattisesti:
- Mawaqit: nimi, koordinaatit, Jumuah; ajat, iqamah ja kuvat haetaan rakennusajossa.
- Masjidbox: nimi ja osoite; ajat ja iqamah haetaan rakennusajossa.
- Muuten koordinaatit osoitteesta (OpenStreetMap Nominatim).
- Nykyinen nettisivu (--nettisivu): logo, värit, yhteystiedot, somet, kuvat, Meistä-teksti,
  WordPress-sivut ja -kirjoitukset (tuo_sivusto.py). Tarkistetaan hallintapaneelissa.
"""
import argparse
import contextlib
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True  # ei __pycache__-tiedostoja sivupohjan kansioon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sisaltorepo

SELAIN = {"User-Agent": "SuomenMoskeijat/1.0 (+https://github.com/suomen-moskeijat/pohja)"}


def ilmoita(rivi):
    """Julkiseen lokiin: ei sisältöä (nimi, osoite, yhteystiedot, tekstit), vain tunnukset ja määrät."""
    print(rivi, file=sys.stderr, flush=True)


def hae(osoite, otsakkeet=None):
    req = urllib.request.Request(osoite, headers={**SELAIN, **(otsakkeet or {})})
    with urllib.request.urlopen(req, timeout=30) as v:
        return v.read().decode("utf-8", "replace")


def slugiksi(teksti):
    t = unicodedata.normalize("NFKD", teksti.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def tunnus(arvo, palvelu):
    """Hyväksyy tunnuksen, osoitteen tai upotuskoodin (esim. mawaqit.net/en/w/<tunnus>?...)."""
    arvo = (arvo or "").strip()
    if not arvo:
        return ""
    if palvelu == "mawaqit":
        m = re.search(r"mawaqit\.net/(?:[a-z]{2}/)?(?:w/|m/)?([A-Za-z0-9-]+)", arvo)
    else:
        m = re.search(r"masjidbox\.com/prayer-times/([A-Za-z0-9-]+)", arvo)
    return m.group(1) if m else re.sub(r"[^A-Za-z0-9-]", "", arvo)


# ------------------------------------------------------------- tietolähteet
def mawaqit_tiedot(t):
    sivu = hae("https://mawaqit.net/fi/" + urllib.parse.quote(t))
    d = json.loads(re.search(r"(?:let|var|const)\s+confData\s*=\s*(\{.*?\});\s*\n", sivu, re.S).group(1))
    return {"nimi": d.get("name") or "", "lat": d.get("latitude"), "lon": d.get("longitude"),
            "juma": (d.get("jumua") or "").replace(":", "."), "puhelin": d.get("phone") or "",
            "sahkoposti": d.get("email") or "", "nettisivu": d.get("site") or ""}


def masjidbox_tiedot(t):
    sivu = hae("https://masjidbox.com/prayer-times/" + urllib.parse.quote(t))
    raaka = re.search(r'window\.REDUX_STATE\s*=\s*(["\'])(.*?)\1', sivu, re.S).group(2)
    raaka = re.sub(r"%u([0-9A-Fa-f]{4})", lambda x: chr(int(x.group(1), 16)), raaka)
    a = json.loads(urllib.parse.unquote(raaka, encoding="latin-1")).get("masjidbox", {}).get("masjidboxAthany") or {}
    return {"nimi": (a.get("name") or "").replace(" - ", " "), "osoite": a.get("address") or ""}


def koordinaatit(osoite, kaupunki):
    for haku in [f"{osoite}, {kaupunki}, Finland" if osoite else None, f"{kaupunki}, Finland"]:
        if not haku:
            continue
        try:
            tulos = json.loads(hae(os.environ.get("NOMINATIM_OSOITE", "https://nominatim.openstreetmap.org/search")
                                   + "?format=json&limit=1&q=" + urllib.parse.quote(haku)))
            if tulos:
                return round(float(tulos[0]["lat"]), 6), round(float(tulos[0]["lon"]), 6)
        except Exception as e:
            ilmoita(f"Koordinaatteja ei saatu osoitteesta ({type(e).__name__})")
        time.sleep(1)  # Nominatimin käyttöehto: enintään 1 haku sekunnissa
    k = KAUPUNKIEN_KESKUSTAT.get(kaupunki.strip().lower())
    if k:
        ilmoita("Koordinaatit: kaupungin keskusta – tarkista kartalta paneelissa")
        return k
    return 0, 0


# Varalla, jos osoitehaku ei onnistu (kartta ja reittiohjeet)
KAUPUNKIEN_KESKUSTAT = {
    "helsinki": (60.1699, 24.9384), "espoo": (60.2055, 24.6559), "vantaa": (60.2934, 25.0378),
    "tampere": (61.4978, 23.761), "turku": (60.4518, 22.2666), "oulu": (65.0121, 25.4651),
    "jyväskylä": (62.2426, 25.7473), "kuopio": (62.8924, 27.677), "lahti": (60.9827, 25.6612),
    "vaasa": (63.0951, 21.6165), "joensuu": (62.601, 29.7636), "seinäjoki": (62.7903, 22.8403),
    "hyvinkää": (60.6305, 24.8581), "pori": (61.4851, 21.7974), "lappeenranta": (61.0587, 28.1887),
    "kotka": (60.4664, 26.9458), "hämeenlinna": (60.9959, 24.4643), "rovaniemi": (66.5039, 25.7294),
    "kouvola": (60.8681, 26.7042), "järvenpää": (60.4737, 25.0899), "kerava": (60.4034, 25.105),
}


# ------------------------------------------------------------- vanha nettisivu
def tuo_nettisivu(osoite):
    """Hakee tiedot moskeijan nykyiseltä sivulta (tuo_sivusto.py). Virhe ei estä sivun luomista."""
    import tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import tuo_sivusto
        kansio = tempfile.mkdtemp(prefix="tuonti-")
        # Tuonnin oma tuloste (sivujen osoitteet, virheet) ei julkiseen lokiin
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            d = tuo_sivusto.tuo(osoite.strip(), kansio)
        d["_kansio"] = kansio
        ilmoita(f"Nettisivu: somekanavia {len(d.get('some', {}))}, kuvia {len(d.get('kuvat', []))}, "
                f"omia sivuja {len(d.get('omat_sivut', []))}, artikkeleita {len(d.get('artikkelit', []))}"
                f"{', logo' if d.get('logo') else ''}{', Meistä-teksti' if d.get('meista') else ''}")
        return d
    except Exception as e:
        ilmoita(f"Nettisivua ei voitu lukea ({type(e).__name__})")
        return {}


# Tuoduista omista sivuista valikkoon vain toimintaa kuvaavat (muut näkyvät sivulla, kun ne lisätään valikkoon CMS:ssä)
VALIKKOON = re.compile(r"(?i)ohjelma|kirjasto|l[äa]hte|resurss|opetus|koulu|madrasa|kurssi|programme|program|library|school|courses|visits|vierail")


def lisaa_tuodut_tiedostot(t, d):
    """Logo, kuvat, omat sivut ja artikkelit vanhalta sivulta uuden repon tiedostoiksi."""
    kansio, slug = d.get("_kansio"), t["slug"]
    lisat = t["lisatiedostot"]
    if d.get("logo") and kansio:
        polku = f"tiedostot/{slug}/{d['logo']}"
        lisat[polku] = open(os.path.join(kansio, d["logo"]), "rb").read()
        t["logo"] = "/" + polku
        t["teema"] = d.get("teema") or {}
    for nimi in d.get("kuvat", []):
        polku = f"tiedostot/{slug}/{nimi}"
        lisat[polku] = open(os.path.join(kansio, nimi), "rb").read()
        t["galleria"].append("/" + polku)
    # Oman sivun teksti on osiossa (Oma teksti, tausta Kortti), kuten paneelissa tehdyillä sivuilla
    for i, s in enumerate(d.get("omat_sivut", [])):
        lisat[f"_sivut/{s['slug']}.md"] = (
            f"---\ntitle: {yaml_str(s['nimi'])}\nvalikossa: {'true' if VALIKKOON.search(s['slug'] + ' ' + s['nimi']) else 'false'}\njarjestys: {i + 1}\n"
            f"# Tuotu vanhalta sivulta: {s['url']} – tarkista\n"
            f"osiot:\n  - osio: teksti\n    teksti: {yaml_teksti(s['html'])}\n    tausta: kortti\n---\n")
    for a in d.get("artikkelit", []):
        lisat[f"_artikkelit/{a['paiva']}-{a['slug'][:60]}.md"] = (
            f"---\ntitle: {yaml_str(a['nimi'])}\npaiva: {a['paiva']}\nkuvaus: {yaml_str(a['kuvaus'])}\n"
            f"# Tuotu vanhalta sivulta: {a['url']}\n---\n{{% raw %}}\n{a['html']}\n{{% endraw %}}\n")


# ------------------------------------------------------------- tiedostot
def yaml_str(s):
    return json.dumps(s or "", ensure_ascii=False)


# Jekyllin YAML (1.1) lukee nämä rivinvaihdoiksi myös lainausmerkeissä: \u-muodossa ne säilyvät merkkeinä
YAML_RIVINVAIHDOT = {chr(0x85): "\\u0085", chr(0x2028): "\\u2028", chr(0x2029): "\\u2029"}


def yaml_teksti(s):
    """Pitkä teksti (esim. tuotu HTML) yhdelle riville lainausmerkkeihin, rivinvaihdot \\n-merkkeinä."""
    t = yaml_str(s)
    for merkki, koodi in YAML_RIVINVAIHDOT.items():
        t = t.replace(merkki, koodi)
    return t


def tiedostot(t):
    """{polku: sisältö} moskeijan kansioon sisältörepossa (moskeijat/<nimi>/). Ei sivun osoitetta: rakennusajo päättää sen
    sivustoluettelosta (ADR-0006), eikä julkaisuajoa tai READMEa (vanhan moskeijarepon tiedostot)."""
    config = (f"# {t['nimi']} – sivun asetukset\n"
              f"# Sivun osoite ja luonnoslinkki ovat sisältörepon sivustoluettelossa (sivustot.yml), ei tässä tiedostossa.\n"
              f"title: {yaml_str(t['nimi'])}\n"
              f"description: {yaml_str(t['nimi'] + ', ' + (t['osoite'] or t['kaupunki']) + '. Rukousajat, tapahtumat ja toiminta.')}\n"
              f"moskeija: {t['slug']}     # tiedosto _moskeijat/{t['slug']}.md\n\n"
              # Uusi moskeija alkaa vain suomeksi (ADR-0001): muut kielet moskeija valitsee itse (paneeli: aloitus tai
              # Asetukset → Sivuston kielet). Sama rivimuoto kuin paneelin tallennuksessa (hallinta: src/kaannosasetus.js).
              f"kielet: [fi]   # sivuston kielivalikko (hallintapaneeli → Asetukset)\n")
    lahde_kommentti = {"mawaqit": "Mawaqitista automaattisesti (adhan, iqamah, Jumuah, kuvat)",
                       "masjidbox": "Masjidboxista automaattisesti (adhan, iqamah, Jumuah)",
                       "": "rukousajat.fi (Helsinki/Espoo/Vantaa); muualla lähde valitaan paneelissa"}[t["lahde"]]
    # Uusi moskeija alkaa tyhjästä (ADR-0001): ei oletusesittelyä, iqamah-minuutteja, toiminnan kieliä, yläosan nappeja eikä
    # valmiita artikkeleita. Vain tuotu tieto (vanhan sivun esittely ja Meistä-teksti, yhteystiedot, somet) tulee sivulle.
    esittely_rivi = f"esittely: {{ fi: {yaml_str(t['esittely'])} }}\n" if t.get("esittely") else ""
    meista_lohko = ""
    if t.get("meista"):
        lyhyt = t["meista"].split("\n\n")[0]
        meista_lohko = (f"\n# Tuotu vanhalta sivulta ({t['nettisivu']}) – tarkista ja muokkaa\n"
                        f"meista_lyhyt: {{ fi: {yaml_str(lyhyt[:600])} }}\n"
                        f"meista: {{ fi: {yaml_str(t['meista'])} }}\n")
    md = f"""---
# Lisätty automaattisesti. Täydennä ja korjaa tietoja hallintapaneelissa (https://hallinta.suomenmoskeijat.fi/).
{"ehdotus: true        # esimerkkisivu: moskeija ei ole vielä mukana (palkki: Ehdotus)" + chr(10) if t.get("ehdotus") else ""}luonnos: true        # uusi sivu on luonnos (palkki ylhäällä, ei Googlessa); kun moskeija hyväksyy → false
title: {yaml_str(t['nimi'])}
slug: {t['slug']}
kaupunki: {yaml_str(t['kaupunki'])}
osoite: {yaml_str(t['osoite'] or t['kaupunki'])}
sijainti: {{ lat: {t['lat']}, lon: {t['lon']} }}

puhelin: {yaml_str(t['puhelin'])}
whatsapp: {yaml_str(t['whatsapp'])}
sahkoposti: {yaml_str(t['sahkoposti'])}
nettisivu: {yaml_str(t['nettisivu'])}
juma: {yaml_str(t['juma'])}

# Rukousajat: {lahde_kommentti}
rukousajat:
  lahde: {yaml_str(t['lahde'])}
  tunnus: {yaml_str(t['tunnus'])}

some:
  instagram: {yaml_str(t['instagram'])}
  facebook: {yaml_str(t['some'].get('facebook'))}
  youtube: {yaml_str(t['youtube'])}      # uusimmat videot näkyvät sivulla
  tiktok: {yaml_str(t['some'].get('tiktok'))}
  telegram: {yaml_str(t['telegram'])}     # julkisen kanavan julkaisut näkyvät sivulla
  snapchat: {yaml_str(t['some'].get('snapchat'))}
  x: {yaml_str(t['some'].get('x'))}
  threads: ""
  whatsapp_kanava: {yaml_str(t['some'].get('whatsapp_kanava'))}

teema:
  vari: oma           # valmis värimaailma (esim. smaragdi, sininen) tai oma = alla olevat värikoodit
  logo: {yaml_str(t['logo'])}            # ilman logoa yläpalkissa näkyy moskeijan nimi
  hero: vaalea
  # Omat värit (tyhjä = pohjan kulta-ruskea){' – arvattu logosta, tarkista' if t['teema'] else ''}
  paa: {yaml_str(t['teema'].get('paa'))}
  korostus: {yaml_str(t['teema'].get('korostus'))}
  korostus_vaalea: {yaml_str(t['teema'].get('korostus_vaalea'))}

hero_tunniste: {{ fi: {yaml_str(t['kaupunki'])} }}
{esittely_rivi}{meista_lohko}
# Etusivun yläosa: tausta kuvio | kuva | vari, napit (enintään 2, moskeija valitsee itse):
# lapsi, toiminta, rukousajat, lahjoita, yhteys, oma tai oman sivun nimi
alku:
  tausta: kuvio
  kuva: ""
  napit: []

# Yhteiset artikkelit (islaminusko.fi, lähdemerkinnällä), kun moskeija valitsee ne. Tyhjä lista = vain omat artikkelit.
artikkelit:
  lahteet: []

# Valikosta piilotettavat sivut, esim. [tapahtumat]. Lahjoita näkyy, kun lahjoitustiedot on lisätty.
valikko_piilota: []
galleria: {json.dumps(t['galleria'], ensure_ascii=False)}
---
"""
    return {
        "_config.yml": config,
        f"_moskeijat/{t['slug']}.md": md,
        "_tapahtumat/.gitkeep": "",
        "_sivut/.gitkeep": "",
        "tiedostot/.gitkeep": "",
        **t.get("lisatiedostot", {}),
    }


# ------------------------------------------------------------- syötteet ja kirjoitus
KENTAT = ["nimi", "kaupunki", "mawaqit", "masjidbox", "osoite", "instagram", "whatsapp", "youtube", "telegram", "repo", "nettisivu",
          "puhelin", "sahkoposti", "facebook", "linkki"]


def kaynnistyksen_syotteet():
    """Työnkulun käynnistyksen syötteet (workflow_dispatch) tapahtumatiedostosta. Niitä ei anneta ympäristömuuttujina, koska
    julkinen loki näyttää vaiheen ympäristömuuttujat."""
    polku = os.environ.get("GITHUB_EVENT_PATH")
    if not polku or not os.path.exists(polku):
        return {}
    try:
        with open(polku, encoding="utf-8") as f:
            syotteet = (json.load(f) or {}).get("inputs") or {}
        return {k: str(v) for k, v in syotteet.items() if v is not None}
    except Exception:
        return {}


def argumentit(argv=None):
    syotteet = kaynnistyksen_syotteet()
    p = argparse.ArgumentParser(description="Lisää uuden moskeijan sisältörepoon")
    for k in KENTAT:
        p.add_argument("--" + k, default=syotteet.get(k, os.environ.get("SYOTE_" + k.upper(), "")))
    p.add_argument("--kuiva", help="vain moskeijan kansio tähän kansioon (ei sisältörepoa)")
    p.add_argument("--sisalto", help="sisältörepon kansio: moskeijat/<nimi>/ ja sivustoluettelon rivi")
    p.add_argument("--tallenna", action="store_true", help="--sisalto: commit ja push sisältörepoon (muuten kuivaharjoitus)")
    p.add_argument("--pohja", default="main", choices=["main", "testi"], help="sivupohjan versio sivustoluetteloon (oletus main)")
    p.add_argument("--ehdotus", action="store_true", help="esimerkkisivu, josta moskeija ei ole vielä päättänyt (palkki: Ehdotus)")
    a = p.parse_args(argv)
    if not a.kuiva and not a.sisalto:
        p.error("anna --sisalto (sisältörepon kansio) tai --kuiva (kansio)")
    return a


def kirjoita(kohde, tiedot):
    for polku, sisalto in tiedot.items():
        tiedosto = os.path.join(kohde, polku)
        os.makedirs(os.path.dirname(tiedosto), exist_ok=True)
        with open(tiedosto, "wb") as f:
            f.write(sisalto if isinstance(sisalto, bytes) else sisalto.encode())


def lisaa_sisaltoon(sisalto, nimi, tiedot, pohja="main"):
    """Moskeijan kansio ja sivustoluettelon rivi sisältörepon kansioon (ei tallennusta). Palauttaa luettelon rivin."""
    if not sisaltorepo.NIMI.fullmatch(nimi):
        raise sisaltorepo.Virhe(f"Sivun tunnus ei kelpaa: pienet kirjaimet a–z, numerot ja viiva ({nimi!r})")
    kansio = sisaltorepo.kansio(sisalto, nimi)
    sivut = sisaltorepo.lue_sivut(sisalto)
    if os.path.exists(kansio) or any(str(s.get("nimi") or "") == nimi for s in sivut):
        raise sisaltorepo.Virhe(f"{nimi} on jo sisältörepossa – valitse toinen tunnus.")
    rivi = {"nimi": nimi, "projekti": sisaltorepo.projektin_nimi(nimi, sivut), "pohja": pohja,
            "salainen_osa": sisaltorepo.uusi_salainen_osa()}  # luonnos ja ehdotus näkyvät vain luonnoslinkillä (ADR-0008)
    kirjoita(kansio, tiedot)
    sisaltorepo.lisaa_sivu(sisalto, rivi)
    return rivi


def valmistele(a):
    """Moskeijan tiedot syötteistä, tietolähteistä ja nettisivulta. Palauttaa (sivun tunnus, tiedot, {polku: sisältö})."""
    if not a.nimi.strip() and not (a.mawaqit or a.masjidbox or a.nettisivu):
        raise SystemExit("Anna vähintään moskeijan nimi (tai Mawaqit-, Masjidbox- tai nettisivun linkki).")
    tuotu = tuo_nettisivu(a.nettisivu) if a.nettisivu.strip() else {}
    if not a.kaupunki.strip() and tuotu.get("osoite"):
        a.kaupunki = tuotu["osoite"].split()[-1]  # "Katu 1, 05800 Hyvinkää" → Hyvinkää
    if not a.nimi.strip() and tuotu.get("nimi"):
        a.nimi = tuotu["nimi"]
    if not a.kaupunki.strip():
        raise SystemExit("Anna kaupunki.")

    t = {"nimi": a.nimi.strip(), "kaupunki": a.kaupunki.strip(), "osoite": a.osoite.strip(),
         "instagram": a.instagram.strip(), "whatsapp": a.whatsapp.strip(),
         "youtube": a.youtube.strip(), "telegram": a.telegram.strip(), "puhelin": "", "sahkoposti": "",
         "nettisivu": "", "juma": "", "lat": 0, "lon": 0, "lahde": "", "tunnus": "",
         "some": {}, "logo": "", "teema": {}, "esittely": "", "meista": "", "galleria": [], "lisatiedostot": {},
         "ehdotus": a.ehdotus}
    t["puhelin"], t["sahkoposti"] = a.puhelin.strip(), a.sahkoposti.strip()
    t["nettisivu"] = a.linkki.strip()
    for k in ("osoite", "puhelin", "sahkoposti", "whatsapp", "juma", "nettisivu", "esittely", "meista"):
        t[k] = t[k] or tuotu.get(k, "")
    for k in ("instagram", "youtube", "telegram"):
        t[k] = t[k] or tuotu.get("some", {}).get(k, "")
    t["some"] = tuotu.get("some", {})
    if a.facebook.strip():
        t["some"]["facebook"] = a.facebook.strip()
    if a.mawaqit:
        t["lahde"], t["tunnus"] = "mawaqit", tunnus(a.mawaqit, "mawaqit")
        try:
            d = mawaqit_tiedot(t["tunnus"])
            t["nimi"] = t["nimi"] or d["nimi"]
            t["lat"], t["lon"] = round(float(d["lat"]), 6), round(float(d["lon"]), 6)
            for k in ("juma", "puhelin", "sahkoposti", "nettisivu"):
                t[k] = t[k] or d[k]
            ilmoita("Mawaqit: tiedot haettu")
        except Exception as e:
            ilmoita(f"Mawaqit-tietoja ei saatu ({type(e).__name__})")
    elif a.masjidbox:
        t["lahde"], t["tunnus"] = "masjidbox", tunnus(a.masjidbox, "masjidbox")
        try:
            d = masjidbox_tiedot(t["tunnus"])
            t["nimi"] = t["nimi"] or d["nimi"]
            t["osoite"] = t["osoite"] or re.sub(r",\s*Suomi$|,\s*Finland$", "", d["osoite"])
            ilmoita("Masjidbox: tiedot haettu")
        except Exception as e:
            ilmoita(f"Masjidbox-tietoja ei saatu ({type(e).__name__})")
    if not t["lat"]:
        t["lat"], t["lon"] = koordinaatit(t["osoite"], t["kaupunki"])
    t["slug"] = slugiksi(t["nimi"])
    if not t["slug"]:
        raise SystemExit("Moskeijan nimestä ei saatu tunnusta: anna nimi tai sivun tunnus (repo).")
    if tuotu:
        lisaa_tuodut_tiedostot(t, tuotu)
    nimi = slugiksi(a.repo) if a.repo.strip() else t["slug"]
    return nimi, t, tiedostot(t)


def kuvaus(t, tiedot):
    """Julkiseen lokiin: määrät, ei sisältöä."""
    omat = sum(1 for p in tiedot if p.startswith("_sivut/") and p.endswith(".md"))
    artikkelit = sum(1 for p in tiedot if p.startswith("_artikkelit/"))
    kuvat = sum(1 for p in tiedot if p.startswith("tiedostot/") and not p.endswith(".gitkeep"))
    return (f"{'ehdotus' if t.get('ehdotus') else 'luonnos'}, {len(tiedot)} tiedostoa (omia sivuja {omat}, artikkeleita {artikkelit}, "
            f"kuvia {kuvat}), rukousaikojen lähde {t['lahde'] or 'ei vielä (oletus kaupungin mukaan)'}")


def yhteenvetoon(teksti):
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(teksti)


def main(argv=None):
    a = argumentit(argv)
    nimi, t, tiedot = valmistele(a)
    if a.kuiva:
        kirjoita(a.kuiva, tiedot)
        ilmoita(f"Kuivaharjoitus: {nimi}: {kuvaus(t, tiedot)} kansioon (ei sisältörepoa)")
        return
    lisaa_sisaltoon(a.sisalto, nimi, tiedot, a.pohja)
    tila = "kuivaharjoitus, mitään ei tallennettu"
    if a.tallenna:
        commit = sisaltorepo.tallenna(a.sisalto, f"Uusi moskeija: {nimi}", [f"moskeijat/{nimi}", sisaltorepo.LUETTELO])
        tila = "tallennettu sisältörepoon" if commit else "ei muutoksia"
    rivi = f"{nimi}: {kuvaus(t, tiedot)}; kansio moskeijat/{nimi}/ ja sivustoluettelon rivi (luonnoslinkki) – {tila}"
    ilmoita(rivi)
    yhteenvetoon(f"## Uusi moskeija: {nimi}\n\n- {rivi}\n"
                 + ("- Sivu rakentuu seuraavassa rakennusajossa omaan Pages-projektiinsa. Se on luonnos ja näkyy vain luonnoslinkillä "
                    "(paneeli). Kutsu moskeijan pääkäyttäjä paneelissa (moskeija → Käyttäjät).\n" if a.tallenna else ""))


if __name__ == "__main__":
    main()
