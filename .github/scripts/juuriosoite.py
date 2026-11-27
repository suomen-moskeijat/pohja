#!/usr/bin/env python3
"""Juuriosoite suomenmoskeijat.fi: rakennusajo julkaisee sinne neutraalin sivun (käyttäjän päätös 27.11.2026, hallinta ADR-0006).

Moskeijalista ja sen Lisää moskeija -lomake (hallinta#52) on otettu pois: käyttäjällä on etusivulle muita suunnitelmia, ja
ylläpitäjä luo moskeijat paneelissa (Ylläpito → Uusi moskeija). Lähteet ovat gitin historiassa.

Rakennusajo (rakennusajo.py) kutsuu paivita() ajon lopuksi:
  - Juuriosoitteen Pages-projekteihin (main: sm-moskeijalista, osoitteet suomenmoskeijat.fi ja www, liitetty projektiin
    Cloudflaressa käsin; testi: sm-moskeijalista-testi) julkaistaan sama neutraali sivu kuin luonnoslinkin juuressa
    (rakenna_sivu.neutraali_juuri: "Tällä osoitteella ei ole julkista sivua", noindex, robots.txt kieltää kaiken, X-Robots-Tag).
    Ei listaa, lomaketta, ohjeita, sitemapia eikä llms.txt:tä.
  - Julkaisu korvaa projektin koko sisällön (vanhan listan /ohjeet/ ym. eivät jää), ja projektin kaikki vanhat julkaisut
    poistetaan (julkaisukohde.poista_vanhat kaikki=True): vanha lista ei näy julkaisukohtaisissakaan osoitteissa.
  - Julkaistaan vain, kun neutraali sivu muuttuu: tiiviste tiedostossa <tiivisteluettelon kansio>/juuriosoite.json (julkinen
    välimuisti: vain tiiviste). Vanhan listan tiiviste (moskeijalista.json) poistetaan, joten ensimmäinen ajo vaihtaa sisällön.
  - NIMI ja PROJEKTI ovat varattuja: sivustoluettelossa ei saa olla sivua tällä nimellä tai näillä projekteilla.
Julkinen loki: vain kuvaus ja määrät.
"""
import hashlib, json, os, shutil, tempfile, time

import rakenna_sivu

NIMI = "moskeijalista"  # varattu: sivustoluettelossa ei saa olla tämän nimistä sivua (vanhan listan nimi)
PROJEKTI = {"main": "sm-moskeijalista", "testi": "sm-moskeijalista-testi"}
TILA = "juuriosoite.json"
VANHA_TILA = "moskeijalista.json"  # vanhan listan tiiviste
MUOTO = 1


class Juurivirhe(Exception):
    """Juuriosoitteen julkaisu epäonnistui. Teksti on julkista lokia varten."""


def varattu(sivut):
    """Sivustoluettelon sivu, jonka nimi tai projekti on varattu juuriosoitteelle; muuten None."""
    return next((s for s in sivut if s["nimi"] == NIMI or s["projekti"] in PROJEKTI.values()), None)


def tiiviste():
    return hashlib.sha256(json.dumps({"muoto": MUOTO, "sivu": rakenna_sivu.JUURI_SIVU, "robots": rakenna_sivu.JUURI_ROBOTS,
                                      "otsakkeet": rakenna_sivu.OTSAKKEET}, sort_keys=True).encode()).hexdigest()


def paivita(versio, kohde, kansio, loki=None, julkaisuvirhe=Exception):
    """Julkaisee neutraalin sivun versiolle (main/testi), jos se muuttui. kansio: tiivisteen kansio. Palauttaa { muuttui, kuvaus }."""
    tila, uusi = os.path.join(kansio, TILA), tiiviste()
    try:
        with open(tila, encoding="utf-8") as f:
            if json.load(f).get("tiiviste") == uusi:
                return {"muuttui": False, "kuvaus": "ei muutoksia"}
    except (OSError, ValueError, AttributeError):
        pass
    sivu = {"nimi": NIMI, "projekti": PROJEKTI[versio], "testisivu": True}  # testisivu: piilossa (julkaisun tarkistus vaatii noindex)
    tyo = tempfile.mkdtemp(prefix="juuriosoite-")
    try:
        t0 = time.time()
        rakenna_sivu.neutraali_juuri(tyo)
        try:
            julkaisu = kohde.julkaise(sivu, tyo, loki, polku="")
            poistettu = kohde.poista_vanhat(sivu, "", loki, kaikki=True)
        except julkaisuvirhe as e:
            raise Juurivirhe(f"julkaisu: {e}")
    finally:
        shutil.rmtree(tyo, ignore_errors=True)
    os.makedirs(kansio, exist_ok=True)
    with open(tila, "w", encoding="utf-8") as f:
        json.dump({"muoto": MUOTO, "tiiviste": uusi}, f)
    try:
        os.remove(os.path.join(kansio, VANHA_TILA))
    except OSError:
        pass
    return {"muuttui": True, "kuvaus": f"neutraali sivu julkaistu ({julkaisu}; poistettu {poistettu} vanhaa julkaisua; {time.time() - t0:.1f} s)"}
