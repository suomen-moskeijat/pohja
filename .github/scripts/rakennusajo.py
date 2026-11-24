#!/usr/bin/env python3
"""Rakennusajo: käy läpi sisältörepon sivustoluettelon ja rakentaa ja julkaisee vain sivut, joiden syötteet muuttuivat.

Työnkulku .github/workflows/rakennusajo.yml ajaa tämän; testit ajavat saman komennon paikallisella julkaisukohteella
(hallinta testi/rakennusajo.mjs). ADR-0006, ADR-0007; hallinta#43.

Käyttö:
  python3 .github/scripts/rakennusajo.py --sisalto <sisältörepon kansio> --versio main|testi \\
      --luettelo tiivisteet/tiivisteet.json --kohde cloudflare|kansio:<polku> \\
      [--haetut haetut] [--hae] [--somet-nyt <nimi>[,<nimi>…]] [--aika "2026-03-01 12:00:00 +0200"] [--lokit <kansio>] [--rinnakkain 4] \\
      [--raportti <paneelin osoite>]   (avain ympäristömuuttujassa RAKENNUSRAPORTTI_AVAIN)
      [--paneeli <paneelin osoite>]    (testisivujen välikerros; oletus: versiosta, main → hallinta, testi → hallinta-testi)

Mitä ajo tekee:
1. Lukee sivustoluettelon (sivustot.yml) ja valitsee sivut, joiden sivupohjan versio (pohja: main/testi) on tämän ajon
   versio. Sivupohja on se kansio, josta tämä komento ajetaan: kukin haara rakentaa omat sivunsa omalla sivupohjallaan.
2. --hae: yhteinen haku (yhteinen_haku.py, hallinta#45) kansioon <haetut>/<nimi>/: rukousajat joka ajossa kerran lähdettä
   kohden ja tallennus jokaiselle moskeijalle sen omalla nimellä; somet sivuille, joilla on tili, 3 tunnin välein tai kun
   käynnistys pyytää (--somet-nyt: paneelin Päivitä somet nyt).
3. Laskee jokaiselle sivulle syötteiden tiivisteen: sisältökansio, sivun asetukset sivustoluettelossa, sivupohja (myös
   yhteiset artikkelit, _artikkelit), haetut tiedot ja rakennuspäivä (Helsingin aikaa). Hakuajat (haettu, yritetty,
   paivitetty) eivät ole tiivisteessä, koska ne muuttuvat joka haulla.
4. Rakentaa (rakenna_sivu.py) ja julkaisee (julkaisukohde.py) sivut, joiden tiiviste eroaa tiivisteluettelon tiivisteestä,
   ja päivittää luettelon onnistuneille sivuille. Jos luettelo puuttuu, kaikki rakennetaan. Rakennuspäivä tiivisteessä
   rakentaa jokaisen sivun kerran vuorokaudessa.
   Luonnoslinkki (ADR-0008, hallinta#49): luonnos ja ehdotus (moskeijan _moskeijat-tiedoston luonnos/ehdotus) rakennetaan
   kokonaan polun /<salainen osa>/ alle (--baseurl, --luonnoslinkki). Luonnosta tai ehdotusta ilman salaista osaa ei julkaista
   (sivun virhe), jotta se ei koskaan päädy juureen. Julkaistu sivu rakennetaan juureen.
   Testisivu, jolla on osoite (hallinta#48, J8), rakennetaan juureen välikerroksen kanssa (--testisivu --sivulupa <paneeli>): sen
   näkee vain paneeliin kirjautunut testaaja tai ylläpitäjä, joten salaista osaa ei käytetä, ja testit.json voi linkittää sivun
   polkuihin. Testisivu ilman osoitetta on kuten ennen luonnoslinkin takana.
   Julkaisukohde asettaa välikerroksen avaimen (ympäristömuuttuja SIVULUPA_AVAIN) Pages-projektin salaisuudeksi; ilman avainta
   testisivua ei julkaista. Avaimen tunniste (HMAC, ei avainta) ja paneelin osoite ovat testisivun asetuksissa: avaimen
   vaihto julkaisee testisivun uudelleen. Julkaisun jälkeen projektin vanhat julkaisut, joiden polku on eri (vaihdettu luonnoslinkki, julkaisu tai
   luonnokseksi palautus), poistetaan (julkaisukohde.poista_vanhat): vanha linkki ei näytä sivua julkaisukohtaisissakaan
   osoitteissa.

   Sivun osoite (hallinta#50, ADR-0007): oma verkkotunnus (sivustoluettelon verkkotunnus: paneeli kirjoittaa sen, kun Cloudflare
   on vahvistanut sen), sivustoluettelon osoite tai <nimi>.suomenmoskeijat.fi. Sivu rakennetaan sillä osoitteella (canonical,
   jakolinkit). Julkaisun jälkeen ajo lisää osoitteen <nimi>.suomenmoskeijat.fi (tai luettelon suomenmoskeijat.fi-osoitteen)
   sivun Pages-projektiin, jos se puuttuu (julkaisukohde.lisaa_verkkotunnus, myös DNS-tietue); se jää omalle verkkotunnukselle
   rinnalle, joten sivu ei katoa siirtymän aikana. Osoitteen tila on tiivisteluettelossa: osoite, joka ei ole vielä käytössä,
   tarkistetaan uudelleen joka ajossa, myös kun sivu ei muutu. Osoitteen lisäyksen virhe ei kaada sivua (varoitus lokiin):
   sivu näkyy silloin projektin omassa osoitteessa.

   Moskeijalista (hallinta#52, moskeijalista.py): ajon lopuksi sivustoluettelosta suomenmoskeijat.fi:n lista omaan
   Pages-projektiinsa (main: sm-moskeijalista, testi: testiversio sm-moskeijalista-testi), kun sen syötteet muuttuivat.
   Julkaistut sivut linkkeinä, luonnokset pelkkinä niminä, ei ehdotuksia eikä testisivuja.

5. --raportti: lähettää rakennusraportin paneeliin (POST <paneeli>/api/rakennusraportti, oma avain RAKENNUSRAPORTTI_AVAIN):
   jokaisesta ajon sivusta sisältöversio (sisältökansion git-puun tunniste sisältörepossa), tulos (rakennettu, ennallaan,
   virhe), aika ja osoite, sekä koko ajon tulos, määrät, kesto ja julkaisukohteen projektien määrä (hallinta#47).
   Paras yritys: julkaisu ei kaadu, jos paneeli ei vastaa (ADR-0004: ajo ei riipu paneelista). Raportissa ei ole sisältöä
   eikä salaista osaa (osoite on sivun osoite ilman luonnoslinkin osaa), ja se kulkee vain paneeliin, ei lokiin.

Virheet: yhden sivun epäonnistunut haku, rakennus tai julkaisu ei estä muita. Epäonnistuneen sivun tiiviste ei päivity, joten
seuraava ajo yrittää uudelleen, ja ajo päättyy virheeseen (poistumiskoodi 1).

Julkinen loki ja välimuisti (pohja on julkinen repo): komento tulostaa vain sivujen nimet, tulokset, syyt, kestot ja
määrät. Sivustoluettelon salaiset osat peitetään (add-mask) ennen muuta tulostetta. Vaiheiden oma tuloste menee
tiedostoihin --lokit (ei julkiseen lokiin). Tiivisteluettelossa on vain tiivisteitä (SHA-256) ja rakennuspäivä, ei sisältöä.
"""
import argparse, concurrent.futures, datetime, glob, hashlib, hmac, json, os, re, shutil, subprocess, sys, tempfile, threading, time
import urllib.error, urllib.request
from zoneinfo import ZoneInfo

