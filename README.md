# Suomen moskeijat – sivupohja

> **Kaikki ohjeet yhdessä paikassa:** [OHJEET.md](OHJEET.md) · verkossa https://suomen-moskeijat.github.io/pohja/ohjeet/
> (moskeijan muokkaajille ja ylläpitäjille)

Yhteinen pohja kaikkien moskeijoiden nettisivuille. Jokaisella moskeijalla on oma repo,
jossa ovat vain sen omat tiedot (nimi, osoite, logo, tekstit, tapahtumat). Ulkoasu,
rukousaikojen ja iqamah-aikojen haku sekä Instagram-julkaisut tulevat tästä pohjasta.

**Muutos tähän pohjaan päivittää kaikki sivut** niiden seuraavassa julkaisuajossa
(kerran tunnissa tai heti, kun moskeijan tietoja muutetaan).

## Miten sivu syntyy

```
suomen-moskeijat/pohja           ← tämä: ulkoasu, haut, julkaisuajo (.github/workflows/rakenna.yml)
suomen-moskeijat/<moskeija>      ← moskeijan tiedot + lyhyt julkaisu.yml, joka kutsuu pohjaa
```

Julkaisuajo yhdistää pohjan ja moskeijan tiedot (moskeijan tiedostot voittavat), hakee
Instagram-julkaisut ja rukousajat, rakentaa sivun ja julkaisee sen moskeijan repon
GitHub Pagesiin. Haetut tiedot säilytetään välimuistissa, joten katkos Instagramissa tai
Masjidboxissa ei tyhjennä sivua.

## Uusi moskeija (noin 2 minuuttia)

