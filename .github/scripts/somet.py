#!/usr/bin/env python3
"""Hakee moskeijan YouTube-videot ja Telegram-julkaisut sivulle (kuten instagram.py).

Moskeijan tiedostossa _moskeijat/<slug>.md, kohdassa some:
    youtube: https://www.youtube.com/@kanava     (tai /channel/UC…)
    telegram: https://t.me/kanava                (julkinen kanava)

- YouTube: kanavan virallinen julkinen syöte (feeds/videos.xml), 6 uusinta videota.
- Telegram: julkisen kanavan selainnäkymä (t.me/s/<kanava>), 6 uusinta julkaisua.
Tiedot: _data/youtube/<slug>.json ja _data/telegram/<slug>.json; kuvat ladataan
sivustolle (tiedostot/youtube/<slug>/, tiedostot/telegram/<slug>/), joten sivulla
ei ladata mitään YouTuben tai Telegramin palvelimilta. Jos haku epäonnistuu,
vanhat tiedot jäävät voimaan. Ei ulkoisia riippuvuuksia.
"""
import datetime
import glob
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

JUURI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENINTAAN = 6
SELAIN = {"User-Agent": "Mozilla/5.0", "Accept-Language": "fi,en;q=0.8"}


def hae(osoite, binaari=False):
    with urllib.request.urlopen(urllib.request.Request(osoite, headers=SELAIN), timeout=30) as v:
        d = v.read()
        return d if binaari else d.decode("utf-8", "replace")


def moskeijat():
    """[(slug, {'youtube': url, 'telegram': url})]"""
    tulos = []
    for polku in sorted(glob.glob(os.path.join(JUURI, "_moskeijat", "*.md"))):
        slug = os.path.splitext(os.path.basename(polku))[0]
        somet = {}
        for rivi in open(polku, encoding="utf-8"):
            m = re.match(r'slug:\s*["\']?([a-z0-9-]+)', rivi)
            if m:
                slug = m.group(1)
            m = re.match(r'\s+(youtube|telegram):\s*["\']?(https?://[^"\'\s#]+)', rivi)
            if m:
                somet[m.group(1)] = m.group(2)
        if somet:
            tulos.append((slug, somet))
    return tulos


def lataa_kuva(osoite, kansio, nimi):
    os.makedirs(kansio, exist_ok=True)
    kohde = os.path.join(kansio, nimi)
    if not os.path.exists(kohde):
        data = hae(osoite, binaari=True)
        if len(data) < 1500:
            raise ValueError("kuva liian pieni")
        open(kohde, "wb").write(data)
    return kohde


def tallenna(laji, slug, tiedot):
    kansio = os.path.join(JUURI, "_data", laji)
    os.makedirs(kansio, exist_ok=True)
    json.dump(tiedot, open(os.path.join(kansio, slug + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- YouTube
def youtube(slug, osoite):
    m = re.search(r"/channel/(UC[A-Za-z0-9_-]{22})", osoite)
    kanava_id = m.group(1) if m else None
    if not kanava_id:  # @nimi, /c/nimi tai /user/nimi → kanavan tunnus kanavan sivulta
        sivu = hae(osoite)
        m = re.search(r'"externalId":"(UC[A-Za-z0-9_-]{22})"', sivu) or \
            re.search(r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[A-Za-z0-9_-]{22})"', sivu)
        if not m:
            raise ValueError("kanavan tunnusta ei löytynyt")
        kanava_id = m.group(1)
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
          "media": "http://search.yahoo.com/mrss/"}
    juuri = ET.fromstring(hae("https://www.youtube.com/feeds/videos.xml?channel_id=" + kanava_id))
    kansio = os.path.join(JUURI, "tiedostot", "youtube", slug)
    videot = []
    for e in juuri.findall("a:entry", ns):
        vid = e.find("yt:videoId", ns).text
        if "/shorts/" in (e.find("a:link", ns).get("href") or ""):
            continue  # lyhyet pystyvideot eivät sovi videoruudukkoon
        try:
            lataa_kuva(f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg", kansio, vid + ".jpg")
        except Exception as ex:
            print(f"  YouTube-kuvaa ei saatu ({vid}): {ex}", file=sys.stderr)
            continue
        videot.append({"id": vid, "otsikko": e.find("a:title", ns).text or "",
                       "paiva": (e.find("a:published", ns).text or "")[:10],
                       "kuva": f"/tiedostot/youtube/{slug}/{vid}.jpg"})
        if len(videot) >= ENINTAAN:
            break
    if not videot:
        raise ValueError("ei videoita")
    tallenna("youtube", slug, {"kanava": juuri.find("a:title", ns).text, "osoite": osoite,
                               "paivitetty": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
                               "videot": videot})
    return len(videot)


# ---------------------------------------------------------------- Telegram
def telegram(slug, osoite):
    m = re.search(r"t\.me/(?:s/)?([A-Za-z0-9_]{4,})", osoite)
    if not m:
        raise ValueError("ei julkisen kanavan osoite (t.me/kanava)")
    nimi = m.group(1)
    sivu = hae(f"https://t.me/s/{nimi}")
    otsikko = re.search(r'<meta property="og:title" content="([^"]*)"', sivu)
    osat = re.split(r'(?=<div class="tgme_widget_message_wrap)', sivu)[1:]
    kansio = os.path.join(JUURI, "tiedostot", "telegram", slug)
    julkaisut = []
    for v in reversed(osat):  # uusin ensin
        pid = re.search(r'data-post="[^"/]+/(\d+)"', v)
        if not pid:
            continue
        teksti = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', v, re.S)
        teksti = html.unescape(re.sub(r"<br\s*/?>", "\n", teksti.group(1))) if teksti else ""
        teksti = re.sub(r"<[^>]+>", "", teksti).strip()
        aika = re.search(r'<time datetime="([^"]+)"', v)
        kuva = re.search(r"tgme_widget_message_(?:photo_wrap|video_thumb)[^>]*background-image:url\('([^']+)'\)", v)
        polku = ""
        if kuva:
            try:
                lataa_kuva(kuva.group(1), kansio, pid.group(1) + ".jpg")
                polku = f"/tiedostot/telegram/{slug}/{pid.group(1)}.jpg"
            except Exception as ex:
                print(f"  Telegram-kuvaa ei saatu ({pid.group(1)}): {ex}", file=sys.stderr)
        if not teksti and not polku:
            continue
        julkaisut.append({"id": pid.group(1), "teksti": teksti[:400], "kuva": polku,
                          "paiva": (aika.group(1) if aika else "")[:10],
                          "linkki": f"https://t.me/{nimi}/{pid.group(1)}"})
        if len(julkaisut) >= ENINTAAN:
            break
    if not julkaisut:
        raise ValueError("ei julkaisuja")
    tallenna("telegram", slug, {"kanava": html.unescape(otsikko.group(1)) if otsikko else nimi, "nimi": nimi,
                                "osoite": f"https://t.me/{nimi}",
                                "paivitetty": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
                                "julkaisut": julkaisut})
    return len(julkaisut)


def main():
    for slug, somet in moskeijat():
        for laji, hakija in (("youtube", youtube), ("telegram", telegram)):
            if laji in somet:
                try:
                    print(f"{slug}: {laji} {hakija(slug, somet[laji])} kpl")
                except Exception as e:  # vanhat tiedot jäävät voimaan
                    print(f"{slug}: {laji}-haku epäonnistui ({somet[laji]}): {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