import yaml

sys.dont_write_bytecode = True  # ei __pycache__-tiedostoja sivupohjan kansioon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import julkaisukohde
import moskeijalista
import rakenna_sivu
import yhteinen_haku

POHJA = rakenna_sivu.POHJA
ALUE = julkaisukohde.ALUE
RAKENNA = os.path.join(POHJA, ".github", "scripts", "rakenna_sivu.py")
VERSIOT = ("main", "testi")
# Paneeli, jonka sivulupa-reittiin testisivujen välikerros ohjaa (hallinta#48): testi-haaran sivut testipaneeliin (sama tietokanta)
PANEELIT = {"main": "https://hallinta.suomenmoskeijat.fi", "testi": "https://hallinta-testi.suomenmoskeijat.fi"}
MUOTO = 1  # tiivisteluettelon muoto: muutos rakentaa kaikki sivut
# Ei sivupohjan versioon: ei sivulle menevät kansiot (kuten rakennuskomento), työnkulut ja asennetut riippuvuudet
_RAKENNUS = os.path.join(".github", "rakennus")
EI_POHJAN_VERSIOON = set(rakenna_sivu.EI_POHJASTA) | {os.path.join(".github", "workflows"), os.path.join(".github", "moskeijalista")} | {
    os.path.join(_RAKENNUS, k, n) for k in ("", "vanha-julkaisu") for n in ("vendor", ".bundle")}
EI_TIIVISTEESEEN = {".git", "__pycache__"}
# Hakuajat haetuissa tiedoissa: muuttuvat joka haulla, vaikka tieto on sama
HAKUAJAT = {"haettu", "yritetty", "paivitetty"}
SYYT = (("sisalto", "sisältö"), ("asetukset", "sivun asetukset"), ("pohja", "sivupohja"), ("haetut", "haetut tiedot"), ("paiva", "päivä"))
# Rakennuskomennon virheilmoitukset, jotka saa näyttää julkisessa lokissa (ei sisältöä eikä polkuja)
JULKISET_VIRHEET = re.compile(r"^(Vaihe [a-zåäö ]+ epäonnistui \(koodi -?\d+\)|Liikaa tiedostoja Cloudflare Pagesiin \(\d+ > \d+\)|"
                              r"Tiedosto on suurempi kuin Cloudflare Pagesin raja 25 MiB|Rakennus epäonnistui \(\w+\)|"
                              r"--sisalto: kansiosta puuttuu _config\.yml)", re.M)
tulostus = threading.Lock()


def sano(rivi):
    with tulostus:
        print(rivi, flush=True)


class Sivuvirhe(Exception):
    """Yhden sivun virhe: vaihe (haku, rakennus, julkaisu) ja julkiseen lokiin sopiva kuvaus."""

    def __init__(self, vaihe, kuvaus):
        super().__init__(f"{vaihe}: {kuvaus}")


# ---------------------------------------------------------------- tiivisteet
def tiedoston_tiiviste(polku, hakuajat=False):
    if os.path.islink(polku):
        return hashlib.sha256(b"linkki:" + os.readlink(polku).encode()).digest()
    if hakuajat and polku.endswith(".json"):  # haettu tieto ilman hakuaikoja
        try:
            with open(polku, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                d = {k: v for k, v in d.items() if k not in HAKUAJAT}
            return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False).encode()).digest()
        except Exception:
            pass
    h = hashlib.sha256()
    with open(polku, "rb") as f:
        for pala in iter(lambda: f.read(1 << 20), b""):
            h.update(pala)
    return h.digest()


