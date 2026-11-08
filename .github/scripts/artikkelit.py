#!/usr/bin/env python3
"""Yhteiset artikkelit moskeijoiden sivuille.

    python3 artikkelit.py --tuo islaminusko      # hakee artikkelit pohjaan (_artikkelit/islaminusko/)
    python3 artikkelit.py --karsi KANSIO          # poistaa kootulta sivulta lähteet, joita moskeija ei käytä

Lähde islaminusko.fi: "Sisältöä saa jakaa ja kopioida ei-kaupallisiin sekä voittoa
tavoittelemattomiin tarkoituksiin" (© Asiya Rosa). Artikkelit tuodaan kokonaisina
lähdemerkinnän ja alkuperäisen linkin kanssa. Kuvia ei tuoda (osa on kuvapankeista).

Moskeija ottaa lähteen käyttöön tiedostossa _moskeijat/<slug>.md:
    artikkelit:
      lahteet: [islaminusko]
Ei ulkoisia riippuvuuksia.
"""
import argparse
import glob
import html
import json
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

# Lähteen aiheet lyhyemmiksi ja yhdistetyiksi (artikkelisivun aihevalinta mahtuu puhelimeen)
AIHEET = {
    "Islamin perusteet": "Islamin perusteet",
    "Kuka on Allah?": "Islamin perusteet",
    "Fiqh (lainopilliset asiat), ohjeet ja säädökset": "Ohjeet",
    "Islamilaiset etiketit ja käytös": "Käytös ja tavat",
    "Islamilainen kalenteri ja erityiset päivät": "Juhlat",
    "Kysymykset ja vastaukset": "Kysymykset",
    "Pyyntörukouksia - Dhikr & Dua": "Dhikr ja dua",
    "Viimeinen profeetta ﷺ": "Profeetta ja hadithit",
    "Haditheja": "Profeetta ja hadithit",
    "Oppineiden tarinoita": "Muut",
    "Hurskaiden lausuntoja": "Muut",
    "": "Muut",
}

JUURI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAHTEET = {
    "islaminusko": {
        "nimi": "islaminusko.fi",
        "perus": "https://www.islaminusko.fi",
        "lista": "/Lue-lisää-islamista/",
        "oikeudet": "© Asiya Rosa, islaminusko.fi. Sisältöä saa jakaa ja kopioida ei-kaupallisiin sekä voittoa tavoittelemattomiin tarkoituksiin.",
    },
}


def hae(osoite):
    pyynto = urllib.request.Request(osoite, headers={"User-Agent": "Mozilla/5.0 (suomen-moskeijat)"})
    with urllib.request.urlopen(pyynto, timeout=40) as v:
        return v.read().decode("utf-8", "replace")


def url(perus, polku):
    p = urllib.parse.urlsplit(urllib.parse.urljoin(perus + "/", polku))
    return urllib.parse.urlunsplit((p.scheme, p.netloc, urllib.parse.quote(urllib.parse.unquote(p.path)), p.query, ""))


def tiedostonimi(polku):
    nimi = urllib.parse.unquote(polku.rstrip("/").split("/")[-1]).lower()
    for a, b in (("ä", "a"), ("ö", "o"), ("å", "a"), ("é", "e"), ("ü", "u")):
        nimi = nimi.replace(a, b)
    nimi = re.sub(r"[^a-z0-9]+", "-", nimi).strip("-")
    return nimi[:80].rstrip("-") or "artikkeli"


# ---------------------------------------------------------------- HTML:n siivous
SALLITUT = {"p", "br", "strong", "em", "ul", "ol", "li", "h2", "h3", "h4", "blockquote", "a", "hr"}
MUUNNOS = {"b": "strong", "i": "em", "h1": "h2", "h5": "h4", "h6": "h4"}
SUUNTA = {"p", "li", "h2", "h3", "h4", "blockquote"}


