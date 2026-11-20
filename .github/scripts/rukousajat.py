#!/usr/bin/env python3
"""Hakee moskeijoiden viralliset rukous- ja iqamah-ajat (ja kuvat) niiden omasta palvelusta.

Moskeijan tiedostossa _moskeijat/<slug>.md, kohdassa rukousajat:

    rukousajat:
      lahde: masjidbox      # masjidbox | mawaqit | rukousajat | taulukko
      tunnus: masjid-sunnah-helsinki

- masjidbox: jos moskeija on valinnut paneelissa Masjidbox-moskeijansa (masjidbox_id: msj_…), ajat
  haetaan Masjidboxin virallisesta rajapinnasta hallintapaneelin kautta (avain pysyy paneelissa):
  kuluva ja seuraava kuukausi (adhan, iqamah, Jumuah). Masjidboxin itse laskemia aikoja (source.type = calculated,
  kukaan moskeijasta ei ylläpidä sivua) ei julkaista: tulevat päivät poistuvat ja sivulla lukee "Rukousajat lisätään pian". Muuten (väliaikaisesti) julkiselta sivulta
  masjidbox.com/prayer-times/<tunnus>, joka näyttää vain 7 päivää.
- mawaqit:   tunnus osoitteesta mawaqit.net/fi/<tunnus>.
  Haetaan vuoden aikataulu (adhan, iqamah, Jumuah) sekä
  moskeijan kuvat (sisä- ja ulkokuva) sivun kuvagalleriaan.
- rukousajat: rukousajat.fi:n Helsingin aikataulu (vuosi eteenpäin).
  Oletus, jos lähdettä ei ole ja kaupunki on Helsinki, Espoo tai Vantaa.
- taulukko:  aikataulu lisätään itse CSV-tiedostoina, ei haeta mitään.
- ei lähdettä muualla: aikoja ei ole, ja sivulla lukee "Rukousajat lisätään pian". Sivu ei laske
  aikoja itse, eikä puuttuvia päiviä täytetä.

Ennen tallennusta ajat tarkistetaan (tarkista): kellonajat ovat kelvollisia, järjestys on Fajr < auringonnousu < Dhuhr
< Asr < Maghrib < Isha (Isha saa olla puolenyön jälkeen, Jumua-päivänä Jumua on auringonnousun ja Maghribin välissä),
eikä haetussa jaksossa ole aukkoja. Rikkinäistä hakua ei julkaista: vanhat ajat jäävät ja tila kertoo virheen.
Sama jäsennin ja tarkistus on paneelissa (hallinta src/rukouslahteet.js, tarkistus lähdettä valittaessa ja päivittäinen
lähdetarkistus); hallinnan testi testi/rukouslahteet.mjs pitää ne samana tallennettua testiaineistoa vasten
(python3 rukousajat.py --jasenna <lähde> <tiedosto>).

Haun tila (tapa, aika, montako päivää, virhe) tallennetaan tiedostoon _data/haku/<slug>.json;
paneeli näyttää sen moskeijalle (rukousajat/tila.json, valvonta). perakkain = montako hakua peräkkäin on epäonnistunut. Ajat tallennetaan tiedostoihin _data/aikataulut/<slug>/VVVV-KK.csv. Tulevat päivät, joita
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
# Lähteiden osoitteet (testeissä paikallinen korvike; samat nimet paneelissa, src/rukouslahteet.js)
MASJIDBOX_SIVU = os.environ.get("MASJIDBOX_SIVU", "https://masjidbox.com/prayer-times/")
MAWAQIT_OSOITE = os.environ.get("MAWAQIT_OSOITE", "https://mawaqit.net/fi/")
RUKOUSAJAT_OSOITE = os.environ.get("RUKOUSAJAT_OSOITE", "https://www.rukousajat.fi")
AJAT = ["fajr", "auringonnousu", "dhuhr", "asr", "maghrib", "isha"]
# rukousajat.fi käyttää valmista (Helsingin) aikataulua vain näille kaupungeille, muualla se laskee ajat
# sijainnista. Siksi se on oletuslähde vain täällä (sama sääntö: _includes/osat/rk-lahde.html, paneeli kaavio.js OLETUSLAHDE).
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
        elif lahde == "rukousajat" or (lahde in (None, "laskenta") and kaupunki.strip().lower() in PAAKAUPUNKISEUTU):
            # Ei omaa lähdettä: pääkaupunkiseudulla rukousajat.fi:n Helsingin aikataulu
            tulos.append((slug, "rukousajat", kaupunki or "Helsinki", lisa))
    return tulos


def hae(osoite):
    with urllib.request.urlopen(urllib.request.Request(osoite, headers=SELAIN), timeout=30) as v:
        return v.read()


# ---------------------------------------------------------------- yhteiset
def rivi_tyhja():
    """Päivän rivi: kaikki sarakkeet (paitsi pv) tyhjinä."""
    return {k: "" for k in SARAKKEET if k != "pv"}


def hhmm(arvo):
    """'5:30' -> '05:30'; muut arvot sellaisinaan (tarkista() hylkää kelvottomat)."""
    arvo = str(arvo or "").strip()
    return arvo.zfill(5) if re.match(r"^\d:\d{2}$", arvo) else arvo


class Kelvoton(ValueError):
    """Lähteen vastaus ei läpäissyt järkevyystarkistusta (koodi: kellonaika | jarjestys | aukko | tyhja)."""

    def __init__(self, koodi, viesti):
        super().__init__(viesti)
        self.koodi = koodi


class Muoto(ValueError):
    """Lähteen vastauksesta ei löytynyt aikataulua (muoto on muuttunut tai tunnus on väärä)."""
    koodi = "muoto"


class Laskettu(ValueError):
    """Masjidbox laskee moskeijan ajat itse (source.type = calculated): kukaan moskeijasta ei ylläpidä sivua, eikä iqamahia ole.
    Laskettuja aikoja ei julkaista (ADR-0003); sama sääntö paneelissa (hallinta src/rukouslahteet.js)."""
    koodi = "laskettu"


def _minuutit(a):
    return int(a[:2]) * 60 + int(a[3:5])


def tarkista(paivat, salli_puuttuvat=()):
    """Järkevyystarkistus ennen julkaisua. Nostaa Kelvoton-poikkeuksen, jos aikataulu on rikki.

    - kellonajat muotoa HH:MM (00–23, 00–59, lisäksi 24:00 = keskiyö, jota rukousajat.fi käyttää); auringonnousu ja
      iqamah saavat puuttua
    - järjestys Fajr < auringonnousu < Dhuhr < Asr < Maghrib < Isha; Isha saa olla puolenyön jälkeen (ennen Fajria,
      kesällä Suomessa), Jumua-päivänä (jumua = 1) Dhuhrin paikalla oleva Jumua on auringonnousun ja Maghribin välissä
    - haetussa jaksossa ei ole aukkoja (salli_puuttuvat: päivät muodossa '-02-29', joita lähde ei koskaan kerro)
    Sama sääntö: hallinta src/rukouslahteet.js tarkistaAjat."""
    if not paivat:
        raise Kelvoton("tyhja", "lähde ei antanut yhtään päivää")
    kelpo = re.compile(r"^(([01]\d|2[0-3]):[0-5]\d|24:00)$")
    for pvm in sorted(paivat):
        r = paivat[pvm]
        for n in AJAT + ["iqamah_" + x for x in VARSINAISET]:
            a = r.get(n) or ""
            if not a and (n == "auringonnousu" or n.startswith("iqamah_")):
                continue
            if not kelpo.match(a):
                raise Kelvoton("kellonaika", f"{pvm}: {n} ei ole kelvollinen kellonaika ({a or 'tyhjä'})")
        m = {n: _minuutit(r[n]) for n in AJAT if r.get(n)}
        ketju = ["fajr", "auringonnousu", "dhuhr", "maghrib"] if r.get("jumua") == "1" else ["fajr", "auringonnousu", "dhuhr", "asr", "maghrib"]
        ketju = [n for n in ketju if n in m]
        pari = next(((a, b) for a, b in zip(ketju, ketju[1:]) if m[a] >= m[b]), None)
        if not pari and r.get("jumua") == "1" and not (m.get("auringonnousu", m["fajr"]) < m["asr"] < m["maghrib"]):
            pari = ("asr", "maghrib")
        if not pari and not (m["isha"] > m["maghrib"] or m["isha"] < m["fajr"]):
            pari = ("maghrib", "isha")
        if pari:
            raise Kelvoton("jarjestys", f"{pvm}: ajat eivät ole oikeassa järjestyksessä ({pari[0]} {r[pari[0]]}, {pari[1]} {r[pari[1]]})")
    jarj = sorted(paivat)
    p, loppu = datetime.date.fromisoformat(jarj[0]), datetime.date.fromisoformat(jarj[-1])
    while p <= loppu:
        if p.isoformat() not in paivat and p.isoformat()[4:] not in salli_puuttuvat:
            raise Kelvoton("aukko", f"aikataulusta puuttuu päivä {p.isoformat()}")
        p += datetime.timedelta(days=1)


# ---------------------------------------------------------------- Masjidbox
def kello(aikaleima):
    """'2026-11-07T18:27:00+02:00' -> '18:27' (moskeijan paikallinen aika)."""
    m = re.match(r"\d{4}-\d{2}-\d{2}T(\d{2}:\d{2})", aikaleima or "")
    return m.group(1) if m else ""


class EiAvainta(Exception):
    """Paneelissa ei ole Masjidboxin rajapinta-avainta."""


def jasenna_masjidbox_api(d):
    """Masjidboxin rajapinnan vastaus (kuukausiaikataulu) -> ({'VVVV-KK-PP': rivi}, tieto)."""
    paivat = {}
    for p in d.get("data") or []:
        pvm = (p.get("date") or "")[:10]
        pr = p.get("prayers") or {}
        rivi = dict(rivi_tyhja(), auringonnousu=hhmm(p.get("sunrise")))
        for n in VARSINAISET:
            x = pr.get(n) or {}
            rivi[n] = hhmm(x.get("adhan"))
            rivi["iqamah_" + n] = hhmm(x.get("iqamah"))
        jumuah = p.get("jumuah") or []
        if jumuah and re.match(r"^\d{1,2}:\d{2}$", jumuah[0] or ""):
            rivi["dhuhr"], rivi["iqamah_dhuhr"], rivi["jumua"] = jumuah[0].zfill(5), "", "1"
        if pvm:
            paivat[pvm] = rivi
    if not paivat:
        raise Muoto("Masjidbox ei palauttanut aikoja")
    lahde = d.get("source") or {}
    if lahde.get("type") == "calculated":
        raise Laskettu("Masjidbox laskee tämän moskeijan ajat (kukaan moskeijasta ei ylläpidä sivua): laskettuja aikoja ei julkaista")
    tieto = {"tapa": "rajapinta", "tyyppi": lahde.get("type", ""), "tila": lahde.get("status", ""),
             "raportti": (d.get("links") or {}).get("report", ""), "haltuunotto": (d.get("links") or {}).get("claim", ""),
             "vanha": bool(d.get("vanha"))}
    return paivat, tieto


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
    paivat, tieto = jasenna_masjidbox_api(d)
    return paivat, [], tieto


def js_literaali(s):
    """Sivulle upotettu JavaScript-olio (seroval-muoto: $R[1]={avain:"arvo",x:!0}) JSONiksi. Vain data, ei suoriteta."""
    ulos, i, n = [], 0, len(s)
    viittaus, nimi = re.compile(r"\$R\[\d+\](=?)"), re.compile(r"([A-Za-z_$][\w$]*):")
    while i < n:
        c = s[i]
        if c == '"':
            j, osa = i + 1, ['"']
            while j < n and s[j] != '"':
                if s[j] == "\\" and j + 1 < n:
                    seur = s[j + 1]
                    if seur == "x":
                        osa.append("\\u00" + s[j + 2:j + 4]); j += 4; continue
                    osa.append(seur if seur == "'" else s[j:j + 2]); j += 2; continue
                osa.append(s[j]); j += 1
            osa.append('"'); ulos.append("".join(osa)); i = j + 1
            continue
        m = viittaus.match(s, i)
        if m:
            if not m.group(1):
                ulos.append("null")  # viittaus aiempaan arvoon: ei tarvita aikataulussa
            i = m.end()
            continue
        if s.startswith("!0", i) or s.startswith("!1", i):
            ulos.append("true" if s[i + 1] == "0" else "false"); i += 2
            continue
        if s.startswith("void 0", i):
            ulos.append("null"); i += 6
            continue
        m = nimi.match(s, i)
        if m and ulos and ulos[-1][-1:] in "{,":
            ulos.append(json.dumps(m.group(1)) + ":"); i = m.end()
            continue
        ulos.append(c); i += 1
    return json.loads("".join(ulos))


def _sulkeet(s, alku):
    """Indeksi, jossa alku-kohdan [ tai { sulkeutuu (merkkijonot huomioiden), tai -1."""
    syvyys, i, n = 0, alku, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            i += 1
            while i < n and s[i] != '"':
                i += 2 if s[i] == "\\" else 1
        elif c in "[{":
            syvyys += 1
        elif c in "]}":
            syvyys -= 1
            if not syvyys:
                return i
        i += 1
    return -1


def jasenna_masjidbox_sivu(sivu):
    """Julkisen Masjidbox-sivun HTML -> ({'VVVV-KK-PP': rivi}, nimi).

    Sivu upottaa aikataulun (7 päivää) joko TanStack-muodossa (timetable:$R[n]=[…], 11/2026 alkaen) tai vanhassa
    window.REDUX_STATE-muodossa. Väliaikainen tapa, kun rajapintaa ei ole käytössä."""
    nimi = ""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', sivu, re.S):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("@type") == "Mosque":
            nimi = d.get("name") or ""
    taulu = None
    m = re.search(r"timetable:(?:\$R\[\d+\]=)?\[", sivu)
    if m:
        loppu = _sulkeet(sivu, m.end() - 1)
        if loppu > 0:
            try:
                taulu = js_literaali(sivu[m.end() - 1:loppu + 1])
            except ValueError:
                taulu = None
        if not nimi:
            n = re.search(r'payload:(?:\$R\[\d+\]=)?\{name:"([^"]*)"', sivu)
            nimi = n.group(1) if n else ""
    if taulu is None:
        m = re.search(r'window\.REDUX_STATE\s*=\s*(["\'])(.*?)\1', sivu, re.S)
        if not m:
            raise Muoto("sivulta ei löytynyt aikataulua")
        raaka = re.sub(r"%u([0-9A-Fa-f]{4})", lambda x: chr(int(x.group(1), 16)), m.group(2))
        athany = json.loads(urllib.parse.unquote(raaka, encoding="latin-1")).get("masjidbox", {}).get("masjidboxAthany") or {}
        taulu = athany.get("timetable") or []
        nimi = nimi or athany.get("name") or ""
    paivat = {}
    for p in taulu or []:
        if not isinstance(p, dict):
            continue
        pvm = (p.get("date") or "")[:10]
        iq = p.get("iqamah") or {}
        rivi = rivi_tyhja()
        rivi.update({"fajr": kello(p.get("fajr")), "auringonnousu": kello(p.get("sunrise")),
                     "dhuhr": kello(p.get("dhuhr")), "asr": kello(p.get("asr")),
                     "maghrib": kello(p.get("maghrib")), "isha": kello(p.get("isha"))})
        for n in VARSINAISET:
            rivi["iqamah_" + n] = kello(iq.get(n))
        jumuah, iq_jumuah = p.get("jumuah") or [], iq.get("jumuah") or []
        if jumuah and kello(jumuah[0]):
            rivi["dhuhr"] = kello(jumuah[0])
            rivi["iqamah_dhuhr"] = kello(iq_jumuah[0]) if iq_jumuah else ""
            rivi["jumua"] = "1"
        if pvm:
            paivat[pvm] = rivi
    if not paivat:
        raise Muoto("aikataulu on tyhjä")
    return paivat, nimi


def masjidbox(tunnus):
    """{'VVVV-KK-PP': rivi} julkiselta Masjidbox-sivulta (Masjidboxin ehtojen mukaan tiedot luetaan rajapinnasta)."""
    paivat, _ = jasenna_masjidbox_sivu(hae(MASJIDBOX_SIVU + urllib.parse.quote(tunnus)).decode("utf-8", "replace"))
    return paivat, []


# ---------------------------------------------------------------- Mawaqit
def lisaa_min(hhmm_, minuutit):
    h, m = map(int, hhmm_.split(":"))
    t = (h * 60 + m + minuutit) % (24 * 60)
    return f"{t // 60:02d}:{t % 60:02d}"


def jasenna_mawaqit(sivu, tanaan=None, kuukausia=13):
    """Julkisen Mawaqit-sivun HTML (confData) -> ({'VVVV-KK-PP': rivi}, kuvat, nimi). Vuoden kalenteri kuukausittain,
    tanaan-päivän kuukaudesta alkaen."""
    m = re.search(r"(?:let|var|const)\s+confData\s*=\s*(\{.*?\});\s*\n", sivu, re.S)
    if not m:
        raise Muoto("sivulta ei löytynyt aikataulua (confData)")
    d = json.loads(m.group(1))
    kalenteri, iqamat = d.get("calendar") or [], d.get("iqamaCalendar") or []
    if len(kalenteri) != 12:
        raise Muoto("kalenteri puuttuu")
    jumua = d.get("jumua") or ""
    tanaan = tanaan or datetime.date.today()
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
            rivi = rivi_tyhja()
            rivi.update(dict(zip(AJAT, [hhmm(a) for a in ajat[:6]])))
            iq = (iqamat[kk - 1] or {}).get(pv) if len(iqamat) == 12 and d.get("iqamaEnabled", True) else None
            for i, n in enumerate(VARSINAISET):
                arvo = (iq[i] if iq and i < len(iq) else "") or ""
                if re.match(r"^[+-]\d+$", arvo) and re.match(r"^\d{2}:\d{2}$", rivi[n]):
                    rivi["iqamah_" + n] = lisaa_min(rivi[n], int(arvo))
                elif re.match(r"^\d{1,2}:\d{2}$", arvo):
                    rivi["iqamah_" + n] = arvo.zfill(5)
            if paiva.weekday() == 4 and re.match(r"^\d{1,2}:\d{2}$", jumua):
                rivi["dhuhr"], rivi["iqamah_dhuhr"], rivi["jumua"] = jumua.zfill(5), "", "1"
            paivat[paiva.isoformat()] = rivi
    kuvat = []
    for avain in ("exteriorPicture", "interiorPicture", "image"):
        u = d.get(avain)
        if u and str(u).startswith("http") and u not in kuvat:
            kuvat.append(u)
    return paivat, kuvat, d.get("name") or d.get("label") or ""


def mawaqit(tunnus, kuukausia=13):
    """{'VVVV-KK-PP': rivi} ja kuvien osoitteet julkiselta Mawaqit-sivulta."""
    paivat, kuvat, _ = jasenna_mawaqit(hae(MAWAQIT_OSOITE + urllib.parse.quote(tunnus)).decode("utf-8", "replace"), kuukausia=kuukausia)
    return paivat, kuvat


# ---------------------------------------------------------------- rukousajat.fi
# rukousajat.fi:n aikataulussa ei ole karkauspäivää (365 päivää, avain PPKK): se ei ole aukko.
RUKOUSAJAT_PUUTTUVAT = ("-02-29",)


def rukousajat_fi_sovellus(etusivu):
    """rukousajat.fi:n etusivu -> sovellustiedoston polku (/static/js/main.<tiiviste>.js)."""
    m = re.search(r'src="(/static/js/main\.[0-9a-f]+\.js)"', etusivu)
    if not m:
        raise Muoto("sovellustiedostoa ei löytynyt")
    return m.group(1)


def jasenna_rukousajat_fi(js, tanaan=None, kuukausia=13):
    """rukousajat.fi:n sovellustiedosto -> {'VVVV-KK-PP': rivi} (Helsingin vuosiaikataulu, tanaan-päivän kuukaudesta)."""
    kuvio = re.compile(r'"?(\d{4})"?:\{date:"(\d{4})",fajr:"([\d:]+)",sunrise:"([\d:]+)",zuhur:"([\d:]+)",'
                       r'asr:"([\d:]+)",maghrib:"([\d:]+)",isha:"([\d:]+)"\}')
    taulu = {}
    for t in kuvio.finditer(js):
        taulu.setdefault(t.group(2), t.groups()[2:])
    if len(taulu) < 360:
        raise Muoto(f"aikataulu vajaa ({len(taulu)} päivää)")
    tanaan = tanaan or datetime.date.today()
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
                rivi = rivi_tyhja()  # iqamah: moskeijan oletusminuutit
                rivi.update(dict(zip(AJAT, [hhmm(a) for a in ajat])))
                paivat[paiva.isoformat()] = rivi
    return paivat


def rukousajat_fi(_kaupunki, kuukausia=13):
    """{'VVVV-KK-PP': rivi} rukousajat.fi:n Helsingin vuosiaikataulusta.

    Sivusto ei tarjoa rajapintaa: aikataulu (365 päivää, avain PPKK) on sen
    sovelluksen JavaScript-tiedostossa, josta se luetaan joka ajossa."""
    polku = rukousajat_fi_sovellus(hae(RUKOUSAJAT_OSOITE + "/").decode("utf-8", "replace"))
    return jasenna_rukousajat_fi(hae(RUKOUSAJAT_OSOITE + polku).decode("utf-8", "replace"), kuukausia=kuukausia), []


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
    if not tila.get("ok"):  # epäonnistui: viimeisin onnistunut haku jää näkyviin, ja peräkkäiset epäonnistumiset lasketaan
        tila = {**{k: vanha.get(k) for k in ("haettu", "tapa", "tyyppi", "tila", "raportti", "haltuunotto") if vanha.get(k)}, **tila,
                "perakkain": (vanha.get("perakkain") or 0) + 1 if vanha.get("ok") is False else 1}
    else:
        tila = {**tila, "perakkain": 0}
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


def jasenna_tiedosto(lahde, polku, tanaan=None):
    """Testeille (hallinta testi/rukouslahteet.mjs): jäsentää tallennetun vastauksen ja tarkistaa sen kuten julkaisuajo."""
    with open(polku, encoding="utf-8") as f:
        teksti = f.read()
    tanaan = datetime.date.fromisoformat(tanaan) if tanaan else None
    nimi, kuvat, salli = "", [], ()
    if lahde == "masjidbox-api":
        paivat, _ = jasenna_masjidbox_api(json.loads(teksti))
    elif lahde == "masjidbox":
        paivat, nimi = jasenna_masjidbox_sivu(teksti)
    elif lahde == "mawaqit":
        paivat, kuvat, nimi = jasenna_mawaqit(teksti, tanaan)
    elif lahde == "rukousajat":
        paivat, salli = jasenna_rukousajat_fi(teksti, tanaan), RUKOUSAJAT_PUUTTUVAT
    else:
        raise SystemExit(f"tuntematon lähde: {lahde}")
    tarkista(paivat, salli)
    return {"nimi": nimi, "kuvat": kuvat, "paivat": paivat}


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "--jasenna":
        try:
            tulos = jasenna_tiedosto(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
        except ValueError as e:
            tulos = {"virhe": str(e), "koodi": getattr(e, "koodi", "")}
        print(json.dumps(tulos, ensure_ascii=False, sort_keys=True))
        return 0
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
            # Järkevyystarkistus: rikkinäistä ei julkaista, vanhat ajat jäävät (except-haara)
            tarkista(paivat, RUKOUSAJAT_PUUTTUVAT if lahde == "rukousajat" else ())
            muutettu, yhteensa = tallenna_ajat(slug, paivat)
            k = tallenna_kuvat(slug, kuvat)
            n, viimeinen = tulevat(slug)
            tallenna_tila(slug, {"ok": True, "lahde": lahde, "haettu": nyt, "paivia": n, "viimeinen": viimeinen,
                                 "varoitus": varoitus, **tieto})
            print(f"{slug}: {yhteensa} päivää lähteestä {lahde} ({tieto.get('tapa')}: {lisa.get('masjidbox_id') or tunnus}), {muutettu} muuttui"
                  + (f", {k} kuvaa" if k else "") + (f" – {varoitus}" if varoitus else ""))
        except Exception as e:  # haku epäonnistui tai aikataulu oli rikki: vanhat ajat jäävät voimaan
            lisatieto = {}
            if isinstance(e, Laskettu):  # Masjidboxin laskemat ajat: aiemmin julkaistut tulevat päivät pois ("Rukousajat lisätään pian")
                tallenna_ajat(slug, {})
                lisatieto = {"tapa": "rajapinta", "tyyppi": "calculated"}
            n, viimeinen = tulevat(slug)
            viesti = (f"Rikkinäinen aikataulu, ei julkaistu: {e}" if isinstance(e, Kelvoton) else str(e))[:300]
            tallenna_tila(slug, {"ok": False, "lahde": lahde, "yritetty": nyt, "virhe": viesti, "koodi": getattr(e, "koodi", "") or "haku",
                                 "paivia": n, "viimeinen": viimeinen, **lisatieto})
            print(f"{slug}: haku lähteestä {lahde} epäonnistui ({tunnus}): {viesti}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
