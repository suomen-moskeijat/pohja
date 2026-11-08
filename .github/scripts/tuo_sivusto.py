#!/usr/bin/env python3
"""Hakee moskeijan nykyiseltä nettisivulta tiedot uutta sivua varten.

    python3 tuo_sivusto.py https://moskeija.fi [--kuvat KANSIO]

Etsii etusivulta ja tärkeimmiltä alasivuilta (Meistä, Yhteystiedot, Toiminta …):
nimen, kuvauksen, logon, osoitteen, puhelimen, sähköpostin, WhatsAppin, somet,
perjantairukouksen ajan, Meistä-tekstin ja valokuvat. WordPress-sivuilta haetaan
lisäksi sivut (omiksi sivuiksi) ja kirjoitukset (moskeijan omiksi artikkeleiksi).
Tulos on arvaus: tarkista ja täydennä Pages CMS:ssä. Ei pakollisia riippuvuuksia
(Pillow-kirjasto, jos asennettu: kuvien koko ja logon värit).
"""
import html
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artikkelit import siivoa, teksti, kuvaus  # noqa: E402  (HTML:n siivous)

try:
    from PIL import Image  # valinnainen
except ImportError:
    Image = None

SELAIN = {"User-Agent": "Mozilla/5.0 (suomen-moskeijat; sivun tuonti)", "Accept-Language": "fi,en;q=0.8"}
AVAINSANAT = {
    "meista": r"meist|tietoa|about|yhdistys|who-we|esittely",
    "yhteys": r"yhtey|contact|ota-yht|kartta|sijainti",
    "toiminta": r"toimin|palvel|opetus|koulu|madrasa|tapahtum|event|ohjelma|kurssi|services",
    "lahjoitus": r"lahjoi|donat|tue-|tuki|support",
}
# WordPress-teemojen esimerkkisisältö ja sivut, jotka pohjassa ovat jo valmiina (rukousajat)
DEMO = r"sample-page|hello-world|lorem|capital-markets|tax-consult|business-consult|finance-manag|resources-no-sidebar|elementor-|social-media-platforms|^shop$|^cart$|rukous-?ajat|prayer-?times|namaz-?vakit"
OHITA_SIVUT = r"my-account|cart|checkout|ostoskori|kassa|login|wp-admin|privacy|tietosuoja|cookie|evaste|feed|xmlrpc|tag/|category/|author/|page/\d"
OHITA_KUVAT = r"logo|icon|favicon|avatar|emoji|sprite|placeholder|arrow|unsplash|pexels|pixabay|stock|shutterstock|adobestock|gemini|chatgpt|dall-?e|ai-generated|banner-ad|\.svg|data:"


# Pohjan omat osoitteet: vanhan sivuston samanniminen sivu tuodaan toisella nimellä
VARATUT = {"tapahtumat": "ohjelma", "palvelut": "toiminta", "artikkelit": "kirjoitukset", "lahjoita": "tue-meita"}
VARATUT_NIMET = {"ohjelma": "Viikko-ohjelma", "toiminta": "Toiminta", "kirjoitukset": "Kirjoitukset", "tue-meita": "Tue meitä"}
VARATUT_KAIKKI = set(VARATUT) | {"rukousajat", "meista", "yhteystiedot", "tietosuoja", "ohjeet", "sitemap", "assets", "tiedostot"}


