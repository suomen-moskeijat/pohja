#!/usr/bin/env python3
"""Kaikkien moskeijasivujen hakemisto: https://suomen-moskeijat.github.io/pohja/

    python3 hakemisto.py KOHDE.html

Listaa organisaation moskeijarepot (tila: Julkaistu / Luonnos / Ehdotus) ja listan
moskeijat.csv moskeijat, joilla ei vielä ole sivua. Linkit: sivu, muokkaus (Pages CMS)
ja repo. Ajetaan Esittelysivu-työnkulussa (GITHUB_TOKEN lukee repot).
"""
import csv
import html
import json
import os
import re
import sys
import urllib.request

POHJA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORG = os.environ.get("ORG", "suomen-moskeijat")
EI_MOSKEIJOITA = {"pohja", ".github"}


def hae(osoite, json_=True):
    otsakkeet = {"User-Agent": "suomen-moskeijat"}
    if os.environ.get("GITHUB_TOKEN") and "api.github.com" in osoite:
        otsakkeet["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(osoite, headers=otsakkeet), timeout=30) as v:
        d = v.read().decode("utf-8", "replace")
    return json.loads(d) if json_ else d


def etu(teksti):
    """Yksinkertainen front matter -luku (title, kaupunki, luonnos, ehdotus)."""
    m = re.match(r"---\s*\n(.*?)\n---", teksti, re.S)
    tulos = {}
    for rivi in (m.group(1) if m else "").splitlines():
        k = re.match(r"^(title|kaupunki|luonnos|ehdotus):\s*(.*?)\s*(#.*)?$", rivi)
        if k:
            tulos[k.group(1)] = k.group(2).strip().strip('"').strip("'")
    return tulos


def repot():
    tulos, sivu = [], 1
    while True:
        osa = hae(f"https://api.github.com/orgs/{ORG}/repos?per_page=100&page={sivu}&type=public")
        tulos += osa
        if len(osa) < 100:
            return tulos
        sivu += 1


def main():
    kohde = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    lista = {r["repo"].strip().lower(): r for r in csv.DictReader(open(os.path.join(POHJA, "moskeijat.csv"), encoding="utf-8"))}
    rivit = []
    try:
        kaikki = repot()
    except Exception as e:
        print(f"Repoja ei saatu: {e}", file=sys.stderr)
        kaikki = []
    for r in kaikki:
        nimi = r["name"]
        if nimi in EI_MOSKEIJOITA or r.get("archived"):
            continue
        try:
            tiedostot = hae(f"https://api.github.com/repos/{ORG}/{nimi}/contents/_moskeijat")
            md = next(t for t in tiedostot if t["name"].endswith(".md"))
            e = etu(hae(md["download_url"], json_=False))
        except Exception:
            continue  # ei moskeijarepo
        tila = "ehdotus" if e.get("ehdotus") == "true" else "luonnos" if e.get("luonnos") == "true" else "julkaistu"
        l = lista.pop(nimi.lower(), {})
        rivit.append({"nimi": e.get("title") or l.get("nimi") or nimi, "kaupunki": e.get("kaupunki") or l.get("kaupunki", ""),
                      "tila": tila, "sivu": f"https://{ORG.lower()}.github.io/{nimi}/",
                      "cms": f"https://app.pagescms.org/{ORG}/{nimi}", "repo": f"https://github.com/{ORG}/{nimi}"})
    for l in lista.values():  # listalla, ei vielä sivua (tila "ei" = moskeija ei halua sivua)
        if l.get("tila", "").strip() == "ei":
            continue
        rivit.append({"nimi": l["nimi"], "kaupunki": l["kaupunki"], "tila": "ei-sivua", "sivu": "", "cms": "", "repo": ""})
    rivit.sort(key=lambda x: (x["kaupunki"], x["nimi"].lower()))
    maarat = {t: sum(1 for x in rivit if x["tila"] == t) for t in ("julkaistu", "luonnos", "ehdotus", "ei-sivua")}
    NIMET = {"julkaistu": "Julkaistu", "luonnos": "Luonnos", "ehdotus": "Ehdotus", "ei-sivua": "Ei sivua"}
    kaupungit, nyt = [], None
    for x in rivit:
        if x["kaupunki"] != nyt:
            nyt = x["kaupunki"]
            kaupungit.append(f'<h2 data-kaupunki>{html.escape(nyt or "–")}</h2>')
        linkit = (f'<a href="{x["sivu"]}">Sivu</a><a href="{x["cms"]}">Muokkaa</a><a href="{x["repo"]}">Repo</a>'
                  if x["sivu"] else '<span class="hiljaa">Luo: Actions → Luo ehdotussivut listasta</span>')
        kaupungit.append(f'<div class="rivi" data-tila="{x["tila"]}"><div><strong>{html.escape(x["nimi"])}</strong>'
                         f'<span class="tila {x["tila"]}">{NIMET[x["tila"]]}</span></div><div class="linkit">{linkit}</div></div>')
    napit = "".join(f'<button type="button" data-suodatin="{t}" aria-pressed="false">{NIMET[t]} {n}</button>' for t, n in maarat.items() if n)
    sivu = f"""<!doctype html>
<html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Suomen moskeijat – sivut</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Manrope:wght@400;600;700&display=swap">
<style>
:root{{--paa:#3f2717;--kulta:#c9a46a;--kerma:#faf6ee;--raja:#ebe3da;--hieno:#6f5b4c}}
*{{box-sizing:border-box}} body{{margin:0;font:16px/1.55 Manrope,system-ui,sans-serif;color:#2b1a0e;background:var(--kerma)}}
.k{{max-width:860px;margin:0 auto;padding:28px 16px 64px}} h1,h2{{font-family:Sora,sans-serif;color:var(--paa);line-height:1.2}}
h1{{font-size:clamp(26px,6vw,36px);margin:0 0 6px}} h2{{font-size:18px;margin:26px 0 8px}}
.yla{{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}} .yla a{{padding:10px 16px;border-radius:999px;background:var(--paa);color:#fff;text-decoration:none;font-weight:700}}
.yla a.toinen{{background:#fff;color:var(--paa);border:1px solid var(--raja)}}
.suodatin{{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 4px}} .suodatin button{{min-height:38px;padding:6px 14px;border:1px solid var(--raja);border-radius:999px;background:#fff;font:600 14px Manrope,sans-serif;color:var(--paa);cursor:pointer}}
.suodatin button[aria-pressed=true]{{background:var(--paa);color:#fff;border-color:var(--paa)}}
.rivi{{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px 16px;padding:12px 16px;margin:6px 0;background:#fff;border:1px solid var(--raja);border-radius:16px}}
.rivi strong{{margin-inline-end:8px}} .tila{{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12.5px;font-weight:700}}
.julkaistu{{background:#e3f4e8;color:#1e6b36}} .luonnos{{background:#fff4d6;color:#6b4e00}} .ehdotus{{background:#eee8f8;color:#4b3684}} .ei-sivua{{background:#f1eeea;color:var(--hieno)}}
.linkit{{display:flex;gap:6px}} .linkit a{{padding:6px 12px;border-radius:999px;border:1px solid var(--raja);color:var(--paa);text-decoration:none;font-weight:600;font-size:14px}}
.hiljaa{{color:var(--hieno);font-size:13px}} .selite{{color:var(--hieno);font-size:14px}} [hidden]{{display:none!important}}
</style></head><body><div class="k">
<h1>Suomen moskeijoiden nettisivut</h1>
<p class="selite">Kaikki sivut ja niiden tila. <b>Ehdotus</b> = esimerkkisivu, moskeija ei vielä mukana · <b>Luonnos</b> = moskeija tarkistaa · <b>Julkaistu</b> = valmis ja Googlessa.</p>
<div class="yla"><a href="ohjeet/">Ohjeet</a><a class="toinen" href="hallinta/">Hallintapaneeli (malli)</a><a class="toinen" href="https://github.com/{ORG}/pohja/actions">Lisää moskeija (Actions)</a><a class="toinen" href="https://app.pagescms.org">Pages CMS</a></div>
<div class="suodatin"><button type="button" data-suodatin="" aria-pressed="true">Kaikki {len(rivit)}</button>{napit}</div>
{''.join(kaupungit)}
<p class="selite" style="margin-top:28px">Esimerkit: <a href="masjid-sunnah/">Masjid Sunnah</a> · <a href="hyvinkaa/">Hyvinkää</a>. Päivittyy automaattisesti.</p>
</div>
<script>
document.querySelectorAll('[data-suodatin]').forEach(function(b){{b.addEventListener('click',function(){{
  var t=b.getAttribute('data-suodatin');
  document.querySelectorAll('[data-suodatin]').forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});
  document.querySelectorAll('.rivi').forEach(function(r){{r.hidden=!!t&&r.getAttribute('data-tila')!==t}});
  document.querySelectorAll('[data-kaupunki]').forEach(function(h){{var n=h.nextElementSibling,nak=false;while(n&&n.classList.contains('rivi')){{if(!n.hidden)nak=true;n=n.nextElementSibling}}h.hidden=!nak}});
}})}});
</script></body></html>"""
    with open(kohde, "w", encoding="utf-8") as f:
        f.write(sivu)
    print(f"Hakemisto: {len(rivit)} moskeijaa ({maarat})")


if __name__ == "__main__":
    main()
