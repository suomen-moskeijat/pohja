#!/usr/bin/env python3
"""Kieliversiot omiin osoitteisiin: /sivu/ → /en/sivu/, /ar/sivu/, /so/sivu/ (Jekyllin rakentaman sivun jälkeen).

Sivupohja kirjoittaa käännettäviin sivuihin <meta name="kieliversiot" content="en,ar" data-juuri="/repo">,
hreflang-linkit ja #kieliseo-tiedot (kunkin kielen otsikko ja kuvaus). Tämä skripti kopioi sivut kielikansioihin ja
- asettaa <html lang/dir> ja data-url-kieli (sivu näkyy heti oikealla kielellä myös ilman JavaScriptiä),
- vaihtaa otsikon, kuvauksen, canonicalin, og:url:n ja og:localen kielen mukaan,
- ohjaa sivujen väliset linkit saman kielen versioihin,
- lisää kieliversiot sivukarttaan (hreflang-vaihtoehdot).
Käyttö: python3 kieliversiot.py <_site-kansio>
"""
import html, json, os, re, sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "_site"
LOKAALIT = {"fi": "fi_FI", "en": "en_GB", "ar": "ar_AR", "so": "so_SO"}
META = re.compile(r'<meta name="kieliversiot" content="([a-z,]*)" data-juuri="([^"]*)">')

sivut = {}  # polku (esim. /meista/) → (tiedosto, kielet, juuri)
for kansio, _, tiedostot in os.walk(SITE):
    for nimi in tiedostot:
        if not nimi.endswith(".html"):
            continue
        tiedosto = os.path.join(kansio, nimi)
        with open(tiedosto, encoding="utf-8") as f:
            alku = f.read(20000)
        m = META.search(alku)
        if not m or not m.group(1):
            continue
        suht = "/" + os.path.relpath(tiedosto, SITE).replace(os.sep, "/")
        polku = suht[: -len("index.html")] if suht.endswith("/index.html") else suht
        sivut[polku] = (tiedosto, m.group(1).split(","), m.group(2))

if not sivut:
    print("Kieliversiot: ei käännettäviä sivuja (yksi kieli)")
    sys.exit(0)
juuri = next(iter(sivut.values()))[2]
kielet = sorted({k for _, kl, _ in sivut.values() for k in kl})


def korvaa_meta(teksti, nimi, arvo, attr="property"):
    return re.sub(r'(<meta %s="%s" content=")[^"]*(")' % (attr, re.escape(nimi)), lambda m: m.group(1) + html.escape(arvo, quote=True) + m.group(2), teksti)


def linkit(teksti, kieli):
    # href="<juuri>/polku/" → href="<juuri>/<kieli>/polku/", jos polulla on kieliversio
    def vaihda(m):
        polku, loppu = m.group(1), m.group(2) or ""
        return f'href="{juuri}/{kieli}{polku}{loppu}"' if polku in sivut else m.group(0)
    teksti = re.sub(r'href="' + re.escape(juuri) + r'(/[^"#?]*)([#?][^"]*)?"', vaihda, teksti)
    return teksti


tehty = 0
for polku, (tiedosto, kl, _) in sivut.items():
    with open(tiedosto, encoding="utf-8") as f:
        alkuperainen = f.read()
    seo = {}
    m = re.search(r'<script type="application/json" id="kieliseo">(.*?)</script>', alkuperainen, re.S)
    if m:
        try:
            seo = json.loads(m.group(1))
        except ValueError:
            seo = {}
    kanoninen = re.search(r'<link rel="canonical" href="([^"]*)">', alkuperainen)
    for kieli in kl:
        t = alkuperainen
        t = re.sub(r'<html lang="[a-z]+" dir="[a-z]+"', f'<html lang="{kieli}" dir="{"rtl" if kieli == "ar" else "ltr"}" data-url-kieli="{kieli}"', t, count=1)
        s = seo.get(kieli, {})
        if s.get("t"):
            t = re.sub(r"<title>.*?</title>", lambda _: f"<title>{html.escape(s['t'], quote=False)}</title>", t, count=1, flags=re.S)
            t = korvaa_meta(t, "og:title", s["t"])
        if s.get("d"):
            t = korvaa_meta(t, "description", s["d"], "name")
            t = korvaa_meta(t, "og:description", s["d"])
        if kanoninen:
            uusi = kanoninen.group(1).replace(f"{juuri}{polku}", f"{juuri}/{kieli}{polku}", 1) if f"{juuri}{polku}" in kanoninen.group(1) else kanoninen.group(1)
            t = t.replace(kanoninen.group(0), f'<link rel="canonical" href="{uusi}">', 1)
            t = korvaa_meta(t, "og:url", uusi)
        t = korvaa_meta(t, "og:locale", LOKAALIT.get(kieli, "en_GB"))
        t = linkit(t, kieli)
        # hreflang-linkit pysyvät absoluuttisina (ne eivät ala href="<juuri>/…") – tarkistetaan silti
        kohde = os.path.join(SITE, kieli, polku.lstrip("/"))
        if polku.endswith("/"):
            kohde = os.path.join(kohde, "index.html")
        os.makedirs(os.path.dirname(kohde), exist_ok=True)
        with open(kohde, "w", encoding="utf-8") as f:
            f.write(t)
        tehty += 1

# Sivukartta: kieliversiot ja hreflang-vaihtoehdot
kartta = os.path.join(SITE, "sitemap.xml")
if os.path.exists(kartta):
    with open(kartta, encoding="utf-8") as f:
        xml = f.read()
    xml = xml.replace('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">', 1)

    def laajenna(m):
        url = m.group(0)
        loc = re.search(r"<loc>([^<]*)</loc>", url).group(1)
        osat = re.match(r"(https?://[^/]+)(.*)$", loc)
        if not osat:
            return url
        origin, p = osat.groups()
        polku = p[len(juuri):] if juuri and p.startswith(juuri) else p
        if polku not in sivut:
            return url
        kl = ["fi"] + sivut[polku][1]
        osoite = lambda k: loc if k == "fi" else f"{origin}{juuri}/{k}{polku}"
        vaihtoehdot = "".join(f'<xhtml:link rel="alternate" hreflang="{k}" href="{osoite(k)}"/>' for k in kl)
        lisat = "\n  ".join(re.sub(r"<loc>[^<]*</loc>", f"<loc>{osoite(k)}</loc>", url).replace("</url>", vaihtoehdot + "</url>") for k in kl[1:])
        return url.replace("</url>", vaihtoehdot + "</url>") + "\n  " + lisat

    xml = re.sub(r"<url>.*?</url>", laajenna, xml, flags=re.S)
    with open(kartta, "w", encoding="utf-8") as f:
        f.write(xml)
print(f"Kieliversiot: {len(sivut)} sivua × {', '.join(kielet)} = {tehty} kieliversiota")
