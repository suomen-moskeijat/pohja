#!/usr/bin/env python3
"""Poistaa moskeijan sivun (hallinta#51, ADR-0006). Käynnistetään paneelista (Ylläpito → moskeija → Poista) tai käsin.

    python3 poista_moskeija.py --sisalto <sisältörepon kansio> --nimi <moskeija> [--syy ei] [--kohde cloudflare|kansio:<polku>] [--tallenna]

- Sisältörepon moskeija (kansio moskeijat/<nimi>/): kansio ja sivustoluettelon rivi poistetaan yhtenä committina, ja sen jälkeen
  sivun Pages-projekti poistetaan julkaisukohteesta (julkaisukohde.py). Testisivua ei poisteta.
- Vanhan julkaisun moskeija (siirtämätön, oma moskeijarepo): repo poistetaan kuten ennen (MOSKEIJA_AVAIN, GitHubin rajapinta).
- Kummassakin moskeijat.csv (sisältörepossa): jos moskeija ei halua sivua (--syy ei), tila "ei", jottei sivua luoda uudelleen;
  muuten luonnoksen, ehdotuksen tai oman sivun tila tyhjäksi (sivun voi luoda myöhemmin uudelleen samalla tunnuksella).
Ilman --tallenna kuivaharjoitus: tiedostot muutetaan sisältörepon kansiossa, mutta mitään ei tallenneta eikä poisteta.

Ympäristö: MOSKEIJA_AVAIN, ORG, GITHUB_API (oletus https://api.github.com); Cloudflare: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID.
Julkiseen lokiin vain tunnus ja tulos.
"""
import argparse, glob, json, os, re, shutil, sys, urllib.error, urllib.request

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import julkaisukohde
import sisaltorepo

VARATUT = {"pohja", "hallinta", ".github", "sisalto"}


def api(polku, metodi="GET"):
    perus = os.environ.get("GITHUB_API", "https://api.github.com").rstrip("/")
    pyynto = urllib.request.Request(perus + polku, method=metodi, headers={
        "Authorization": f"Bearer {os.environ.get('MOSKEIJA_AVAIN', '')}", "Accept": "application/vnd.github+json", "User-Agent": "suomen-moskeijat"})
    with urllib.request.urlopen(pyynto, timeout=30) as v:
        teksti = v.read()
        return json.loads(teksti) if teksti else {}


def merkitse_listaan(sisalto, nimi, syy):
    """moskeijat.csv: poistettu sivu → tila tyhjäksi; jos moskeija ei halua sivua, tila "ei". Palauttaa, muuttuiko lista."""
    try:
        sarakkeet, rivit = sisaltorepo.lue_csv(sisalto)
    except SystemExit:
        return False  # listaa ei ole: ei merkittävää
    muuttui = False
    for r in rivit:
        if (r.get("repo") or "").strip().lower() == nimi.lower():
            uusi = "ei" if syy == "ei" else ("" if r.get("tila") in ("luonnos", "ehdotus", "oma") else r.get("tila"))
            muuttui |= uusi != r.get("tila")
            r["tila"] = uusi
    if muuttui:
        sisaltorepo.kirjoita_csv(sisalto, sarakkeet, rivit)
    return muuttui


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--sisalto", required=True)
    p.add_argument("--nimi", default=os.environ.get("REPO", ""))
    p.add_argument("--syy", default=os.environ.get("SYY", ""), help='"ei" = moskeija ei halua sivua')
    p.add_argument("--kohde", default="cloudflare", help='julkaisukohde: "cloudflare" tai "kansio:<polku>"')
    p.add_argument("--tallenna", action="store_true", help="tallenna ja poista (muuten kuivaharjoitus)")
    a = p.parse_args(argv)
    nimi, syy, org = a.nimi.strip(), a.syy.strip(), os.environ.get("ORG", "suomen-moskeijat")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", nimi) or nimi.lower() in VARATUT:
        raise SystemExit(f"Ei poisteta: {nimi!r}")
    kuiva = "" if a.tallenna else " (kuivaharjoitus: ei tallennettu eikä poistettu)"
    kansio = sisaltorepo.kansio(a.sisalto, nimi)

    if os.path.isdir(kansio):
        # Sisältörepon moskeija: kansio ja sivustoluettelon rivi pois, sitten Pages-projekti
        if not glob.glob(os.path.join(kansio, "_moskeijat", "*.md")):
            raise SystemExit("Ei moskeijan kansio (_moskeijat/*.md puuttuu)")
        sivu = sisaltorepo.sivu(a.sisalto, nimi)
        if sivu and sivu.get("testisivu"):
            raise SystemExit(f"{nimi} on testisivu: sitä ei poisteta")
        shutil.rmtree(kansio)
        sisaltorepo.poista_sivu(a.sisalto, nimi)
        merkitse_listaan(a.sisalto, nimi, syy)
        if a.tallenna:
            sisaltorepo.tallenna(a.sisalto, f"Poista moskeija: {nimi}", [f"moskeijat/{nimi}", sisaltorepo.LUETTELO, sisaltorepo.MOSKEIJAT_CSV])
        print(f"{nimi}: kansio ja sivustoluettelon rivi poistettu sisältöreposta{kuiva}", flush=True)
        if not sivu:
            print(f"{nimi}: ei sivustoluettelossa, joten Pages-projektia ei ole", flush=True)
        elif not a.tallenna:
            print(f"{nimi}: Pages-projekti poistettaisiin{kuiva}", flush=True)
        else:
            try:
                tulos = julkaisukohde.luo(a.kohde).poista(sivu)
            except julkaisukohde.Julkaisuvirhe as e:
                raise SystemExit(f"{nimi}: sisältö poistettiin, mutta Pages-projektin poisto epäonnistui ({e}). "
                                 f"Poista projekti {sivu.get('projekti')} Cloudflaressa (Workers & Pages).")
            print(f"{nimi}: Pages-projekti {tulos}", flush=True)
    else:
        # Vanhan julkaisun moskeija: oma moskeijarepo (siirtämätön moskeija)
        if not os.environ.get("MOSKEIJA_AVAIN"):
            raise SystemExit("MOSKEIJA_AVAIN puuttuu (vanhan julkaisun moskeijarepon poisto)")
        try:
            tiedostot = api(f"/repos/{org}/{nimi}/contents/_moskeijat")
        except urllib.error.HTTPError as e:
            raise SystemExit(f"Moskeijaa ei löytynyt sisältöreposta eikä vanhasta julkaisusta ({e.code})")
        if not isinstance(tiedostot, list) or not any(t.get("name", "").endswith(".md") for t in tiedostot):
            raise SystemExit("Ei moskeijan repo (_moskeijat/*.md puuttuu)")
        if a.tallenna:
            api(f"/repos/{org}/{nimi}", "DELETE")
        print(f"{nimi}: vanhan julkaisun moskeijarepo poistettu{kuiva}", flush=True)
        if merkitse_listaan(a.sisalto, nimi, syy) and a.tallenna:
            sisaltorepo.tallenna(a.sisalto, f"Moskeijalista: {nimi} poistettu", [sisaltorepo.MOSKEIJAT_CSV])
    if syy == "ei":
        print(f"{nimi}: merkitty listaan, ettei moskeija halua sivua", flush=True)


if __name__ == "__main__":
    main()
