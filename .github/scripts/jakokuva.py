#!/usr/bin/env python3
"""Automaattinen jakokuva (1200 × 630) jokaiselle moskeijalle julkaisun yhteydessä: sivu/jakokuva.jpg.

Näkyy, kun sivun linkki jaetaan (WhatsApp, Facebook, viestit), jos moskeija ei ole valinnut omaa jakokuvaa
(Haku ja jakaminen) tai etusivun taustakuvaa. Kuvassa moskeijan värit, kuvio, logo, nimi ja kaupunki.
Fontit: .github/fontit (Sora, Manrope – SIL Open Font License). Lopuksi _config.yml:ään `jakokuva_auto: true`.
Käyttö: python3 jakokuva.py <sivun kansio>
"""
import math, os, re, sys

juuri = sys.argv[1] if len(sys.argv) > 1 else "."
try:
    import yaml
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"Jakokuva ohitettu: {e}")
    sys.exit(0)

FONTIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fontit")


def fontti(nimi, koko, paino):
    try:
        f = ImageFont.truetype(os.path.join(FONTIT, nimi), koko)
    except OSError:  # varafontti, jos pohjan fontit puuttuvat
        return ImageFont.truetype("DejaVuSans-Bold.ttf", koko)
    try:
        f.set_variation_by_name(paino)
    except Exception:
        pass
    return f


def vari(hex_, oletus):
    h = str(hex_ or "").strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if re.fullmatch(r"[0-9a-fA-F]{6}", h) else oletus


config = open(os.path.join(juuri, "_config.yml"), encoding="utf-8").read()
slug = (re.findall(r"^moskeija:\s*([A-Za-z0-9_-]+)", config, re.M) or [""])[-1]
url = (re.findall(r'^url:\s*"?([^"\s]+)', config, re.M) or [""])[-1]
baseurl = (re.findall(r'^baseurl:\s*"?([^"\s]*)"?', config, re.M) or [""])[-1]
md = os.path.join(juuri, "_moskeijat", f"{slug}.md")
if not slug or not os.path.exists(md):
    print("Jakokuva ohitettu: moskeijan tiedostoa ei löytynyt")
    sys.exit(0)
teksti = open(md, encoding="utf-8").read()
m = yaml.safe_load(re.match(r"^---\s*\n(.*?)\n---", teksti, re.S).group(1)) or {}
t = m.get("teema") or {}
teemat = {}
try:
    teemat = yaml.safe_load(open(os.path.join(juuri, "_data", "teemat.yml"), encoding="utf-8")) or {}
except Exception:
    pass
valmis = teemat.get(t.get("vari")) if t.get("vari") not in (None, "", "oma") else None
lahde = valmis or t
paa = vari(lahde.get("paa"), (63, 39, 23))
tumma = vari(lahde.get("paa_tumma"), tuple(max(0, c - 22) for c in paa))
korostus = vari(lahde.get("korostus"), (222, 187, 134))

W, H = 1200, 630
kuva = Image.new("RGB", (W, H), paa)
# Liukuväri päävärista tummaan
liuku = Image.linear_gradient("L").resize((W, H))
kuva = Image.composite(Image.new("RGB", (W, H), tumma), kuva, liuku)
# Hehku oikeassa yläkulmassa
hehku = Image.new("L", (W, H), 0)
ImageDraw.Draw(hehku).ellipse((W * 0.55, -H * 0.6, W * 1.25, H * 0.7), fill=70)
from PIL import ImageFilter
hehku = hehku.filter(ImageFilter.GaussianBlur(120))
kuva = Image.composite(Image.new("RGB", (W, H), korostus), kuva, hehku)
# Kahdeksansakarainen tähtikuvio korostusvärillä
kerros = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(kerros)
vali, r = 84, 26
for rivi in range(-1, H // vali + 2):
    for sarake in range(-1, W // vali + 2):
        cx, cy = sarake * vali + (vali / 2 if rivi % 2 else 0), rivi * vali
        for kulma0 in (0, 45):
            pisteet = [(cx + r * math.cos(math.radians(kulma0 + 90 * i)), cy + r * math.sin(math.radians(kulma0 + 90 * i))) for i in range(4)]
            d.polygon(pisteet, outline=korostus + (46,), width=2)
kuva = Image.alpha_composite(kuva.convert("RGBA"), kerros).convert("RGB")
d = ImageDraw.Draw(kuva)

y = 110
logo = t.get("logo_vaalea") or t.get("logo")
if logo and str(logo).startswith("/"):
    polku = os.path.join(juuri, str(logo).lstrip("/"))
    if os.path.exists(polku):
        try:
            l = Image.open(polku).convert("RGBA")
            lh = 120
            lw = min(440, int(l.width * lh / l.height))
            l = l.resize((lw, int(l.height * lw / l.width)) if lw == 440 else (lw, lh))
            if not t.get("logo_vaalea"):
                d.rounded_rectangle((80 - 18, y - 18, 80 + l.width + 18, y + l.height + 18), 14, fill=(255, 255, 255))
            kuva.paste(l, (80, y), l)
            y += l.height + 64
        except Exception as e:
            print(f"  logo ohitettu: {e}")
if y == 110:
    y = 190

nimi = str(m.get("title") or slug)
koko = 70 if len(nimi) <= 26 else 58
f_nimi = fontti("Sora.ttf", koko, "ExtraBold")
rivit, nyk = [], ""
for sana in nimi.split():
    koe = (nyk + " " + sana).strip()
    if d.textlength(koe, font=f_nimi) > W - 160 and nyk:
        rivit.append(nyk); nyk = sana
    else:
        nyk = koe
rivit.append(nyk)
for i, rv in enumerate(rivit[:2]):
    d.text((80, y + i * (koko + 12)), rv, font=f_nimi, fill=(255, 255, 255))

d.rectangle((80, 470, 200, 476), fill=korostus)
kaupunki = str(m.get("kaupunki") or "")
d.text((80, 496), f"Moskeija · {kaupunki}" if kaupunki else "Moskeija", font=fontti("Manrope.ttf", 32, "Bold"), fill=korostus)
d.text((80, 546), "Rukousajat · Toiminta · Tapahtumat", font=fontti("Manrope.ttf", 26, "SemiBold"), fill=(235, 235, 235))
osoite = re.sub(r"^https?://", "", (url + baseurl).rstrip("/"))
f_os = fontti("Manrope.ttf", 22, "SemiBold")
d.text((W - 60 - d.textlength(osoite, font=f_os), H - 56), osoite, font=f_os, fill=(200, 200, 200))

kuva.save(os.path.join(juuri, "jakokuva.jpg"), "JPEG", quality=86, optimize=True, progressive=True)
with open(os.path.join(juuri, "_config.yml"), "a", encoding="utf-8") as f:
    f.write("\njakokuva_auto: true\n")
print(f"Jakokuva luotu: {nimi}")
