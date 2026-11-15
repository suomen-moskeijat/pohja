#!/usr/bin/env python3
"""Hakee moskeijoiden viralliset rukous- ja iqamah-ajat (ja kuvat) niiden omasta palvelusta.

Moskeijan tiedostossa _moskeijat/<slug>.md, kohdassa rukousajat:

    rukousajat:
      lahde: masjidbox      # masjidbox | mawaqit | taulukko | laskenta
      tunnus: masjid-sunnah-helsinki

- masjidbox: jos moskeija on valinnut paneelissa Masjidbox-moskeijansa (masjidbox_id: msj_…), ajat
  haetaan Masjidboxin virallisesta rajapinnasta hallintapaneelin kautta (avain pysyy paneelissa):
  kuluva ja seuraava kuukausi (adhan, iqamah, Jumuah). Muuten (väliaikaisesti) julkiselta sivulta
  masjidbox.com/prayer-times/<tunnus>, joka näyttää vain 7 päivää.
- mawaqit:   tunnus osoitteesta mawaqit.net/fi/<tunnus>.
  Haetaan vuoden aikataulu (adhan, iqamah, Jumuah) sekä
  moskeijan kuvat (sisä- ja ulkokuva) sivun kuvagalleriaan.
- rukousajat: rukousajat.fi:n Helsingin aikataulu (vuosi eteenpäin).
  Oletus, jos lähdettä ei ole ja kaupunki on Helsinki, Espoo tai Vantaa.
- taulukko:  aikataulu lisätään itse CSV-tiedostoina, ei haeta mitään.
- laskenta (tai ei mitään muualla): sivu laskee ajat koordinaateista samoin
  kuin rukousajat.fi muissa kaupungeissa.

Haun tila (tapa, aika, montako päivää, virhe) tallennetaan tiedostoon _data/haku/<slug>.json;
paneeli näyttää sen moskeijalle. Ajat tallennetaan tiedostoihin _data/aikataulut/<slug>/VVVV-KK.csv. Tulevat päivät, joita
lähde ei kertonut (esim. vanhasta lähteestä tai repoon tallennetusta taulukosta jääneet), poistetaan:
haetun lähteen moskeijalla näytetään vain lähteen ajat, eikä puuttuvia päiviä lasketa itse. Mawaqitin kuvat tallennetaan kansioon tiedostot/<slug>/mawaqit/
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
import urllib.error
import urllib.parse
import urllib.request

JUURI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SARAKKEET = ["pv", "fajr", "auringonnousu", "dhuhr", "asr", "maghrib", "isha",
             "iqamah_fajr", "iqamah_dhuhr", "iqamah_asr", "iqamah_maghrib", "iqamah_isha", "jumua"]
# jumua = "1", kun lähde kertoi perjantaina Jumuan ajan Dhuhrin paikalle (se voittaa käsin kirjoitetun ajan).
VARSINAISET = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
SELAIN = {"User-Agent": "Mozilla/5.0 (compatible; MoskeijaSivusto/1.0)"}
HALLINTA = os.environ.get("HALLINTA_API", "https://hallinta.suomenmoskeijat.fi/api")
# rukousajat.fi käyttää valmista aikataulua näille kaupungeille, muualla se laskee ajat
# (sama laskenta on sivuston varalaskenta: MuslimWorldLeague, Shafi, TwilightAngle).
PAAKAUPUNKISEUTU = ("helsinki", "espoo", "vantaa")


# ---------------------------------------------------------------- moskeijat
def moskeijat():
    """[(slug, lähde, tunnus, lisä)] tiedostoista _moskeijat/*.md (lisä = {"masjidbox_id": …}).

    Tukee myös vanhaa muotoa (ylätason kenttä masjidbox: <tunnus>)."""
    tulos = []
    for polku in sorted(glob.glob(os.path.join(JUURI, "_moskeijat", "*.md"))):
        slug = os.path.splitext(os.path.basename(polku))[0]
        lahde = tunnus = None
        lisa = {}
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
                    m = re.match(r'\s+masjidbox_id:\s*["\']?(msj_[A-Za-z0-9]+)', rivi)
                    if m:
                        lisa["masjidbox_id"] = m.group(1)
        if lahde == "masjidbox" and (tunnus or lisa.get("masjidbox_id")):
            tulos.append((slug, lahde, tunnus, lisa))
        elif lahde == "mawaqit" and tunnus:
            tulos.append((slug, lahde, tunnus, lisa))
        elif lahde == "rukousajat" or (not lahde and kaupunki.lower() in PAAKAUPUNKISEUTU):
            # Ei omaa lähdettä: pääkaupunkiseudulla rukousajat.fi:n Helsingin aikataulu
            tulos.append((slug, "rukousajat", kaupunki or "Helsinki", lisa))
    return tulos


def hae(osoite):
    with urllib.request.urlopen(urllib.request.Request(osoite, headers=SELAIN), timeout=30) as v:
        return v.read()


# ---------------------------------------------------------------- Masjidbox
def kello(aikaleima):
    """'2026-11-07T18:27:00+02:00' -> '18:27' (moskeijan paikallinen aika)."""
    m = re.match(r"\d{4}-\d{2}-\d{2}T(\d{2}:\d{2})", aikaleima or "")
    return m.group(1) if m else ""


class EiAvainta(Exception):
    """Paneelissa ei ole Masjidboxin rajapinta-avainta."""


def masjidbox_api(masjidbox_id):
    """{'VVVV-KK-PP': rivi} Masjidboxin virallisesta rajapinnasta hallintapaneelin kautta."""
    osoite = f"{HALLINTA}/masjidbox/aikataulu?id={urllib.parse.quote(masjidbox_id)}"
    try:
        d = json.loads(hae(osoite))
    except urllib.error.HTTPError as e:
        viesti = ""
        try:
            viesti = json.loads(e.read()).get("virhe", "")
        except Exception:
            pass
        if e.code == 503:
            raise EiAvainta(viesti or "rajapinta-avain puuttuu")
        raise ValueError(viesti or f"paneeli vastasi {e.code}")
    paivat = {}
    for p in d.get("data") or []:
        pvm = (p.get("date") or "")[:10]
        pr = p.get("prayers") or {}
        rivi = {"auringonnousu": p.get("sunrise") or ""}
        for n in VARSINAISET:
            x = pr.get(n) or {}
            rivi[n] = x.get("adhan") or ""
            rivi["iqamah_" + n] = x.get("iqamah") or ""
        jumuah = p.get("jumuah") or []
        if jumuah and re.match(r"^\d{1,2}:\d{2}$", jumuah[0] or ""):
            rivi["dhuhr"], rivi["iqamah_dhuhr"], rivi["jumua"] = jumuah[0].zfill(5), "", "1"
        if pvm:
            paivat[pvm] = rivi
    if not paivat:
        raise ValueError("Masjidbox ei palauttanut aikoja")
    lahde = d.get("source") or {}
    tieto = {"tapa": "rajapinta", "tyyppi": lahde.get("type", ""), "tila": lahde.get("status", ""),
             "raportti": (d.get("links") or {}).get("report", ""), "vanha": bool(d.get("vanha"))}
    return paivat, [], tieto


def masjidbox(tunnus):
    """{'VVVV-KK-PP': rivi} julkisen Masjidbox-sivun upotetusta tilasta (window.REDUX_STATE).
    Väliaikainen tapa, kun rajapintaa ei ole käytössä: Masjidboxin ehtojen mukaan tiedot luetaan rajapinnasta."""
    sivu = hae("https://masjidbox.com/prayer-times/" + urllib.parse.quote(tunnus)).decode("utf-8", "replace")
    m = re.search(r'window\.REDUX_STATE\s*=\s*(["\'])(.*?)\1', sivu, re.S)
    if not m:
        raise ValueError("sivulta ei löytynyt aikataulua")
    raaka = re.sub(r"%u([0-9A-Fa-f]{4})", lambda x: chr(int(x.group(1), 16)), m.group(2))
    athany = json.loads(urllib.parse.unquote(raaka, encoding="latin-1")).get("masjidbox", {}).get("masjidboxAthany") or {}
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
            rivi["jumua"] = "1"
        paivat[pvm] = rivi
    if not paivat:
        raise ValueError("aikataulu on tyhjä")
    return paivat, []


# ---------------------------------------------------------------- Mawaqit
def lisaa_min(hhmm, minuutit):
    h, m = map(int, hhmm.split(":"))
    t = (h * 60 + m + minuutit) % (24 * 60)
    return f"{t // 60:02d}:{t % 60:02d}"


def mawaqit(tunnus, kuukausia=13):
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
                rivi["dhuhr"], rivi["iqamah_dhuhr"], rivi["jumua"] = jumua.zfill(5), "", "1"
            paivat[paiva.isoformat()] = rivi
    kuvat = []
    for avain in ("exteriorPicture", "interiorPicture", "image"):
        u = d.get(avain)
        if u and u.startswith("http") and u not in kuvat:
            kuvat.append(u)
    return paivat, kuvat


# ---------------------------------------------------------------- rukousajat.fi
def rukousajat_fi(_kaupunki, kuukausia=13):
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
    tanaan = datetime.date.today().isoformat()
    # Kuukaudet, joissa on vanhoja tulevia päiviä mutta joihin lähde ei nyt antanut mitään
    for polku in glob.glob(os.path.join(kansio, "????-??.csv")):
        kk = os.path.basename(polku)[:7]
        if kk not in kuukausittain and kk + "-31" >= tanaan:
            kuukausittain[kk] = {}
    for kk, rivit in kuukausittain.items():
        polku = os.path.join(kansio, kk + ".csv")
        vanhat = {}
        if os.path.exists(polku):
            with open(polku, encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    pv = str(int(r["pv"]))
                    if f"{kk}-{int(pv):02d}" >= tanaan and pv not in rivit:
                        muutettu += 1  # lähde ei kertonut tätä tulevaa päivää: ei näytetä vanhaa
                        continue
                    vanhat[pv] = {k: r.get(k, "") or "" for k in SARAKKEET}
        for pv, r in rivit.items():
            uusi = {k: r.get(k, "") or "" for k in SARAKKEET}
            if vanhat.get(pv) != uusi:
                muutettu += 1
            vanhat[pv] = uusi
        if not vanhat:
            os.remove(polku) if os.path.exists(polku) else None
            continue
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


def tallenna_tila(slug, tila):
    """Haun tila paneelia varten: _data/haku/<slug>.json (säilyy välimuistissa ajojen välillä)."""
    kansio = os.path.join(JUURI, "_data", "haku")
    os.makedirs(kansio, exist_ok=True)
    polku = os.path.join(kansio, slug + ".json")
    vanha = {}
    if os.path.exists(polku):
        try:
            with open(polku, encoding="utf-8") as f:
                vanha = json.load(f)
        except Exception:
            vanha = {}
    if not tila.get("ok"):  # epäonnistui: viimeisin onnistunut haku jää näkyviin
        tila = {**{k: vanha.get(k) for k in ("haettu", "tapa", "tyyppi", "tila", "raportti") if vanha.get(k)}, **tila}
    with open(polku, "w", encoding="utf-8") as f:
        json.dump(tila, f, ensure_ascii=False, indent=1)


def tulevat(slug):
    """(montako tulevaa päivää on tallessa, viimeinen päivä) – paneelin tilaa varten."""
    tanaan = datetime.date.today().isoformat()
    paivat = []
    for polku in glob.glob(os.path.join(JUURI, "_data", "aikataulut", slug, "????-??.csv")):
        kk = os.path.basename(polku)[:7]
        with open(polku, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                p = f"{kk}-{int(r['pv']):02d}"
                if p >= tanaan and r.get("fajr"):
                    paivat.append(p)
    return len(paivat), max(paivat) if paivat else ""


def main():
    lista = moskeijat()
    if not lista:
        print("Yhdelläkään moskeijalla ei ole rukousaikojen lähdettä (masjidbox/mawaqit).")
    for slug, lahde, tunnus, lisa in lista:
        nyt = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        tieto = {"tapa": "sivu"}
        varoitus = ""
        try:
            if lahde == "masjidbox" and lisa.get("masjidbox_id"):
                try:
                    paivat, kuvat, tieto = masjidbox_api(lisa["masjidbox_id"])
                except EiAvainta as e:
                    if not tunnus:
                        raise ValueError(f"Masjidboxin rajapinta-avain puuttuu paneelista ({e})")
                    varoitus = "Masjidboxin rajapinta-avain puuttuu – ajat luettiin väliaikaisesti julkiselta sivulta (7 päivää)."
                    paivat, kuvat = masjidbox(tunnus)
            else:
                paivat, kuvat = {"masjidbox": masjidbox, "mawaqit": mawaqit, "rukousajat": rukousajat_fi}[lahde](tunnus)
            muutettu, yhteensa = tallenna_ajat(slug, paivat)
            k = tallenna_kuvat(slug, kuvat)
            n, viimeinen = tulevat(slug)
            tallenna_tila(slug, {"ok": True, "lahde": lahde, "haettu": nyt, "paivia": n, "viimeinen": viimeinen,
                                 "varoitus": varoitus, **tieto})
            print(f"{slug}: {yhteensa} päivää lähteestä {lahde} ({tieto.get('tapa')}: {lisa.get('masjidbox_id') or tunnus}), {muutettu} muuttui"
                  + (f", {k} kuvaa" if k else "") + (f" – {varoitus}" if varoitus else ""))
        except Exception as e:  # haku epäonnistui: vanhat ajat jäävät voimaan
            n, viimeinen = tulevat(slug)
            tallenna_tila(slug, {"ok": False, "lahde": lahde, "yritetty": nyt, "virhe": str(e)[:300], "paivia": n, "viimeinen": viimeinen})
            print(f"{slug}: haku lähteestä {lahde} epäonnistui ({tunnus}): {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
