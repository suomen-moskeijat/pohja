#!/usr/bin/env python3
"""Julkaisukohde: paikka, johon rakennusajo (rakennusajo.py) julkaisee valmiin sivun (ADR-0007).

Yksi rajapinta, kaksi sovitinta:
  osoite(sivu)                  sivun osoite kohteessa, kun sivustoluettelossa ei ole osoitetta
  julkaise(sivu, kansio, loki, polku, sivulupa)
                                julkaisee valmiin sivun kansion; palauttaa lyhyen kuvauksen julkiseen lokiin. polku: luonnoslinkin
                                salainen osa, jonka alla sivu on, tai "" (juuri); sen tunniste (polun_tunniste) kirjataan julkaisuun.
                                sivulupa: testisivu välikerroksen takana (hallinta#48): Cloudflare-sovitin asettaa ensin välikerroksen
                                avaimen (SIVULUPA_AVAIN) projektin salaisuudeksi ja tarkistaa julkaisun jälkeen, että sivu on suojattu
  poista_vanhat(sivu, polku, loki, sivulupa)
                                poistaa projektin vanhat julkaisut, joiden polku on eri (hallinta#49, ADR-0008): luonnoslinkin
                                vaihdon tai julkaisun jälkeen vanha linkki ei näytä sivua julkaisukohtaisissakaan osoitteissa
                                (Cloudflare Pages säilyttää jokaisen julkaisun omassa osoitteessaan). Palauttaa poistettujen määrän.
  projekteja()                  projektien määrä kohteessa (Cloudflaren raja 100, valvonta hallinta#47) tai None
  poista(sivu)                  poistaa sivun projektin kaikkine julkaisuineen (moskeijan poisto, hallinta#51); palauttaa kuvauksen

- CloudflarePages ("cloudflare"): oma Pages-projekti jokaiselle sivulle, suora lataus (wrangler pages deploy).
  Avain ja tilin tunnus ympäristömuuttujista CLOUDFLARE_API_TOKEN ja CLOUDFLARE_ACCOUNT_ID; testisivujen välikerroksen avain
  ympäristömuuttujasta SIVULUPA_AVAIN (sama arvo paneelin salaisuuksissa), joka asetetaan projektin salaisuudeksi julkaisun yhteydessä. Wrangler (lukittu versio)
  asennetaan vasta ensimmäiseen julkaisuun: ajo, jossa mikään sivu ei muuttunut, ei tarvitse sitä.
- Kansio ("kansio:<polku>"): paikallinen kansio testeille (hallinta testi/rakennusajo.mjs), sivu kansioon <polku>/<projekti>/.
  Julkaisuhistoria kuten Cloudflaren julkaisukohtaiset osoitteet: <polku>/<projekti>.julkaisut/<numero>-<tunniste>/.

`sivu` on sivustoluettelon kohta (nimi, projekti, salainen_osa, testisivu …). Virheen (Julkaisuvirhe) teksti on julkista
lokia varten: ei sisältöä, osoitteita eikä salaista osaa. Wranglerin tuloste (julkaisun osoite) menee lokitiedostoon.
"""
import hashlib, json, os, re, shutil, subprocess, tempfile, threading, time, urllib.error, urllib.request

SIVULUPA_AVAIN_VAHINTAAN = 32  # merkkiä (vain ASCII-kirjaimia ja numeroita), sama raja kuin välikerroksessa ja paneelissa
SELAIN = {"User-Agent": "SuomenMoskeijat-rakennusajo/1.0 (+https://github.com/suomen-moskeijat/pohja)"}


