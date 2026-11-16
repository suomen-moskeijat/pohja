#!/usr/bin/env python3
"""Lisää valmiin sivuston <img>-tageihin width- ja height-attribuutit, jos ne puuttuvat.

Selain varaa kuvalle oikean tilan jo ennen latautumista, joten sivu ei hypi (CLS).
Mitat luetaan kuvatiedoston otsakkeesta (PNG, JPEG, GIF, WebP) ilman lisäkirjastoja.
Vain sivuston omat kuvat käsitellään; ulkoiset osoitteet ohitetaan.

Käyttö: python3 kuvakoot.py <_site-kansio>
"""
import os
import re
import struct
import sys
from urllib.parse import unquote, urlparse


def mitat(polku):
    try:
        with open(polku, "rb") as f:
            d = f.read(65536)
    except OSError:
        return None
    if d[:8] == b"\x89PNG\r\n\x1a\n" and len(d) >= 24:
        return struct.unpack(">II", d[16:24])
    if d[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", d[6:10])
    if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
        lohko = d[12:16]
        if lohko == b"VP8 " and len(d) >= 30:
            w, h = struct.unpack("<HH", d[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if lohko == b"VP8L" and len(d) >= 25:
            b = d[21:25]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return w, h
        if lohko == b"VP8X" and len(d) >= 30:
            w = 1 + int.from_bytes(d[24:27], "little")
            h = 1 + int.from_bytes(d[27:30], "little")
            return w, h
        return None
    if d[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(d):
            if d[i] != 0xFF:
                i += 1
                continue
            merkki = d[i + 1]
            if merkki in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", d[i + 5:i + 9])
                return w, h
            pituus = struct.unpack(">H", d[i + 2:i + 4])[0]
            i += 2 + pituus
        return None
    return None


IMG = re.compile(r"<img\b[^>]*>", re.I)
SRC = re.compile(r'\ssrc="([^"]+)"', re.I)


def tiedosto(juuri, src):
    u = urlparse(src)
    if u.scheme or u.netloc or not u.path.startswith("/"):
        return None
    osat = unquote(u.path).lstrip("/").split("/")
    # Ensin sellaisenaan, sitten ilman ensimmäistä osaa (baseurl, esim. /testimoskeija/...)
    for alku in (0, 1):
        p = os.path.join(juuri, *osat[alku:])
        if os.path.isfile(p):
            return p
    return None


def kasittele(juuri):
    muutettu = 0
    for kansio, _, tiedostot in os.walk(juuri):
        for nimi in tiedostot:
            if not nimi.endswith(".html"):
                continue
            polku = os.path.join(kansio, nimi)
            with open(polku, encoding="utf-8") as f:
                html = f.read()

            def lisaa(m):
                tagi = m.group(0)
                if re.search(r"\swidth=", tagi, re.I) or re.search(r"\sheight=", tagi, re.I):
                    return tagi
                s = SRC.search(tagi)
                if not s:
                    return tagi
                p = tiedosto(juuri, s.group(1))
                koko = mitat(p) if p else None
                if not koko or not koko[0] or not koko[1]:
                    return tagi
                loppu = "/>" if tagi.endswith("/>") else ">"
                return tagi[: -len(loppu)].rstrip() + f' width="{koko[0]}" height="{koko[1]}"' + loppu

            uusi = IMG.sub(lisaa, html)
            if uusi != html:
                with open(polku, "w", encoding="utf-8") as f:
                    f.write(uusi)
                muutettu += 1
    print(f"Kuvien mitat lisätty {muutettu} sivulle")


if __name__ == "__main__":
    kasittele(sys.argv[1] if len(sys.argv) > 1 else "_site")
