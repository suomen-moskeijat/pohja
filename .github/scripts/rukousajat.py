#!/usr/bin/env python3
"""Hakee moskeijoiden viralliset rukous- ja iqamah-ajat (ja kuvat) niiden omasta palvelusta.

Moskeijan tiedostossa _moskeijat/<slug>.md, kohdassa rukousajat:

    rukousajat:
      lahde: masjidbox      # masjidbox | mawaqit | taulukko | laskenta
      tunnus: masjid-sunnah-helsinki

- masjidbox: tunnus osoitteesta masjidbox.com/prayer-times/<tunnus>.
  Haetaan seuraavat 7 päivää (adhan, iqamah, perjantaina Jumuah).
- mawaqit:   tunnus osoitteesta mawaqit.net/fi/<tunnus>.
  Haetaan kuluva ja kaksi seuraavaa kuukautta (adhan, iqamah, Jumuah) sekä
  moskeijan kuvat (sisä- ja ulkokuva) sivun kuvagalleriaan.
- rukousajat: rukousajat.fi:n Helsingin aikataulu (kuluva + 2 kuukautta).
  Oletus, jos lähdettä ei ole ja kaupunki on Helsinki, Espoo tai Vantaa.
- taulukko:  aikataulu lisätään itse CSV-tiedostoina, ei haeta mitään.
- laskenta (tai ei mitään muualla): sivu laskee ajat koordinaateista samoin
  kuin rukousajat.fi muissa kaupungeissa.

Ajat tallennetaan tiedostoihin _data/aikataulut/<slug>/VVVV-KK.csv; muut päivät
jäävät ennalleen. Mawaqitin kuvat tallennetaan kansioon tiedostot/<slug>/mawaqit/
ja luetteloon _data/kuvat/<slug>.json. Jos haku epäonnistuu, vanhat tiedot jäävät
voimaan. Ei ulkoisia riippuvuuksia.
"""
import csv
import datetime
import glob
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

JUURI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SARAKKEET = ["pv", "fajr", "auringonnousu", "dhuhr", "asr", "maghrib", "isha",
             "iqamah_fajr", "iqamah_dhuhr", "iqamah_asr", "iqamah_maghrib", "iqamah_isha"]
VARSINAISET = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
SELAIN = {"User-Agent": "Mozilla/5.0 (compatible; MoskeijaSivusto/1.0)"}
# rukousajat.fi käyttää valmista aikataulua näille kaupungeille, muualla se laskee ajat
# (sama laskenta on sivuston varalaskenta: MuslimWorldLeague, Shafi, TwilightAngle).
PAAKAUPUNKISEUTU = ("helsinki", "espoo", "vantaa")


# ---------------------------------------------------------------- moskeijat
def moskeijat():
    """[(slug, lähde, tunnus)] tiedostoista _moskeijat/*.md.

    Tukee myös vanhaa muotoa (ylätason kenttä masjidbox: <tunnus>)."""
    tulos = []
    for polku in sorted(glob.glob(os.path.join(JUURI, "_moskeijat", "*.md"))):
        slug = os.path.splitext(os.path.basename(polku))[0]
        lahde = tunnus = None
        kaupunki = ""
        lohkossa = False
        with open(polku, encoding="utf-8") as f:
            for rivi in f:
                m = re.match(r'slug:\s*["\']?([a-z0-9-]+)', rivi)
                if m:
                    slug = m.group(1)
                m = re.match(r'kaupunki:\s*["\']?([^"\'#\n]+)', rivi)
                if m:
                    kaupunki = m.group(1).strip()
                m = re.match(r'masjidbox:\s*["\']?([A-Za-z0-9-]+)', rivi)  # vanha muoto
                if m and not lahde:
                    lahde, tunnus = "masjidbox", m.group(1)
                if re.match(r"rukousajat:\s*$", rivi):
                    lohkossa = True
                    continue
                if lohkossa:
                    if rivi.strip() and not rivi.startswith((" ", "\t")):
                        lohkossa = False
                        continue
                    m = re.match(r'\s+lahde:\s*["\']?([a-z]+)', rivi)
                    if m:
                        lahde = m.group(1)
                    m = re.match(r'\s+tunnus:\s*["\']?([A-Za-z0-9._-]+)', rivi)
                    if m:
                        tunnus = m.group(1)
        if lahde in ("masjidbox", "mawaqit") and tunnus:
            tulos.append((slug, lahde, tunnus))
        elif lahde == "rukousajat" or (not lahde and kaupunki.lower() in PAAKAUPUNKISEUTU):
            # Ei omaa lähdettä: pääkaupunkiseudulla rukousajat.fi:n Helsingin aikataulu
            tulos.append((slug, "rukousajat", kaupunki or "Helsinki"))
    return tulos