def polun_tunniste(polku, sivulupa=False):
    """Sivun polun (luonnoslinkin salainen osa tai "" = juuri) lyhyt tunniste julkaisuun. Tiiviste, ei polkua: salainen osa ei
    päädy julkaisun tietoihin. Salainen osa on vähintään 128 bittiä satunnaista, joten tiivisteestä ei voi päätellä sitä.
    Välikerroksen takana olevan testisivun (sivulupa) tunniste on eri kuin saman polun ilman välikerrosta: kun sivusta tulee
    testisivu, sen vanhat suojaamattomat julkaisut poistetaan (poista_vanhat), eivätkä ne näy julkaisukohtaisissa osoitteissa."""
    return hashlib.sha256(("polku:" + (polku or "") + ("|sivulupa" if sivulupa else "")).encode()).hexdigest()[:16]


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

    def julkaise(self, sivu, kansio, loki=None, polku="", sivulupa=False):
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
        shutil.copytree(kohde, os.path.join(historia, f"{nro:04d}-{polun_tunniste(polku, sivulupa)}"), copy_function=os.link)
        return "paikallinen kansio"

    def poista_vanhat(self, sivu, polku, loki=None, sivulupa=False):
        tunniste, historia = polun_tunniste(polku, sivulupa), self.historia(sivu)
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

    def poista(self, sivu):
        kohde = os.path.join(self.polku, sivu["projekti"])
        if not os.path.isdir(kohde):
            return "ei ollut"
        shutil.rmtree(kohde)
        shutil.rmtree(self.historia(sivu), ignore_errors=True)  # projektin kaikki julkaisut
        return "poistettu"


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

    def poista(self, sivu):
        """Poistaa projektin. Jos Cloudflare ei poista projektia, jolla on paljon julkaisuja, julkaisut poistetaan ensin."""
        projekti = sivu["projekti"]
        koodi, _ = self._api("/" + projekti, metodi="DELETE")
        if koodi == 404:
            return "ei ollut"
        if koodi == 200:
            return "poistettu"
        poistettu = 0
        for _ in range(40):  # enintään 1 000 julkaisua, 25 kerrallaan
            koodi_, v = self._api(f"/{projekti}/deployments?per_page=25")
            julkaisut = v.get("result") if koodi_ == 200 and isinstance(v.get("result"), list) else []
            if not julkaisut:
                break
            for j in julkaisut:
                if self._api(f"/{projekti}/deployments/{j.get('id')}?force=true", metodi="DELETE")[0] == 200:
                    poistettu += 1
        koodi, v = self._api("/" + projekti, metodi="DELETE")
        if koodi in (200, 404):
            return f"poistettu ({poistettu} julkaisua ensin)"
        virheet = ", ".join(str(e.get("code")) for e in v.get("errors") or [] if isinstance(e, dict))
        raise Julkaisuvirhe(f"Pages-projektia ei voitu poistaa (HTTP {koodi}{', koodit ' + virheet if virheet else ''})")

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

    def aseta_sivulupa(self, sivu):
        """Testisivun välikerroksen avain (SIVULUPA_AVAIN) projektin tuotantoympäristön salaisuudeksi ennen julkaisua: julkaisu
        saa salaisuudet luontihetkellä, joten avaimen vaihto tulee voimaan seuraavassa julkaisussa. Ilman kelvollista avainta
        testisivua ei julkaista (välikerros ei päästäisi ketään, eikä vanhaa julkaisua korvata). Avainta ei tulosteta."""
        avain = (os.environ.get("SIVULUPA_AVAIN") or "").strip()
        if len(avain) < SIVULUPA_AVAIN_VAHINTAAN or not re.fullmatch(r"[A-Za-z0-9]+", avain):
            raise Julkaisuvirhe(f"SIVULUPA_AVAIN puuttuu ympäristöstä julkaisu tai ei kelpaa (vähintään {SIVULUPA_AVAIN_VAHINTAAN} merkkiä A-Z, a-z, 0-9): "
                                "testisivua ei julkaista ilman välikerroksen avainta")
        koodi, v = self._api("/" + sivu["projekti"], {"deployment_configs": {"production": {"env_vars": {
            "SIVULUPA_AVAIN": {"type": "secret_text", "value": avain}}}}}, metodi="PATCH")
        if koodi != 200:
            virheet = ", ".join(str(e.get("code")) for e in v.get("errors") or [] if isinstance(e, dict))
            raise Julkaisuvirhe(f"välikerroksen avainta ei voitu asettaa Pages-projektiin (HTTP {koodi}{', koodit ' + virheet if virheet else ''})")

    def julkaise(self, sivu, kansio, loki=None, polku="", sivulupa=False):
        osoite = self.osoite(sivu)
        if sivulupa:
            self.aseta_sivulupa(sivu)
        wrangler = self._wrangler()
        tyo = tempfile.mkdtemp(prefix="julkaisu-")
        tuloste = os.path.join(tyo, "wrangler.log")
        try:
            with open(tuloste, "w", encoding="utf-8") as f:
                try:
                    koodi = subprocess.call(
                        [wrangler, "pages", "deploy", os.path.abspath(kansio), "--project-name", sivu["projekti"], "--branch", "main",
                         "--commit-dirty=true", "--commit-message", f"Rakennusajo {self.ajo} polku:{polun_tunniste(polku, sivulupa)}"],
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
        self._tarkista(sivu, osoite, polku, sivulupa=sivulupa)
        return f"ladattu {ladattu[-1][0]} tiedostoa, ennestään {ladattu[-1][1] or 0}" if ladattu else "ei ladattavaa"

    def _ohjaus(self, osoite):
        """(tila, otsakkeet) seuraamatta uudelleenohjausta (testisivun välikerros ohjaa paneeliin)."""
        class Ei(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        virhe = ""
        for _ in range(12):
            try:
                with urllib.request.build_opener(Ei).open(urllib.request.Request(osoite, headers=SELAIN), timeout=20) as v:
                    return v.status, v.headers
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    return e.code, e.headers
                virhe = f"HTTP {e.code}"
            except Exception as e:
                virhe = type(e).__name__
            time.sleep(5)
        raise Julkaisuvirhe(f"julkaistu sivu ei vastaa projektin osoitteessa ({virhe})")

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

    def _tarkista(self, sivu, osoite, salainen, sivulupa=False):
        """Julkaistu sivu vastaa projektin osoitteessa. Välikerroksen takana olevalla testisivulla (sivulupa) juuri ohjaa paneelin
        sivulupa-reittiin (ei näytä sivua) ja robots.txt kieltää kaiken, molemmissa X-Robots-Tag: noindex (hallinta#48).
        Muulla piilossa olevalla sivulla hakukoneet kieltävä otsake; luonnoslinkin sivulla
        (salainen: polku, jonka alla sivu on) myös noai ja no-referrer otsakkeissa ja sivun omissa meta-tiedoissa sekä neutraali
        juuri ja robots.txt (ADR-0008, hallinta#49). Virheiden tekstissä vain tarkistuksen nimi: ei osoitetta eikä salaista osaa."""
        if sivulupa:
            tila, otsakkeet = self._ohjaus(osoite + "/")
            if tila != 302 or "/api/sivulupa?paluu=" not in (otsakkeet.get("Location") or ""):
                raise Julkaisuvirhe(f"testisivu ei ole välikerroksen takana: juuri vastasi HTTP {tila} ilman ohjausta paneeliin")
            r_otsakkeet, robots_txt = self._hae(osoite + "/robots.txt")
            if "noindex" not in ", ".join(otsakkeet.get_all("X-Robots-Tag") or []).lower() or "noindex" not in ", ".join(r_otsakkeet.get_all("X-Robots-Tag") or []).lower() \
                    or not re.search(r"^User-agent: \*\s*\nDisallow: /\s*$", robots_txt, re.M):
                raise Julkaisuvirhe("testisivun välikerroksen vastauksista puuttuu X-Robots-Tag: noindex tai robots.txt-kielto")
            return
        piilossa = bool(salainen or sivu.get("testisivu"))
        otsakkeet, teksti = self._hae(osoite + (f"/{salainen}/" if salainen else "/"))
        # Otsake voi tulla monta kertaa (Pagesin oletus ja _headers): kaikki arvot. Arvot eivät ole salaisia, joten ne saa näyttää.
        kaikki = lambda nimi: ", ".join(otsakkeet.get_all(nimi) or []).lower()
        robots, viittaus = kaikki("X-Robots-Tag"), kaikki("Referrer-Policy")
        if piilossa and "noindex" not in robots:
            raise Julkaisuvirhe("julkaistulta piilossa olevalta sivulta puuttuu X-Robots-Tag: noindex")
        if not salainen:
            return
        # Selain käyttää Referrer-Policyn viimeistä tuntemaansa arvoa
        if "noai" not in robots or [x.strip() for x in viittaus.split(",") if x.strip()][-1:] != ["no-referrer"]:
            raise Julkaisuvirhe(f"luonnoslinkin sivun otsakkeet eivät ole oikein (X-Robots-Tag: {robots or '-'}; Referrer-Policy: {viittaus or '-'})")
        if '<meta name="referrer" content="no-referrer">' not in teksti or not re.search(r'<meta name="robots" content="noindex[^"]*noai', teksti):
            raise Julkaisuvirhe("luonnoslinkin sivun omista meta-tiedoista puuttuu referrer no-referrer tai robots noindex, noai")
        _, juuri = self._hae(osoite + "/")
        _, robots_txt = self._hae(osoite + "/robots.txt")
        if salainen in juuri or not re.search(r"^User-agent: \*\s*\nDisallow: /\s*$", robots_txt, re.M):
            raise Julkaisuvirhe("luonnoslinkin osoitteen juuri ei ole neutraali (juuren sivu tai robots.txt)")

    def poista_vanhat(self, sivu, polku, loki=None, sivulupa=False):
        """Poistaa projektin julkaisut, joiden polun tunniste (julkaisun viestissä) on eri kuin nyt, paitsi nykyisen
        tuotantojulkaisun. Myös ennen tunnisteita tehdyt julkaisut poistetaan. Epäonnistunut poisto on julkaisuvirhe: sivun
        tiiviste ei päivity, joten seuraava ajo julkaisee ja yrittää poistoa uudelleen."""
        projekti, tunniste = sivu["projekti"], polun_tunniste(polku, sivulupa)
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
