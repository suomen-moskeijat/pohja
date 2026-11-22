#!/usr/bin/env python3
"""Julkaisukohde: paikka, johon rakennusajo (rakennusajo.py) julkaisee valmiin sivun (ADR-0007).

Yksi rajapinta, kaksi sovitinta:
  osoite(sivu)                  sivun osoite kohteessa, kun sivustoluettelossa ei ole osoitetta
  julkaise(sivu, kansio, loki, polku)
                                julkaisee valmiin sivun kansion; palauttaa lyhyen kuvauksen julkiseen lokiin. polku: luonnoslinkin
                                salainen osa, jonka alla sivu on, tai "" (juuri); sen tunniste (polun_tunniste) kirjataan julkaisuun
  poista_vanhat(sivu, polku, loki)
                                poistaa projektin vanhat julkaisut, joiden polku on eri (hallinta#49, ADR-0008): luonnoslinkin
                                vaihdon tai julkaisun jälkeen vanha linkki ei näytä sivua julkaisukohtaisissakaan osoitteissa
                                (Cloudflare Pages säilyttää jokaisen julkaisun omassa osoitteessaan). Palauttaa poistettujen määrän.
  projekteja()                  projektien määrä kohteessa (Cloudflaren raja 100, valvonta hallinta#47) tai None

- CloudflarePages ("cloudflare"): oma Pages-projekti jokaiselle sivulle, suora lataus (wrangler pages deploy).
  Avain ja tilin tunnus ympäristömuuttujista CLOUDFLARE_API_TOKEN ja CLOUDFLARE_ACCOUNT_ID. Wrangler (lukittu versio)
  asennetaan vasta ensimmäiseen julkaisuun: ajo, jossa mikään sivu ei muuttunut, ei tarvitse sitä.
- Kansio ("kansio:<polku>"): paikallinen kansio testeille (hallinta testi/rakennusajo.mjs), sivu kansioon <polku>/<projekti>/.
  Julkaisuhistoria kuten Cloudflaren julkaisukohtaiset osoitteet: <polku>/<projekti>.julkaisut/<numero>-<tunniste>/.

`sivu` on sivustoluettelon kohta (nimi, projekti, salainen_osa, testisivu …). Virheen (Julkaisuvirhe) teksti on julkista
lokia varten: ei sisältöä, osoitteita eikä salaista osaa. Wranglerin tuloste (julkaisun osoite) menee lokitiedostoon.
"""
import hashlib, json, os, re, shutil, subprocess, tempfile, threading, time, urllib.error, urllib.request

SELAIN = {"User-Agent": "SuomenMoskeijat-rakennusajo/1.0 (+https://github.com/suomen-moskeijat/pohja)"}


def polun_tunniste(polku):
    """Sivun polun (luonnoslinkin salainen osa tai "" = juuri) lyhyt tunniste julkaisuun. Tiiviste, ei polkua: salainen osa ei
    päädy julkaisun tietoihin. Salainen osa on vähintään 128 bittiä satunnaista, joten tiivisteestä ei voi päätellä sitä."""
    return hashlib.sha256(("polku:" + (polku or "")).encode()).hexdigest()[:16]


class Julkaisuvirhe(Exception):
    """Julkaisu epäonnistui. Teksti on julkista lokia varten."""