def hae(osoite):
    with urllib.request.urlopen(urllib.request.Request(osoite, headers=SELAIN), timeout=30) as v:
        return v.read()


# ---------------------------------------------------------------- Masjidbox
def kello(aikaleima):
    """'2026-11-07T18:27:00+02:00' -> '18:27' (moskeijan paikallinen aika)."""
    m = re.match(r"\d{4}-\d{2}-\d{2}T(\d{2}:\d{2})", aikaleima or "")
    return m.group(1) if m else ""


def masjidbox(tunnus):
    """{'VVVV-KK-PP': rivi} julkisen Masjidbox-sivun upotetusta tilasta (window.REDUX_STATE)."""
    sivu = hae("https://masjidbox.com/prayer-times/" + urllib.parse.quote(tunnus)).decode("utf-8", "replace")
    m = re.search(r'window\.REDUX_STATE\s*=\s*(["\'])(.*?)\1', sivu, re.S)
    if not m:
        raise ValueError("sivulta ei löytynyt aikataulua")
    raaka = re.sub(r"%u([0-9A-Fa-f]{4})", lambda x: chr(int(x.group(1), 16)), m.group(2))
    athany = json.loads(urllib.parse.unquote(raaka)).get("masjidbox", {}).get("masjidboxAthany") or {}
    paivat = {}
    for p in athany.get("timetable") or []:
        pvm = (p.get("date") or "")[:10]
        iq = p.get("iqamah") or {}
        rivi = {"fajr": kello(p.get("fajr")), "auringonnousu": kello(p.get("sunrise")),
                "dhuhr": kello(p.get("dhuhr")), "asr": kello(p.get("asr")),
                "maghrib": kello(p.get("maghrib")), "isha": kello(p.get("isha"))}
        for n in VARSINAISET:
            rivi["iqamah_" + n] = kello(iq.get(n))
        jumuah, iq_jumuah = p.get("jumuah") or [], iq.get("jumuah") or []
        if jumuah and kello(jumuah[0]):
            rivi["dhuhr"] = kello(jumuah[0])
            rivi["iqamah_dhuhr"] = kello(iq_jumuah[0]) if iq_jumuah else ""
        paivat[pvm] = rivi
    if not paivat:
        raise ValueError("aikataulu on tyhjä")
    return paivat, []


# ---------------------------------------------------------------- Mawaqit
def lisaa_min(hhmm, minuutit):
    h, m = map(int, hhmm.split(":"))
    t = (h * 60 + m + minuutit) % (24 * 60)
    return f"{t // 60:02d}:{t % 60:02d}"


