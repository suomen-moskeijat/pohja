#!/usr/bin/env python3
"""Koraanin jae -osion haettavat tiedostot Tanzilin alkuperäisistä tiedostoista (hallinta#36).

    python3 .github/scripts/koraani.py          # _tanzil/ → _data/koraani/

Alkuperäiset tiedostot ovat muuttamattomina kansiossa _tanzil/ (ks. _tanzil/LISENSSI.md). Tämä skripti jakaa ne suura
kerrallaan Jekyllin datatiedostoiksi, jotta sivupohja ja paneeli löytävät jakeen nopeasti:

    _data/koraani/suurat.json                  suurien nimet ja jakeiden määrä (quran-data.xml)
    _data/koraani/kaannokset.json              käännökset (tunnus, kieli, nimi, kääntäjä) käännöstiedostojen otsakkeista
    _data/koraani/<tunnus>/<suura>.json        jakeet sellaisinaan, esim. quran-uthmani/4.json, en-sahih/4.json

Jae kopioidaan tavuja muuttamatta (rivi "suura|jae|teksti", vain rivinvaihto jakeiden välissä on erotin), ja jokaisessa
tiedostossa on alkuperäisen tiedoston tekijänoikeusilmoitus sellaisenaan (Tanzilin ehto). Tunnuksen piste vaihtuu
viivaksi (en.sahih → en-sahih), koska Jekyll poistaa pisteet datatiedostojen nimistä.
Testi: hallinta testi/koraani-tanzil.mjs (jokainen jae tavu tavulta sama kuin alkuperäisessä). Ei ulkoisia riippuvuuksia.
"""
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET

JUURI = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LAHDE = os.path.join(JUURI, "_tanzil")
KOHDE = os.path.join(JUURI, "_data", "koraani")
TEKSTI = "quran-uthmani.txt"
EHDOT_KAANNOS = ("Tanzil.net terms of use (https://tanzil.net/trans/): The translations provided at this page are for "
                 "non-commercial purposes only. If used otherwise, you need to obtain necessary permission from the "
                 "translator or the publisher.")


def lue(nimi):
    """Rivit tavuina: jakeet {(suura, jae): tavut} ja kommenttirivit (#) sellaisinaan. Erotin on vain \\n (ei esim. U+0085)."""
    with open(os.path.join(LAHDE, nimi), "rb") as f:
        tavut = f.read()
    jakeet, kommentit = {}, []
    for rivi in tavut.split(b"\n"):
        if rivi.startswith(b"#"):
            kommentit.append(rivi.decode("utf-8"))
            continue
        if not rivi:
            continue
        s, a, teksti = rivi.split(b"|", 2)
        jakeet[(int(s), int(a))] = teksti
    return jakeet, kommentit


def otsake(kommentit, kentta):
    for k in kommentit:
        m = re.match(r"#\s+%s:\s*(.*\S)" % kentta, k)
        if m:
            return m.group(1)
    return ""


def kirjoita(polku, data):
    os.makedirs(os.path.dirname(polku), exist_ok=True)
    with open(polku, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def main():
    if os.path.isdir(KOHDE):
        shutil.rmtree(KOHDE)
    juuri = ET.parse(os.path.join(LAHDE, "quran-data.xml")).getroot()
    suurat = [{"nro": int(s.get("index")), "nimi": s.get("tname"), "ar": s.get("name"), "en": s.get("ename"), "jakeita": int(s.get("ayas"))}
              for s in juuri.find("suras").findall("sura")]
    assert len(suurat) == 114 and [s["nro"] for s in suurat] == list(range(1, 115))
    kirjoita(os.path.join(KOHDE, "suurat.json"), {
        "lahde": "Tanzil Quran Metadata (quran-data.xml), https://tanzil.net/docs/Quran_Metadata",
        "lisenssi": "Copyright %s, license: %s" % (juuri.get("copyright"), juuri.get("license")),
        "suurat": suurat,
    })

    kaannokset = {}
    tiedostot = [TEKSTI] + sorted(n for n in os.listdir(LAHDE) if re.match(r"^[a-z]{2,3}\.[a-z0-9]+\.txt$", n))
    for nimi in tiedostot:
        jakeet, kommentit = lue(nimi)
        tunnus = "quran-uthmani" if nimi == TEKSTI else nimi[:-4]
        avain = tunnus.replace(".", "-")
        for s in suurat:  # jokainen jae on tiedostossa
            for a in range(1, s["jakeita"] + 1):
                assert (s["nro"], a) in jakeet, (nimi, s["nro"], a)
        assert len(jakeet) == sum(s["jakeita"] for s in suurat), nimi
        ilmoitus = "\n".join(kommentit)
        if nimi == TEKSTI:
            lahde = "Tanzil Quran Text (Uthmani, Version 1.1), https://tanzil.net"
            lisenssi = ilmoitus
        else:
            lahde = "Tanzil.net, %s (%s), https://tanzil.net/trans/" % (otsake(kommentit, "Name"), tunnus)
            lisenssi = ilmoitus + "\n" + EHDOT_KAANNOS
            kaannokset[avain] = {"id": tunnus, "kieli": tunnus.split(".")[0], "nimi": otsake(kommentit, "Name"),
                                 "kaantaja": otsake(kommentit, "Translator"), "kieli_nimi": otsake(kommentit, "Language"),
                                 "paivitetty": otsake(kommentit, "Last Update")}
        for s in suurat:
            kirjoita(os.path.join(KOHDE, avain, "%d.json" % s["nro"]), {
                "lahde": lahde, "lisenssi": lisenssi, "suura": s["nro"],
                "jakeet": [jakeet[(s["nro"], a)].decode("utf-8") for a in range(1, s["jakeita"] + 1)],
            })
    kirjoita(os.path.join(KOHDE, "kaannokset.json"), {
        "lahde": "Tanzil.net, https://tanzil.net/trans/", "ehdot": EHDOT_KAANNOS, "kaannokset": kaannokset,
    })
    print("Koraani: %d tekstiä, %d suuraa → %s" % (len(tiedostot), len(suurat), os.path.relpath(KOHDE, JUURI)))


if __name__ == "__main__":
    main()