class Kansio:
    """Paikallinen kansio: sivu kopioidaan kansioon <polku>/<projekti>/ (edellinen julkaisu korvataan kerralla)."""

    def __init__(self, polku):
        self.polku = os.path.abspath(polku)

    def osoite(self, sivu):
        return f"https://{sivu['projekti']}.invalid"

    def historia(self, sivu):
        return os.path.join(self.polku, sivu["projekti"] + ".julkaisut")

    def julkaise(self, sivu, kansio, loki=None, polku=""):
        os.makedirs(self.polku, exist_ok=True)
        kohde = os.path.join(self.polku, sivu["projekti"])
        uusi = tempfile.mkdtemp(prefix=sivu["projekti"] + ".", dir=self.polku)
        try:
            shutil.copytree(kansio, uusi, dirs_exist_ok=True)
            shutil.rmtree(kohde, ignore_errors=True)
            os.rename(uusi, kohde)
        finally:
            shutil.rmtree(uusi, ignore_errors=True)
        # Julkaisuhistoria (kova linkki, ei kopiota): kuten Cloudflaren julkaisukohtainen osoite
        historia = self.historia(sivu)
        os.makedirs(historia, exist_ok=True)
        nro = max([int(n.split("-")[0]) for n in os.listdir(historia) if n.split("-")[0].isdigit()] or [0]) + 1
        shutil.copytree(kohde, os.path.join(historia, f"{nro:04d}-{polun_tunniste(polku)}"), copy_function=os.link)
        return "paikallinen kansio"

    def poista_vanhat(self, sivu, polku, loki=None):
        tunniste, historia = polun_tunniste(polku), self.historia(sivu)
        julkaisut = sorted(n for n in os.listdir(historia) if n.split("-")[0].isdigit()) if os.path.isdir(historia) else []
        poistettavat = [n for n in julkaisut[:-1] if n.split("-", 1)[1] != tunniste]  # uusin on nykyinen julkaisu
        for n in poistettavat:
            shutil.rmtree(os.path.join(historia, n))
        return len(poistettavat)

    def projekteja(self):
        try:
            return sum(1 for n in os.listdir(self.polku) if "." not in n and os.path.isdir(os.path.join(self.polku, n)))
        except OSError:
            return None