def kansion_tiiviste(kansio, ohita=(), hakuajat=False):
    """Tiiviste kansion tiedostoista (polku ja sisältö). `ohita`: polut kansion juuresta, joita ei lasketa."""
    h = hashlib.sha256()
    for juuri, kansiot, tiedostot in os.walk(kansio):
        suhde = lambda n: os.path.normpath(os.path.join(os.path.relpath(juuri, kansio), n))
        kansiot[:] = sorted(k for k in kansiot if k not in EI_TIIVISTEESEEN and suhde(k) not in ohita)
        for n in sorted(tiedostot):
            if suhde(n) in ohita:
                continue
            h.update(suhde(n).encode() + b"\0" + tiedoston_tiiviste(os.path.join(juuri, n), hakuajat) + b"\0")
    return h.hexdigest()


def yhdista(osat):
    return hashlib.sha256(json.dumps({"muoto": MUOTO, **osat}, sort_keys=True).encode()).hexdigest()


def helsingin_paiva(aika=None):
    """Rakennuspäivä Helsingin aikaa. `aika` kuten rakennuskomennon --aika: "2026-03-01 12:00:00 +0200"."""
    hetki = datetime.datetime.strptime(aika, "%Y-%m-%d %H:%M:%S %z") if aika else datetime.datetime.now(datetime.timezone.utc)
    return hetki.astimezone(ZoneInfo("Europe/Helsinki")).date().isoformat()


# ---------------------------------------------------------------- sivustoluettelo ja tiivisteluettelo
def lue_sivustoluettelo(sisalto):
    """Sivustoluettelon sivut ja virheelliset kohdat. Salaiset osat peitetään lokista ennen kuin mitään muuta tulostetaan."""
    try:
        with open(os.path.join(sisalto, "sivustot.yml"), encoding="utf-8") as f:
            kohdat = (yaml.safe_load(f) or {}).get("sivut")
        if not isinstance(kohdat, list):
            raise ValueError
    except Exception:
        raise SystemExit("Sivustoluetteloa (sivustot.yml) ei voitu lukea, tai siinä ei ole sivuja")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for s in kohdat:
            if isinstance(s, dict) and s.get("salainen_osa"):
                print(f"::add-mask::{s['salainen_osa']}", flush=True)
    sivut, virheet, nimet, projektit = [], [], set(), set()
    for i, s in enumerate(kohdat, 1):
        nimi = str(s.get("nimi") or "") if isinstance(s, dict) else ""
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", nimi) or nimi in nimet:
            virheet.append((f"sivustoluettelon kohta {i}", "nimi puuttuu, on huono tai on luettelossa kahdesti"))
            continue
        nimet.add(nimi)
        s = {**s, "nimi": nimi, "pohja": str(s.get("pohja") or "main")}
        if s.get("salainen_osa") is not None: s["salainen_osa"] = str(s["salainen_osa"])
        salainen = str(s.get("salainen_osa") or "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,57}", str(s.get("projekti") or "")) or s["projekti"] in projektit:
            virheet.append((nimi, "projekti: Cloudflare Pages -projektin nimi puuttuu, on huono tai on luettelossa kahdesti"))
        elif salainen and not re.fullmatch(r"[A-Za-z0-9_-]{22,}", salainen):
            virheet.append((nimi, "salainen_osa: vähintään 22 merkkiä A-Z, a-z, 0-9, - tai _ (128 bittiä)"))
        elif s["pohja"] not in VERSIOT:
            virheet.append((nimi, "pohja: sivupohjan versio on main tai testi"))
        else:
            projektit.add(s["projekti"])
            sivut.append(s)
    return sivut, virheet


