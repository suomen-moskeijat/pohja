#!/usr/bin/env python3
"""Lisää uuden moskeijan: luo sille repon mallista ja julkaisee sivun.

Käyttö GitHubissa: pohja → Actions → "Lisää moskeija" → Run workflow.
Kokeilu paikallisesti (ei luo mitään GitHubiin):
    python3 .github/scripts/lisaa_moskeija.py --kuiva /tmp/kokeilu --nimi "..." --kaupunki "..." [--mawaqit ...]

Tiedot täydennetään automaattisesti:
- Mawaqit: nimi, koordinaatit, Jumuah; ajat, iqamah ja kuvat haetaan julkaisussa.
- Masjidbox: nimi ja osoite; ajat ja iqamah haetaan julkaisussa.
- Muuten koordinaatit osoitteesta (OpenStreetMap Nominatim).
Ympäristömuuttujat GitHubissa: MOSKEIJA_AVAIN (organisaation avain), ORG.
"""
import argparse
import base64
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

POHJA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SELAIN = {"User-Agent": "SuomenMoskeijat/1.0 (+https://github.com/suomen-moskeijat/pohja)"}


def hae(osoite, otsakkeet=None):
    req = urllib.request.Request(osoite, headers={**SELAIN, **(otsakkeet or {})})
    with urllib.request.urlopen(req, timeout=30) as v:
        return v.read().decode("utf-8", "replace")


