#!/usr/bin/env python3
"""Moskeijalista (suomenmoskeijat.fi, hallinta#52): rakennusajo rakentaa ja julkaisee sen sivustoluettelosta omaan Pages-projektiinsa.

Rakennusajo (rakennusajo.py) kokoaa listan rivit sivustoluettelosta ja sisältökansioista ja kutsuu paivita():
  - rivit: julkaistut sivut (nimi, kaupunki, sivun osoite) ja luonnokset pelkkinä niminä (käyttäjän päätös, hallinta#40:
    luonnoksen linkki paljastaisi luonnoslinkin, ADR-0008). Ehdotuksia ja testisivuja ei listata. Rivissä ei ole projektia,
    tunnusta eikä salaista osaa, joten mikään listan tiedosto ei voi vuotaa luonnoksen osoitetta.
  - Lähde .github/moskeijalista/ (Jekyll): etusivu (lista ja Lisää moskeija -lomake), ohjeet (OHJEET.md → /ohjeet/), robots.txt,
    sitemap.xml, llms.txt ja 404. Tyylit ja fontit ovat sivupohjan omat (assets/css/sivu.css, assets/fontit): samat kortit,
    napit ja lomakkeen kentät kuin moskeijoiden sivuilla.
  - Lomake lähettää pyynnön paneelin reittiin /api/moskeijapyynto (Turnstile sivupohjan julkisella avaimella ja rajoitus
    paneelissa). Pyyntö ei luo sivua: ylläpitäjä hyväksyy sen paneelissa (Ylläpito → Pyynnöt → Luo sivu, hallinta#51:n Uusi moskeija).
  - Versiot: main-haaran ajo julkaisee tuotannon listan (projekti sm-moskeijalista, osoite https://suomenmoskeijat.fi, paneeli
    hallinta), testi-haaran ajo testiversion (sm-moskeijalista-testi, piilossa hakukoneilta, lomake testipaneeliin ilman
    Turnstilea). Molemmat näyttävät sivupohjan versiolla main julkaistavat sivut, joten testiversio näyttää saman kuin tuotanto.
  - Lista rakennetaan vain, kun sen syötteet muuttuvat (rivit, asetukset ja lähdetiedostot): tiiviste tiedostossa
    <tiivisteluettelon kansio>/moskeijalista.json (julkinen välimuisti: vain tiiviste).
  - suomenmoskeijat.fi ja www liitetään projektiin Cloudflaressa käsin (käyttäjän toimi): rakennusajo ei lisää niitä.
Julkinen loki: vain kuvaus ja määrät; Jekyllin tuloste lokitiedostoon.
"""
import hashlib, json, os, re, shutil, subprocess, tempfile, time

POHJA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LAHDE = os.path.join(POHJA, ".github", "moskeijalista")
GEMFILE = os.path.join(POHJA, ".github", "rakennus", "Gemfile")
NIMI = "moskeijalista"  # varattu: sivustoluettelossa ei saa olla tämän nimistä sivua
PROJEKTI = {"main": "sm-moskeijalista", "testi": "sm-moskeijalista-testi"}
OSOITE = {"main": "https://suomenmoskeijat.fi", "testi": "https://sm-moskeijalista-testi.pages.dev"}
# Sivupohjan tiedostot, jotka tulevat listalle sellaisinaan (tyylit, fontit) ja ohjeet
POHJASTA = [os.path.join("assets", "css", "sivu.css"), os.path.join("assets", "fontit")]
OHJEET = os.path.join(POHJA, "OHJEET.md")
MUOTO = 1


class Listavirhe(Exception):
    """Listan rakennus tai julkaisu epäonnistui. Teksti on julkista lokia varten."""


def turnstile_avain():
    """Sivupohjan julkinen Turnstile-avain (_config.yml turnstile_avain), sama kuin moskeijoiden lomakkeissa."""
    try:
        with open(os.path.join(POHJA, "_config.yml"), encoding="utf-8") as f:
            m = re.search(r"^turnstile_avain:\s*\"?([A-Za-z0-9_-]+)", f.read(), re.M)
        return m.group(1) if m else ""
    except OSError:
        return ""


def asetukset(versio, paneeli):
    testi = versio != "main"
    return {"versio": versio, "projekti": PROJEKTI[versio], "url": OSOITE[versio], "paneeli": paneeli.rstrip("/"), "testi": testi,
            "turnstile": "" if testi else turnstile_avain()}


def kaupungeittain(rivit):
    """Rivit kaupungeittain (aakkosjärjestys) listan sivulle."""
    jarj = sorted(rivit, key=lambda r: ((r.get("kaupunki") or "").lower(), r["nimi"].lower()))
    kaupungit = []
    for r in jarj:
        k = r.get("kaupunki") or "Muut"
        if not kaupungit or kaupungit[-1]["nimi"] != k:
            kaupungit.append({"nimi": k, "sivut": []})
        kaupungit[-1]["sivut"].append(r)
    return {"kaupungit": kaupungit, "julkaistut": [r for r in jarj if r.get("osoite")], "maara": len(jarj),
            "julkaistuja": sum(1 for r in jarj if r.get("osoite"))}