def lue_tiivisteluettelo(polku):
    """Edellisen ajon tiivisteet. Puuttuva tai rikkinäinen luettelo on tyhjä: kaikki rakennetaan."""
    try:
        with open(polku, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("muoto") == MUOTO and isinstance(d.get("sivut"), dict):
            return {n: t for n, t in d["sivut"].items() if isinstance(t, dict)}
    except Exception:
        pass
    return {}


def tallenna_tiivisteluettelo(polku, sivut):
    os.makedirs(os.path.dirname(os.path.abspath(polku)), exist_ok=True)
    with open(polku + ".uusi", "w", encoding="utf-8") as f:
        json.dump({"muoto": MUOTO, "sivut": sivut}, f, sort_keys=True, indent=1)
    os.replace(polku + ".uusi", polku)


# ---------------------------------------------------------------- ajo
class Ajo:
    def __init__(self, a):
        self.a = a
        self.sisalto = os.path.abspath(a.sisalto)
        self.haetut = os.path.abspath(a.haetut) if a.haetut else None
        self.lokit = os.path.abspath(a.lokit) if a.lokit else tempfile.mkdtemp(prefix="rakennusajo-lokit-")
        os.makedirs(self.lokit, exist_ok=True)
        # Rakennuskomento ei tarvitse julkaisun avaimia
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("CLOUDFLARE_") and k != "SIVULUPA_AVAIN"}
        self.paneeli = (a.paneeli or PANEELIT[a.versio]).rstrip("/")

    def kansio(self, s):
        return os.path.join(self.sisalto, "moskeijat", s["nimi"])

    def haettujen_kansio(self, s):
        return os.path.join(self.haetut, s["nimi"]) if self.haetut else None

    def loki(self, s):
        return os.path.join(self.lokit, s["nimi"] + ".log")

    def komento(self, s, vaihe, argumentit):
        """Rakennuskomento yhdelle sivulle. Tuloste lokitiedostoon; palauttaa komennon julkisen tulosteen (kestot ja määrät)."""
        try:
            t = subprocess.run([sys.executable, RAKENNA, "--sisalto", self.kansio(s), "--loki", self.loki(s), *argumentit],
                               capture_output=True, text=True, env=self.env, timeout=1200)
        except subprocess.TimeoutExpired:
            raise Sivuvirhe(vaihe, "ei valmistunut 20 minuutissa")
        if t.returncode != 0:
            m = JULKISET_VIRHEET.search(t.stderr or "")
            raise Sivuvirhe(vaihe, m.group(1) if m else f"rakennuskomento epäonnistui (koodi {t.returncode})")
        return t.stdout or ""

    def polku(self, s):
        """Polku, jonka alle sivu rakennetaan: luonnoslinkin salainen osa (luonnos, ehdotus tai testisivu ilman välikerrosta, jolla
        on salainen osa) tai "" (juuri: julkaistu sivu ja välikerroksen takana oleva testisivu, hallinta#48). Luonnos tai ehdotus
        ilman salaista osaa on virhe: sitä ei julkaista juureen."""
        if valikerroksen_takana(s):
            return ""
        salainen = str(s.get("salainen_osa") or "")
        tila = sivun_tila(self.kansio(s))
        if tila != "julkaistu" and not salainen:
            raise Sivuvirhe("luonnoslinkki", f"sivu on {tila}, mutta sivustoluettelosta puuttuu salainen_osa (luonnoslinkki): sivua ei julkaista")
        return salainen if tila != "julkaistu" or s.get("testisivu") else ""

    def asetukset(self, s):
        """Sivun asetukset tiivisteeseen: sivustoluettelon kohta, testisivulla myös välikerroksen paneeli ja avaimen tunniste
        (HMAC vakiotekstistä, ei avainta: avaimen vaihto julkaisee testisivun uudelleen, jotta uusi avain tulee voimaan)."""
        if not valikerroksen_takana(s):
            return s
        avain = (os.environ.get("SIVULUPA_AVAIN") or "").strip()
        tunniste = hmac.new(avain.encode(), b"sivulupa-avaimen-tunniste", hashlib.sha256).hexdigest()[:16] if avain else ""
        return {**s, "_sivulupa": {"paneeli": self.paneeli, "avain": tunniste}}

    def osat(self, s, pohja, paiva):
        haetut = self.haettujen_kansio(s)
        return {
            "sisalto": kansion_tiiviste(self.kansio(s), ohita={".github"}),
            "asetukset": hashlib.sha256(json.dumps(self.asetukset(s), sort_keys=True, default=str).encode()).hexdigest(),
            "pohja": pohja,
            "haetut": kansion_tiiviste(haetut, hakuajat=True) if haetut and os.path.isdir(haetut) else hashlib.sha256(b"").hexdigest(),
            "paiva": paiva,
        }

    def rakenna_ja_julkaise(self, s, kohde):
        """Rakentaa sivun ja julkaisee sen. Palauttaa { kuvaus (julkiseen lokiin), osoite, tiedostoja }."""
        tyo = tempfile.mkdtemp(prefix="rakennusajo-")
        try:
            t0 = time.time()
            polku = self.polku(s)
            try:
                projektin = kohde.osoite(s)  # luo projektin, jos sitä ei ole
            except julkaisukohde.Julkaisuvirhe as e:
                raise Sivuvirhe("julkaisu", str(e))
            osoite = rakennusosoite(s)
            ulos = os.path.join(tyo, "valmis")
            argumentit = ["--ulos", ulos, "--url", osoite, "--nimi", s["nimi"]]
            if polku: argumentit += ["--baseurl", "/" + polku, "--luonnoslinkki"]
            if s.get("testisivu"): argumentit += ["--testisivu"] + (["--sivulupa", self.paneeli] if valikerroksen_takana(s) else [])
            haetut = self.haettujen_kansio(s)
            if haetut and os.path.isdir(haetut): argumentit += ["--haetut", haetut]
            if self.a.aika: argumentit += ["--aika", self.a.aika]
            tuloste = self.komento(s, "rakennus", argumentit)
            for varoitus in re.findall(r"^::warning::(Vaihe [a-zåäö ]+ epäonnistui \(koodi -?\d+\), sivu julkaistaan ilman sitä)$", tuloste, re.M):
                sano(f"::warning::{s['nimi']}: {varoitus}")
            valmis = re.search(r"^Valmis: ((\d+) tiedostoa, [\d.]+ MiB)", tuloste, re.M)
            t1 = time.time()
            try:
                sivulupa = valikerroksen_takana(s)
                julkaisu = kohde.julkaise(s, ulos, self.loki(s), polku=polku, sivulupa=sivulupa)
                poistettu = kohde.poista_vanhat(s, polku, self.loki(s), sivulupa=sivulupa)
            except julkaisukohde.Julkaisuvirhe as e:
                raise Sivuvirhe("julkaisu", str(e))
            if poistettu: julkaisu += f"; poistettu {poistettu} vanha{'a' if poistettu > 1 else ''} julkaisu{'a' if poistettu > 1 else ''}"
            osoitteen_tila = self.varmista_osoite(s, kohde)
            return {"kuvaus": f"rakennus {t1 - t0:.1f} s ({valmis.group(1) if valmis else 'valmis'}), julkaisu {time.time() - t1:.1f} s ({julkaisu})",
                    "osoite": raportin_osoite(s, osoitteen_tila, projektin), "osoitteen_tila": osoitteen_tila,
                    "tiedostoja": int(valmis.group(2)) if valmis else None, "luonnoslinkki": bool(polku)}
        finally:
            shutil.rmtree(tyo, ignore_errors=True)

    def varmista_osoite(self, s, kohde):
        """Sivun suomenmoskeijat.fi-osoite projektiin, jos se puuttuu (hallinta#50). Palauttaa { host, tila } tai None (sivulla ei
        ole suomenmoskeijat.fi-osoitetta). Ei kaada sivua: virhe ja odottava osoite ovat varoituksia. Lokiin ei osoitetta."""
        host = alueen_osoite(s)
        if not host:
            return None
        try:
            t = kohde.lisaa_verkkotunnus(s, host, self.loki(s))
        except julkaisukohde.Julkaisuvirhe as e:
            sano(f"::warning::{s['nimi']}: sivun osoitetta ei voitu lisätä Pages-projektiin ({e}). Sivu näkyy projektin omassa osoitteessa, ja seuraava ajo yrittää uudelleen.")
            return {"host": host, "tila": "virhe"}
        if t["tila"] != "active":
            sano(f"::warning::{s['nimi']}: sivun osoite ei ole vielä käytössä (Cloudflare: {t['tila']}{'; ' + t['dns'] if t.get('dns') else ''}). "
                 "Sivu näkyy projektin omassa osoitteessa, ja seuraava ajo tarkistaa osoitteen uudelleen.")
        elif t.get("lisatty") or t.get("dns"):
            sano(f"{s['nimi']}: sivun osoite lisätty Pages-projektiin{' (' + t['dns'] + ')' if t.get('dns') else ''}")
        return {"host": host, "tila": t["tila"]}


