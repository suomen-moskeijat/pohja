# Suomen moskeijat – sivupohja

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

1. **Actions → Lisää moskeija → Run workflow**
   (https://github.com/suomen-moskeijat/pohja/actions/workflows/lisaa-moskeija.yml)
2. Täytä lomake:
   - **kaupunki** (pakollinen)
   - **Mawaqit- tai Masjidbox-linkki**, jos moskeija käyttää niitä (linkin tai upotuskoodin
     voi liittää sellaisenaan) – silloin nimi, koordinaatit, Jumuah, rukousajat, iqamah
     (ja Mawaqitista kuvat) tulevat automaattisesti
   - muuten **nimi** ja **katuosoite** (koordinaatit haetaan osoitteesta)
   - valinnaisesti Instagram ja WhatsApp
3. Valmis: ajon yhteenvedossa on sivun osoite. Repo luodaan nimellä
   `suomen-moskeijat/<moskeijan-nimi>` ja sivu julkaistaan noin kahdessa minuutissa.
4. Täydennä tiedot (osoite, puhelin, logo, tekstit) Pages CMS:ssä: https://app.pagescms.org

**Kokeilu ilman että mitään luodaan:**
`python3 .github/scripts/lisaa_moskeija.py --kuiva /tmp/kokeilu --kaupunki Hyvinkää --mawaqit <linkki>`

### Kertaluonteinen asetus: avain, jolla automaatio luo repoja

1. Luo avain: https://github.com/settings/personal-access-tokens/new
   - **Resource owner:** `suomen-moskeijat`
   - **Expiration:** esim. 1 vuosi (uusi avain ennen kuin se vanhenee)
   - **Repository access:** All repositories
   - **Repository permissions:** Administration, Contents, Pages ja Workflows → *Read and write*
2. Jos organisaatio vaatii hyväksynnän: Organisaation asetukset → Personal access tokens →
   hyväksy avain.
3. Tallenna avain: tämän repon **Settings → Secrets and variables → Actions →
   New repository secret**, nimi `MOSKEIJA_AVAIN`.

### Käsin (ilman automaatiota)

1. Luo organisaatioon julkinen repo ja kopioi sinne kansion `malli/` sisältö; korvaa `SLUG`,
   `REPO`, `MOSKEIJAN NIMI` ja osoitetiedot (`_moskeijat/SLUG.md` → `_moskeijat/<slug>.md`).
2. Repon asetuksista: **Settings → Pages → Source: GitHub Actions**.

## Mitä moskeija voi muokata itse (Pages CMS)

Kaikki alla oleva muokataan selaimessa osoitteessa https://app.pagescms.org, eikä koodia tarvita.
Valinnat ovat valmiita vaihtoehtoja, joten sivu pysyy siistinä, vaikka moskeijoita on sata.

| Mitä | Kenttä | Vaihtoehdot |
|---|---|---|
| Etusivun yläosan tausta | `alku.tausta` | `kuvio` (vaalea kuvio, oletus), `kuva` (oma valokuva, tummennetaan ja teksti on valkoinen), `vari` (moskeijan pääväri) |
| Taustakuva | `alku.kuva` | vaakakuva, vähintään 1600 px leveä |
| Etusivun napit (enintään 2) | `alku.napit` | `lapsi`, `toiminta`, `rukousajat`, `lahjoita`, `yhteys`, `oma` (teksti ja linkki kentässä `alku.oma_nappi`) tai oman sivun nimi, esim. `hyvat-lahteet` |
| Valikosta piilotettavat sivut | `valikko_piilota` | `rukousajat`, `meista`, `palvelut`, `tapahtumat`, `yhteystiedot`, `lahjoita`. Lahjoita on piilossa myös silloin, kun lahjoitustietoja ei ole |
| Omat sivut (kirjat, lähteet, artikkelit…) | kokoelma **Omat sivut** (`_sivut/`) | teksti neljällä kielellä, kuva ja linkkikortit (myös PDF-tiedostot). Näkyy valikossa, kun valinta *Näytä valikossa* on päällä |
| Värit ja logo | `teema` | pääväri, korostusväri, logo ja vaalea logo alapalkkiin |
| Tekstit | `esittely`, `meista`, `palvelut`, `kortit`, `lasten_opetus`, `lahjoitus` | suomi, englanti, arabia, somali (puuttuva kieli → englanti → suomi) |

Esimerkki: `esittely/hyvinkaa/` (oma sivu `_sivut/hyvat-lahteet.md`).

## Rakenne

| Polku | Sisältö |
|---|---|
| `_layouts/sivu.html`, `_layouts/tapahtuma.html` | Sivupohja ja tapahtuman sivu |
| `_includes/osat/` | Sivun osat (yläpalkki, rukouskortti, galleria, lomakkeet …) |
| `*.html`, `palvelut/` | Sivut: etusivu, rukousajat, meistä, palvelut, lasten opetus, tapahtumat, yhteystiedot, lahjoita, tietosuoja |
| `assets/css/sivu.css`, `assets/js/sivu.js` | Tyylit ja toiminnot (kielet, rukousajat, lomakkeet …) |
| `_data/kaannokset.yml` | Käännökset: suomi, englanti, arabia, somali |
| `.github/scripts/` | Haut: `instagram.py`, `somet.py` (YouTube, Telegram), `rukousajat.py`; uuden moskeijan luonti: `lisaa_moskeija.py` |
| `.github/workflows/rakenna.yml` | Yhteinen julkaisuajo |
| `.github/workflows/lisaa-moskeija.yml` | Lomake: Lisää moskeija |
| `malli/` | Mallitiedostot uuden moskeijan repoon |

Kuvakkeet: Phosphor Icons (MIT). Rukousaikojen laskenta: adhan.js (MIT).

## Rukousajat ja kuvat

Sivusto toimii jokaiselle moskeijalle ilman ylimääräistä työtä. Jos moskeijalla on oma
rukousaikapalvelu tai kuvia, ne saa käyttöön yhdellä asetuksella. Kaikki asetukset ovat
moskeijan repon tiedostossa `_moskeijat/<moskeija>.md`, ja niitä voi muokata selaimessa
Pages CMS:ssä (Moskeijat → moskeija → Rukousajat).

### 1. Rukousajat: valitse lähde

```yaml
rukousajat:
  lahde: masjidbox        # masjidbox | mawaqit | rukousajat | taulukko | laskenta
  tunnus: masjid-sunnah-helsinki
  iqamah_oletus: { fajr: 10, dhuhr: 10, asr: 10, maghrib: 5, isha: 10 }
```

| Moskeijalla on… | `lahde` | `tunnus` | Mitä tapahtuu |
|---|---|---|---|
| **Masjidbox** | `masjidbox` | osoitteen `masjidbox.com/prayer-times/TUNNUS` loppuosa | Adhan, iqamah ja Jumuah haetaan **automaattisesti kerran tunnissa** (seuraavat 7 päivää). |
| **Mawaqit** | `mawaqit` | osoitteen `mawaqit.net/fi/TUNNUS` loppuosa | Adhan, iqamah ja Jumuah haetaan **automaattisesti kerran tunnissa** (kuluva + 2 seuraavaa kuukautta). Myös moskeijan **kuvat** Mawaqitista lisätään galleriaan. |
| **Ei omaa, pääkaupunkiseutu** | `rukousajat` (oletus, jos kaupunki on Helsinki, Espoo tai Vantaa) | – | Ajat haetaan **rukousajat.fi:n Helsingin aikataulusta** kerran tunnissa (kuluva + 2 kuukautta). Iqamah = rukousaika + `iqamah_oletus` minuuttia. |
| **Oma aikataulu** (Excel, PDF tms.) | `taulukko` | – | Kuukauden ajat lisätään CSV-tiedostona: `_data/aikataulut/<moskeija>/VVVV-KK.csv` (malli alla). |
| **Ei omaa, muu kaupunki** | `laskenta` (tai jätä tyhjäksi) | – | Ajat lasketaan **samalla tavalla kuin [rukousajat.fi](https://www.rukousajat.fi/) muissa kaupungeissa** moskeijan koordinaateista (`sijainti: lat, lon`). Iqamah = rukousaika + `iqamah_oletus` minuuttia. |

**Miten rukousajat.fi toimii:** Helsingissä, Espoossa ja Vantaalla se näyttää valmiin
vuosiaikataulun (sama kuin esim. Masjid Sunnahin Masjidbox-näytöllä); muualla se laskee ajat.
Sivusto tekee samoin. Taulukko luetaan rukousajat.fi:n sovelluksesta joka ajossa, joten jos
se päivittyy, sivu seuraa. Jos haku joskus epäonnistuu, käytetään viimeisimpiä haettuja aikoja
ja niiden jälkeen laskentaa.

**Tarkistettu oikeaa rukousajat.fi:tä vasten (7.11.2026):** kaupunkia vaihtamalla
Tampere, Turku, Oulu, Jyväskylä ja Kuopio täsmäsivät sivuston laskentaan minuutilleen;
Espoo ja Vantaa näyttävät rukousajat.fi:ssä Helsingin taulukon, jonka sivusto hakee
lähteellä `rukousajat`. Jokainen moskeija saa siis ajat oman sijaintinsa mukaan.

Ilman lähdettä tarvitaan siis vain moskeijan sijainti. Laskennan oletusasetukset ovat samat kuin
rukousajat.fi:ssä: `laskentatapa: MuslimWorldLeague`, `madhab: Shafi` ja
`korkeat_leveysasteet: TwilightAngle` (kesän valoisat yöt). Niitä voi muuttaa, jos moskeija
haluaa toisin. Sama laskenta täyttää myös päivät, joille virallista aikaa ei vielä ole.

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

Iqamah-sarakkeet saa jättää tyhjiksi; silloin käytetään `iqamah_oletus`-minuutteja.
Puuttuville päiville sivu laskee ajat koordinaateista.

### 2. Kuvat

- **Omat kuvat:** Pages CMS → Moskeijat → *Kuvagalleria* → lisää kuvat. Ne näkyvät
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
