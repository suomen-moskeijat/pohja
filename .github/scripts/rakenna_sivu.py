#!/usr/bin/env python3
"""Rakennuskomento: sivupohja + moskeijan sisältökansio + sivun asetukset + haetut tiedot → valmis sivu kansioon.

Yksi komento, jota rakennusajo (.github/workflows/rakennusajo.yml) käyttää. Vaiheet ovat samat kuin vanhan
julkaisuajon (rakenna.yml): kokoaminen, artikkelien valinta, (haku), pienet kuvat, jakokuva, Jekyll, karsinta (ADR-0002),
kuvien mitat, kieliversiot ja kalenterit. Jekyll on lukittu tiedostoon .github/rakennus/Gemfile.lock (bundle exec).

Käyttö:
  python3 .github/scripts/rakenna_sivu.py --sisalto moskeijat/testimoskeija --ulos valmis \\
      --url https://esimerkki.pages.dev [--baseurl /<salainen osa>] [--nimi testimoskeija] [--testisivu] \\
      [--haetut haetut/testimoskeija] [--hae] [--aika "2026-03-01 12:00:00 +0200"] [--loki rakennus.log]

Sivun asetukset:
  --url, --baseurl  sivun osoite (sisältökansiossa ei ole osoitetta, ADR-0006). Kun baseurl on annettu, sivu
                    rakennetaan kokonaan sen alle, ja juureen tulee vain neutraali noindex-sivu ja robots.txt (ADR-0008).
  --testisivu       sivu piiloon hakukoneilta (noindex ja X-Robots-Tag).
  --haetut          haettujen tietojen kansio (rukousajat, somet …): kopioidaan sivulle, ja --hae päivittää sen.
  --hae             hakee rukousajat ja somet nyt (verkko).

Julkinen loki: komento tulostaa vain vaiheiden kestot ja lukumäärät, ei sisältöä, polkuja eikä tiedostonimiä. Vaiheiden
oma tuloste menee tiedostoon --loki (ei julkiseen lokiin); ilman sitä virheilmoitusvirtaan (paikallinen käyttö).
"""
import argparse, glob, os, re, shutil, subprocess, sys, tempfile, time

POHJA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GEMFILE = os.path.join(POHJA, ".github", "rakennus", "Gemfile")
# Sivupohjasta ei sivulle (kuten rakenna.yml; lisäksi pohjan omat ohjeet ja päätökset)
EI_POHJASTA = {".git", ".claude", "docs", "malli", "testi", "testit.json", "esittely", "_site"}
# Haetut tiedot (kuten rakenna.yml:n välimuisti)
HAETUT = ["_data/instagram", "_data/aikataulut", "_data/haku", "_data/kuvat", "_data/youtube", "_data/telegram",
          "tiedostot/instagram", "tiedostot/youtube", "tiedostot/telegram", "tiedostot/*/mawaqit"]
# Cloudflare Pagesin rajat (suora lataus, ilmainen taso): ADR-0007
TIEDOSTOJA_ENINT, TIEDOSTO_ENINT = 20000, 25 * 1024 * 1024
JUURI_SIVU = """<!doctype html>
<html lang="fi"><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow">
<meta name="referrer" content="no-referrer"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Suomen moskeijat</title></head>
<body style="font-family:system-ui,sans-serif;margin:3rem 1rem;text-align:center;color:#444">
<p>Tällä osoitteella ei ole julkista sivua.</p></body></html>
"""
OTSAKKEET = "/*\n  X-Robots-Tag: noindex, nofollow\n  Referrer-Policy: no-referrer\n"


class Rakennus:
    def __init__(self, loki):
        self.loki = open(loki, "a", encoding="utf-8") if loki else None
        self.ajat = []

    def aja(self, nimi, komento, cwd, valinnainen=False, env=None):
        """Ajaa vaiheen. Tuloste lokitiedostoon; julkiseen lokiin vain vaiheen nimi ja kesto."""
        t0 = time.time()
        kohde = self.loki or sys.stderr
        kohde.write(f"\n== {nimi}\n"); kohde.flush()
        koodi = subprocess.call(komento, cwd=cwd, stdout=kohde, stderr=kohde, env={**os.environ, **(env or {})})
        self.kesto(nimi, t0)
        if koodi != 0:
            if valinnainen:
                print(f"::warning::Vaihe {nimi} epäonnistui (koodi {koodi}), sivu julkaistaan ilman sitä")
            else:
                raise SystemExit(f"Vaihe {nimi} epäonnistui (koodi {koodi}). Tarkemmin lokitiedostossa.")

    def kesto(self, nimi, t0):
        self.ajat.append((nimi, time.time() - t0))
        print(f"{nimi}: {time.time() - t0:.1f} s", flush=True)