VERKKOTUNNUS = re.compile(r"(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}")


def verkkotunnus(s):
    """Moskeijan oma verkkotunnus sivustoluettelosta (paneeli kirjoittaa sen, kun Cloudflare on vahvistanut sen) tai ""."""
    d = str(s.get("verkkotunnus") or "").strip().lower().rstrip(".")
    return d if VERKKOTUNNUS.fullmatch(d) else ""


def rakennusosoite(s):
    """Osoite, jolla sivu rakennetaan (canonical, jakolinkit): oma verkkotunnus, luettelon osoite tai <nimi>.suomenmoskeijat.fi."""
    d = verkkotunnus(s)
    if d:
        return f"https://{d}"
    return str(s.get("osoite") or "") or f"https://{s['nimi']}.{ALUE}"


def alueen_osoite(s):
    """suomenmoskeijat.fi-osoite, jonka rakennusajo pitää sivun projektissa: luettelon osoite, jos se on alueella, muuten
    <nimi>.suomenmoskeijat.fi; None, jos luettelon osoite on muualla."""
    oma = str(s.get("osoite") or "").strip()
    if not oma:
        return f"{s['nimi']}.{ALUE}"
    m = re.fullmatch(r"https://([a-z0-9.-]+)/?", oma.lower())
    return m.group(1) if m and (m.group(1) == ALUE or m.group(1).endswith("." + ALUE)) else None


def raportin_osoite(s, osoitteen_tila, projektin=None):
    """Osoite rakennusraporttiin: oma verkkotunnus, luettelon osoite, käytössä oleva <nimi>.suomenmoskeijat.fi tai projektin oma
    osoite (None: paneeli päättelee sen projektista). Paneeli näyttää sivun tästä osoitteesta."""
    d = verkkotunnus(s)
    if d:
        return f"https://{d}"
    oma = str(s.get("osoite") or "").strip().rstrip("/")
    if oma:
        return oma
    host = alueen_osoite(s)
    if osoitteen_tila and osoitteen_tila.get("tila") == "active" and osoitteen_tila.get("host") == host:
        return f"https://{host}"
    return projektin


def valikerroksen_takana(s):
    """Testisivu, jolla on sivustoluettelossa osoite, on välikerroksen takana (hallinta#48, ADR-0008). Osoite (esim.
    testimoskeija.suomenmoskeijat.fi) on samaa sivustoa kuin paneeli, joten esikatselukehys saa välikerroksen evästeen, ja
    sen lisääminen luetteloon vaihtaa testisivun välikerroksen taakse yhdellä kertaa paneelissa ja rakennusajossa (paneeli
    src/sivustoluettelo.js tekee saman päätelmän). Ilman osoitetta testisivu on kuten ennen luonnoslinkin takana."""
    return bool(s.get("testisivu") and re.fullmatch(r"https://[A-Za-z0-9.-]+/?", str(s.get("osoite") or "").strip()))


def sivun_tila(kansio):
    """Sivun tila moskeijan omasta tiedostosta (_moskeijat/<moskeija>.md, kuten paneeli ja sivupohja): luonnos, ehdotus tai
    julkaistu. Jos tiedostoa ei voi lukea, sivu on luonnos (turvallinen oletus: ei juureen)."""
    return sivun_tiedot(kansio)["tila"]


def sivun_tiedot(kansio):
    """Sivun tila, nimi (title) ja kaupunki moskeijan omasta tiedostosta. Ilman luettavaa tiedostoa: luonnos ilman nimeä."""
    teksti = lambda v: str((v.get("fi") or next(iter(v.values()), "")) if isinstance(v, dict) and v else (v or "")).strip()
    try:
        with open(os.path.join(kansio, "_config.yml"), encoding="utf-8") as f:
            moskeija = str((yaml.safe_load(f) or {}).get("moskeija") or "")
        tiedostot = sorted(glob.glob(os.path.join(kansio, "_moskeijat", "*.md")))
        for polku in sorted(tiedostot, key=lambda p: os.path.basename(p) != f"{moskeija}.md"):
            with open(polku, encoding="utf-8") as f:
                osat = f.read().split("---", 2)
            d = yaml.safe_load(osat[1]) if len(osat) == 3 else None
            if isinstance(d, dict) and (not moskeija or str(d.get("slug") or os.path.basename(polku)[:-3]) == moskeija or len(tiedostot) == 1):
                return {"tila": "ehdotus" if d.get("ehdotus") is True else "luonnos" if d.get("luonnos") is True else "julkaistu",
                        "nimi": teksti(d.get("title")), "kaupunki": teksti(d.get("kaupunki"))}
    except Exception:
        pass
    return {"tila": "luonnos", "nimi": "", "kaupunki": ""}