def tiivista(h):
    """Poistaa sivurakentajien (Elementor ym.) jättämät tyhjät rivit ja sisennykset."""
    h = re.sub(r">\s*\n\s*", ">", h)
    h = re.sub(r"\s*\n\s*<", "<", h)
    h = re.sub(r"[ \t]{2,}", " ", h)
    h = re.sub(r"(</(?:p|h2|h3|h4|ul|ol|li|blockquote)>)", r"\1\n", h)
    # irrallinen sisältö lohkojen välissä (teksti, linkit) omiksi kappaleikseen
    h = re.sub(r"<a [^>]*>\s*</a>", "", h)
    osat, loppu = [], 0
    for m in re.finditer(r"(?s)<(p|h2|h3|h4|ul|ol|blockquote)\b.*?</\1>|<hr>", h):
        osat.append(("irto", h[loppu:m.start()]))
        osat.append(("lohko", m.group(0)))
        loppu = m.end()
    osat.append(("irto", h[loppu:]))
    tulos = []
    for laji, sis in osat:
        sis = sis.strip()
        if not sis:
            continue
        if laji == "lohko":
            tulos.append(sis)
        elif re.sub(r"<[^>]+>", "", sis).strip():
            lyhyt = "<" not in sis and len(sis) < 40
            tulos.append('<p dir="auto">' + ("<strong>" + sis + "</strong>" if lyhyt else sis) + "</p>")
    h = "\n".join(tulos)
    return h.strip()


def kuvan_pisteet(u):
    """Oikeat valokuvat ensin, julisteet ja kuvakaappaukset viimeisiksi."""
    nimi = urllib.parse.unquote(os.path.basename(urllib.parse.urlsplit(u).path)).lower()
    p = 0
    if re.search(r"^(img|dsc|pxl|photo|kuva|foto)[_-]?\d|wa\d{3,}|\d{8}_\d{6}", nimi):
        p += 3
    if re.search(r"eid|ramadan|juliste|poster|flyer|mainos|ilmoitus|event|tapahtuma|kampanja", nimi):
        p -= 3
    if re.search(r"nayttokuva|näyttökuva|screenshot|kuvakaappaus", nimi):
        p -= 1
    if re.search(r"introduction|sample|example|default|template|quran-photo", nimi):
        p -= 2
    return p


def hae(osoite, binaari=False, aikaraja=25):
    req = urllib.request.Request(osoite, headers=SELAIN)
    with urllib.request.urlopen(req, timeout=aikaraja) as v:
        d = v.read()
        if binaari:
            return d
        merkisto = v.headers.get_content_charset() or "utf-8"
        return d.decode(merkisto, "replace")


def puhdas(t):
    return re.sub(r"\s+", " ", html.unescape(t or "")).strip()


def meta(sivu, nimi):
    m = re.search(r'<meta[^>]+(?:property|name)=["\']' + re.escape(nimi) + r'["\'][^>]*content=["\']([^"\']*)', sivu, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\']' + re.escape(nimi) + r'["\']', sivu, re.I)
    return puhdas(m.group(1)) if m else ""


def runko(sivu):
    """Sivun pääsisältö ilman ylä- ja alapalkkia, skriptejä ja valikoita."""
    s = re.sub(r"(?is)<(script|style|noscript|svg|nav|header|footer|form)\b.*?</\1>", " ", sivu)
    m = re.search(r"(?is)<main\b.*?</main>", s) or re.search(r"(?is)<article\b.*?</article>", s)
    return m.group(0) if m else s


def sivun_nimi(otsikko):
    """Otsikosta (esim. "Kotisivu - Moskeija" tai "MOSKEIJA - HELSINKI") moskeijan nimi."""
    osat = [puhdas(o) for o in re.split(r"\s[-|–—:]\s", puhdas(otsikko)) if puhdas(o)]
    osat = [o for o in osat if not re.fullmatch(r"(?i)kotisivu|etusivu|home|welcome|tervetuloa|front page", o)] or osat
    if not osat:
        return ""
    nimi = max(osat, key=len)
    return nimi.title() if nimi.isupper() else nimi


def kappaleet(h, vahintaan=50):
    tulos = []
    for k in re.findall(r"(?is)<(?:p|li|h2|h3)\b[^>]*>(.*?)</(?:p|li|h2|h3)>", h):
        t = puhdas(re.sub(r"<[^>]+>", " ", k))
        if len(t) >= vahintaan and t not in tulos and not re.search(r"cookie|eväste|©|copyright|all rights", t, re.I):
            tulos.append(t)
    return tulos


