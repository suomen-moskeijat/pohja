#!/usr/bin/env python3
"""Poistaa moskeijan repon (ja sivun). Turvatarkistukset: ei pohjaa/hallintaa, repossa pitää olla _moskeijat/.

Ympäristö: MOSKEIJA_AVAIN, ORG, REPO, SYY ("ei" = merkitään moskeijat.csv:hen tila "ei").
"""
import csv, io, json, os, re, sys, urllib.error, urllib.request

ORG, REPO, SYY = os.environ["ORG"], os.environ["REPO"].strip(), os.environ.get("SYY", "").strip()
AVAIN = os.environ.get("MOSKEIJA_AVAIN")
JUURI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def api(polku, metodi="GET"):
    pyynto = urllib.request.Request("https://api.github.com" + polku, method=metodi, headers={
        "Authorization": f"Bearer {AVAIN}", "Accept": "application/vnd.github+json", "User-Agent": "suomen-moskeijat"})
    with urllib.request.urlopen(pyynto, timeout=30) as v:
        teksti = v.read()
        return json.loads(teksti) if teksti else {}


if not AVAIN:
    sys.exit("MOSKEIJA_AVAIN puuttuu")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", REPO) or REPO.lower() in {"pohja", "hallinta", ".github"}:
    sys.exit(f"Ei poisteta: {REPO}")
try:
    tiedostot = api(f"/repos/{ORG}/{REPO}/contents/_moskeijat")
except urllib.error.HTTPError as e:
    sys.exit(f"Repoa ei löytynyt tai se ei ole moskeijan repo ({e.code})")
if not any(t["name"].endswith(".md") for t in tiedostot):
    sys.exit("Ei moskeijan repo (_moskeijat/*.md puuttuu)")

api(f"/repos/{ORG}/{REPO}", "DELETE")
print(f"Poistettu: {ORG}/{REPO}")

# Moskeijalista: poistettu sivu → repo-sarake tyhjäksi; jos moskeija ei halua sivua, tila "ei"
polku = os.path.join(JUURI, "moskeijat.csv")
with open(polku, encoding="utf-8") as f:
    rivit = list(csv.DictReader(f))
    kentat = list(rivit[0].keys()) if rivit else []
for r in rivit:
    if r.get("repo", "").strip().lower() == REPO.lower():
        if SYY == "ei":
            r["tila"] = "ei"
        elif r.get("tila") in ("luonnos", "ehdotus", "oma"):
            r["tila"] = ""  # sivun voi luoda myöhemmin uudelleen samalla nimellä
ulos = io.StringIO()
w = csv.DictWriter(ulos, fieldnames=kentat, lineterminator="\n")
w.writeheader()
w.writerows(rivit)
with open(polku, "w", encoding="utf-8") as f:
    f.write(ulos.getvalue())