Uusi moskeija luodaan yksityiseen sisältörepoon (kansio `moskeijat/<nimi>/` ja sivustoluettelon rivi), ei omaksi
repokseen (hallinta#51, ADR-0006). Sivu rakentuu rakennusajossa omaan Cloudflare Pages -projektiinsa, ja luonnos näkyy
vain luonnoslinkillä.

1. Hallintapaneeli → Ylläpito → **Uusi moskeija** (tai **Actions → Lisää moskeija → Run workflow**).
2. Täytä lomake:
   - **nettisivu**: moskeijan nykyinen sivu. Sieltä haetaan logo, värit, yhteystiedot, somet, kuvat ja tekstit
   - **kaupunki** (ei tarvita, jos nettisivulla on osoite)
   - **Mawaqit- tai Masjidbox-linkki**, jos moskeija käyttää niitä (linkin tai upotuskoodin
     voi liittää sellaisenaan) – silloin nimi, koordinaatit, Jumuah, rukousajat, iqamah
     (ja Mawaqitista kuvat) tulevat automaattisesti
   - muuten **nimi** ja **katuosoite** (koordinaatit haetaan osoitteesta)
3. Työnkulku kirjoittaa moskeijan sisältörepoon yhtenä committina ja käynnistää rakennusajon. Julkinen loki näyttää vain
   sivun tunnuksen ja määrät, ei tuotua sisältöä eikä luonnoslinkkiä.
4. Täydennä tiedot (osoite, puhelin, logo, tekstit) hallintapaneelissa: https://hallinta.suomenmoskeijat.fi/

Ehdotukset listasta (`lisaa-listasta.yml`, sisältörepon `moskeijat.csv`) ja poisto (`poista-moskeija.yml`: kansio,
sivustoluettelon rivi ja Pages-projekti) toimivat samoin. Vanhan julkaisun moskeijat (siirtämättömät, Hyvinkää) poistetaan
kuten ennen (moskeijarepo).

Siirrettyjen moskeijoiden vanhat moskeijarepot poistetaan erikseen käsin (`poista-vanhat-repot.yml`, hallinta#56): syöte
`moskeijat` (nimet pilkuin tai `siirretyt` = sivustoluettelon sivut, joilla on vanha repo) ja `kuiva` (oletus: vain lista).
Työnkulku poistaa vain vanhan GitHub-repon, ei mitään sisältörepossa eikä Cloudflaressa, ja vain kun sisältörepossa on kansio
`moskeijat/<nimi>/` ja sivustoluettelossa rivi samalla nimellä (GitHubin repon nimessä kirjainkoko saa erota: sivu
masjid-sunnah, vanha repo Masjid-sunnah). Pohja, hallinta, sisalto, .github, Hyvinkää ja testimoskeija eivät koskaan kuulu
poistettaviin.

Uusi moskeija alkaa tyhjästä (ADR-0001): sivulla ei ole oletusesittelyä, iqamah-minuutteja, valmiita artikkeleita,
toiminnan kieliä eikä yläosan nappeja, ennen kuin moskeija lisää tai valitsee ne. Vain tuotu tieto (nimi, osoite,
yhteystiedot, somet, vanhan sivun tekstit) tulee sivulle valmiiksi.

**Kokeilu ilman että mitään tallennetaan:**
`python3 .github/scripts/lisaa_moskeija.py --kuiva /tmp/kokeilu --kaupunki Hyvinkää --mawaqit <linkki>` (vain moskeijan
kansio) tai `--sisalto <sisältörepon kopio>` ilman `--tallenna` (kansio ja sivustoluettelon rivi, ei commitia). Työnkuluissa
sama valinta on **kuiva** (testipaneeli käyttää sitä aina).

### Kertaluonteinen asetus: sisältörepon kirjoitusavain

1. Luo hienojakoinen avain: https://github.com/settings/personal-access-tokens/new
   - **Resource owner:** `suomen-moskeijat`, **Repository access:** vain `sisalto`
   - **Repository permissions:** Contents → *Read and write*
2. Tallenna se: tämän repon **Settings → Environments → julkaisu → Add secret**, nimi `SISALTO_KIRJOITUS`
   (ympäristö sallii vain main- ja testi-haaran).
3. Vanhan julkaisun moskeijarepojen poistoon tarvitaan edelleen repon salaisuus `MOSKEIJA_AVAIN`
   (Administration: Read and write), ja Pages-projektien poistoon ympäristön `CLOUDFLARE_API_TOKEN` (sama kuin rakennusajossa).

### Käsin (ilman automaatiota)

Aja `lisaa_moskeija.py --sisalto <sisältörepon kopio>` omalla koneella ja tee commit ja push sisältörepoon (tai lisää
`--tallenna`). Uusia julkisia moskeijarepoja ei enää luoda.

## Mitä moskeija voi muokata itse (hallintapaneeli)

Kaikki alla oleva muokataan selaimessa hallintapaneelissa https://hallinta.suomenmoskeijat.fi/, eikä koodia tarvita.
Valinnat ovat valmiita vaihtoehtoja, joten sivu pysyy siistinä, vaikka moskeijoita on sata.

| Mitä | Kenttä | Vaihtoehdot |
|---|---|---|
| Etusivun yläosan tausta | `alku.tausta` | `kuvio` (vaalea kuvio, oletus), `kuva` (oma valokuva, tummennetaan ja teksti on valkoinen), `vari` (moskeijan pääväri) |
| Taustakuva | `alku.kuva` | vaakakuva, vähintään 1600 px leveä |
| Etusivun napit (enintään 2) | `alku.napit` | `lapsi`, `toiminta`, `rukousajat`, `lahjoita`, `yhteys`, `oma` (teksti ja linkki kentässä `alku.oma_nappi`) tai oman sivun nimi, esim. `hyvat-lahteet` |
| Valikosta piilotettavat sivut | `valikko_piilota` | `rukousajat`, `meista`, `palvelut`, `tapahtumat`, `yhteystiedot`, `lahjoita`. Lahjoita on piilossa myös silloin, kun lahjoitustietoja ei ole. Maksutiedot näkyvät vain kentällä `lahjoitus.lupanumero` tai voimassa olevalla `lahjoitus.pienkerays` (+ `paattyy`) |
| Omat sivut (kirjat, lähteet, artikkelit…) | kokoelma **Omat sivut** (`_sivut/`) | teksti neljällä kielellä, kuva ja linkkikortit (myös PDF-tiedostot). Näkyy valikossa, kun valinta *Näytä valikossa* on päällä |
| Artikkelit | kokoelma **Artikkelit** (`_artikkelit/`) | omat artikkelit: otsikko, päivä, aihe, kuvaus, kuva ja teksti. Sivulla /artikkelit/ on haku ja aiheet, ja kolme uusinta näkyy etusivulla |
| Yhteiset artikkelit | `artikkelit.lahteet` | `islaminusko` = noin 110 suomenkielistä artikkelia islaminusko.fi:stä lähdemerkinnällä (sallittu ei-kaupalliseen käyttöön). Päivittyy viikoittain (Actions → *Päivitä yhteiset artikkelit*). Tyhjä lista = vain omat |
| Värit ja logo | `teema` | pääväri, korostusväri, logo ja vaalea logo alapalkkiin |
| Tekstit | `esittely`, `meista`, `palvelut`, `kortit`, `lasten_opetus`, `lahjoitus` | suomi, englanti, arabia, somali (puuttuva kieli → englanti → suomi) |

Esimerkki: testimoskeija (`suomen-moskeijat/testimoskeija`), https://suomen-moskeijat.github.io/testimoskeija/.

## Muokkaajat: vain oman moskeijan sivu

Käyttäjät kutsutaan hallintapaneelissa sähköpostilla (moskeija → **Käyttäjät**). Muokkaaja pääsee
vain oman moskeijansa sivuun, eikä hän tarvitse GitHub-tunnusta. Paneeli tallentaa muutokset
moskeijan repoon omalla GitHub-sovelluksellaan. Muokkaajia **ei** lisätä GitHubiin; organisaation
asetuksissa (Settings → Member privileges → Base permissions) kannattaa pitää *No permission*.

## Näkyvyys Googlessa

Sivut tekevät automaattisesti:

- otsikot hakusanoja varten, esim. *Rukousajat Hyvinkää – Hyvinkää Islam Keskus*, ja kuvaukset joka sivulle
- schema.org-tiedot: moskeija (osoite, sijainti, yhteystiedot, somet), tapahtumat ja omat artikkelit
- jakokuvat (Open Graph), kun linkki jaetaan WhatsAppissa tai somessa
- `sitemap.xml` ja `robots.txt`
- yhteisistä lähteistä tuoduissa artikkeleissa canonical-linkin alkuperäiseen, jottei Google pidä niitä kaksoissisältönä

Moskeijan kannattaa tehdä itse (kerran, ilmaiseksi):

1. **Google-yritysprofiili** (business.google.com): moskeija Google Mapsiin, ja kenttään *Verkkosivusto* tämä sivu.
   Tämä on tärkein, koska haku "moskeija Hyvinkää" näyttää ensin karttatulokset.
2. **Google Search Console** (search.google.com/search-console): lisää sivu ja lähetä `sitemap.xml`.
3. **Oma verkkotunnus** (esim. moskeija.fi): `url` ja `baseurl` moskeijan `_config.yml`:ään sekä CNAME.
4. **Linkit sivulle** Instagramin biosta, Mawaqitista, Masjidboxista ja rukousajat.fi:stä.

## Rakenne

| Polku | Sisältö |
|---|---|
| `_layouts/sivu.html`, `_layouts/tapahtuma.html` | Sivupohja ja tapahtuman sivu |
| `_includes/osat/` | Sivun osat (yläpalkki, rukouskortti, galleria, lomakkeet …) |
| `*.html`, `palvelut/` | Sivut: etusivu, rukousajat, meistä, palvelut, lasten opetus, tapahtumat, yhteystiedot, lahjoita, tietosuoja |
| `assets/css/sivu.css`, `assets/js/sivu.js` | Tyylit ja toiminnot (kielet, rukousajat, lomakkeet …) |
| `_data/kaannokset.yml` | Käännökset: suomi, englanti, arabia, somali |
| `.github/scripts/` | Haut: `instagram.py`, `somet.py` (YouTube, Telegram), `rukousajat.py`; uusi moskeija, ehdotukset ja poisto sisältörepossa: `lisaa_moskeija.py`, `lisaa_listasta.py`, `poista_moskeija.py`, `sisaltorepo.py` |
| `.github/workflows/rakenna.yml` | Yhteinen julkaisuajo |
| `.github/workflows/lisaa-moskeija.yml` | Lomake: Lisää moskeija |
| `.github/workflows/poista-vanhat-repot.yml` | Siirrettyjen moskeijoiden vanhojen moskeijarepojen poisto (käsin, kuivaharjoitus oletuksena; `poista_vanhat_repot.py`) |

Kuvakkeet: Phosphor Icons (MIT).

## Rukousajat ja kuvat

Sivusto ei laske rukousaikoja itse: ajat tulevat moskeijan valitsemasta lähteestä tai sen omasta
aikataulusta. Ilman lähdettä ja aikoja Rukousajat-sivulla ja etusivulla lukee "Rukousajat lisätään pian". Kaikki asetukset ovat
moskeijan repon tiedostossa `_moskeijat/<moskeija>.md`, ja niitä muokataan hallintapaneelissa
(moskeija → Rukousajat ja Jumua).

### 1. Rukousajat: valitse lähde

```yaml
rukousajat:
  lahde: masjidbox        # masjidbox | mawaqit | rukousajat | taulukko
  masjidbox_id: msj_…     # Masjidbox: moskeija valitaan paneelissa nimellä (virallinen rajapinta)
  tunnus: ""              # Mawaqit: mawaqit.net/fi/TUNNUS (Masjidboxilla vain vanha varatapa)
  iqamah: { fajr: 10, dhuhr: 10, asr: 10, maghrib: 5, isha: 10 }   # valinnainen: moskeijan antamat minuutit adhanin jälkeen
```

| Moskeijalla on… | `lahde` | `tunnus` | Mitä tapahtuu |
|---|---|---|---|
| **Masjidbox** | `masjidbox` | osoitteen `masjidbox.com/prayer-times/TUNNUS` loppuosa | Adhan, iqamah ja Jumuah haetaan **automaattisesti kerran tunnissa** (seuraavat 7 päivää). |
| **Mawaqit** | `mawaqit` | osoitteen `mawaqit.net/fi/TUNNUS` loppuosa | Adhan, iqamah ja Jumuah haetaan **automaattisesti kerran tunnissa** (kuluva + 2 seuraavaa kuukautta). Myös moskeijan **kuvat** Mawaqitista lisätään galleriaan. |
| **Ei omaa, pääkaupunkiseutu** | `rukousajat` (oletus, jos kaupunki on Helsinki, Espoo tai Vantaa) | – | Ajat haetaan **rukousajat.fi:n Helsingin aikataulusta** kerran tunnissa (kuluva + 2 kuukautta). Iqamah = rukousaika + `iqamah_oletus` minuuttia. |
| **Oma aikataulu** (Excel, PDF tms.) | `taulukko` | – | Kuukauden ajat lisätään CSV-tiedostona: `_data/aikataulut/<moskeija>/VVVV-KK.csv` (malli alla). |
| **Ei lähdettä, muu kaupunki** | tyhjä | – | Aikoja ei näytetä: Rukousajat-sivulla ja etusivulla lukee **"Rukousajat lisätään pian"**, kunnes moskeija valitsee lähteen tai lisää oman aikataulun. |

**Miten rukousajat.fi toimii:** Helsingissä, Espoossa ja Vantaalla se näyttää valmiin
vuosiaikataulun (Helsingin aikataulu); muualla se laskee ajat sijainnista. Siksi rukousajat.fi on
oletuslähde vain näissä kolmessa kaupungissa (kaupunki on muokattavissa paneelin Rukousajat-sivulla,
jossa oletuksen peruste näkyy). Taulukko luetaan rukousajat.fi:n sovelluksesta joka ajossa. Jos haku
epäonnistuu, käytetään viimeisimpiä haettuja aikoja; niiden jälkeen päivät jäävät tyhjiksi.

**Aikoja ei lasketa itse.** Päivä, jolle lähde tai oma aikataulu ei anna aikaa, näkyy tyhjänä
(kuukausitaulukossa viivana). Mitään ei täytetä automaattisesti.

**Perjantai:** Masjidbox ja Mawaqit antavat Jumuah-ajan. Muuten kenttä `juma: "13.30"`.

**Mistä tunnus löytyy?** Avaa moskeijan sivu palvelussa selaimella ja kopioi osoitteen
viimeinen osa. Esim. `https://masjidbox.com/prayer-times/masjid-sunnah-helsinki` →
`masjid-sunnah-helsinki`.

### CSV-malli (lahde: taulukko)

```
pv,fajr,auringonnousu,dhuhr,asr,maghrib,isha,iqamah_fajr,iqamah_dhuhr,iqamah_asr,iqamah_maghrib,iqamah_isha
1,05:19,07:39,12:06,13:54,16:27,18:39,06:00,12:16,14:04,16:32,20:00
2,05:21,07:42,12:06,13:52,16:25,18:37,06:00,12:16,14:02,16:30,20:00
```

Iqamah-sarakkeet saa jättää tyhjiksi; silloin käytetään moskeijan antamia iqamah-minuutteja (`rukousajat.iqamah`), muuten iqamah-aikaa ei näytetä.
Puuttuville päiville sivu laskee ajat koordinaateista.

### 2. Kuvat

- **Omat kuvat:** hallintapaneeli → Kuvat ja tiedostot → lisää galleriaan. Ne näkyvät
  etusivulla ja Meistä-sivulla (enintään 9).
- **Mawaqitista automaattisesti:** jos `lahde: mawaqit`, moskeijan Mawaqitiin lisäämät
  sisä- ja ulkokuvat ladataan sivustolle ja lisätään galleriaan.
- **Instagramista automaattisesti:** jos kentässä `some.instagram` on tilin osoite,
  uusimmat julkaisut näkyvät sivulla omana osionaan.
- **Ei kuvia:** galleriaa ei näytetä; sivu näyttää silti valmiilta (kuvio, värit, logo).

Kuvissa ei mielellään näy ihmisten kasvoja ilman lupaa.

### 3. Miten päivitys toimii

Moskeijan repon julkaisuajo (`.github/workflows/julkaisu.yml`, joka kutsuu tämän pohjan ajoa `rakenna.yml`) käy **kerran tunnissa** ja aina, kun
sivustoon tehdään muutos: se hakee Instagram-julkaisut ja rukousajat
(tämän pohjan `.github/scripts/rukousajat.py`) ja julkaisee sivun. Jos palvelu on hetken alhaalla,
sivu käyttää viimeisimpiä tunnettuja aikoja. Ajon voi käynnistää myös käsin:
GitHub → Actions → *Julkaise sivusto* → *Run workflow*.