# ---------------------------------------------------------------- tunnistus
def yhteystiedot(teksti_, sivut_html):
    tiedot = {}
    sp = re.findall(r'mailto:([^"\'?\s>]+)', sivut_html) + re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", teksti_)
    sp = [s.lower().strip(".") for s in sp if not re.search(r"example|sentry|wixpress|domain\.|\.png|\.jpg|@2x", s, re.I)]
    if sp:
        tiedot["sahkoposti"] = max(set(sp), key=sp.count)
    pu = re.findall(r'tel:([+\d\s()-]{7,})', sivut_html) + \
        re.findall(r"(?<!\d)(\+358[\s\d-]{7,14}\d|0[1-9]\d?[\s-]?\d{3}[\s-]?\d{2,4}[\s-]?\d{0,4})(?!\d)", teksti_)
    pu = [re.sub(r"\s+", " ", p).strip() for p in pu if len(re.sub(r"\D", "", p)) >= 8]
    if pu:
        tiedot["puhelin"] = max(set(pu), key=pu.count)
    wa = re.findall(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=)\+?(\d{8,15})", sivut_html)
    if wa:
        n = wa[0]
        tiedot["whatsapp"] = "+" + n if not n.startswith("0") else n
    sana = r"[A-ZÅÄÖ][A-Za-zÅÄÖåäö\-]+"
    paate = r"(?:katu|tie|kuja|polku|tori|väylä|kaari|rinne|ranta|aukio|puistikko|bulevardi|gatan|vägen|gränd|torget)"
    katu = r"(?:" + sana + r"\s)?" + r"[A-Za-zÅÄÖåäö\-]*" + paate + r"\s+\d+\s?[A-Za-z]?(?:\s*[-–]\s*\d+)?(?:\s+[A-Z]\s?\d*\b)?"
    m = re.search(r"(" + katu + r")\s*,?\s*(\d{5})\s+(" + sana + r")", teksti_) or \
        re.search(r"(" + katu + r")\s*,?\s*(" + sana + r")\s*,?\s*(\d{5})\b", teksti_)
    if m:
        a, b, c = (x.strip() for x in m.groups())
        posti, kunta = (b, c) if b.isdigit() else (c, b)
        tiedot["osoite"] = f"{re.sub(chr(32) + '+', ' ', a)}, {posti} {kunta}"
    j = re.search(r"(?is)(jumu.?a|juma|jum'?a|perjantai|friday)[^0-9]{0,80}?\b(1[0-5])[.:](\d{2})\b", teksti_)
    if j:
        tiedot["juma"] = f"{j.group(2)}.{j.group(3)}"
    return tiedot


def somet(sivut_html):
    kuviot = {
        "instagram": r"https?://(?:www\.)?instagram\.com/(?!p/|reel/|explore/|share)[A-Za-z0-9_.]+/?",
        "facebook": r"https?://(?:www\.|m\.)?facebook\.com/(?!sharer|share|dialog|plugins|tr\?)[A-Za-z0-9_.\-/]+",
        "youtube": r"https?://(?:www\.)?youtube\.com/(?:@[\w.-]+|channel/UC[\w-]{22}|c/[\w.-]+|user/[\w.-]+)",
        "tiktok": r"https?://(?:www\.)?tiktok\.com/@[\w.]+",
        "telegram": r"https?://t\.me/(?!share)[A-Za-z0-9_]{4,}",
        "x": r"https?://(?:www\.)?(?:x|twitter)\.com/(?!share|intent|home)[A-Za-z0-9_]{2,}",
        "snapchat": r"https?://(?:www\.)?snapchat\.com/add/[\w.-]+",
        "whatsapp_kanava": r"https?://(?:www\.)?whatsapp\.com/channel/[\w]+",
    }
    tulos = {}
    for nimi, k in kuviot.items():
        loydot = re.findall(k, sivut_html)
        if loydot:
            tulos[nimi] = max(set(loydot), key=loydot.count).rstrip("/") + ("/" if nimi == "instagram" else "")
    return tulos


