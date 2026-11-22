#!/usr/bin/env python3
"""Julkaisukohde: paikka, johon rakennusajo (rakennusajo.py) julkaisee valmiin sivun (ADR-0007).

Yksi rajapinta, kaksi sovitinta:
  osoite(sivu)                  sivun osoite kohteessa, kun sivustoluettelossa ei ole osoitetta
  julkaise(sivu, kansio, loki)  julkaisee valmiin sivun kansion; palauttaa lyhyen kuvauksen julkiseen lokiin

- CloudflarePages ("cloudflare"): oma Pages-projekti jokaiselle sivulle, suora lataus (wrangler pages deploy).
  Avain ja tilin tunnus ympäristömuuttujista CLOUDFLARE_API_TOKEN ja CLOUDFLARE_ACCOUNT_ID.
- Kansio ("kansio:<polku>"): paikallinen kansio testeille (hallinta testi/rakennusajo.mjs), sivu kansioon <polku>/<projekti>/.

`sivu` on sivustoluettelon kohta (nimi, projekti, salainen_osa, testisivu …). Virheen (Julkaisuvirhe) teksti on julkista
lokia varten: ei sisältöä, osoitteita eikä salaista osaa. Wranglerin tuloste (julkaisun osoite) menee lokitiedostoon.
"""
import json, os, re, shutil, subprocess, tempfile, threading, time, urllib.error, urllib.request

SELAIN = {"User-Agent": "SuomenMoskeijat-rakennusajo/1.0 (+https://github.com/suomen-moskeijat/pohja)"}


class Julkaisuvirhe(Exception):
    """Julkaisu epäonnistui. Teksti on julkista lokia varten."""


class Kansio:
    """Paikallinen kansio: sivu kopioidaan kansioon <polku>/<projekti>/ (edellinen julkaisu korvataan kerralla)."""

    def __init__(self, polku):
        self.polku = os.path.abspath(polku)

    def osoite(self, sivu):
        return f"https://{sivu['projekti']}.invalid"

    def julkaise(self, sivu, kansio, loki=None):
        os.makedirs(self.polku, exist_ok=True)
        kohde = os.path.join(self.polku, sivu["projekti"])
        uusi = tempfile.mkdtemp(prefix=sivu["projekti"] + ".", dir=self.polku)
        try:
            shutil.copytree(kansio, uusi, dirs_exist_ok=True)
            shutil.rmtree(kohde, ignore_errors=True)
            os.rename(uusi, kohde)
        finally:
            shutil.rmtree(uusi, ignore_errors=True)
        return "paikallinen kansio"


class CloudflarePages:
    """Cloudflare Pages, suora lataus. Projekti luodaan, jos sitä ei ole (tuotantohaara main, ei Git-yhteyttä)."""

    API = "https://api.cloudflare.com/client/v4/accounts/{tili}/pages/projects"

    def __init__(self, avain=None, tili=None, ajo=""):
        # Tunnuksen tai avaimen lopussa voi olla rivinvaihto, jos se liitettiin sellaisenaan
        puhdas = lambda s: re.sub(r"\s+", "", s or "")
        self.avain = puhdas(avain if avain is not None else os.environ.get("CLOUDFLARE_API_TOKEN"))
        self.tili = puhdas(tili if tili is not None else os.environ.get("CLOUDFLARE_ACCOUNT_ID"))
        if not self.avain or not self.tili:
            raise SystemExit("CLOUDFLARE_API_TOKEN (salaisuus) tai CLOUDFLARE_ACCOUNT_ID (muuttuja) puuttuu ympäristöstä julkaisu")
        self.ajo = ajo or os.environ.get("GITHUB_RUN_ID", "")
        self.osoitteet, self.lukko = {}, threading.Lock()

    def _api(self, polku="", data=None):
        pyynto = urllib.request.Request(self.API.format(tili=self.tili) + polku, headers={**SELAIN, "Authorization": f"Bearer {self.avain}",
                                        "Content-Type": "application/json"}, data=json.dumps(data).encode() if data is not None else None)
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

    def julkaise(self, sivu, kansio, loki=None):
        osoite = self.osoite(sivu)
        tyo = tempfile.mkdtemp(prefix="julkaisu-")
        tuloste = os.path.join(tyo, "wrangler.log")
        try:
            with open(tuloste, "w", encoding="utf-8") as f:
                try:
                    koodi = subprocess.call(
                        ["wrangler", "pages", "deploy", os.path.abspath(kansio), "--project-name", sivu["projekti"], "--branch", "main",
                         "--commit-dirty=true", "--commit-message", f"Rakennusajo {self.ajo}".strip()],
                        cwd=tyo, stdout=f, stderr=f, timeout=600,
                        env={**os.environ, "CLOUDFLARE_API_TOKEN": self.avain, "CLOUDFLARE_ACCOUNT_ID": self.tili, "WRANGLER_SEND_METRICS": "false"})
                except subprocess.TimeoutExpired:
                    raise Julkaisuvirhe("suora lataus ei valmistunut 10 minuutissa")
                except FileNotFoundError:
                    raise Julkaisuvirhe("wrangler puuttuu")
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
        self._tarkista(sivu, osoite)
        return f"ladattu {ladattu[-1][0]} tiedostoa, ennestään {ladattu[-1][1] or 0}" if ladattu else "ei ladattavaa"

    def _tarkista(self, sivu, osoite):
        """Sivu vastaa projektin osoitteessa, ja piilossa olevalla sivulla on hakukoneet kieltävä otsake (ADR-0008)."""
        salainen = str(sivu.get("salainen_osa") or "")
        piilossa = bool(salainen or sivu.get("testisivu"))
        virhe = ""
        for _ in range(12):
            try:
                with urllib.request.urlopen(urllib.request.Request(osoite + (f"/{salainen}/" if salainen else "/"), headers=SELAIN), timeout=20) as v:
                    robots = v.headers.get("X-Robots-Tag") or ""
                    if piilossa and "noindex" not in robots.lower():
                        raise Julkaisuvirhe("julkaistulta piilossa olevalta sivulta puuttuu X-Robots-Tag: noindex")
                    return
            except urllib.error.HTTPError as e:
                virhe = f"HTTP {e.code}"
            except Julkaisuvirhe:
                raise
            except Exception as e:
                virhe = type(e).__name__
            time.sleep(5)
        raise Julkaisuvirhe(f"julkaistu sivu ei vastaa projektin osoitteessa ({virhe})")


def luo(kuvaus):
    """Julkaisukohde komentorivin kuvauksesta: "cloudflare" tai "kansio:<polku>"."""
    if kuvaus == "cloudflare":
        return CloudflarePages()
    if kuvaus.startswith("kansio:") and kuvaus[7:]:
        return Kansio(kuvaus[7:])
    raise SystemExit('--kohde: "cloudflare" tai "kansio:<polku>"')