def slugiksi(teksti):
    t = unicodedata.normalize("NFKD", teksti.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def tunnus(arvo, palvelu):
    """Hyväksyy tunnuksen, osoitteen tai upotuskoodin (esim. mawaqit.net/en/w/<tunnus>?...)."""
    arvo = (arvo or "").strip()
    if not arvo:
        return ""
    if palvelu == "mawaqit":
        m = re.search(r"mawaqit\.net/(?:[a-z]{2}/)?(?:w/|m/)?([A-Za-z0-9-]+)", arvo)
    else:
        m = re.search(r"masjidbox\.com/prayer-times/([A-Za-z0-9-]+)", arvo)
    return m.group(1) if m else re.sub(r"[^A-Za-z0-9-]", "", arvo)


# ------------------------------------------------------------- tietolähteet
def mawaqit_tiedot(t):
    sivu = hae("https://mawaqit.net/fi/" + urllib.parse.quote(t))
    d = json.loads(re.search(r"(?:let|var|const)\s+confData\s*=\s*(\{.*?\});\s*\n", sivu, re.S).group(1))
    return {"nimi": d.get("name") or "", "lat": d.get("latitude"), "lon": d.get("longitude"),
            "juma": (d.get("jumua") or "").replace(":", "."), "puhelin": d.get("phone") or "",
            "sahkoposti": d.get("email") or "", "nettisivu": d.get("site") or ""}


def masjidbox_tiedot(t):
    sivu = hae("https://masjidbox.com/prayer-times/" + urllib.parse.quote(t))
    raaka = re.search(r'window\.REDUX_STATE\s*=\s*(["\'])(.*?)\1', sivu, re.S).group(2)
    raaka = re.sub(r"%u([0-9A-Fa-f]{4})", lambda x: chr(int(x.group(1), 16)), raaka)
    a = json.loads(urllib.parse.unquote(raaka, encoding="latin-1")).get("masjidbox", {}).get("masjidboxAthany") or {}
    return {"nimi": (a.get("name") or "").replace(" - ", " "), "osoite": a.get("address") or ""}


def koordinaatit(osoite, kaupunki):
    for haku in [f"{osoite}, {kaupunki}, Finland" if osoite else None, f"{kaupunki}, Finland"]:
        if not haku:
            continue
        try:
            tulos = json.loads(hae("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
                                   + urllib.parse.quote(haku)))
            if tulos:
                return round(float(tulos[0]["lat"]), 6), round(float(tulos[0]["lon"]), 6)
        except Exception as e:
            print(f"  koordinaatteja ei saatu ({haku}): {e}", file=sys.stderr)
        time.sleep(1)  # Nominatimin käyttöehto: enintään 1 haku sekunnissa
    return 0, 0


# ------------------------------------------------------------- tiedostot
def yaml_str(s):
    return json.dumps(s or "", ensure_ascii=False)


def tiedostot(t, repo, org):
    """{polku: sisältö} uuden moskeijan repoon."""
    m = os.path.join(POHJA, "malli")
    lue = lambda p: open(os.path.join(m, p), encoding="utf-8").read()
    perus = f"https://{org.lower()}.github.io"
    config = (f"# {t['nimi']} – sivun asetukset\n"
              f"# Ulkoasu, rukousaikojen ja Instagramin haku: https://github.com/{org}/pohja\n"
              f"title: {yaml_str(t['nimi'])}\n"
              f"description: {yaml_str(t['nimi'] + ', ' + (t['osoite'] or t['kaupunki']) + '. Rukousajat, tapahtumat ja toiminta.')}\n"
              f"moskeija: {t['slug']}     # tiedosto _moskeijat/{t['slug']}.md\n\n"
              f"# Osoite: {perus}/{repo}/\n"
              f"# Omalla verkkotunnuksella (esim. moskeija.fi): url: \"https://moskeija.fi\" ja baseurl: \"\"\n"
              f"url: \"{perus}\"\nbaseurl: \"/{repo}\"\n")
    lahde_kommentti = {"mawaqit": "Mawaqitista automaattisesti (adhan, iqamah, Jumuah, kuvat)",
                       "masjidbox": "Masjidboxista automaattisesti (adhan, iqamah, Jumuah)",
                       "": "rukousajat.fi (Helsinki/Espoo/Vantaa) tai laskenta sijainnista"}[t["lahde"]]
    md = f"""---
# Lisätty automaattisesti. Täydennä ja korjaa tietoja Pages CMS:ssä (https://app.pagescms.org).
title: {yaml_str(t['nimi'])}
slug: {t['slug']}
kaupunki: {yaml_str(t['kaupunki'])}
osoite: {yaml_str(t['osoite'] or t['kaupunki'])}
sijainti: {{ lat: {t['lat']}, lon: {t['lon']} }}

puhelin: {yaml_str(t['puhelin'])}
whatsapp: {yaml_str(t['whatsapp'])}
sahkoposti: {yaml_str(t['sahkoposti'])}
nettisivu: {yaml_str(t['nettisivu'])}
kielet: [suomi]
juma: {yaml_str(t['juma'])}

# Rukousajat: {lahde_kommentti}
rukousajat:
  lahde: {yaml_str(t['lahde'])}
  tunnus: {yaml_str(t['tunnus'])}
  iqamah_oletus: {{ fajr: 10, dhuhr: 10, asr: 10, maghrib: 5, isha: 10 }}

some:
  instagram: {yaml_str(t['instagram'])}
  facebook: ""
  youtube: {yaml_str(t['youtube'])}      # uusimmat videot näkyvät sivulla
  tiktok: ""
  telegram: {yaml_str(t['telegram'])}     # julkisen kanavan julkaisut näkyvät sivulla
  snapchat: ""
  x: ""
  threads: ""
  whatsapp_kanava: ""

teema:
  logo: ""            # ilman logoa yläpalkissa näkyy moskeijan nimi
  hero: vaalea
  # Omat värit (tyhjä = pohjan kulta-ruskea), esim. paa "#123d30", korostus "#5fae8a", korostus_vaalea "#e7f4ee"
  paa: ""
  korostus: ""
  korostus_vaalea: ""

hero_tunniste: {{ fi: {yaml_str(t['kaupunki'])} }}
esittely: {{ fi: "Rukouksen, oppimisen ja yhteisön paikka." }}

# Etusivun yläosa: tausta kuvio | kuva | vari, napit (enintään 2):
# lapsi, toiminta, rukousajat, lahjoita, yhteys, oma tai oman sivun nimi
alku:
  tausta: kuvio
  kuva: ""
  napit: [toiminta, yhteys]

# Yhteiset artikkelit (islaminusko.fi, lähdemerkinnällä). Tyhjä lista = vain omat artikkelit.
artikkelit:
  lahteet: [islaminusko]

# Valikosta piilotettavat sivut, esim. [tapahtumat]. Lahjoita näkyy, kun lahjoitustiedot on lisätty.
valikko_piilota: []
galleria: []
---
"""
    readme = lue("README.md").replace("MOSKEIJAN NIMI", t["nimi"]).replace("SLUG", t["slug"]) \
        .replace("https://suomen-moskeijat.github.io/REPO/", f"{perus}/{repo}/")
    return {
        "_config.yml": config,
        f"_moskeijat/{t['slug']}.md": md,
        "README.md": readme,
        ".pages.yml": lue(".pages.yml"),
        "_tapahtumat/.gitkeep": "",
        "_sivut/.gitkeep": "",
        "tiedostot/.gitkeep": "",
        ".github/workflows/julkaisu.yml": lue(".github/workflows/julkaisu.yml"),  # viimeisenä: käynnistää julkaisun
    }


# ------------------------------------------------------------- GitHub
def api(menetelma, polku, data=None, avain=None, sallitut=()):
    req = urllib.request.Request("https://api.github.com" + polku, method=menetelma,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 headers={**SELAIN, "Authorization": f"Bearer {avain}",
                                          "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=30) as v:
            sis = v.read()
            return v.status, json.loads(sis) if sis else {}
    except urllib.error.HTTPError as e:
        sis = e.read().decode("utf-8", "replace")
        if e.code in sallitut:
            return e.code, {}
        raise SystemExit(f"GitHub-virhe {e.code} ({menetelma} {polku}): {sis[:400]}")


def julkaise(t, repo, org, avain, tiedot):
    tila, _ = api("GET", f"/repos/{org}/{repo}", avain=avain, sallitut=(404,))
    if tila == 200:
        raise SystemExit(f"Repo {org}/{repo} on jo olemassa – valitse toinen nimi.")
    print(f"Luodaan repo {org}/{repo} …")
    api("POST", f"/orgs/{org}/repos", {"name": repo, "description": f"{t['nimi']} – nettisivu",
                                      "homepage": f"https://{org.lower()}.github.io/{repo}/",
                                      "private": False, "auto_init": True, "has_wiki": False}, avain)
    time.sleep(3)
    print("Otetaan julkaisu käyttöön (Pages: GitHub Actions) …")
    api("POST", f"/repos/{org}/{repo}/pages", {"build_type": "workflow"}, avain, sallitut=(409,))
    for polku, sisalto in tiedot.items():
        nykyinen = {}
        if polku == "README.md":
            _, nykyinen = api("GET", f"/repos/{org}/{repo}/contents/README.md", avain=avain, sallitut=(404,))
        data = {"message": f"Lisää {polku}", "content": base64.b64encode(sisalto.encode()).decode()}
        if nykyinen.get("sha"):
            data["sha"] = nykyinen["sha"]
        api("PUT", f"/repos/{org}/{repo}/contents/{polku}", data, avain)
        print(f"  + {polku}")
    return f"https://{org.lower()}.github.io/{repo}/"


def kutsu_muokkaajat(tunnukset, repo, org, avain):
    """Kutsuu muokkaajat vain tähän repoon (Write). He eivät näe muiden moskeijoiden repoja muokattavina."""
    kutsutut = []
    for tunnus_ in re.split(r"[,\s]+", tunnukset or ""):
        tunnus_ = tunnus_.strip().lstrip("@")
        if not re.match(r"^[A-Za-z0-9-]{1,39}$", tunnus_):
            continue
        tila, _ = api("PUT", f"/repos/{org}/{repo}/collaborators/{tunnus_}", {"permission": "push"}, avain, sallitut=(404, 422))
        if tila in (201, 204):
            kutsutut.append(tunnus_)
            print(f"  kutsuttu muokkaajaksi: {tunnus_}")
        else:
            print(f"  muokkaajaa ei voitu kutsua: {tunnus_} ({tila})", file=sys.stderr)
    return kutsutut


def main():
    p = argparse.ArgumentParser()
    for k in ["nimi", "kaupunki", "mawaqit", "masjidbox", "osoite", "instagram", "whatsapp", "youtube", "telegram", "repo", "muokkaajat"]:
        p.add_argument("--" + k, default=os.environ.get("SYOTE_" + k.upper(), ""))
    p.add_argument("--kuiva", help="kirjoita tiedostot tähän kansioon, älä luo mitään GitHubiin")
    p.add_argument("--vain-muokkaajat", action="store_true", help="kutsu muokkaajat olemassa olevaan repoon (--repo)")
    a = p.parse_args()
    if a.vain_muokkaajat:
        avain, org = os.environ.get("MOSKEIJA_AVAIN"), os.environ.get("ORG", "suomen-moskeijat")
        if not (avain and a.repo.strip() and a.muokkaajat.strip()):
            raise SystemExit("Anna repo ja muokkaajien GitHub-tunnukset (ja MOSKEIJA_AVAIN).")
        repo = a.repo.strip().split("/")[-1]
        tila, _ = api("GET", f"/repos/{org}/{repo}", avain=avain, sallitut=(404,))
        if tila != 200:
            raise SystemExit(f"Repoa {org}/{repo} ei löydy.")
        k = kutsu_muokkaajat(a.muokkaajat, repo, org, avain)
        viesti = f"## Muokkaajat: {org}/{repo}\n\nKutsuttu: {', '.join(k) or 'ei ketään'}. Kutsu tulee sähköpostiin, ja oikeus koskee vain tätä moskeijaa.\n"
        print(viesti)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8").write(viesti)
        return
    if not a.nimi.strip() and not (a.mawaqit or a.masjidbox):
        raise SystemExit("Anna vähintään moskeijan nimi (tai Mawaqit/Masjidbox-linkki).")
    if not a.kaupunki.strip():
        raise SystemExit("Anna kaupunki.")

    t = {"nimi": a.nimi.strip(), "kaupunki": a.kaupunki.strip(), "osoite": a.osoite.strip(),
         "instagram": a.instagram.strip(), "whatsapp": a.whatsapp.strip(),
         "youtube": a.youtube.strip(), "telegram": a.telegram.strip(), "puhelin": "", "sahkoposti": "",
         "nettisivu": "", "juma": "", "lat": 0, "lon": 0, "lahde": "", "tunnus": ""}
    if a.mawaqit:
        t["lahde"], t["tunnus"] = "mawaqit", tunnus(a.mawaqit, "mawaqit")
        try:
            d = mawaqit_tiedot(t["tunnus"])
            print(f"Mawaqit: {d['nimi']}, {d['lat']}, {d['lon']}, Jumuah {d['juma']}")
            t["nimi"] = t["nimi"] or d["nimi"]
            t["lat"], t["lon"] = round(float(d["lat"]), 6), round(float(d["lon"]), 6)
            for k in ("juma", "puhelin", "sahkoposti", "nettisivu"):
                t[k] = t[k] or d[k]
        except Exception as e:
            print(f"Mawaqit-tietoja ei saatu ({t['tunnus']}): {e}", file=sys.stderr)
    elif a.masjidbox:
        t["lahde"], t["tunnus"] = "masjidbox", tunnus(a.masjidbox, "masjidbox")
        try:
            d = masjidbox_tiedot(t["tunnus"])
            print(f"Masjidbox: {d['nimi']}, {d['osoite']}")
            t["nimi"] = t["nimi"] or d["nimi"]
            t["osoite"] = t["osoite"] or re.sub(r",\s*Suomi$|,\s*Finland$", "", d["osoite"])
        except Exception as e:
            print(f"Masjidbox-tietoja ei saatu ({t['tunnus']}): {e}", file=sys.stderr)
    if not t["lat"]:
        t["lat"], t["lon"] = koordinaatit(t["osoite"], t["kaupunki"])
        print(f"Koordinaatit osoitteesta: {t['lat']}, {t['lon']}")
    t["slug"] = slugiksi(t["nimi"])
    repo = slugiksi(a.repo) if a.repo.strip() else t["slug"]
    org = os.environ.get("ORG", "suomen-moskeijat")
    tiedot = tiedostot(t, repo, org)

    if a.kuiva:
        for polku, sisalto in tiedot.items():
            kohde = os.path.join(a.kuiva, polku)
            os.makedirs(os.path.dirname(kohde), exist_ok=True)
            open(kohde, "w", encoding="utf-8").write(sisalto)
        print(f"Kuivaharjoitus: {len(tiedot)} tiedostoa kansioon {a.kuiva} (repo olisi {org}/{repo})")
        return
    avain = os.environ.get("MOSKEIJA_AVAIN")
    if not avain:
        raise SystemExit("Avain puuttuu: lisää pohja-repon asetuksiin salaisuus MOSKEIJA_AVAIN (ks. README).")
    osoite = julkaise(t, repo, org, avain, tiedot)
    kutsutut = kutsu_muokkaajat(a.muokkaajat, repo, org, avain)
    yhteenveto = (f"## ✅ {t['nimi']} lisätty\n\n- **Sivu:** {osoite} (valmis noin 2 minuutin päästä)\n"
                  f"- **Repo:** https://github.com/{org}/{repo}\n- **Rukousajat:** {t['lahde'] or 'rukousajat.fi / laskenta'}"
                  f"{' (' + t['tunnus'] + ')' if t['tunnus'] else ''}\n- **Koordinaatit:** {t['lat']}, {t['lon']}\n"
                  f"- **Muokkaajat:** {', '.join(kutsutut) if kutsutut else 'ei vielä (lisää: repo → Settings → Collaborators → Add people → Write)'}"
                  f"{' – he saavat kutsun sähköpostiinsa ja hyväksyvät sen' if kutsutut else ''}\n\n"
                  f"Täydennä tiedot (osoite, puhelin, logo, tekstit) Pages CMS:ssä: https://app.pagescms.org\n")
    print(yhteenveto)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8").write(yhteenveto)


if __name__ == "__main__":
    main()