def kuvien_osoitteet(sivu, perus):
    osoitteet = []
    for tag in re.findall(r"(?is)<img\b[^>]*>", sivu):
        src = None
        ss = re.search(r'(?:data-)?srcset=["\']([^"\']+)', tag)
        if ss:  # suurin srcset-vaihtoehto
            vaiht = [(int(w), u) for u, w in re.findall(r"(\S+)\s+(\d+)w", ss.group(1))]
            if vaiht:
                src = max(vaiht)[1]
        if not src:
            m = re.search(r'(?:data-src|data-lazy-src|src)=["\']([^"\']+)', tag)
            src = m.group(1) if m else None
        alt = re.search(r'alt=["\']([^"\']*)', tag)
        if src:
            osoitteet.append((urllib.parse.urljoin(perus, html.unescape(src)), (alt.group(1) if alt else "") + " " + tag))
    for u in re.findall(r"background-image:\s*url\(\s*['\"]?([^'\")]+)", html.unescape(sivu)):
        osoitteet.append((urllib.parse.urljoin(perus, u.strip()), ""))
    return osoitteet


def alkuperainen(u):
    """WordPressin pienennöksestä alkuperäinen (kuva-300x200.jpg → kuva.jpg)."""
    return re.sub(r"-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp)$)", "", u, flags=re.I)


def logo(sivu, perus):
    for tag in re.findall(r"(?is)<img\b[^>]*>", sivu[:60000]):
        if re.search(r"logo", tag, re.I):
            m = re.search(r'(?:data-src|src)=["\']([^"\']+)', tag)
            if m and not m.group(1).startswith("data:"):
                return alkuperainen(urllib.parse.urljoin(perus, html.unescape(m.group(1))))
    m = re.search(r'<link[^>]+rel=["\'](?:apple-touch-icon|icon)["\'][^>]*href=["\']([^"\']+)', sivu, re.I)
    return urllib.parse.urljoin(perus, m.group(1)) if m else ""


