---
# ===== Pakolliset =====
title: MOSKEIJAN NIMI
slug: SLUG
kaupunki: KAUPUNKI
osoite: "KATUOSOITE, POSTINUMERO KAUPUNKI"
sijainti: { lat: 0, lon: 0 }   # kartta ja rukousaikojen laskenta

# ===== Yhteystiedot (valinnainen) =====
puhelin: ""
whatsapp: ""          # näkyy pikanappina; lomakkeet lähetetään tähän, jos lomakeosoitetta ei ole
sahkoposti: ""
kielet: [suomi]
juma: ""              # perjantairukous, esim. "13.30" (Masjidbox/Mawaqit antaa sen itse)

# ===== Rukousajat =====
# lahde: masjidbox | mawaqit | rukousajat | taulukko | laskenta
#   tyhjä = Helsinki/Espoo/Vantaa: rukousajat.fi:n taulukko, muualla laskenta sijainnista
rukousajat:
  lahde: ""
  tunnus: ""          # Masjidbox: masjidbox.com/prayer-times/TUNNUS · Mawaqit: mawaqit.net/fi/TUNNUS
  iqamah_oletus: { fajr: 10, dhuhr: 10, asr: 10, maghrib: 5, isha: 10 }

# ===== Some (valinnainen) =====
some:
  instagram: ""       # esim. https://www.instagram.com/tili/ – uusimmat julkaisut näkyvät sivulla
  facebook: ""
  youtube: ""          # uusimmat videot näkyvät sivulla
  tiktok: ""
  telegram: ""         # julkisen kanavan julkaisut näkyvät sivulla
  snapchat: ""
  x: ""
  threads: ""
  whatsapp_kanava: ""   # https://whatsapp.com/channel/...

# ===== Ulkoasu (valinnainen) =====
teema:
  logo: ""            # esim. /tiedostot/logo.png – ilman logoa näytetään nimi
  logo_vaalea: ""     # valinnainen: vaalea versio alapalkin tummalle taustalle
  hero: vaalea
  # Omat värit (tyhjä = pohjan kulta-ruskea). Esim. vihreä: paa "#123d30", korostus "#5fae8a", korostus_vaalea "#e7f4ee"
  paa: ""             # otsikot ja teksti
  korostus: ""        # painikkeet, kuvio, korostukset
  korostus_vaalea: "" # vaaleat pohjat

# ===== Tekstit (valinnainen; suomi riittää, muut kielet näkyvät kun ne lisätään) =====
hero_tunniste: { fi: "KAUPUNKI" }
esittely: { fi: "Rukouksen, oppimisen ja yhteisön paikka." }

# Etusivun yläosa: tausta (kuvio | kuva | vari) ja enintään 2 nappia
# (lapsi, toiminta, rukousajat, lahjoita, yhteys, oma tai oman sivun nimi)
alku:
  tausta: kuvio
  kuva: ""            # kun tausta: kuva, esim. /tiedostot/sali.jpg
  napit: [lapsi, toiminta]

# Sivut, joita ei ole käytössä (piilotetaan valikosta), esim. [tapahtumat, lahjoita]
valikko_piilota: []
galleria: []          # omat kuvat, esim. /tiedostot/sali.jpg
---