def listan_rivit(ajo, kaikki):
    """Moskeijalistan rivit (hallinta#52): sivupohjan versiolla main julkaistavat sivut (ei testisivuja). Julkaistu: nimi, kaupunki
    ja sivun osoite; luonnos: nimi ja kaupunki ilman osoitetta (luonnoslinkki ei saa näkyä); ehdotus ei näy. Ei projektia,
    tunnusta eikä salaista osaa. Sivu, jonka nimeä ei voi lukea, jätetään pois."""
    rivit = []
    for s in kaikki:
        if s["pohja"] != "main" or s.get("testisivu"):
            continue
        t = sivun_tiedot(ajo.kansio(s))
        if t["tila"] == "ehdotus" or not t["nimi"]:
            continue
        rivit.append({"nimi": t["nimi"][:120], "kaupunki": t["kaupunki"][:80], "tila": t["tila"],
                      "osoite": rakennusosoite(s).rstrip("/") + "/" if t["tila"] == "julkaistu" else None})
    return rivit


def sisaltoversio(sisalto, nimi):
    """Sivun sisältöversio: sisältökansion git-puun tunniste sisältörepossa (sama kuin paneelin tallennuksen jälkeen
    GitHubista lukema). None, jos sisältö ei ole git-repo."""
    try:
        t = subprocess.run(["git", "-C", sisalto, "rev-parse", "--verify", "--quiet", f"HEAD:moskeijat/{nimi}"],
                           capture_output=True, text=True, timeout=30)
        v = t.stdout.strip()
        return v if t.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", v) else None
    except Exception:
        return None


def raportoi(paneeli, avain, raportti):
    """Rakennusraportti paneeliin. Paras yritys: virhe ei kaada ajoa. Lokiin vain tulos (ei raporttia, ei avainta)."""
    if not paneeli or not avain:
        sano("Rakennusraportti: ei lähetetty (paneelin osoite tai avain RAKENNUSRAPORTTI_AVAIN puuttuu)")
        return False
    data = json.dumps(raportti, ensure_ascii=False).encode()
    virhe = ""
    for yritys in range(3):
        pyynto = urllib.request.Request(paneeli.rstrip("/") + "/api/rakennusraportti", data=data, method="POST", headers={
            **julkaisukohde.SELAIN, "Content-Type": "application/json", "Authorization": f"Bearer {avain}"})
        try:
            with urllib.request.urlopen(pyynto, timeout=20):
                sano(f"Rakennusraportti: lähetetty paneeliin ({len(raportti['sivut'])} sivua)")
                return True
        except urllib.error.HTTPError as e:
            virhe = f"HTTP {e.code}"
            if 400 <= e.code < 500 and e.code != 429:  # avain tai raportti ei kelpaa: uusi yritys ei auta
                break
        except Exception as e:
            virhe = type(e).__name__
        time.sleep(2 * (yritys + 1))
    sano(f"::warning::Rakennusraportti: paneeli ei vastaanottanut raporttia ({virhe}). Julkaisu ei riipu siitä.")
    return False


def rinnakkain(n, tehtava, kohteet):
    """Ajaa tehtävän jokaiselle kohteelle (n kerralla). Palauttaa {nimi: tulos tai Sivuvirhe}."""
    def yksi(s):
        try:
            return s["nimi"], tehtava(s)
        except Sivuvirhe as e:
            return s["nimi"], e
        except Exception as e:  # odottamaton: julkiseen lokiin vain virheen laji
            return s["nimi"], Sivuvirhe("ajo", f"odottamaton virhe ({type(e).__name__})")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, n)) as tyot:
        return dict(tyot.map(yksi, kohteet))