def varit(data):
    """Logon kaksi hallitsevaa väriä (tumma pääväri ja korostus), jos Pillow on asennettu."""
    if not Image:
        return {}
    try:
        k = Image.open(io.BytesIO(data)).convert("RGBA")
        k.thumbnail((200, 200))
        laskut = {}
        for r, g, b, a in (k.get_flattened_data() if hasattr(k, 'get_flattened_data') else k.getdata()):
            if a < 200 or (r > 225 and g > 225 and b > 225) or max(r, g, b) - min(r, g, b) < 30:
                continue  # läpinäkyvä, valkoinen tai harmaa
            avain = (r // 24 * 24, g // 24 * 24, b // 24 * 24)
            laskut[avain] = laskut.get(avain, 0) + 1
        if not laskut:
            return {}
        jarj = sorted(laskut, key=laskut.get, reverse=True)
        def hexi(c): return "#%02x%02x%02x" % c
        def kirkkaus(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
        korostus = jarj[0]
        tumma = tuple(int(v * 0.32) for v in korostus)  # pääväri: korostuksen tumma sävy
        vaalea = tuple(int(v + (255 - v) * 0.88) for v in korostus)
        if kirkkaus(korostus) < 70:  # logo on jo tumma: se pääväriksi, korostus vaaleammaksi
            tumma, korostus = korostus, tuple(min(255, int(v + (255 - v) * 0.45)) for v in korostus)
        return {"paa": hexi(tumma), "korostus": hexi(korostus), "korostus_vaalea": hexi(vaalea)}
    except Exception:
        return {}


# ---------------------------------------------------------------- WordPress
def wordpress(perus):
    try:
        juuri = json.loads(hae(perus.rstrip("/") + "/wp-json/"))
    except Exception:
        return None
    wp = {"nimi": puhdas(juuri.get("name")), "kuvaus": puhdas(juuri.get("description")), "sivut": [], "kirjoitukset": []}
    try:
        for s in json.loads(hae(perus.rstrip("/") + "/wp-json/wp/v2/pages?per_page=50&_fields=slug,title,content,link")):
            wp["sivut"].append({"slug": s["slug"], "nimi": puhdas(s["title"]["rendered"]), "html": s["content"]["rendered"], "url": s["link"]})
    except Exception:
        pass
    try:
        for s in json.loads(hae(perus.rstrip("/") + "/wp-json/wp/v2/posts?per_page=50&_fields=slug,title,content,date,link")):
            wp["kirjoitukset"].append({"slug": s["slug"], "nimi": puhdas(s["title"]["rendered"]), "html": s["content"]["rendered"],
                                       "paiva": s["date"][:10], "url": s["link"]})
    except Exception:
        pass
    return wp


# ---------------------------------------------------------------- pääfunktio
def tuo(osoite, kuvakansio=None, enintaan_kuvia=6):
    if not re.match(r"https?://", osoite):
        osoite = "https://" + osoite
    etusivu = hae(osoite)
    perus = osoite
    isanta = urllib.parse.urlsplit(osoite).netloc.replace("www.", "")
    tulos = {"nettisivu": osoite, "lahde_sivut": [osoite]}

    # alasivut: tärkeimmät linkit samasta osoitteesta
    linkit = []
    for href, nimi in re.findall(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', etusivu):
        u = urllib.parse.urljoin(perus, html.unescape(href)).split("#")[0]
        if urllib.parse.urlsplit(u).netloc.replace("www.", "") != isanta or re.search(OHITA_SIVUT, u, re.I):
            continue
        if re.search(r"\.(pdf|jpe?g|png|zip|docx?)$", u, re.I) or u.rstrip("/") == osoite.rstrip("/"):
            continue
        if u not in [l[0] for l in linkit]:
            linkit.append((u, puhdas(re.sub(r"<[^>]+>", " ", nimi))))
    sivut = {osoite: etusivu}
    for laji, kuvio in AVAINSANAT.items():
        for u, nimi in linkit:
            if (re.search(kuvio, urllib.parse.urlsplit(u).path, re.I) or re.search(kuvio, nimi, re.I)) and u not in sivut and len(sivut) < 9:
                try:
                    sivut[u] = hae(u)
                except Exception as e:
                    print(f"  sivua ei saatu: {u}: {e}", file=sys.stderr)
    tulos["lahde_sivut"] = list(sivut)
    kaikki_html = "\n".join(sivut.values())
    kaikki_teksti = puhdas(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", kaikki_html)))

    wp = wordpress(perus)
    tulos["nimi"] = (wp or {}).get("nimi") or meta(etusivu, "og:site_name") or sivun_nimi(meta(etusivu, "og:title") or
                                                                            (re.search(r"(?is)<title>(.*?)</title>", etusivu) or [None, ""])[1])
    k = meta(etusivu, "og:description") or meta(etusivu, "description") or (wp or {}).get("kuvaus", "")
    if 20 <= len(k) <= 220:
        tulos["esittely"] = k
    tulos.update(yhteystiedot(kaikki_teksti, kaikki_html))
    tulos["some"] = somet(kaikki_html)

    # Meistä-teksti: Meistä-sivun kappaleet, muuten etusivun
    meista_html = next((h for u, h in sivut.items() if u != osoite and re.search(AVAINSANAT["meista"], urllib.parse.urlsplit(u).path, re.I)), None)
    kpl = kappaleet(runko(meista_html)) if meista_html else []
    if len(" ".join(kpl)) < 120:
        kpl = kappaleet(runko(etusivu), 60)
    if kpl:
        tulos["meista"] = "\n\n".join(kpl[:8])[:2500]

    # omat sivut (WordPress): muut sisältösivut, joita uudessa pohjassa ei ole valmiina
    tulos["omat_sivut"] = []
    if wp:
        valmiit = AVAINSANAT["meista"] + "|" + AVAINSANAT["yhteys"] + "|" + AVAINSANAT["lahjoitus"] + "|koti|home|etusivu|front"
        for s in wp["sivut"]:
            if re.search(OHITA_SIVUT, s["slug"]) or re.search(DEMO, s["slug"], re.I) or re.search(valmiit, s["slug"] + " " + s["nimi"], re.I):
                continue
            h = tiivista(siivoa(s["html"], perus.rstrip("/")))
            if len(teksti(h)) >= 120:
                slug = VARATUT.get(s["slug"], s["slug"] + "-sivu" if s["slug"] in VARATUT_KAIKKI else s["slug"])
                nimi = VARATUT_NIMET.get(slug, s["nimi"]) if slug != s["slug"] else s["nimi"]
                tulos["omat_sivut"].append({"slug": slug, "nimi": nimi, "html": h, "url": s["url"]})
        tulos["artikkelit"] = []
        for s in wp["kirjoitukset"]:
            if re.search(DEMO, s["slug"], re.I) or re.search(r"(?i)lorem ipsum", s["html"]):
                continue
            h = tiivista(siivoa(s["html"], perus.rstrip("/")))
            if len(teksti(h)) >= 120:
                tulos["artikkelit"].append({"slug": s["slug"], "nimi": s["nimi"], "html": h, "paiva": s["paiva"],
                                            "kuvaus": kuvaus(h, s["nimi"]), "url": s["url"]})

    # logo ja kuvat
    tulos["logo_url"] = logo(etusivu, perus)
    ehdokkaat = []
    for h in sivut.values():
        for u, konteksti in kuvien_osoitteet(h, perus):
            u = alkuperainen(u)
            if not re.search(r"\.(jpe?g|png|webp)(\?|$)", u, re.I) or re.search(OHITA_KUVAT, u + " " + konteksti, re.I):
                continue
            if u != tulos["logo_url"] and u not in ehdokkaat:
                ehdokkaat.append(u)
    tulos["kuva_ehdokkaat"] = sorted(ehdokkaat, key=kuvan_pisteet, reverse=True)
    if kuvakansio:
        tulos.update(lataa_kuvat(tulos, kuvakansio, enintaan_kuvia))
    return tulos


def lataa_kuvat(tulos, kansio, enintaan):
    os.makedirs(kansio, exist_ok=True)
    valmiit = {"kuvat": [], "logo": "", "teema": {}}
    if tulos.get("logo_url"):
        try:
            d = hae(tulos["logo_url"], binaari=True)
            if len(d) > 500:
                paate = os.path.splitext(urllib.parse.urlsplit(tulos["logo_url"]).path)[1].lower() or ".png"
                open(os.path.join(kansio, "logo" + paate), "wb").write(d)
                valmiit["logo"] = "logo" + paate
                valmiit["teema"] = varit(d)
        except Exception as e:
            print(f"  logoa ei saatu: {e}", file=sys.stderr)
    for u in tulos.get("kuva_ehdokkaat", []):
        if len(valmiit["kuvat"]) >= enintaan:
            break
        try:
            d = hae(u, binaari=True)
        except Exception:
            continue
        if len(d) < 40000:  # pienet kuvakkeet ja pikkukuvat pois
            continue
        nimi = f"kuva-{len(valmiit['kuvat']) + 1}.jpg"
        if Image:
            try:
                k = Image.open(io.BytesIO(d))
                if min(k.size) < 400 or k.size[0] / k.size[1] > 3 or k.size[1] / k.size[0] > 3:
                    continue
                k = k.convert("RGB")
                k.thumbnail((1600, 1600))
                b = io.BytesIO()
                k.save(b, "JPEG", quality=82, optimize=True)  # ilman EXIF-tietoja (sijainti)
                d = b.getvalue()
            except Exception:
                continue
        open(os.path.join(kansio, nimi), "wb").write(d)
        valmiit["kuvat"].append(nimi)
    return valmiit


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("osoite")
    ap.add_argument("--kuvat")
    a = ap.parse_args()
    t = tuo(a.osoite, a.kuvat)
    for k in ("omat_sivut", "artikkelit"):
        if t.get(k):
            t[k] = [{x: (v[:80] + "…" if isinstance(v, str) and len(v) > 80 else v) for x, v in s.items()} for s in t[k]]
    t["kuva_ehdokkaat"] = t.get("kuva_ehdokkaat", [])[:10]
    print(json.dumps(t, ensure_ascii=False, indent=1))
