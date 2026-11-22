#!/usr/bin/env python3
"""Yhteinen haku: rakennusajo hakee haetut tiedot (rukousajat ja somet) kerran kaikille sivuille (hallinta#45, J5; ADR-0006).

Rakennusajo (rakennusajo.py) kutsuu tätä ennen syötteiden tiivisteitä, koska haetut tiedot ovat sivun syötteitä. Jokaisen
sivun haetut tiedot ovat omassa kansiossaan <haetut>/<nimi>/ samoissa poluissa kuin sivulla (_data/aikataulut, _data/haku,
_data/instagram …), ja rakennuskomento kopioi ne sivulle.

Rukousajat haetaan joka ajossa (tunnin välein):
- Moskeijat ryhmitellään lähteen ja tunnuksen mukaan (rukousajat.ryhma: Masjidbox-tunnus, Mawaqit-tunnus, rukousajat.fi ja
  kaupunki), ja jokainen ryhmä haetaan kerran (rinnakkain).
- Tulos tarkistetaan ja tallennetaan jokaiselle moskeijalle sen omalla nimellä (rukousajat.kasittele): järkevyystarkistus,
  haun tila ja "vanhat kelvolliset ajat jäävät" kuten vanhassa julkaisuajossa (ADR-0004). Moskeija käyttää aina omaa lähdettään
  ja sijaintiaan; ryhmä vain säästää saman haun toistamisen.

Somet (Instagram, YouTube, Telegram) haetaan vain sivuille, joilla on tili, ja vain kun:
- edellisestä hausta on 3 tuntia (SOMET_VALI; jousto JOUSTO, koska tunnin ajastus ei osu minuutilleen), tai
- tilit muuttuivat (uusi tili haetaan heti), tai
- käynnistys pyytää (paneelin Päivitä somet nyt, --somet-nyt), mutta enintään kerran PYYNTO_VALI:ssa.
Hakuaika ja tilien tiiviste tallennetaan sivun kansioon (SOMET_TILA). Myös epäonnistunut haku merkitään, joten estetty tai
rikki oleva lähde yritetään uudelleen vasta 3 tunnin päästä (Instagram estää tiheät haut), ja edelliset julkaisut jäävät sivulle.
Instagram haetaan yksi tili kerrallaan.

Julkinen loki: vain määrät ja sivujen nimet. Lähteiden tunnukset, kaupungit, tilit ja virheiden tiedot menevät sivun
lokitiedostoon (ei julkiseen lokiin). Välimuistiin (haettujen tietojen kansio) tulee vain julkisista lähteistä haettua tietoa,
hakuajat ja tiivisteitä.
"""
import concurrent.futures, copy, datetime, hashlib, json, os, threading, time

import instagram
import rukousajat
import somet as somet_haku

SOMET_VALI = datetime.timedelta(hours=3)
JOUSTO = datetime.timedelta(minutes=10)
PYYNTO_VALI = datetime.timedelta(minutes=10)
SOMET_TILA = "somet-haku.json"


class Sivu:
    """Yksi sivu haussa: nimi, sisältökansio, haettujen tietojen kansio ja lokitiedosto (ei julkinen)."""

    def __init__(self, nimi, sisalto, haetut, loki):
        self.nimi, self.sisalto, self.haetut, self.loki_polku = nimi, sisalto, haetut, loki
        self._lukko = threading.Lock()

    def loki(self, rivi):
        with self._lukko, open(self.loki_polku, "a", encoding="utf-8") as f:
            f.write(rivi.rstrip("\n") + "\n")


def _rinnakkain(n, tehtava, kohteet):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, n)) as tyot:
        return list(tyot.map(tehtava, kohteet))


# ---------------------------------------------------------------- rukousajat
def hae_rukousajat(sivut, rinnakkain=4):
    """Rukousajat kaikille sivuille, kukin lähde kerran. Palauttaa (virheet {nimi: kuvaus}, yhteenveto)."""
    virheet, moskeijat = {}, []
    for s in sivut:
        try:
            moskeijat += [(s, m) for m in rukousajat.moskeijat(s.sisalto)]
        except Exception as e:
            virheet[s.nimi] = f"haku: moskeijan tietoja ei voitu lukea ({type(e).__name__})"
    ryhmat = {}
    for _, (slug, lahde, tunnus, lisa) in moskeijat:
        ryhmat.setdefault(rukousajat.ryhma(lahde, tunnus, lisa), (lahde, tunnus, lisa))

    def hae(avain):
        try:
            return avain, (True, rukousajat.hae_lahde(*ryhmat[avain]))
        except Exception as e:  # käsitellään moskeijoittain (haun tila, vanhat ajat jäävät)
            return avain, (False, e)
    tulokset = dict(_rinnakkain(rinnakkain, hae, list(ryhmat)))

    epaonnistui = 0
    for s, (slug, lahde, tunnus, lisa) in moskeijat:
        onnistui, tulos = tulokset[rukousajat.ryhma(lahde, tunnus, lisa)]

        def ryhman_tulos(*_):
            if not onnistui:
                raise tulos
            return copy.deepcopy(tulos)
        try:
            with open(s.loki_polku, "a", encoding="utf-8") as loki:
                ok, rivi = rukousajat.kasittele(slug, lahde, tunnus, lisa, juuri=s.haetut, haku=ryhman_tulos, loki=loki)
            s.loki(f"rukousajat: {rivi}")
            epaonnistui += 0 if ok else 1
        except Exception as e:  # tallennus kaatui: sivun virhe kuten vanhassa julkaisussa
            virheet[s.nimi] = f"haku: rukousaikojen tallennus epäonnistui ({type(e).__name__})"
    lahteet_epaonnistui = sum(1 for ok, _ in tulokset.values() if not ok)
    return virheet, (f"rukousajat {len(moskeijat)} moskeijaa, {len(ryhmat)} lähdettä"
                     + (f" ({lahteet_epaonnistui} lähdettä ei vastannut, {epaonnistui} moskeijan vanhat ajat jäivät)" if epaonnistui or lahteet_epaonnistui else ""))