def iso_aika():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ajon_tiedot():
    """GitHubin ajon tunniste ja lokin osoite (julkinen), paikallisesti None."""
    tunnus, repo = os.environ.get("GITHUB_RUN_ID", ""), os.environ.get("GITHUB_REPOSITORY", "")
    if not tunnus.isdigit() or not repo:
        return None
    return {"id": int(tunnus), "osoite": f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{tunnus}"}


def luonnoslinkin_alla(ajo, s):
    try:
        return bool(ajo.polku(s))
    except Sivuvirhe:
        return False


def sivun_raportti(ajo, s, valmis, virhe, osoitteen_tila=None):
    """Yhden sivun rivi rakennusraporttiin: ei sisältöä eikä salaista osaa (osoite ilman luonnoslinkin osaa)."""
    rivi = {"nimi": s["nimi"], "sisaltoversio": sisaltoversio(ajo.sisalto, s["nimi"]), "aika": iso_aika(),
            "osoite": raportin_osoite(s, osoitteen_tila), "luonnoslinkki": luonnoslinkin_alla(ajo, s), "tiedostoja": None}
    if virhe:
        rivi.update(tulos="virhe", virhe=virhe)
    elif valmis:
        tulos, aika = valmis
        rivi.update(tulos="rakennettu", aika=aika, osoite=tulos["osoite"], tiedostoja=tulos["tiedostoja"], luonnoslinkki=tulos["luonnoslinkki"])
    else:
        rivi["tulos"] = "ennallaan"
    return rivi


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sisalto", required=True, help="sisältörepon kansio (sivustot.yml ja moskeijat/<nimi>/)")
    p.add_argument("--versio", required=True, choices=VERSIOT, help="tämän ajon sivupohjan versio: rakennetaan sivut, joiden pohja on tämä")
    p.add_argument("--luettelo", required=True, help="tiivisteluettelo (JSON): luetaan ja päivitetään")
    p.add_argument("--kohde", required=True, help='julkaisukohde: "cloudflare" tai "kansio:<polku>"')
    p.add_argument("--haetut", help="haettujen tietojen kansio: <haetut>/<nimi>/")
    p.add_argument("--hae", action="store_true", help="hae rukousajat ja somet nyt (verkko)")
    p.add_argument("--somet-nyt", default="", help="sivut (nimet pilkuin), joiden somet haetaan heti (käynnistyksen pyyntö)")
    p.add_argument("--aika", help='rakennushetki, esim. "2026-03-01 12:00:00 +0200" (oletus: nyt)')
    p.add_argument("--lokit", help="kansio vaiheiden tulosteille (ei julkiseen lokiin)")
    p.add_argument("--rinnakkain", type=int, default=1, help="montako sivua kerralla")
    p.add_argument("--paneeli", help="paneelin osoite testisivujen välikerrokselle (oletus: versiosta)")
    p.add_argument("--raportti", help="paneelin osoite: rakennusraportti (avain ympäristömuuttujassa RAKENNUSRAPORTTI_AVAIN)")
    a = p.parse_args()
    if a.hae and not a.haetut:
        raise SystemExit("--hae: anna haettujen tietojen kansio (--haetut)")
    # Käynnistyksen somepyyntö on vain vihje: tuntemattomat ja huonot nimet ohitetaan
    pyydetyt = {n for n in re.split(r"[\s,]+", a.somet_nyt or "") if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", n)}
    t_alku = time.time()
    ajo = Ajo(a)
    kaikki, virheelliset = lue_sivustoluettelo(ajo.sisalto)  # peittää salaiset osat: ensimmäisenä
    kohde = julkaisukohde.luo(a.kohde)
    paiva = helsingin_paiva(a.aika)
    sivut = [s for s in kaikki if s["pohja"] == a.versio]
    sano(f"Rakennusajo: sivupohjan versio {a.versio}, {len(sivut)} sivua ({len(kaikki) - len(sivut)} muilla versioilla), rakennuspäivä {paiva}")
    epaonnistuneet = dict(virheelliset)

    # 1. Haetut tiedot (rukousajat, somet): ennen tiivisteitä, koska ne ovat sivun syötteitä
    # Välimuistiin tallennetaan, kun haettu tieto tai somejen hakuaika muuttui (hakuaika ratkaisee seuraavan somehaun, joten sen
    # pitää säilyä, vaikka julkaisut olisivat ennallaan; sivun tiivisteessä hakuaikoja ei ole)
    valimuisti = lambda: kansion_tiiviste(ajo.haetut, hakuajat=True) + "".join(sorted(
        n + tiedoston_tiiviste(os.path.join(ajo.haetut, n, yhteinen_haku.SOMET_TILA)).hex()
        for n in (os.listdir(ajo.haetut) if os.path.isdir(ajo.haetut) else []) if os.path.isfile(os.path.join(ajo.haetut, n, yhteinen_haku.SOMET_TILA))))
    haetut_ennen = valimuisti() if a.hae else ""  # puuttuva kansio = tyhjä
    if a.hae:
        os.makedirs(ajo.haetut, exist_ok=True)
        nimet = {s["nimi"] for s in sivut}
        for n in os.listdir(ajo.haetut):  # poistuneen sivun haetut tiedot pois
            if n not in nimet:
                shutil.rmtree(os.path.join(ajo.haetut, n), ignore_errors=True)
        hetki = datetime.datetime.strptime(a.aika, "%Y-%m-%d %H:%M:%S %z") if a.aika else datetime.datetime.now(datetime.timezone.utc)
        haettavat = [yhteinen_haku.Sivu(s["nimi"], ajo.kansio(s), ajo.haettujen_kansio(s), ajo.loki(s)) for s in sivut]
        try:
            virheet, yhteenveto = yhteinen_haku.hae(haettavat, hetki, pyydetyt & {s["nimi"] for s in sivut}, a.rinnakkain)
            sano(yhteenveto)
        except Exception as e:  # odottamaton: julkiseen lokiin vain virheen laji; sivut rakennetaan edellisillä haetuilla tiedoilla
            virheet = {}
            sano(f"::warning::Haku epäonnistui ({type(e).__name__}), edelliset haetut tiedot jäävät")
        epaonnistuneet.update(virheet)

    # 2. Syötteiden tiivisteet: sivu rakennetaan, kun tiiviste eroaa viimeksi onnistuneesti julkaistusta
    t0 = time.time()
    luettelo = lue_tiivisteluettelo(a.luettelo)
    alussa = json.dumps(luettelo, sort_keys=True)
    pohja = kansion_tiiviste(POHJA, ohita=EI_POHJAN_VERSIOON)
    muuttuneet, uudet, syyt = [], {}, {}
    for s in sivut:
        nimi = s["nimi"]
        if nimi in epaonnistuneet:
            continue
        try:
            osat = ajo.osat(s, pohja, paiva)
        except Exception as e:
            epaonnistuneet[nimi] = f"tiiviste: sisältökansiota ei voitu lukea ({type(e).__name__})"
            continue
        uudet[nimi] = {"tiiviste": yhdista(osat), "osat": osat}
        vanha = luettelo.get(nimi) or {}
        if vanha.get("tiiviste") == uudet[nimi]["tiiviste"]:
            sano(f"{nimi}: ei muutoksia")
            continue
        vanhat = vanha.get("osat") if isinstance(vanha.get("osat"), dict) else None
        syyt[nimi] = ", ".join(t for k, t in SYYT if vanhat.get(k) != osat[k]) if vanhat else "ei aiempaa julkaisua tiivisteluettelossa"
        muuttuneet.append(s)
    sano(f"Tiivisteet: {len(muuttuneet)} muuttunutta, {len(sivut) - len(muuttuneet) - len([s for s in sivut if s['nimi'] in epaonnistuneet])} ennallaan, {time.time() - t0:.1f} s")

    # 3. Rakennus ja julkaisu. Tiivisteluettelo päivittyy vain onnistuneille sivuille (heti, jotta keskeytynyt ajo ei hukkaa niitä).
    lukko = threading.Lock()
    def rakenna(s):
        tulos = ajo.rakenna_ja_julkaise(s, kohde)
        with lukko:
            luettelo[s["nimi"]] = {**uudet[s["nimi"]], **({"osoite": tulos["osoitteen_tila"]} if tulos.get("osoitteen_tila") else {})}
            tallenna_tiivisteluettelo(a.luettelo, luettelo)
        sano(f"{s['nimi']}: rakennettu ja julkaistu (syy: {syyt[s['nimi']]}) – {tulos['kuvaus']}")
        return tulos
    rakennetut, valmiit = 0, {}
    for nimi, tulos in rinnakkain(a.rinnakkain, rakenna, muuttuneet).items():
        if isinstance(tulos, Sivuvirhe):
            epaonnistuneet[nimi] = str(tulos)
        else:
            rakennetut += 1
            valmiit[nimi] = (tulos, iso_aika())

    # Sivun osoite, joka ei ollut käytössä (tai luettelon osoite muuttui), tarkistetaan myös, kun sivu ei muuttunut (hallinta#50)
    def tarkista_osoite(s):
        return ajo.varmista_osoite(s, kohde)
    tarkistettavat = [s for s in sivut if s["nimi"] in luettelo and s["nimi"] not in valmiit and s["nimi"] not in epaonnistuneet
                      and alueen_osoite(s) and (luettelo[s["nimi"]].get("osoite") or {}) != {"host": alueen_osoite(s), "tila": "active"}]
    for nimi, tila in rinnakkain(a.rinnakkain, tarkista_osoite, tarkistettavat).items():
        if isinstance(tila, dict):
            luettelo[nimi] = {**luettelo[nimi], "osoite": tila}

    # Moskeijalista (hallinta#52): sivustoluettelosta omaan Pages-projektiinsa, kun sen syötteet muuttuivat. Virhe ei estä sivuja.
    lista_muuttui = False
    try:
        if any(s["nimi"] == moskeijalista.NIMI or s["projekti"] in moskeijalista.PROJEKTI.values() for s in kaikki):
            raise moskeijalista.Listavirhe(f"sivustoluettelossa on sivu, jonka nimi tai projekti on varattu moskeijalistalle")
        lista = moskeijalista.paivita(listan_rivit(ajo, kaikki), a.versio, ajo.paneeli, kohde,
                                      os.path.join(os.path.dirname(os.path.abspath(a.luettelo)), "moskeijalista.json"),
                                      os.path.join(ajo.lokit, "moskeijalista.log"), julkaisuvirhe=julkaisukohde.Julkaisuvirhe)
        lista_muuttui = lista["muuttui"]
        sano(f"Moskeijalista: {lista['kuvaus']}")
    except moskeijalista.Listavirhe as e:
        epaonnistuneet[moskeijalista.NIMI] = str(e)
    except Exception as e:  # odottamaton: julkiseen lokiin vain virheen laji
        epaonnistuneet[moskeijalista.NIMI] = f"odottamaton virhe ({type(e).__name__})"

    # Poistuneet sivut pois luettelosta (muiden versioiden sivut jäävät, jos luettelo on yhteinen)
    for nimi in [n for n in luettelo if n not in {s["nimi"] for s in kaikki}]:
        del luettelo[nimi]
    luettelo_muuttui = json.dumps(luettelo, sort_keys=True) != alussa
    if luettelo_muuttui or not os.path.exists(a.luettelo):
        tallenna_tiivisteluettelo(a.luettelo, luettelo)
    luettelo_muuttui = luettelo_muuttui or lista_muuttui  # listan tiiviste on samassa välimuistin kansiossa

    # 4. Yhteenveto
    for nimi, kuvaus in epaonnistuneet.items():
        sano(f"::error::{nimi}: epäonnistui ({kuvaus}). Aiempi julkaisu jää näkyviin, ja seuraava ajo yrittää uudelleen.")
    ennallaan = len(sivut) - rakennetut - len([s for s in sivut if s["nimi"] in epaonnistuneet])
    yhteenveto = f"Rakennettu ja julkaistu {rakennetut}, ei muutoksia {ennallaan}, epäonnistui {len(epaonnistuneet)}, yhteensä {time.time() - t_alku:.1f} s"
    sano(yhteenveto)
    haetut_muuttui = bool(a.hae) and valimuisti() != haetut_ennen
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"luettelo_muuttui={str(luettelo_muuttui).lower()}\nhaetut_muuttui={str(haetut_muuttui).lower()}\n"
                    f"rakennettu={rakennetut}\nennallaan={ennallaan}\nepaonnistui={len(epaonnistuneet)}\n")
    if a.raportti is not None:
        raportoi(a.raportti, os.environ.get("RAKENNUSRAPORTTI_AVAIN", "").strip(), {
            "muoto": 1, "versio": a.versio, "aika": iso_aika(), "kesto": round(time.time() - t_alku, 1),
            "tulos": "virhe" if epaonnistuneet else "ok", "rakennettu": rakennetut, "ennallaan": ennallaan,
            "epaonnistui": len([x for x in sivut if x["nimi"] in epaonnistuneet]), "luettelonVirheet": len(virheelliset), "ajo": ajon_tiedot(),
            "projekteja": kohde.projekteja(),
            "sivut": [sivun_raportti(ajo, s, valmiit.get(s["nimi"]), epaonnistuneet.get(s["nimi"]), (luettelo.get(s["nimi"]) or {}).get("osoite")) for s in sivut],
        })
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(f"### Rakennusajo ({a.versio}, {paiva})\n\n{yhteenveto}\n\n")
            for s in muuttuneet:
                f.write(f"- {s['nimi']}: {'epäonnistui' if s['nimi'] in epaonnistuneet else 'rakennettu ja julkaistu'} (syy: {syyt[s['nimi']]})\n")
    if not a.lokit:
        shutil.rmtree(ajo.lokit, ignore_errors=True)
    sys.exit(1 if epaonnistuneet else 0)


if __name__ == "__main__":
    main()