class Siivoaja(HTMLParser):
    def __init__(self, perus):
        super().__init__(convert_charrefs=True)
        self.perus, self.ulos, self.pino, self.ohita = perus, [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "iframe", "img", "video", "svg"):
            self.ohita += tag not in ("img",)
            return
        tag = MUUNNOS.get(tag, tag)
        if tag not in SALLITUT:
            return
        if tag in ("br", "hr"):
            self.ulos.append(f"<{tag}>")
            return
        a = ""
        if tag == "a":
            href = dict(attrs).get("href") or ""
            if href.startswith(("javascript:", "#", "mailto:")) or not href:
                self.pino.append(None)
                return
            href = urllib.parse.urljoin(self.perus + "/", href)
            a = f' href="{html.escape(href, quote=True)}" target="_blank" rel="noopener"'
        elif tag in SUUNTA:
            a = ' dir="auto"'
        self.pino.append(tag)
        self.ulos.append(f"<{tag}{a}>")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "iframe", "video", "svg"):
            self.ohita = max(0, self.ohita - 1)
            return
        tag = MUUNNOS.get(tag, tag)
        if tag not in SALLITUT or tag in ("br", "hr"):
            return
        if tag == "a" and self.pino and self.pino[-1] is None:
            self.pino.pop()
            return
        if tag in self.pino:
            while self.pino:
                t = self.pino.pop()
                if t:
                    self.ulos.append(f"</{t}>")
                if t == tag:
                    break

    def handle_data(self, data):
        if not self.ohita:
            self.ulos.append(html.escape(data, quote=False))

    def tulos(self):
        while self.pino:
            t = self.pino.pop()
            if t:
                self.ulos.append(f"</{t}>")
        h = "".join(self.ulos)
        h = re.sub(r"\xa0", " ", h)
        tyhja = r'<(p|h2|h3|h4|li|strong|em)(?: dir="auto")?>(?:\s|<br>)*</\1>'
        for _ in range(3):
            h = re.sub(tyhja, "", h)
        h = re.sub(r"(<br>\s*){3,}", "<br><br>", h)
        h = re.sub(r"\n{3,}", "\n\n", h)
        return h.strip()


def merkitse_arabia(h):
    """Kappaleet, joissa on pääosin arabiaa (esim. Koraanin jakeet): lang="ar" dir="rtl" (oma fontti sivulla)."""
    def korvaa(m):
        sisalto = m.group(3)
        kirjaimet = re.findall(r"[^\W\d_]", re.sub(r"<[^>]+>", "", sisalto))
        arab = sum(1 for c in kirjaimet if "\u0600" <= c <= "\u06ff" or "\u0750" <= c <= "\u08ff" or "\ufb50" <= c <= "\ufeff")
        if kirjaimet and arab / len(kirjaimet) > 0.6:
            return f'<{m.group(1)} lang="ar" dir="rtl">{sisalto}</{m.group(1)}>'
        return m.group(0)
    return re.sub(r'<(p|li|blockquote|h2|h3|h4)( dir="auto")?>(.*?)</\1>', korvaa, h, flags=re.S)


def siivoa(sisalto, perus):
    s = Siivoaja(perus)
    s.feed(sisalto)
    return merkitse_arabia(s.tulos())