def mawaqit(tunnus, kuukausia=3):
    """{'VVVV-KK-PP': rivi} ja kuvien osoitteet julkisen Mawaqit-sivun confData-tiedoista."""
    sivu = hae("https://mawaqit.net/fi/" + urllib.parse.quote(tunnus)).decode("utf-8", "replace")
    m = re.search(r"(?:let|var|const)\s+confData\s*=\s*(\{.*?\});\s*\n", sivu, re.S)
    if not m:
        raise ValueError("sivulta ei löytynyt aikataulua (confData)")
    d = json.loads(m.group(1))
    kalenteri, iqamat = d.get("calendar") or [], d.get("iqamaCalendar") or []
    if len(kalenteri) != 12:
        raise ValueError("kalenteri puuttuu")
    jumua = d.get("jumua") or ""
    tanaan = datetime.date.today()
    paivat = {}
    for k in range(kuukausia):
        v, kk = tanaan.year + (tanaan.month - 1 + k) // 12, (tanaan.month - 1 + k) % 12 + 1
        for pv, ajat in (kalenteri[kk - 1] or {}).items():
            try:
                paiva = datetime.date(v, kk, int(pv))
            except ValueError:
                continue
            if len(ajat) < 6:
                continue
            rivi = dict(zip(["fajr", "auringonnousu", "dhuhr", "asr", "maghrib", "isha"], ajat[:6]))
            iq = (iqamat[kk - 1] or {}).get(pv) if len(iqamat) == 12 and d.get("iqamaEnabled", True) else None
            for i, n in enumerate(VARSINAISET):
                arvo = (iq[i] if iq and i < len(iq) else "") or ""
                if re.match(r"^[+-]\d+$", arvo):
                    rivi["iqamah_" + n] = lisaa_min(rivi[n], int(arvo))
                elif re.match(r"^\d{1,2}:\d{2}$", arvo):
                    rivi["iqamah_" + n] = arvo.zfill(5)
                else:
                    rivi["iqamah_" + n] = ""
            if paiva.weekday() == 4 and re.match(r"^\d{1,2}:\d{2}$", jumua):
                rivi["dhuhr"], rivi["iqamah_dhuhr"] = jumua.zfill(5), ""
            paivat[paiva.isoformat()] = rivi
    kuvat = []
    for avain in ("exteriorPicture", "interiorPicture", "image"):
        u = d.get(avain)
        if u and u.startswith("http") and u not in kuvat:
            kuvat.append(u)
    return paivat, kuvat


# ---------------------------------------------------------------- rukousajat.fi
def rukousajat_fi(_kaupunki, kuukausia=3):
    """{'VVVV-KK-PP': rivi} rukousajat.fi:n Helsingin vuosiaikataulusta.

    Sivusto ei tarjoa rajapintaa: aikataulu (365 päivää, avain PPKK) on sen
    sovelluksen JavaScript-tiedostossa, josta se luetaan joka ajossa."""
    etusivu = hae("https://www.rukousajat.fi/").decode("utf-8", "replace")
    m = re.search(r'src="(/static/js/main\.[0-9a-f]+\.js)"', etusivu)
    if not m:
        raise ValueError("sovellustiedostoa ei löytynyt")
    js = hae("https://www.rukousajat.fi" + m.group(1)).decode("utf-8", "replace")
    kuvio = re.compile(r'"?(\d{4})"?:\{date:"(\d{4})",fajr:"([\d:]+)",sunrise:"([\d:]+)",zuhur:"([\d:]+)",'
                       r'asr:"([\d:]+)",maghrib:"([\d:]+)",isha:"([\d:]+)"\}')
    taulu = {}
    for t in kuvio.finditer(js):
        taulu.setdefault(t.group(2), t.groups()[2:])
    if len(taulu) < 360:
        raise ValueError(f"aikataulu vajaa ({len(taulu)} päivää)")
    tanaan = datetime.date.today()
    paivat = {}
    for k in range(kuukausia):
        v, kk = tanaan.year + (tanaan.month - 1 + k) // 12, (tanaan.month - 1 + k) % 12 + 1
        for pv in range(1, 32):
            try:
                paiva = datetime.date(v, kk, pv)
            except ValueError:
                break
            ajat = taulu.get(f"{pv:02d}{kk:02d}")
            if ajat:
                rivi = dict(zip(["fajr", "auringonnousu", "dhuhr", "asr", "maghrib", "isha"], ajat))
                rivi.update({"iqamah_" + n: "" for n in VARSINAISET})  # iqamah: moskeijan oletusminuutit
                paivat[paiva.isoformat()] = rivi
    return paivat, []