def _tiiviste(polut):
    h = hashlib.sha256()
    for alku in polut:
        kaikki = [alku] if os.path.isfile(alku) else sorted(os.path.join(j, n) for j, _, t in os.walk(alku) for n in t)
        for p in kaikki:
            h.update(os.path.relpath(p, POHJA).encode() + b"\0")
            with open(p, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()


def tiiviste(rivit, a):
    return hashlib.sha256(json.dumps({"muoto": MUOTO, "rivit": rivit, "asetukset": a,
                                      "lahde": _tiiviste([LAHDE, OHJEET] + [os.path.join(POHJA, p) for p in POHJASTA])}, sort_keys=True).encode()).hexdigest()


def rakenna(rivit, a, ulos, loki=None):
    """Rakentaa listan kansioon ulos. Palauttaa tiedostojen määrän."""
    tyo = tempfile.mkdtemp(prefix="moskeijalista-")
    try:
        lahde = os.path.join(tyo, "lahde")
        shutil.copytree(LAHDE, lahde)
        for p in POHJASTA:
            a_, b = os.path.join(POHJA, p), os.path.join(lahde, p)
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copytree(a_, b) if os.path.isdir(a_) else shutil.copy2(a_, b)
        # Ohjeet: OHJEET.md sivuksi /ohjeet/ (otsikko ohjeiden ensimmäisestä rivistä)
        with open(OHJEET, encoding="utf-8") as f:
            ohjeet = f.read()
        otsikko = (re.match(r"#\s+(.+)", ohjeet) or [None, "Ohjeet"])[1].strip()
        os.makedirs(os.path.join(lahde, "ohjeet"), exist_ok=True)
        with open(os.path.join(lahde, "ohjeet", "index.md"), "w", encoding="utf-8") as f:
            f.write(f"---\nlayout: ohje\ntitle: {json.dumps(otsikko, ensure_ascii=False)}\n---\n{ohjeet}")
        os.makedirs(os.path.join(lahde, "_data"), exist_ok=True)
        with open(os.path.join(lahde, "_data", "lista.json"), "w", encoding="utf-8") as f:
            json.dump(kaupungeittain(rivit), f, ensure_ascii=False)
        with open(os.path.join(lahde, "_asetukset.yml"), "w", encoding="utf-8") as f:
            json.dump({"url": a["url"], "paneeli": a["paneeli"], "testi": a["testi"], "turnstile_avain": a["turnstile"]}, f)  # JSON on YAMLia
        if a["testi"]:  # testiversio piiloon hakukoneilta myös otsakkeella (julkaisukohteen tarkistus: X-Robots-Tag noindex)
            with open(os.path.join(lahde, "_headers"), "w", encoding="utf-8") as f:
                f.write("/*\n  X-Robots-Tag: noindex, nofollow\n")
        shutil.rmtree(ulos, ignore_errors=True)
        kohde = open(loki, "a", encoding="utf-8") if loki else subprocess.DEVNULL
        try:
            koodi = subprocess.call(["bundle", "exec", "jekyll", "build", "-s", lahde, "-d", ulos, "--config",
                                     f"{lahde}/_config.yml,{lahde}/_asetukset.yml"], cwd=lahde, stdout=kohde, stderr=kohde,
                                    env={**os.environ, "BUNDLE_GEMFILE": GEMFILE, "JEKYLL_ENV": "production"}, timeout=600)
        finally:
            if loki: kohde.close()
        if koodi != 0:
            raise Listavirhe(f"Jekyll epäonnistui (koodi {koodi})")
        return sum(len(t) for _, _, t in os.walk(ulos))
    finally:
        shutil.rmtree(tyo, ignore_errors=True)


def paivita(rivit, versio, paneeli, kohde, tila, loki=None, julkaisuvirhe=Exception):
    """Rakentaa ja julkaisee listan, jos sen syötteet muuttuivat. tila: tiivisteen tiedosto. Palauttaa { muuttui, kuvaus }."""
    a = asetukset(versio, paneeli)
    uusi = tiiviste(rivit, a)
    try:
        with open(tila, encoding="utf-8") as f:
            if json.load(f).get("tiiviste") == uusi:
                return {"muuttui": False, "kuvaus": "ei muutoksia"}
    except (OSError, ValueError, AttributeError):
        pass
    tyo = tempfile.mkdtemp(prefix="moskeijalista-valmis-")
    try:
        t0 = time.time()
        ulos = os.path.join(tyo, "valmis")
        maara = rakenna(rivit, a, ulos, loki)
        t1 = time.time()
        try:
            julkaisu = kohde.julkaise({"nimi": NIMI, "projekti": a["projekti"], "testisivu": a["testi"]}, ulos, loki, polku="")
        except julkaisuvirhe as e:
            raise Listavirhe(f"julkaisu: {e}")
    finally:
        shutil.rmtree(tyo, ignore_errors=True)
    os.makedirs(os.path.dirname(os.path.abspath(tila)), exist_ok=True)
    with open(tila, "w", encoding="utf-8") as f:
        json.dump({"muoto": MUOTO, "tiiviste": uusi}, f)
    k = kaupungeittain(rivit)
    return {"muuttui": True, "kuvaus": f"rakennettu ja julkaistu ({k['julkaistuja']} julkaistua, {k['maara'] - k['julkaistuja']} luonnosta; "
                                       f"rakennus {t1 - t0:.1f} s, {maara} tiedostoa; julkaisu {time.time() - t1:.1f} s, {julkaisu})"}