def teksti(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def kuvaus(runko, otsikko):
    """Ensimmäiset suomenkieliset kappaleet (ei arabiaa eikä basmalaa), noin 200 merkkiä."""
    osat = []
    for kpl in re.findall(r"<p[^>]*>(.*?)</p>", runko, re.S):
        t = teksti(kpl)
        if not t or t == otsikko or re.search(r"[؀-ۿ]", t) or t.lower().startswith(("allahin, armeliaimman", "kaikki ylistys")):
            continue
        osat.append(t)
        if sum(len(o) for o in osat) > 200:
            break
    t = " ".join(osat)
    if len(t) > 220:
        t = t[:220].rsplit(" ", 1)[0].rstrip(",.;:–-") + "…"
    return t


def lohko(sivu, alku):
    """Palauttaa div-elementin (alkaen kohdasta alku) koko sisällön."""
    syv = 0
    for m in re.finditer(r"<(/?)div\b", sivu[alku:]):
        syv += -1 if m.group(1) else 1
        if syv == 0:
            return sivu[alku:alku + m.start()]
    return sivu[alku:]


# ---------------------------------------------------------------- islaminusko.fi (Webnode-blogi)
def islaminusko(asetus):
    perus = asetus["perus"]
    lista, nahty = [], set()
    for sivu in range(1, 40):
        h = hae(url(perus, asetus["lista"]) + f"?bpage={sivu}&bcpp=10")
        uudet = 0
        for polku, ots, aika in re.findall(r'<a href="([^"]+)"\s+class="wb-blog-item".*?<div class="title">(.*?)</div>.*?data-timestamp="([^"]+)"', h, re.S):
            polku = polku.split("#")[0]
            if polku not in nahty:
                nahty.add(polku)
                lista.append((polku, html.unescape(ots).strip(), aika[:10]))
                uudet += 1
        if not uudet:
            break
        time.sleep(0.4)
    artikkelit = []
    for polku, otsikko, paiva in lista:
        osoite = url(perus, polku)
        try:
            s = hae(osoite)
        except Exception as e:
            print(f"  ei saatu: {osoite}: {e}", file=sys.stderr)
            continue
        i = s.find('itemtype="https://schema.org/BlogPosting"')
        j = s.find('<div style="overflow: hidden;">', i)
        if i < 0 or j < 0:
            print(f"  sisältöä ei löytynyt: {osoite}", file=sys.stderr)
            continue
        aihe = re.search(r'itemprop="termCode" content="([^"]*)"', s[i:j])
        runko = lohko(s, j)
        runko = re.sub(r"^<div[^>]*>", "", runko)
        runko = siivoa(runko, perus)
        # otsikko on sivulla myös sisällön alussa
        runko = re.sub(r'^<h[234][^>]*>\s*(?:<strong>)?\s*' + re.escape(html.escape(otsikko, quote=False)) + r'\s*(?:</strong>)?\s*</h[234]>', "", runko).strip()
        if len(teksti(runko)) < 200:  # pelkkä kuva (kuvia ei tuoda)
            print(f"  ohitettu, ei tekstiä: {otsikko}", file=sys.stderr)
            continue
        tekija = re.search(r"(?:Kirjoittaja(?: ja kääntäjä)?|Kääntäjä|Kirjoittanut)\s*:\s*([^<]{3,80})", runko)
        artikkelit.append({
            "nimi": tiedostonimi(polku), "title": otsikko, "paiva": paiva,
            "aihe": AIHEET.get(html.unescape(aihe.group(1)) if aihe else "", html.unescape(aihe.group(1)) if aihe else "Muut"),
            "kirjoittaja": tekija.group(1).strip().rstrip(".") if tekija else "",
            "kuvaus": kuvaus(runko, otsikko), "lahde_url": osoite, "runko": runko,
        })
        time.sleep(0.4)
    return artikkelit


def tuo(lahde):
    asetus = LAHTEET[lahde]
    artikkelit = {"islaminusko": islaminusko}[lahde](asetus)
    kansio = os.path.join(JUURI, "_artikkelit", lahde)
    os.makedirs(kansio, exist_ok=True)
    vanhat = set(glob.glob(os.path.join(kansio, "*.md")))
    if vanhat and len(artikkelit) < len(vanhat) * 0.6:
        raise SystemExit(f"Vain {len(artikkelit)} artikkelia (aiemmin {len(vanhat)}) – haku lienee epäonnistunut, ei muuteta mitään.")
    muuttui, kaytetyt = 0, set()
    for a in artikkelit:
        nimi = a["nimi"]
        while nimi in kaytetyt:
            nimi += "-2"
        kaytetyt.add(nimi)
        polku = os.path.join(kansio, nimi + ".md")
        etu = {"title": a["title"], "paiva": a["paiva"], "lahde": lahde, "lahde_nimi": asetus["nimi"],
               "lahde_url": a["lahde_url"], "oikeudet": asetus["oikeudet"], "kirjoittaja": a["kirjoittaja"],
               "aihe": a["aihe"], "kuvaus": a["kuvaus"]}
        sisalto = "---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in etu.items()) + \
                  "---\n{% raw %}\n" + a["runko"].replace("{% endraw %}", "") + "\n{% endraw %}\n"
        vanha = open(polku, encoding="utf-8").read() if os.path.exists(polku) else None
        if vanha != sisalto:
            with open(polku, "w", encoding="utf-8") as f:
                f.write(sisalto)
            muuttui += 1
        vanhat.discard(polku)
    for p in vanhat:  # lähteestä poistetut
        os.remove(p)
    print(f"{lahde}: {len(artikkelit)} artikkelia, {muuttui} uutta tai muuttunutta, {len(vanhat)} poistettu")


def karsi(kansio):
    """Poistaa kootulta sivulta yhteiset artikkelilähteet, joita moskeija ei ole valinnut."""
    valitut = set()
    for md in glob.glob(os.path.join(kansio, "_moskeijat", "*.md")):
        teksti_ = open(md, encoding="utf-8").read()
        m = re.search(r"^artikkelit:\s*\n((?:[ \t]+.*\n?)*)", teksti_, re.M)
        if m:
            l = re.search(r"lahteet:\s*\[([^\]]*)\]", m.group(1))
            if l:
                valitut |= {x.strip().strip("\"'") for x in l.group(1).split(",") if x.strip()}
    for lahde in LAHTEET:
        p = os.path.join(kansio, "_artikkelit", lahde)
        if lahde not in valitut and os.path.isdir(p):
            shutil.rmtree(p)
            print(f"artikkelit: {lahde} ei käytössä – poistettu")
        elif os.path.isdir(p):
            print(f"artikkelit: {lahde} käytössä ({len(os.listdir(p))} artikkelia)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tuo", choices=sorted(LAHTEET))
    ap.add_argument("--karsi", metavar="KANSIO")
    a = ap.parse_args()
    if a.tuo:
        tuo(a.tuo)
    if a.karsi:
        karsi(a.karsi)
    if not (a.tuo or a.karsi):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