# ---------------------------------------------------------------- somet
def _tilit(sisalto):
    """Sivun tilit: [("instagram", tunnus, None) | (laji, url, slug)]."""
    tilit = [("instagram", t, None) for t in instagram.tunnukset(sisalto)]
    for slug, kanavat in somet_haku.moskeijat(sisalto):
        tilit += [(laji, kanavat[laji], slug) for laji in ("youtube", "telegram") if laji in kanavat]
    return tilit


def _lue_aika(arvo):
    try:
        return datetime.datetime.fromisoformat(arvo)
    except Exception:
        return None


def somet_haetaan(tila, tiiviste, nyt, pyydetty):
    """Haetaanko sivun somet nyt: (kyllä/ei, syy). tila: edellinen SOMET_TILA tai {}."""
    edellinen = _lue_aika(tila.get("haettu") or "")
    if not edellinen or tila.get("tilit") != tiiviste:
        return True, "uusi tili" if edellinen else "ei aiempaa hakua"
    if pyydetty and nyt - edellinen >= PYYNTO_VALI:
        return True, "pyynnöstä"
    if nyt - edellinen >= SOMET_VALI - JOUSTO:
        return True, "3 tunnin väli"
    return False, "pyyntö alle 10 min edellisestä" if pyydetty else ""


def hae_somet(sivut, nyt, pyydetyt=(), rinnakkain=4):
    """Somet sivuille, joilla on tili, kun väli tai pyyntö sen sallii. Palauttaa (virheet, yhteenveto)."""
    virheet, haettavat, tilillisia = {}, [], 0
    for s in sivut:
        try:
            tilit = _tilit(s.sisalto)
        except Exception as e:
            virheet[s.nimi] = f"haku: moskeijan tietoja ei voitu lukea ({type(e).__name__})"
            continue
        if not tilit:
            continue
        tilillisia += 1
        tiiviste = hashlib.sha256(json.dumps(sorted(map(list, tilit)), default=str).encode()).hexdigest()
        try:
            with open(os.path.join(s.haetut, SOMET_TILA), encoding="utf-8") as f:
                tila = json.load(f)
        except Exception:
            tila = {}
        haetaan, syy = somet_haetaan(tila if isinstance(tila, dict) else {}, tiiviste, nyt, s.nimi in pyydetyt)
        if syy and not haetaan:
            s.loki(f"somet: ei haeta ({syy})")
        if haetaan:
            haettavat.append((s, tilit, tiiviste, syy))

    instagram_lukko = threading.Lock()  # yksi Instagram-tili kerrallaan (estot)

    def hae(kohde):
        s, tilit, tiiviste, syy = kohde
        onnistui = 0
        with open(s.loki_polku, "a", encoding="utf-8") as loki:
            for laji, tunnus, slug in tilit:
                try:
                    if laji == "instagram":
                        with instagram_lukko:
                            n = instagram.kasittele(tunnus, juuri=s.haetut, loki=loki)
                    else:
                        n = getattr(somet_haku, laji)(slug, tunnus, juuri=s.haetut, loki=loki)
                    loki.write(f"somet: {laji} {tunnus}: {n} kpl\n")
                    onnistui += 1
                except Exception as e:  # edelliset tiedot jäävät voimaan
                    loki.write(f"somet: {laji} {tunnus}: haku epäonnistui, edelliset jäävät ({e})\n")
        os.makedirs(s.haetut, exist_ok=True)
        with open(os.path.join(s.haetut, SOMET_TILA), "w", encoding="utf-8") as f:
            json.dump({"haettu": nyt.isoformat(timespec="seconds"), "tilit": tiiviste}, f)
        return s.nimi, syy, onnistui, len(tilit)
    tulokset = _rinnakkain(rinnakkain, hae, haettavat)
    kuvaus = ", ".join(f"{nimi} ({syy}{'' if ok == n else f', {n - ok}/{n} epäonnistui'})" for nimi, syy, ok, n in tulokset)
    return virheet, f"somet {len(tulokset)}/{tilillisia} sivua, joilla on tili" + (f": {kuvaus}" if kuvaus else "")


def hae(sivut, nyt, pyydetyt=(), rinnakkain=4):
    """Rukousajat ja somet kaikille sivuille. sivut: [Sivu]. nyt: ajon hetki (aikavyöhykkeellinen). pyydetyt: sivujen nimet,
    joiden somet käynnistys pyytää hakemaan heti. Palauttaa (virheet {nimi: kuvaus}, julkinen yhteenveto)."""
    t0 = time.time()
    for s in sivut:
        os.makedirs(s.haetut, exist_ok=True)
    virheet, rk = hae_rukousajat(sivut, rinnakkain)
    v2, so = hae_somet([s for s in sivut if s.nimi not in virheet], nyt, set(pyydetyt), rinnakkain)
    virheet.update(v2)
    return virheet, f"Haku: {rk}; {so}; {time.time() - t0:.1f} s"