class CloudflarePages:
    """Cloudflare Pages, suora lataus. Projekti luodaan, jos sitä ei ole (tuotantohaara main, ei Git-yhteyttä)."""

    API = "https://api.cloudflare.com/client/v4/accounts/{tili}/pages/projects"
    WRANGLER = "wrangler@4.158.0"

    def __init__(self, avain=None, tili=None, ajo=""):
        # Tunnuksen tai avaimen lopussa voi olla rivinvaihto, jos se liitettiin sellaisenaan
        puhdas = lambda s: re.sub(r"\s+", "", s or "")
        self.avain = puhdas(avain if avain is not None else os.environ.get("CLOUDFLARE_API_TOKEN"))
        self.tili = puhdas(tili if tili is not None else os.environ.get("CLOUDFLARE_ACCOUNT_ID"))
        if not self.avain or not self.tili:
            raise SystemExit("CLOUDFLARE_API_TOKEN (salaisuus) tai CLOUDFLARE_ACCOUNT_ID (muuttuja) puuttuu ympäristöstä julkaisu")
        self.ajo = ajo or os.environ.get("GITHUB_RUN_ID", "")
        self.osoitteet, self.lukko = {}, threading.Lock()
        self.wrangler, self.asennus = None, threading.Lock()

    def _api(self, polku="", data=None, metodi=None):
        pyynto = urllib.request.Request(self.API.format(tili=self.tili) + polku, headers={**SELAIN, "Authorization": f"Bearer {self.avain}",
                                        "Content-Type": "application/json"}, data=json.dumps(data).encode() if data is not None else None, method=metodi)
        try:
            with urllib.request.urlopen(pyynto, timeout=30) as v:
                return v.status, json.load(v)
        except urllib.error.HTTPError as e:
            try: return e.code, json.load(e)
            except Exception: return e.code, {}
        except Exception as e:
            raise Julkaisuvirhe(f"Cloudflaren rajapinta ei vastaa ({type(e).__name__})")

    def osoite(self, sivu):
        projekti = sivu["projekti"]
        with self.lukko:
            if projekti in self.osoitteet:
                return self.osoitteet[projekti]
        koodi, v = self._api("/" + projekti)
        if koodi == 404:
            koodi, v = self._api("", {"name": projekti, "production_branch": "main"})
        if koodi != 200 or not (v.get("result") or {}).get("subdomain"):
            virheet = ", ".join(str(e.get("code")) for e in v.get("errors") or [] if isinstance(e, dict))
            raise Julkaisuvirhe(f"Pages-projektia ei voitu lukea tai luoda (HTTP {koodi}{', koodit ' + virheet if virheet else ''})")
        if ((v["result"].get("source") or {}).get("type") or ""):
            raise Julkaisuvirhe("Pages-projekti on kytketty Git-repoon; rakennusajo julkaisee vain suoralla latauksella")
        osoite = "https://" + v["result"]["subdomain"]
        with self.lukko:
            self.osoitteet[projekti] = osoite
        return osoite

    def projekteja(self):
        """Tilin Pages-projektien määrä (paras yritys: None, jos rajapinta ei vastaa)."""
        try:
            koodi, v = self._api("?per_page=10")
        except Julkaisuvirhe:
            return None
        if koodi != 200 or not isinstance(v.get("result"), list):
            return None
        maara = (v.get("result_info") or {}).get("total_count")
        return maara if isinstance(maara, int) else len(v["result"])

    def _wrangler(self):
        """Wranglerin komento. Asennetaan kerran (npm, lukittu versio), jos sitä ei ole valmiina."""
        with self.asennus:
            if not self.wrangler:
                if not shutil.which("wrangler"):
                    try:
                        koodi = subprocess.call(["npm", "install", "--global", "--silent", self.WRANGLER], timeout=600,
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception as e:
                        raise Julkaisuvirhe(f"wranglerin asennus epäonnistui ({type(e).__name__})")
                    if koodi != 0 or not shutil.which("wrangler"):
                        raise Julkaisuvirhe(f"wranglerin asennus epäonnistui (koodi {koodi})")
                self.wrangler = shutil.which("wrangler")
            return self.wrangler

    def julkaise(self, sivu, kansio, loki=None, polku=""):
        osoite = self.osoite(sivu)
        wrangler = self._wrangler()
        tyo = tempfile.mkdtemp(prefix="julkaisu-")
        tuloste = os.path.join(tyo, "wrangler.log")
        try:
            with open(tuloste, "w", encoding="utf-8") as f:
                try:
                    koodi = subprocess.call(
                        [wrangler, "pages", "deploy", os.path.abspath(kansio), "--project-name", sivu["projekti"], "--branch", "main",
                         "--commit-dirty=true", "--commit-message", f"Rakennusajo {self.ajo} polku:{polun_tunniste(polku)}"],
                        cwd=tyo, stdout=f, stderr=f, timeout=600,
                        env={**os.environ, "CLOUDFLARE_API_TOKEN": self.avain, "CLOUDFLARE_ACCOUNT_ID": self.tili, "WRANGLER_SEND_METRICS": "false"})
                except subprocess.TimeoutExpired:
                    raise Julkaisuvirhe("suora lataus ei valmistunut 10 minuutissa")
            with open(tuloste, encoding="utf-8", errors="replace") as f:
                teksti = f.read()
            if loki:
                with open(loki, "a", encoding="utf-8") as f:
                    f.write("\n== julkaisu\n" + teksti)
            if koodi != 0:
                koodit = " ".join(sorted(set(re.findall(r"\[code: \d+\]", teksti))))
                raise Julkaisuvirhe(f"suora lataus epäonnistui (koodi {koodi}{' ' + koodit if koodit else ''})")
            ladattu = re.findall(r"Uploaded (\d+) files(?: \((\d+) already uploaded\))?", teksti)
        finally:
            shutil.rmtree(tyo, ignore_errors=True)
        self._tarkista(sivu, osoite, polku)
        return f"ladattu {ladattu[-1][0]} tiedostoa, ennestään {ladattu[-1][1] or 0}" if ladattu else "ei ladattavaa"

    def _hae(self, osoite):
        """(otsakkeet, teksti) tai Julkaisuvirhe. Uusi julkaisu voi näkyä tuotanto-osoitteessa vasta hetken päästä."""
        virhe = ""
        for _ in range(12):
            try:
                with urllib.request.urlopen(urllib.request.Request(osoite, headers=SELAIN), timeout=20) as v:
                    return v.headers, v.read(400_000).decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                virhe = f"HTTP {e.code}"
            except Exception as e:
                virhe = type(e).__name__
            time.sleep(5)
        raise Julkaisuvirhe(f"julkaistu sivu ei vastaa projektin osoitteessa ({virhe})")

    def _tarkista(self, sivu, osoite, salainen):
        """Julkaistu sivu vastaa projektin osoitteessa. Piilossa olevalla sivulla hakukoneet kieltävä otsake; luonnoslinkin sivulla
        (salainen: polku, jonka alla sivu on) myös noai ja no-referrer otsakkeissa ja sivun omissa meta-tiedoissa sekä neutraali
        juuri ja robots.txt (ADR-0008, hallinta#49). Virheiden tekstissä vain tarkistuksen nimi: ei osoitetta eikä salaista osaa."""
        piilossa = bool(salainen or sivu.get("testisivu"))
        otsakkeet, teksti = self._hae(osoite + (f"/{salainen}/" if salainen else "/"))
        robots = (otsakkeet.get("X-Robots-Tag") or "").lower()
        if piilossa and "noindex" not in robots:
            raise Julkaisuvirhe("julkaistulta piilossa olevalta sivulta puuttuu X-Robots-Tag: noindex")
        if not salainen:
            return
        if "noai" not in robots or (otsakkeet.get("Referrer-Policy") or "").lower() != "no-referrer":
            raise Julkaisuvirhe("luonnoslinkin sivulta puuttuu otsake X-Robots-Tag: noai tai Referrer-Policy: no-referrer")
        if '<meta name="referrer" content="no-referrer">' not in teksti or not re.search(r'<meta name="robots" content="noindex[^"]*noai', teksti):
            raise Julkaisuvirhe("luonnoslinkin sivun omista meta-tiedoista puuttuu referrer no-referrer tai robots noindex, noai")
        _, juuri = self._hae(osoite + "/")
        _, robots_txt = self._hae(osoite + "/robots.txt")
        if salainen in juuri or not re.search(r"^User-agent: \*\s*\nDisallow: /\s*$", robots_txt, re.M):
            raise Julkaisuvirhe("luonnoslinkin osoitteen juuri ei ole neutraali (juuren sivu tai robots.txt)")

    def poista_vanhat(self, sivu, polku, loki=None):
        """Poistaa projektin julkaisut, joiden polun tunniste (julkaisun viestissä) on eri kuin nyt, paitsi nykyisen
        tuotantojulkaisun. Myös ennen tunnisteita tehdyt julkaisut poistetaan. Epäonnistunut poisto on julkaisuvirhe: sivun
        tiiviste ei päivity, joten seuraava ajo julkaisee ja yrittää poistoa uudelleen."""
        projekti, tunniste = sivu["projekti"], polun_tunniste(polku)
        koodi, v = self._api("/" + projekti)
        nykyinen = ((v.get("result") or {}).get("canonical_deployment") or {}).get("id") if koodi == 200 else None
        if not nykyinen:
            raise Julkaisuvirhe(f"Pages-projektin nykyistä julkaisua ei voitu lukea (HTTP {koodi})")
        poistettavat = []
        for sivunro in range(1, 41):  # enintään 1 000 julkaisua
            koodi, v = self._api(f"/{projekti}/deployments?per_page=25&page={sivunro}")
            if koodi != 200 or not isinstance(v.get("result"), list):
                raise Julkaisuvirhe(f"Pages-projektin julkaisuja ei voitu listata (HTTP {koodi})")
            for j in v["result"]:
                viesti = str(((j.get("deployment_trigger") or {}).get("metadata") or {}).get("commit_message") or "")
                if j.get("id") and j["id"] != nykyinen and not viesti.endswith(f"polku:{tunniste}"):
                    poistettavat.append(j["id"])
            if len(v["result"]) < 25:
                break
        for tunnus in poistettavat:
            koodi, v = self._api(f"/{projekti}/deployments/{tunnus}?force=true", metodi="DELETE")
            if koodi not in (200, 404):
                raise Julkaisuvirhe(f"vanhan julkaisun poisto epäonnistui (HTTP {koodi}, poistettu {poistettavat.index(tunnus)}/{len(poistettavat)})")
        if loki and poistettavat:
            with open(loki, "a", encoding="utf-8") as f:
                f.write(f"\n== vanhat julkaisut: poistettu {len(poistettavat)}\n")
        return len(poistettavat)


def luo(kuvaus):
    """Julkaisukohde komentorivin kuvauksesta: "cloudflare" tai "kansio:<polku>"."""
    if kuvaus == "cloudflare":
        return CloudflarePages()
    if kuvaus.startswith("kansio:") and kuvaus[7:]:
        return Kansio(kuvaus[7:])
    raise SystemExit('--kohde: "cloudflare" tai "kansio:<polku>"')
