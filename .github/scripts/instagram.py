#!/usr/bin/env python3
"""Hakee moskeijoiden Instagram-tilien uusimmat julkaisut sivustoa varten.

Lukee Instagram-osoitteet tiedostoista _moskeijat/*.md (kenttä some.instagram),
hakee kunkin tilin julkisen profiiliupotuksen (instagram.com/<tunnus>/embed/) ja
- tallentaa julkaisujen tiedot (teksti, päivä, tyyppi) tiedostoon
  _data/instagram/<tunnus>.json
- lataa kuvat sivustolle kansioon tiedostot/instagram/<tunnus>/
Näin sivu näyttää julkaisut omana kevyenä galleriana ilman Instagramin
upotuksia, evästeitä tai vanhenevia kuvaosoitteita.

Jos haku epäonnistuu, vanhoja tiedostoja ei muuteta. Ei ulkoisia riippuvuuksia.
"""
import datetime
import glob
import json
import os
import re
import sys
import urllib.request

JUURI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENINTAAN = 12
# Lyhyellä selaintunnisteella Instagram palauttaa upotuksen, jossa julkaisutiedot ovat
# valmiina HTML:ssä (täydellä Chrome-tunnisteella ne ladataan vasta JavaScriptillä).
SELAIMET = ["Mozilla/5.0", "Mozilla/5.0 (compatible; MoskeijaSivusto/1.0)"]
TYYPIT = {"GraphImage": "kuva", "GraphVideo": "video", "GraphSidecar": "albumi"}


def tunnukset():
    """Instagram-käyttäjätunnukset moskeijoiden tiedoista (pienillä kirjaimilla)."""
    loydetyt = []
    for polku in sorted(glob.glob(os.path.join(JUURI, "_moskeijat", "*.md"))):
        with open(polku, encoding="utf-8") as f:
            for rivi in f:
                m = re.match(r'\s+instagram:\s*["\']?https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]+)', rivi)
                if m and m.group(1).lower() not in loydetyt:
                    loydetyt.append(m.group(1).lower())
    return loydetyt


def lataa(url, selain="Mozilla/5.0"):
    pyynto = urllib.request.Request(url, headers={"User-Agent": selain, "Accept-Language": "fi,en;q=0.8"})
    with urllib.request.urlopen(pyynto, timeout=30) as vastaus:
        return vastaus.read()


def profiili(tunnus):
    """Palauttaa profiiliupotuksen contextJSON-tiedot tai None."""
    for selain in SELAIMET:
        html = lataa(f"https://www.instagram.com/{tunnus}/embed/", selain).decode("utf-8", "replace")
        i = html.find('"contextJSON"')
        if i < 0:
            continue
        alku = html.find(":", i) + 1
        teksti, _ = json.JSONDecoder().raw_decode(html[alku:].lstrip())  # JSON merkkijonon sisällä
        konteksti = json.loads(teksti).get("context") or {}
        if konteksti.get("graphql_media"):
            return konteksti
    return None


def kasittele(tunnus):
    konteksti = profiili(tunnus)
    if not konteksti:
        raise RuntimeError("julkaisuja ei löytynyt")
    avain = tunnus.replace(".", "_")
    kuvakansio = os.path.join(JUURI, "tiedostot", "instagram", avain)
    os.makedirs(kuvakansio, exist_ok=True)

    julkaisut = []
    for g in konteksti["graphql_media"][:ENINTAAN]:
        m = g.get("shortcode_media") or {}
        koodi = m.get("shortcode")
        if not koodi:
            continue
        kuvat = sorted(m.get("display_resources") or [], key=lambda r: r.get("config_width", 0))
        kuva_url = (kuvat[0]["src"] if kuvat else None) or m.get("display_url")
        kuvapolku = f"tiedostot/instagram/{avain}/{koodi}.jpg"
        tiedosto = os.path.join(JUURI, kuvapolku)
        if kuva_url and not os.path.exists(tiedosto):
            try:
                with open(tiedosto, "wb") as f:
                    f.write(lataa(kuva_url))
            except Exception as e:
                print(f"{tunnus}/{koodi}: kuvan lataus epäonnistui ({e})", file=sys.stderr)
                if os.path.exists(tiedosto):
                    os.remove(tiedosto)
        if not os.path.exists(tiedosto):
            continue
        reunat = (m.get("edge_media_to_caption") or {}).get("edges") or [{}]
        aika = m.get("taken_at_timestamp")
        koko = m.get("dimensions") or {}
        julkaisut.append({
            "koodi": koodi,
            "tyyppi": TYYPIT.get(m.get("__typename"), "kuva"),
            "paiva": datetime.datetime.fromtimestamp(aika, datetime.timezone.utc).strftime("%Y-%m-%d") if aika else "",
            "teksti": (reunat[0].get("node") or {}).get("text", ""),
            "kuva": kuvapolku,
            "leveys": koko.get("width"),
            "korkeus": koko.get("height"),
        })
    if not julkaisut:
        raise RuntimeError("kuvia ei saatu ladattua")

    # Poistetaan kuvat, joita ei enää näytetä
    kaytossa = {os.path.basename(j["kuva"]) for j in julkaisut}
    for vanha in glob.glob(os.path.join(kuvakansio, "*.jpg")):
        if os.path.basename(vanha) not in kaytossa:
            os.remove(vanha)

    os.makedirs(os.path.join(JUURI, "_data", "instagram"), exist_ok=True)
    with open(os.path.join(JUURI, "_data", "instagram", avain + ".json"), "w", encoding="utf-8") as f:
        json.dump({
            "kayttaja": tunnus,
            "nimi": konteksti.get("full_name") or tunnus,
            "seuraajia": konteksti.get("followers_count"),
            "julkaisuja": konteksti.get("posts_count"),
            "paivitetty": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
            "julkaisut": julkaisut,
        }, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return len(julkaisut)


def main():
    for tunnus in tunnukset():
        try:
            print(f"{tunnus}: {kasittele(tunnus)} julkaisua")
        except Exception as e:  # epäonnistunut haku ei estä sivuston julkaisua
            print(f"{tunnus}: haku epäonnistui, vanha tieto säilytetään ({e})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