def kopioi(lahde, kohde, ohita=()):
    for n in os.listdir(lahde):
        if n in ohita:
            continue
        a, b = os.path.join(lahde, n), os.path.join(kohde, n)
        if os.path.isdir(a):
            shutil.copytree(a, b, dirs_exist_ok=True, symlinks=False)
        else:
            os.makedirs(kohde, exist_ok=True)
            shutil.copy2(a, b)


def kopioi_haetut(lahde, kohde):
    """Haettujen tietojen polut (HAETUT) kansiosta toiseen."""
    for kuvio in HAETUT:
        for a in glob.glob(os.path.join(lahde, kuvio)):
            b = os.path.join(kohde, os.path.relpath(a, lahde))
            if os.path.isdir(a):
                shutil.rmtree(b, ignore_errors=True)
                shutil.copytree(a, b)


def yaml_arvo(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sisalto", required=True)
    p.add_argument("--ulos", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--baseurl", default="")
    p.add_argument("--nimi", default="")
    p.add_argument("--testisivu", action="store_true")
    p.add_argument("--haetut")
    p.add_argument("--hae", action="store_true")
    p.add_argument("--aika")
    p.add_argument("--loki")
    a = p.parse_args()

    baseurl = a.baseurl.strip("/")
    if baseurl and not re.fullmatch(r"[A-Za-z0-9_-]+", baseurl):
        raise SystemExit("--baseurl: vain kirjaimia, numeroita, - ja _ (yksi polun osa)")
    sisalto, ulos = os.path.abspath(a.sisalto), os.path.abspath(a.ulos)
    if not os.path.isfile(os.path.join(sisalto, "_config.yml")):
        raise SystemExit("--sisalto: kansiosta puuttuu _config.yml")
    r = Rakennus(a.loki)
    t_alku = time.time()
    tyo = tempfile.mkdtemp(prefix="rakennus-")
    sivu = os.path.join(tyo, "sivu")
    try:
        # 1. Kokoaminen: sivupohja, haetut tiedot ja moskeijan oma sisältö (voittaa pohjan)
        t0 = time.time()
        os.makedirs(sivu)
        kopioi(POHJA, sivu, EI_POHJASTA)
        shutil.rmtree(os.path.join(sivu, ".github", "workflows"), ignore_errors=True)
        if a.haetut and os.path.isdir(a.haetut):
            kopioi_haetut(os.path.abspath(a.haetut), sivu)
        kopioi(sisalto, sivu, {".git", ".github", "_config.yml"})
        # Lasten opetus siirretty tavalliseksi palveluksi (paneeli): moskeijan palvelusivu korvaa pohjan vanhan sivun
        if os.path.isfile(os.path.join(sivu, "_palvelut", "lasten-opetus.md")):
            try: os.remove(os.path.join(sivu, "palvelut", "lasten-opetus.html"))
            except FileNotFoundError: pass
        with open(os.path.join(POHJA, "_config.yml"), encoding="utf-8") as f: asetukset = f.read()
        with open(os.path.join(sisalto, "_config.yml"), encoding="utf-8") as f: asetukset += "\n" + f.read()
        # Sivun asetukset viimeisinä (voittavat sisältökansion mahdolliset vanhat url- ja baseurl-rivit)
        asetukset += "\n# Rakennuskomento: sivun asetukset\n"
        asetukset += f"url: {yaml_arvo(a.url.rstrip('/'))}\nbaseurl: {yaml_arvo('/' + baseurl if baseurl else '')}\n"
        if a.nimi: asetukset += f"repo: {yaml_arvo(a.nimi)}\n"  # lomakkeet (osat/lomake-tapa.html), ei baseurlista
        if a.testisivu: asetukset += "noindex: true\n"
        if a.aika: asetukset += f"time: {yaml_arvo(a.aika)}\n"
        with open(os.path.join(sivu, "_config.yml"), "w", encoding="utf-8") as f: f.write(asetukset)
        r.kesto("kokoaminen", t0)

        skriptit = os.path.join(sivu, ".github", "scripts")
        py = lambda nimi, *argv: [sys.executable, os.path.join(skriptit, nimi), *argv]
        r.aja("artikkelit", py("artikkelit.py", "--karsi", "."), sivu)

        # 2. Haku (valinnainen): rukousajat ja somet; tulos talteen haettujen tietojen kansioon
        if a.hae:
            r.aja("instagram", py("instagram.py"), sivu)
            r.aja("rukousajat", py("rukousajat.py"), sivu)
            r.aja("somet", py("somet.py"), sivu)
            if a.haetut:
                os.makedirs(a.haetut, exist_ok=True)
                kopioi_haetut(sivu, os.path.abspath(a.haetut))

        # 3. Kuvat ennen Jekylliä: gallerioiden pienet kuvat ja jakokuva
        r.aja("pienet kuvat", py("pienet.py", sivu), sivu)
        r.aja("jakokuva", py("jakokuva.py", sivu), sivu, valinnainen=True)

        # 4. Jekyll (lukittu versio) sivun osoitteen polkuun
        shutil.rmtree(ulos, ignore_errors=True)
        site = os.path.join(ulos, baseurl) if baseurl else ulos
        versio = subprocess.run(["bundle", "exec", "jekyll", "-v"], cwd=sivu, capture_output=True, text=True,
                                env={**os.environ, "BUNDLE_GEMFILE": GEMFILE}).stdout.strip()
        print(f"Jekyll: {versio.replace('jekyll ', '') or 'ei löytynyt'}", flush=True)
        r.aja("jekyll", ["bundle", "exec", "jekyll", "build", "--future", "-s", sivu, "-d", site], sivu,
              env={"BUNDLE_GEMFILE": GEMFILE, "JEKYLL_ENV": "production"})

        # 5. Jekyllin jälkeen: karsinta (ADR-0002), kuvien mitat, kieliversiot ja kalenterit
        r.aja("karsinta", py("karsi_sivut.py", site), sivu)
        r.aja("kuvien mitat", py("kuvakoot.py", site), sivu, valinnainen=True)
        r.aja("kieliversiot", py("kieliversiot.py", site), sivu)
        r.aja("kalenterit", ["node", os.path.join(skriptit, "kalenteri.js"), site], sivu, valinnainen=True,
              env={"TZ": "Europe/Helsinki"})

        # 6. Piilossa oleva sivu (salainen polku tai testisivu): juureen vain neutraali sivu, ei hakukoneille
        if baseurl:
            for nimi, teksti in (("index.html", JUURI_SIVU), ("404.html", JUURI_SIVU), ("robots.txt", "User-agent: *\nDisallow: /\n")):
                with open(os.path.join(ulos, nimi), "w", encoding="utf-8") as f: f.write(teksti)
        if baseurl or a.testisivu:
            with open(os.path.join(ulos, "_headers"), "w", encoding="utf-8") as f: f.write(OTSAKKEET)

        # 7. Cloudflare Pagesin rajat: tiedostojen määrä ja koko (ei tiedostonimiä julkiseen lokiin)
        koot = [os.path.getsize(os.path.join(k, n)) for k, _, ts in os.walk(ulos) for n in ts]
        print(f"Valmis: {len(koot)} tiedostoa, {sum(koot) / 1048576:.1f} MiB, suurin {max(koot, default=0) / 1024:.0f} KiB, "
              f"yhteensä {time.time() - t_alku:.1f} s", flush=True)
        if len(koot) > TIEDOSTOJA_ENINT:
            raise SystemExit(f"Liikaa tiedostoja Cloudflare Pagesiin ({len(koot)} > {TIEDOSTOJA_ENINT})")
        if max(koot, default=0) > TIEDOSTO_ENINT:
            raise SystemExit("Tiedosto on suurempi kuin Cloudflare Pagesin raja 25 MiB")
    except Exception:
        # Odottamaton virhe: tarkemmat tiedot (polut, tiedostonimet) vain lokitiedostoon, ei julkiseen lokiin
        import traceback
        if not r.loki:
            raise
        traceback.print_exc(file=r.loki)
        raise SystemExit(f"Rakennus epäonnistui ({sys.exc_info()[0].__name__}). Tarkemmin lokitiedostossa.")
    finally:
        shutil.rmtree(tyo, ignore_errors=True)


if __name__ == "__main__":
    main()