# ---------------------------------------------------------------- tallennus
def tallenna_ajat(slug, paivat):
    kansio = os.path.join(JUURI, "_data", "aikataulut", slug)
    os.makedirs(kansio, exist_ok=True)
    kuukausittain = {}
    for pvm, rivi in paivat.items():
        if not re.match(r"\d{4}-\d{2}-\d{2}$", pvm) or not all(rivi.get(n) for n in VARSINAISET):
            continue
        kuukausittain.setdefault(pvm[:7], {})[str(int(pvm[8:10]))] = dict(rivi, pv=str(int(pvm[8:10])))
    muutettu = 0
    for kk, rivit in kuukausittain.items():
        polku = os.path.join(kansio, kk + ".csv")
        vanhat = {}
        if os.path.exists(polku):
            with open(polku, encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    vanhat[str(int(r["pv"]))] = {k: r.get(k, "") or "" for k in SARAKKEET}
        for pv, r in rivit.items():
            uusi = {k: r.get(k, "") or "" for k in SARAKKEET}
            if vanhat.get(pv) != uusi:
                muutettu += 1
            vanhat[pv] = uusi
        ulos = io.StringIO()
        w = csv.DictWriter(ulos, fieldnames=SARAKKEET, lineterminator="\n")
        w.writeheader()
        for pv in sorted(vanhat, key=int):
            w.writerow(vanhat[pv])
        with open(polku, "w", encoding="utf-8", newline="") as f:
            f.write(ulos.getvalue())
    return muutettu, sum(len(r) for r in kuukausittain.values())


def tallenna_kuvat(slug, osoitteet):
    """Lataa kuvat sivustolle ja kirjoittaa luettelon _data/kuvat/<slug>.json."""
    if not osoitteet:
        return 0
    kansio = os.path.join(JUURI, "tiedostot", slug, "mawaqit")
    os.makedirs(kansio, exist_ok=True)
    polut = []
    for u in osoitteet:
        nimi = re.sub(r"[^A-Za-z0-9._-]", "", os.path.basename(urllib.parse.urlparse(u).path)) or "kuva.jpg"
        kohde = os.path.join(kansio, nimi)
        try:
            if not os.path.exists(kohde):
                data = hae(u)
                if len(data) < 2000:
                    continue
                with open(kohde, "wb") as f:
                    f.write(data)
            polut.append(f"/tiedostot/{slug}/mawaqit/{nimi}")
        except Exception as e:
            print(f"  kuvaa ei saatu ({u}): {e}", file=sys.stderr)
    if polut:
        os.makedirs(os.path.join(JUURI, "_data", "kuvat"), exist_ok=True)
        with open(os.path.join(JUURI, "_data", "kuvat", slug + ".json"), "w", encoding="utf-8") as f:
            json.dump({"lahde": "mawaqit", "kuvat": polut}, f, ensure_ascii=False, indent=1)
    return len(polut)


def main():
    lista = moskeijat()
    if not lista:
        print("Yhdelläkään moskeijalla ei ole rukousaikojen lähdettä (masjidbox/mawaqit).")
    for slug, lahde, tunnus in lista:
        try:
            paivat, kuvat = {"masjidbox": masjidbox, "mawaqit": mawaqit, "rukousajat": rukousajat_fi}[lahde](tunnus)
            muutettu, yhteensa = tallenna_ajat(slug, paivat)
            k = tallenna_kuvat(slug, kuvat)
            print(f"{slug}: {yhteensa} päivää lähteestä {lahde} ({tunnus}), {muutettu} muuttui"
                  + (f", {k} kuvaa" if k else ""))
        except Exception as e:  # haku epäonnistui: vanhat ajat jäävät voimaan
            print(f"{slug}: haku lähteestä {lahde} epäonnistui ({tunnus}): {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
