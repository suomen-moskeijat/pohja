# Ohjeet Claudelle: pohja (moskeijoiden sivupohja)

## Ulkoasu: käytä aina unslop-taitoa
Kaikissa ulkoasuun vaikuttavissa muutoksissa (CSS, sivupohjat, osiot, uudet sivut ja ominaisuudet)
käytetään taitoa `.claude/skills/unslop` (SKILL.md):
1. Katso sivu selaimessa tietokoneella (1440 px) ja puhelimella (390 px ja 320 px).
2. Käy läpi `references/signs.md` ja kirjaa löydökset. Arabia / oikealta vasemmalle: `references/rtl.md` ensin.
3. Moskeijan omat valinnat (värit, fontit, kuviot, kulmat, varjot, korttityylit) ovat brändiä: pidä ne.
4. Korjaa järjestyksessä: välit, värit, kuvakkeet, teksti, typografia, asettelu, yksityiskohdat, kuvat, liike.
5. Tarkista lopuksi: ei vaakavierintää 320–1440 px, ei tyhjiä kaistoja, arabia toimii.
Ei keksittyä sisältöä: käytä moskeijan omia tekstejä. Koraanin jakeisiin ei kosketa tekstiin, vain esitykseen.

## Kaikki paneelista
Kaikki, mitä moskeijan sivulla näkyy, pitää voida muokata hallintapaneelista. Kun lisäät sivupohjaan uuden
moskeijan tiedon (m.kentta, teema t.kentta, ramadan, rukousajat …), lisää sama kenttä paneelin kaavioon
(hallinta: src/kaavio.js) samassa muutoksessa. Tarkistus: hallinta `node testi/kattavuus.mjs` (ei saa olla ❌).
Etusivun osiot eivät tallenna omaa sisältöä: ne näyttävät tiedon sieltä, missä sitä muokataan (palvelut, tapahtumat …),
ettei samaa tietoa ylläpidetä kahdessa paikassa. Vanhat tiedot siirretään paneelin muotoon (esim. palvelut omiksi sivuikseen), ei jätetä piiloon.

## Yhtenäisyys
Sama asia näyttää samalta kaikkialla: kortit, napit, lomakkeet, tekstit ja välit. Kun lisäät tai muutat osaa
(esim. palvelukortti, toimintonappi, lomakkeen kenttä), käytä olemassa olevaa osaa (_includes/osat) ja tarkista sen
kaikki esiintymät (etusivu, listasivu, oma sivu, "Muut …"). Ei uusia rinnakkaisia tyylejä samalle asialle.

## Kehitysprosessi
- Uudet muutokset `testi`-haaraan, ei suoraan `main`-haaraan.
- Jokaisesta muutoksesta kohta `testit.json`-tiedostoon (testi-haarassa): otsikko, kuvaus, aloitus,
  kohdat muodossa "Mitä tarkistetaan — Missä: polku", nimetyt linkit. Hylätyn korjauksen jälkeen `versio` + 1.
- Testaajat kuittaavat paneelin Testaus ja julkaisu -sivulla; ylläpitäjä julkaisee kaikille.
- Repo on julkinen: ei henkilötietoja, avaimia tai salaisuuksia tiedostoihin eikä commit-viesteihin.
