# Ohjeet: moskeijoiden nettisivut

Kaikki ohjeet yhdessä paikassa. Verkossa: **https://suomen-moskeijat.github.io/pohja/ohjeet/**

- **[Missä mikin on](#kartta)**: linkit ja kokonaisuus yhdellä silmäyksellä
- **[Tilanteet: mitä teen, kun…](#tilanteet)**: nopeat vastaukset
- **[Osa 1: Moskeijan muokkaajalle](#osa-1)**: sivun päivittäminen selaimessa ilman koodia
- **[Osa 2: Ylläpitäjälle](#osa-2)**: uudet moskeijat, oikeudet, automaatiot ja vianetsintä

---

<a id="kartta"></a>

## Missä mikin on

| Mikä | Osoite | Kenelle |
|---|---|---|
| **Nämä ohjeet** | https://suomen-moskeijat.github.io/pohja/ohjeet/ | kaikille |
| **Kaikki sivut ja niiden tila (vanha hakemisto)** | https://suomen-moskeijat.github.io/pohja/ | ylläpitäjille siirron ajan |
| **Moskeijan sivu** | `https://suomen-moskeijat.github.io/<moskeija>/` (tai oma verkkotunnus) | kävijöille |
| **Sivun muokkaus (hallintapaneeli)** | https://hallinta.suomenmoskeijat.fi/ | moskeijan pääkäyttäjille ja muokkaajille |
| **Uusi moskeija, käyttäjät, kielet, tekstit** | hallintapaneeli → Ylläpito | ylläpitäjille |
| **Automaatiot (varalla)** | https://github.com/suomen-moskeijat/pohja/actions | ylläpitäjille |
| **Moskeijalista** | `moskeijat.csv` yksityisessä sisältörepossa (paneeli → Ylläpito → Moskeijalista) | ylläpitäjille |
| **Esimerkkisivu** | https://suomen-moskeijat.github.io/testimoskeija/ (testimoskeija, esimerkkidata) | esittelyyn ja kokeiluun |

**Miten kokonaisuus toimii:**

- **Pohja** (`suomen-moskeijat/pohja`) on yhteinen "moottori": ulkoasu, sivut, rukousaikojen haku,
  automaatiot, hakemisto ja ohjeet. Pohja on aina olemassa. Kun sitä parannetaan, kaikki moskeijasivut
  päivittyvät tunnin sisällä.
- **Jokainen moskeija on oma reponsa** (esim. `suomen-moskeijat/hyvinkaa-islam-keskus`), jossa on vain
  sen omat tiedot: tekstit, kuvat, tapahtumat ja artikkelit. Moskeijan muokkaajat pääsevät vain omaansa.
- **Sivun tila** näkyy palkkina sivun yläreunassa ja hakemistossa:

| Tila | Palkki sivulla | Google | Tarkoitus |
|---|---|---|---|
| **Ehdotus** | "Ehdotus – tämä ei ole moskeijan virallinen sivu" | ei näy | esimerkkisivu, josta moskeija ei ole vielä päättänyt |
| **Luonnos** | "Luonnos – sivua ei ole vielä julkaistu" | ei näy | moskeija on mukana ja tarkistaa sivua |
| **Julkaistu** | ei palkkia | näkyy | valmis sivu |

---

<a id="tilanteet"></a>

## Tilanteet: mitä teen, kun…

| Tilanne | Kuka | Mitä tehdään |
|---|---|---|
| Haluan näyttää moskeijalle, millainen sivu heille tulisi | ylläpitäjä | Katso hakemistosta, onko heillä ehdotussivu. Jos ei, lisää heidät paneelin **Moskeijalistaan** ja paina **Luo ehdotussivu** (Osa 2, kohta 3a). Lähetä luonnoslinkki. |
| Moskeija haluaa lähteä mukaan | ylläpitäjä | 1) Paneeli → avaa moskeija → **Moskeija lähtee mukaan** (sivu muuttuu luonnokseksi). 2) Jos heillä on vanha nettisivu: kysy lupa ja tuo tiedot (Osa 2, kohta 3b). 3) **Käyttäjät** → kutsu moskeijan pääkäyttäjä sähköpostilla. Pääkäyttäjä hyväksyy käyttöehdot paneelin etusivulla. |
| Moskeija on tarkistanut sivun ja hyväksyy sen | pääkäyttäjä tai ylläpitäjä | Paneelin etusivu → **Julkaise sivu**. Sivu on julkinen noin 2 minuutissa. |
| Moskeija ei halua sivua | ylläpitäjä | Paneeli → avaa moskeija → Sivuston asetukset → **Poista moskeija**. Se merkitään listaan, eikä sivua luoda uudelleen. |
| Uusi moskeija, joka ei ole listalla | ylläpitäjä | Paneeli → Ylläpito → **Uusi moskeija** (nimi, kaupunki, Mawaqit- tai Masjidbox-linkki, nettisivu luvalla). |
| Moskeija haluaa muokata tekstejä tai lisätä tapahtuman | muokkaaja | Hallintapaneeli (Osa 1). |
| Uusi henkilö haluaa muokkausoikeuden | pääkäyttäjä | Paneeli → **Käyttäjät** → kutsu sähköpostilla (muokkaaja tai pääkäyttäjä). |
| Henkilö lopettaa | pääkäyttäjä | Paneeli → **Käyttäjät** → Poista. |
| Rukousajat ovat väärin | pääkäyttäjä | Paneeli → Rukousajat ja Jumua: tarkista lähde ja seuraavat 7 päivää. Yksittäisen päivän voi korjata kohdassa Muutokset yksittäisiin päiviin. |
| Moskeija ottaa Mawaqitin tai Masjidboxin käyttöön | pääkäyttäjä | Paneeli → **Rukousajat ja Jumua** → Rukousaikojen lähde. |
| Moskeija haluaa oman osoitteen (esim. moskeija.fi) | ylläpitäjä | Osa 2, kohta 8. Tee vasta, kun sivu on julkaistu. |
| Sivu ei päivity tai näyttää rikkinäiseltä | ylläpitäjä | Osa 2, kohta 10 (Actions-loki). |
| Haluan muuttaa ulkoasua kaikille | ylläpitäjä | Muutos pohjaan → tarkista testimoskeijalta → kaikki päivittyvät tunnin sisällä. |
| Avain `MOSKEIJA_AVAIN` vanhenee | ylläpitäjä | Tee uusi (Osa 2, kohta 2) ja korvaa salaisuus. |

---

<a id="osa-1"></a>

## Osa 1: Moskeijan muokkaajalle

### 1. Mitä tarvitset

> **Uusi sivu on aluksi luonnos** (keltainen palkki ylhäällä). Kun sivu on kunnossa, pääkäyttäjä painaa
> paneelin etusivulla **Julkaise sivu**, ja sivu on julkinen.

1. **Kutsu sähköpostiin.** Moskeijan pääkäyttäjä (tai ylläpitäjä) kutsuu sinut paneelin **Käyttäjät**-sivulta.
   GitHub-tunnusta ei tarvita.
2. **Kirjaudu:** https://hallinta.suomenmoskeijat.fi/. Kirjoita sähköpostiosoitteesi, niin saat 6-numeroisen koodin.
   Voit myös tallentaa **pääsyavaimen** (sormenjälki, kasvot tai laitteen PIN) tai kirjautua Googlella tai Microsoftilla.
3. **Roolit:** *muokkaaja* lisää tapahtumia, tiedotteita, kuvia ja ilmoituksia. *Pääkäyttäjä* muokkaa lisäksi sivuja,
   ulkoasua, rukousaikoja ja käyttäjiä, ja julkaisee sivun.

> Toimii puhelimella ja tietokoneella. Tallennuksen jälkeen sivu päivittyy noin 2 minuutissa.
> Kaikki muutokset näkyvät **Historia**-sivulla, ja ne voi perua.

### 2. Mistä mitäkin muokataan

| Paneelin valikossa | Mitä siellä tehdään |
|---|---|
| **Yleiskatsaus** | sivun tila, mitä on vielä tekemättä, pikanapit; uudella sivulla linkki kesken jääneeseen aloitukseen |
| **Sivusto** | sivut samassa järjestyksessä ja samoilla nimillä kuin kävijän valikossa: Etusivu, Rukousajat (lähde, iqamah, Jumua, päivien muutokset), Meistä, Palvelut, Tapahtumat, Artikkelit (omat tiedotteet ja valmiit artikkelit), omat sivut ja Yhteystiedot. Valikon ulkopuoliset sivut (esim. Tuki ja jäsenyys) ovat omana rivinään. **Järjestä** muuttaa valikon järjestystä samassa listassa, **+ Lisää sivu** lisää oman sivun. Sivu, jolla ei ole vielä sisältöä, on merkitty *Ei näy – ei vielä sisältöä*. |
| **Muut** | Ilmoituspalkki (lyhyt ilmoitus kaikkien sivujen ylälaitaan), Kuvat (kuvat ja PDF-tiedostot), Jakokuva someen (valmiit pohjat, esim. tarawih-vuorot, tapahtuma, tiedote, Eid: kuva someen ja WhatsAppiin sekä tiedote sivulle yhdellä kertaa) |
| **Asetukset** | Ulkoasu (värit, logo, taustakuviot, kulmat ja varjot), Käyttäjät (kutsut ja oikeudet), Historia, Sivuston asetukset (kielet, oma verkkotunnus, sivun tila, käyttöehdot) |

Puhelimella alapalkissa ovat **Koti**, **Sivusto**, **+ Lisää** (tapahtuma, tiedote, palvelu, sivu tai kuva) ja **Kaikki** (koko navigaatio).
Muokkaaja näkee omat toimintonsa: Tapahtumat, Tiedotteet ja artikkelit, Luo julkaisu, Ilmoituspalkki, Kuvat ja tiedostot sekä Historia.

Muokkaa kenttiä ja paina lopuksi **Tallenna**. Muiden kielten tekstit kirjoitetaan valitsemalla ylhäältä
Muokattava kieli. **Sivuston asetukset → Sivuston kielet** -kohdassa valitaan kerran, käännetäänkö puuttuvat tekstit
tallennettaessa automaattisesti tekoälyllä vai onko sivu vain suomeksi; tallennus ei kysy sitä erikseen. Tekoälyn
käännöksestä näkyy sivulla huomautus, kunnes kieltä osaava on tarkistanut tekstit.

### 3. Tapahtumat ja viikoittainen toiminta

1. **Tapahtumat → Uusi tapahtuma**
2. Valitse ensin **Kuinka usein?**
   - **Kerran:** yksittäinen tapahtuma, esim. Eid-rukous, avoimet ovet tai yhteinen iftar. Täytä päivä ja kellonaika.
   - **Joka viikko:** säännöllinen toiminta, esim. Koraanikoulu sunnuntaisin tai naisten opintopiiri torstaisin.
     Valitse **viikonpäivät**, kellonaika ja halutessasi **kenelle** (lapset, naiset …). **Päivä** = mistä alkaen,
     **Päättymispäivä** = kauden viimeinen kerta (tyhjä = toistaiseksi).
3. **Tallenna.** Kertaluonteiset näkyvät etusivulla ja Tapahtumat-sivulla, ja ne katoavat, kun päivä on mennyt.
   Joka viikko toistuvat näkyvät Tapahtumat-sivun **viikko-ohjelmassa** ja tilattavassa kalenterissa.

> **Palvelut** (nikah, hautajaiset, kouluvierailut, neuvonta) ovat eri asia: ne lisätään kohtaan
> **Sivusto → Palvelut**, koska niillä ei ole kellonaikaa.

### 4. Tiedotteen tai artikkelin kirjoittaminen

1. **Tiedotteet → Uusi tiedote**
2. **Otsikko**, **päivämäärä** ja **aihe**. Valitse aihe listasta, esim. *Tiedotteet* tai *Islamin perusteet*.
   Jos sopivaa ei ole, kirjoita uusi aihe. Se tulee artikkelisivulle omaksi napikseen.
3. **Lyhyt kuvaus** näkyy listassa, ja **teksti** on varsinainen kirjoitus. Lisää halutessasi kuva.
4. **Tallenna.** Kolme uusinta näkyy etusivulla, ja kaikki löytyvät Artikkelit-sivulta haun ja aiheiden kautta.

**Valmiit artikkelit:** sivulla on noin 110 suomenkielistä artikkelia islaminusko.fi:stä
(lähde mainitaan jokaisessa). Ne saa pois tai takaisin kohdasta **Sivusto → Artikkelit → Artikkelit-sivun asetukset → Valmiit artikkelit**.

### 5. Oma sivu (kirjasto, lähteet, viikko-ohjelma …)

1. **Sivusto → + Lisää sivu** ja valitse pohja
2. **Sivun nimi.** Nimestä tulee osoite, esim. *Hyvät lähteet* → `/hyvat-lahteet/`.
3. Kirjoita teksti **Oma teksti** -osioon ja lisää halutessasi linkit **Linkkikortit**-osioon (nimi, kuvaus, osoite tai PDF-tiedosto, kuvake).
4. **Näytä valikossa** päälle, niin sivu tulee valikkoon heti, kun siinä on sisältöä. Järjestystä voi muuttaa kohdassa **Sivusto → Järjestä**.

### 6. Kokeile ulkoasua ennen valintaa: /esikatselu/

Avaa oma sivusi ja lisää osoitteen perään **`/esikatselu/`**, esim.
`https://suomen-moskeijat.github.io/hyvinkaa-islam-keskus/esikatselu/`.
Napauta värimaailmaa ja taustaa: etusivu vaihtuu heti puhelimen kokoisessa ikkunassa.
Sivu kertoo myös, mistä saman valinnan tekee paneelissa. Esikatselu ei muuta mitään.

**Värimaailmat** (valitaan nimellä, värikoodeja ei tarvita): Kulta-ruskea, Smaragdinvihreä,
Metsänvihreä ja kulta, Turkoosi, Sininen, Yönsininen ja kulta, Persiansininen, Violetti,
Viininpunainen, Terrakotta, Oliivinvihreä, Grafiitti ja kulta, sekä *Nykyiset värit (logon mukaan)*.
Valinta: **Ulkoasu → Värit**.

**Taustakuviot alueittain** (hallintapaneeli → Ulkoasu): kuvio valitaan erikseen sivujen yläosaan,
alapalkkiin ja nostoihin (lahjoitus, lasten opetus), tai "Ei kuviota". Kuvion väri tulee värimaailmasta.

**Lomakkeiden lähetys ja WhatsApp-napit** (hallintapaneeli → Sivusto → Yhteystiedot):
lomakkeiden viestit sähköpostiin, WhatsAppiin tai kävijän valinnan mukaan, ja WhatsApp-napit
näkyviin, ilman kulman pikanappia tai kokonaan piiloon.

### 6b. Etusivun yläosa: tausta ja napit

**Sivusto → Etusivu** (yläosan tausta ja napit)

| Tausta | Miltä näyttää |
|---|---|
| `kuvio` | vaalea kuviotausta (oletus) |
| `kuva` | oma valokuva, joka tummennetaan automaattisesti, jotta teksti erottuu. Lisää kuva kenttään **Taustakuva**. |
| `vari` | moskeijan oma pääväri |

**Napit** (enintään 2, ensimmäinen korostetaan; ilman valintaa yläosassa ei ole nappeja):

| Valinta | Nappi |
|---|---|
| `lapsi` | Ilmoita lapsesi opetukseen |
| `toiminta` | Tutustu toimintaamme |
| `rukousajat` | Katso rukousajat |
| `lahjoita` | Lahjoita nyt (rahankeräysluvalla) tai Tuki ja jäsenyys |
| `yhteys` | Ota yhteyttä |
| `oma` | oma teksti ja linkki (kenttä *Oma nappi*), esim. "Liity jäseneksi" |
| oman sivun nimi | esim. `hyvat-lahteet` |

**Taustakuvan vinkit:** vaakakuva, vähintään 1600 px leveä, esim. rukoussali tai moskeija ulkoa.

### 7. Valikko

**Sivusto → Järjestä**: siirrä sivuja nuolilla, lisää omia linkkejä ja piilota sivut, joita moskeijallanne ei ole, esim. *tapahtumat*.
Paneelin Sivusto-lista on samassa järjestyksessä kuin kävijän valikko, joten muutos näkyy molemmissa.
**Lahjoita / Tuki ja jäsenyys** on piilossa automaattisesti, kunnes tiedot on lisätty.

### 8. Tekstit eri kielillä

Sivun kielet valitaan kohdassa **Sivuston asetukset → Sivuston kielet** (esim. suomi, englanti, arabia, somali, turkki …).
Kävijä valitsee kielen yläpalkista. Kentissä on rivi jokaiselle kielelle; paneeli varoittaa puuttuvista
käännöksistä ja voi kääntää ne tekoälyllä. Jos jokin kieli puuttuu, näytetään englanti tai suomi.
Arabia näkyy automaattisesti oikealta vasemmalle.

### 9. Kuvat ja logo

- **Logo:** Ulkoasu → Logo. Jos logossa on tummaa tekstiä, lisää myös **vaalea logo**
  alapalkkia varten (tumma tausta).
- **Kuvagalleria:** Sivusto → Meistä → Kuvagalleria (kuvat lisätään kohdassa Muut → Kuvat). Käytä omia valokuvia. Kuvapankkien kuvia saa käyttää vain luvalla.
- Lapsista ja ihmisistä otettuihin kuviin kysytään lupa.
- Mawaqitissa olevat moskeijan kuvat tulevat sivulle automaattisesti.

### 10. Rukousajat

Rukousajat tulevat automaattisesti, eikä niitä tarvitse muokata sivulla:

| Lähde | Mitä tulee |
|---|---|
| **Masjidbox** | adhan, iqamah ja perjantaina Jumuah. Kun muutat aikoja Masjidboxissa, sivu seuraa perässä. |
| **Mawaqit** | adhan, iqamah, Jumuah ja moskeijan kuvat |
| **rukousajat.fi** | Helsinki, Espoo ja Vantaa, jos moskeijalla ei ole omaa palvelua (oletus näissä kaupungeissa) |

Ilman lähdettä ja aikoja sivulla lukee "Rukousajat lisätään pian". Sivusto ei laske aikoja itse.

Ajat päivittyvät kerran tunnissa. Lisäksi lähteenä voi olla **oma aikataulu**, jonka moskeija kirjoittaa
tai liittää Excelistä paneelissa kuukausi kerrallaan (tyhjä päivä näkyy sivulla tyhjänä).

Paneelissa (Rukousajat ja Jumua) näkyvät **seuraavat 7 päivää** juuri niin kuin ne ovat sivulla, ja
näkymä päivittyy heti asetuksia muutettaessa. Lisäksi:

- **Iqamah** jokaiselle rukoukselle: minuutteja adhanin jälkeen (käytetään, jos lähde ei kerro iqamahia)
  tai **kiinteä kellonaika** (esim. Dhuhr 13.30, voittaa aina).
- **Jumua** ja valinnainen **toinen Jumua**.
- **Muutokset yksittäisiin päiviin** (esim. juhlapäivä, ramadanin Isha): vain muuttuvat ajat. Menneet
  päivät poistuvat itsestään. Toimii kaikkien lähteiden kanssa.

**Mistä ajat tulevat ja mitä puuttuu.** Paneelin Rukousajat-sivulla kohdassa "Miten ajat haetaan" näkyy valitun lähteen hakutapa, milloin ajat haettiin viimeksi, mihin päivään asti aikoja on ja mahdollinen virhe. Lähteestä haettuja aikoja ei koskaan lasketa itse: päivät, joita lähde ei ole vielä julkaissut, näkyvät viivana.
- **Masjidbox:** valitse moskeija hakemalla nimellä. Ajat tulevat Masjidboxin virallisesta rajapinnasta (kuluva ja seuraava kuukausi). Ylläpitäjä lisää rajapinnan avaimen kerran kaikille (Ylläpito → Rukousaikapalvelut, ohjeet sivulla). Ilman avainta ajat luetaan väliaikaisesti julkiselta sivulta (vain 7 päivää). Sivulla näkyy Masjidboxin ehtojen mukaan "Prayer times provided by Masjidbox" ja "Ilmoita virheestä".
- **Mawaqit:** koko vuoden aikataulu, iqamah ja Jumua julkiselta sivulta, avainta ei tarvita.
- **rukousajat.fi:** Helsingin vuosiaikataulu; ei iqamahia eikä Jumuaa.

**Ramadan.** Ramadan on toistaiseksi vain testimoskeijassa (ADR-0002, `ramadan.testi: true`): muiden moskeijoiden sivuilla ei ole Ramadan-sivua lainkaan (`/ramadan/` antaa 404, myös kieliversiot; julkaisuajo poistaa sivun: `.github/scripts/karsi_sivut.py`), ei valikkokohtaa, etusivun riviä eikä Ramadania kalenteriin, eikä paneelissa näy Ramadan-kohtia (Ramadan-välilehti, tiedotteen Näytä Ramadan-sivulla, julkaisustudion Tarawih- ja Eid-pohjat, haku). Aiemmin tallennetut Ramadan-tiedot säilyvät, ne vain eivät näy. Testimoskeijassa Rukousajat-sivulla on Ramadan-osio: tämän päivän suhur ja iftar, koko kuukauden aikataulu (tulostettava) ja Eid-rukous, ja etusivulla lyhyt rivi "Ramadan, päivä 5 · Suhur … · Iftar …". Paneelissa (Rukousajat → Ramadan) voi lisätä tarawih-ajan, Eid-rukouksen ajan ja paikan, fitran ja muuta tietoa. Päivät ovat oletuksena arvio (Umm al-Qura, `_data/ramadan.yml`).

**Lisää kalenteriin.** Rukousajat- ja Tapahtumat-sivuilla kävijä voi rastia, mitä haluaa puhelimensa kalenteriin (rukousajat, Jumua, tapahtumat; testimoskeijassa myös Ramadan), ja tilata sen. Kalenteri päivittyy itsestään: uudet tapahtumat ja muuttuneet ajat tulevat puhelimeen muutaman tunnin sisällä. Moskeijan ei tarvitse tehdä mitään.

### 11. Somet

- **Instagram, YouTube ja Telegram:** uusimmat julkaisut näkyvät sivulla automaattisesti ("Seuraa meitä").
- **Facebook, TikTok, X, Snapchat, WhatsApp-kanava:** näkyvät kuvakkeina.
- Lisää osoitteet paneelin kohtaan **Muut → Some** (Yhteystiedoissa on linkki sinne).

### 12. Lahjoitukset ja lomakkeet

- **Tuki ja lahjoitukset:** Sivusto → Tuki ja jäsenyys (rahankeräysluvalla Lahjoita). Rahankeräyslain (863/2019) vuoksi
  tilinumero, MobilePay, verkkolahjoituksen linkki ja "Lahjoita nyt" -napit näkyvät vain, kun moskeijalla on
  Poliisihallituksen **rahankeräyslupa** tai voimassa oleva **pienkeräysnumero** (pienkeräyksen päättymispäivän
  jälkeen maksutiedot piilotetaan itsestään). Silloin sivulla näkyvät myös lain vaatimat tiedot: keräyksen
  järjestäjä, varojen käyttötarkoitus ja lupanumero. Ilman lupaa sivu on "Tuki ja jäsenyys": moskeijan oma
  teksti (jäsenyys, lahjoituslipas paikan päällä) ja yhteystiedot. Jäsenmaksu ja lahjoituslipas moskeijan
  avoimessa tilaisuudessa eivät vaadi lupaa.
- **Lomakkeet** (lasten opetus, Kysy moskeijalta) avautuvat valmiina WhatsApp-viestinä tai
  sähköpostina. Ilman WhatsAppia viesti lähtee sähköpostilla.

### 13. Näkyvyys Googlessa: tee nämä kerran

Sivu on jo valmiiksi hakukoneystävällinen: siinä on hakusanoja vastaavat otsikot, moskeijan
tiedot Googlelle, sivukartta ja jakokuvat. Nämä kannattaa lisäksi tehdä itse:

1. **Google-yritysprofiili** (business.google.com): moskeija Google Mapsiin ja linkki sivulle.
   Tämä on tärkein, koska haku "moskeija + kaupunki" näyttää ensin kartan.
2. **Google Search Console** (search.google.com/search-console): lisää sivu ja lähetä `sitemap.xml`.
3. **Linkit sivulle** Instagramin biosta, Mawaqitista, Masjidboxista ja muualta.
4. **Oma verkkotunnus** (esim. `moskeija.fi`): pyydä ylläpitäjää ottamaan se käyttöön.

### 14. Ongelmatilanteet

| Ongelma | Ratkaisu |
|---|---|
| Muutos ei näy | Odota 2–3 minuuttia ja päivitä sivu. Kokeile myös yksityisessä ikkunassa. |
| En pääse paneeliin tai en näe moskeijaani | Pyydä pääkäyttäjää kutsumaan sinut, tai pyydä kertakäyttöinen kirjautumislinkki. |
| Rukousaika on väärin | Tarkista aika Masjidboxista tai Mawaqitista. Sivu päivittyy tunnin sisällä. |
| Tapahtuma ei näy | Tarkista päivämäärä. Menneet tapahtumat piiloutuvat. |
| Jokin muu | Ota yhteyttä ylläpitäjään ja kerro sivu, laite ja kuvakaappaus. |

---

<a id="osa-2"></a>

## Osa 2: Ylläpitäjälle

> **Kaikki ylläpito onnistuu hallintapaneelista** (Ylläpito-välilehdet). GitHubia ei tarvita arjessa:
>
> | Välilehti | Mitä siellä tehdään |
> |---|---|
> | 🕌 Moskeijat | Kaikki sivut, tila (julkaistu / luonnos / ehdotus), avaa ja muokkaa, + Uusi moskeija |
> | 🚀 Julkaisut | Jokaisen sivun viimeisin päivitys ✅/❌, julkaise uudelleen tai kaikki kerralla |
> | 📋 Moskeijalista | Suomen moskeijat (sisältörepon moskeijat.csv): lisää moskeija, luo ehdotussivut napista |
> | 🔤 Yhteiset tekstit | Valikot, napit ja otsikot kaikilla sivuilla neljällä kielellä |
> | 🎨 Värimaailmat | Valmiit värit, joista moskeijat valitsevat – muokkaa tai lisää uusia |
> | 🖼️ Taustat ja kuviot | Valmiit taustakuvat (etusivun yläosa) ja taustakuviot – lisää uusia tai poista (`_data/taustakuvat.yml`, `_data/kuviot.yml`) |
> | 🛡️ Ylläpitäjät · 📜 Muutokset · 🐞 Virheloki | Oikeudet, kaikki muutokset ja virheet |
>
> Moskeijan sivulla (Avaa → ⚙️ Ylläpitäjän toiminnot): julkaise uudelleen, muuta ehdotukseksi tai **poista moskeija**
> (kirjoita tunnus vahvistukseksi; jos moskeija ei halua sivua, se merkitään listaan eikä sivua luoda uudelleen).
> Alla olevat GitHub-ohjeet ovat varalla ja pohjan kehittämistä varten.

### 1. Kokonaisuus

```
suomen-moskeijat/pohja            ← yhteinen pohja: ulkoasu, sivut, haut, automaatiot, ohjeet
suomen-moskeijat/<moskeija>       ← yhden moskeijan tiedot + julkaisu.yml, joka kutsuu pohjaa
```

- Jokainen moskeija on **oma reponsa** ja oma sivunsa: `https://suomen-moskeijat.github.io/<moskeija>/`.
- **Muutos pohjaan päivittää kaikki sivut** niiden seuraavassa julkaisussa (kerran tunnissa).
- Moskeijan tiedostot voittavat pohjan tiedostot. Haetut tiedot (rukousajat, somet) säilyvät
  välimuistissa, joten katkos lähteessä ei tyhjennä sivua.

### 2. Kertaluonteiset asetukset

1. **Avain `MOSKEIJA_AVAIN`** (automaatio luo repot ja kutsuu muokkaajat):
   - https://github.com/settings/personal-access-tokens/new
   - Resource owner: `suomen-moskeijat`. Repository access: All repositories.
   - Permissions: **Administration, Contents, Pages, Workflows → Read and write**.
   - Tallenna: pohja → Settings → Secrets and variables → Actions → `MOSKEIJA_AVAIN`.
   - Uusi avain ennen kuin se vanhenee.
2. **Hallintapaneeli:** asennus ja avaimet yksityisen repon `suomen-moskeijat/hallinta` README:ssä.
3. **Organisaation oikeudet:** Settings → Member privileges → Base permissions: **No permission**.
   Muokkaajia ei lisätä organisaation jäseniksi.
4. **Pohjan Pages:** pohja → Settings → Pages → Source: **GitHub Actions** (hakemisto ja ohjeet).

### 3. Uuden moskeijan prosessi: luonnos → hyväksyntä → julkinen

1. **Uusi moskeija** paneelissa (kohta 3c) tai ehdotussivulla **Moskeija lähtee mukaan**. Sivu on nyt **luonnos**: ylhäällä on keltainen palkki
   "Luonnos – sivua ei ole vielä julkaistu", eikä Google näytä sivua.
2. **Tarkista** sivu itse tarkistuslistalla (alla).
3. **Lähetä linkki moskeijalle**, esim. `https://suomen-moskeijat.github.io/<moskeija>/`.
   He katsovat sivun puhelimella ja kertovat korjaukset, tai korjaavat itse paneelissa.
4. **Hyväksyntä:** pääkäyttäjä hyväksyy käyttöehdot ja painaa paneelin etusivulla **Julkaise sivu**.
   Palkki katoaa noin 2 minuutissa, ja Google saa näyttää sivun.
   Kutsuttu pääkäyttäjä saa ensimmäisellä kirjautumisella **aloituksen**: askel kerrallaan käyttöehdot ja oma nimi,
   perustiedot ja mihin viestit tulevat, rukousajat ja Jumua, logo ja värit, kielet (sivu on aluksi vain suomeksi) ja
   valmiit artikkelit, ensimmäiset palvelut sekä lopuksi sivun katsominen ja julkaisu. Jokaisessa askeleessa voi valita
   **Jatka myöhemmin**, ja kesken jäänyt aloitus jatkuu Yleiskatsauksen linkistä. Aloitus tulee vain, kun pääkäyttäjä
   kutsutaan julkaisemattomalle sivulle, jonka käyttöehtoja ei ole vielä hyväksytty; muokkaaja ei näe sitä.
5. Myöhemmin halutessa **oma verkkotunnus** (kohta 8).

> Luonnos ei ole salainen: kuka tahansa, jolla on linkki, voi avata sen. Se ei kuitenkaan näy
> Googlessa eikä missään listassa.

### 3a. Ehdotussivut listasta (moskeijat, jotka eivät vielä ole mukana)

1. Lisää moskeija paneelin **Ylläpito → Moskeijalista** -välilehdellä (tiedosto `moskeijat.csv` on yksityisessä
   sisältörepossa, ei pohjassa). Sarakkeet: nimi, kaupunki, osoite, puhelin, sähköposti, nettisivu, facebook, **repo**
   (sivun tunnus, esim. `masjid-al-nuur`), **tila** (tyhjä = tee ehdotus, `ei` = ei sivua), lähde, huomautus.
2. Paina moskeijan kohdalla **Luo ehdotussivu** (tai **Luo ehdotussivut kaikille**). Paneeli käynnistää työnkulun
   **Luo ehdotussivut listasta**, joka kirjoittaa ehdotukset sisältörepoon (kansio ja sivustoluettelon rivi); sivut
   rakentuvat seuraavassa rakennusajossa ja näkyvät vain luonnoslinkillä.
3. Sivut syntyvät **ehdotuksina**, ja niissä on vain listan julkiset tiedot: nimi, osoite, yhteystiedot ja linkit.
   Rukousajat tulevat rukousajat.fi:stä (Helsinki, Espoo ja Vantaa); muualla sivulla lukee "Rukousajat lisätään pian".
4. Hakemisto https://suomen-moskeijat.github.io/pohja/ päivittyy. Lähetä moskeijalle linkki heidän sivuunsa.

> Moskeijan omaa nettisivua (logo, kuvat, tekstit) **ei** tuoda ehdotukseen. Se tuodaan vasta, kun moskeija
> on lähtenyt mukaan ja antanut luvan (kohta 3b).

### 3b. Mukaan lähtevän moskeijan tiedot heidän vanhalta sivultaan

Kun moskeija lähtee mukaan ja antaa luvan, voit tuoda heidän vanhalta sivultaan logon, kuvat ja tekstit:
- **Uusi repo:** Lisää moskeija -lomake ja kenttä **nettisivu**.
- **Ehdotussivu on jo olemassa:** täydennä tiedot paneelissa, tai pyydä Claudea tuomaan ne (`tuo_sivusto.py`).

### 3c. Uuden moskeijan lisääminen lomakkeella (noin 2 minuuttia)

**pohja → Actions → Lisää moskeija → Run workflow**

| Kenttä | Selitys |
|---|---|
| **nettisivu** | Moskeijan nykyinen sivu. Sieltä haetaan logo, värit, osoite, sähköposti, puhelin, WhatsApp, somet, Jumuan aika, Meistä-teksti ja valokuvat. WordPress-sivuilta tulevat myös sivut ja kirjoitukset. |
| **mawaqit / masjidbox** | Linkin tai upotuskoodin voi liittää sellaisenaan. Rukousajat, iqamah ja Jumuah tulevat niistä automaattisesti. |
| **nimi, kaupunki, osoite** | Voi jättää tyhjiksi, jos nettisivu, Mawaqit tai Masjidbox kertoo ne. |
| **instagram, whatsapp, youtube, telegram** | valinnaisia |
| **repo** | valinnainen, oletuksena nimestä |

**Lisäyksen jälkeen tarkista** (paneelissa):
- [ ] nimi, osoite ja kartan sijainti
- [ ] logo ja värit (värit arvataan logosta)
- [ ] kuvat: poista julisteet ja kuvapankkikuvat
- [ ] Meistä-teksti sekä tuodut omat sivut ja artikkelit
- [ ] rukousajat verrattuna moskeijan omaan näyttöön
- [ ] käännökset (tuotu teksti on vain suomeksi)

**Kokeilu ilman että mitään luodaan:**

```
python3 .github/scripts/lisaa_moskeija.py --kuiva /tmp/kokeilu --nettisivu https://moskeija.fi
```

### 4. Muokkaajat

**Suositus: hallintapaneeli.** Muokkaajat eivät tarvitse GitHub-tunnusta. He kirjautuvat sähköpostiin tulevalla koodilla.

- Paneelin koodi ja käyttöönotto-ohje ovat yksityisessä repossa `suomen-moskeijat/hallinta` (README).
- **Ylläpitäjä** näkee kaikki moskeijat. Avaa moskeija → **Käyttäjät** → kutsu moskeijan pääkäyttäjä sähköpostilla.
- **Pääkäyttäjä** kutsuu itse omat muokkaajansa. Muokkaaja pääsee vain oman moskeijansa tapahtumiin, tiedotteisiin ja kuviin.
- **Pääkäyttäjä julkaisee sivun** paneelin etusivulla: *Sivu on luonnos → Julkaise sivu*.
- Paneelin esikatselu näyttää värit, taustan ja esittelytekstin heti moskeijan oikealla sivulla.
- **Historia:** kuka muutti mitä, ja muutoksen voi perua yhdellä napilla.

Kaikki muokkaus tapahtuu paneelissa. GitHub-tunnusta ei tarvita, eikä muokkaajia lisätä GitHubiin.

### 5. Mitä tapahtuu automaattisesti

| Mitä | Milloin | Missä |
|---|---|---|
| Moskeijan sivun julkaisu: rukousajat, Instagram, YouTube, Telegram, Mawaqitin kuvat | kerran tunnissa ja aina kun tietoja muutetaan | moskeijan repo → Actions → *Julkaise sivusto* |
| Yhteiset artikkelit (islaminusko.fi) | maanantaisin | pohja → Actions → *Päivitä yhteiset artikkelit* |
| suomenmoskeijat.fi (neutraali sivu, ei julkista sisältöä) | rakennusajossa, kun sivu muuttuu | pohja → Actions → *Rakennusajo* |
| Vanha moskeijahakemisto (github.io) | pohjan muutoksesta ja 6 tunnin välein | pohja → Actions → *Esittelysivu* |

Jokaisen ajon voi käynnistää myös käsin: Actions → työnkulku → **Run workflow**.

### 6. Pohjan muuttaminen

- Ulkoasu: `assets/css/sivu.css`. Toiminnot: `assets/js/sivu.js`.
- Sivut: juuren `*.html`. Osat: `_includes/osat/`. Käännökset: `_data/kaannokset.yml`.
- Uusi moskeija: pohjan `lisaa_moskeija.py` (Lisää moskeija -työnkulku). Paneelin kentät: `hallinta`-repon `src/kaavio.js`.
- **Muutokset tehdään `testi`-haaraan, ei suoraan `main`-haaraan.** Testimoskeija (https://suomen-moskeijat.github.io/testimoskeija/) ja testipaneeli (https://hallinta-testi.suomenmoskeijat.fi) näyttävät testiversion heti. Muiden moskeijoiden sivut eivät muutu.
- Kirjoita jokaisesta muutoksesta kohta tiedostoon `testit.json` (otsikko, mitä tarkistetaan, linkit). Testaaja kuittaa kohdat paneelissa: **Testaus ja julkaisu** → Toimii ✓ / Ei toimi ✗ ja syy. Kun korjaat hylätyn kohdan, nosta sen `versio`.
- Kun kaikki on hyväksytty, ylläpitäjä painaa paneelissa **Julkaise kaikille**. `testi` yhdistyy `main`-haaraan, ja kaikki moskeijat saavat muutoksen tunnin sisällä. Kuka testasi ja kuka julkaisi, näkyy paneelin historiassa.
- Älä kirjoita `testit.json`-tiedostoon nimiä tai muita henkilötietoja: repo on julkinen.
- Siirrettyjen moskeijoiden vanhat moskeijarepot poistetaan käsin: pohja → Actions → **Poista vanhat repot** (kuivaharjoitus ensin; Hyvinkää ja testimoskeija eivät koskaan kuulu poistettaviin).

### 7. Rukousaikojen lähteet

Moskeijan tiedostossa `_moskeijat/<slug>.md`:

```yaml
rukousajat:
  lahde: masjidbox        # masjidbox | mawaqit | rukousajat | taulukko | laskenta
  tunnus: masjid-sunnah-helsinki
  iqamah: { fajr: 10, dhuhr: 10, asr: 10, maghrib: 5, isha: 10 }   # valinnainen: moskeijan antamat minuutit adhanin jälkeen
```

- `rukousajat`: Helsingin taulukko rukousajat.fi:stä. Se on oletus Helsingissä, Espoossa ja Vantaalla.
- `laskenta`: muualla MWL ja Shafi samoin kuin rukousajat.fi (tarkistettu: Tampere, Turku, Oulu, Jyväskylä, Kuopio).
- `taulukko`: oma CSV `_data/aikataulut/<slug>/VVVV-KK.csv`.

### 8. Oma verkkotunnus

1. Moskeijan repo → Settings → Pages → Custom domain, esim. `moskeija.fi`.
2. Verkkotunnuksen DNS: `CNAME` → `suomen-moskeijat.github.io` (tai A-tietueet GitHubin ohjeen mukaan).
3. Moskeijan `_config.yml`: `url: "https://moskeija.fi"` ja `baseurl: ""`.

### 9. Yhteiset artikkelit

- Lähteet on määritelty tiedostossa `.github/scripts/artikkelit.py` (`LAHTEET`).
- Moskeija valitsee ne kentässä `artikkelit.lahteet`. Valitsemattomat poistetaan julkaisussa.
- islaminusko.fi: "Sisältöä saa jakaa ja kopioida ei-kaupallisiin sekä voittoa tavoittelemattomiin
  tarkoituksiin." Lähde ja linkki alkuperäiseen ovat mukana, ja Googlelle merkitään alkuperäinen (canonical).
  Kuvia ei tuoda.

### 10. Vianetsintä

| Ongelma | Katso |
|---|---|
| Sivu ei päivity | moskeijan repo → Actions → viimeisin *Julkaise sivusto* → punainen vaihe |
| "Get Pages site failed" | moskeijan repo → Settings → Pages → Source: GitHub Actions |
| Lisää moskeija epäonnistuu | `MOSKEIJA_AVAIN` puuttuu tai on vanhentunut, tai sen oikeudet eivät riitä |
| Rukousajat puuttuvat | lähteen tunnus väärin: avaa `masjidbox.com/prayer-times/<tunnus>` tai `mawaqit.net/fi/<tunnus>` |
| Instagram ei päivity | Instagram estää välillä haun. Vanhat julkaisut jäävät näkyviin. |

### 11. Tiedostot

```
pohja/
  OHJEET.md                  ← nämä ohjeet
  README.md                  ← tekninen yleiskuva
  _layouts/ _includes/       ← sivupohjat ja osat
  assets/                    ← tyylit, toiminnot, kuvakkeet
  _data/kaannokset.yml       ← käyttöliittymän tekstit neljällä kielellä
  _artikkelit/islaminusko/   ← yhteiset artikkelit
  esittely/ohjeet/           ← ohjesivun ulkoasu (hakemisto + ohjeet: /pohja/)
  .github/scripts/           ← haut ja automaatiot (Python, ei riippuvuuksia)
  .github/workflows/         ← rakennusajo, julkaisu (Hyvinkää), Lisää moskeija, poisto, artikkelit, hakemisto ja ohjeet, Poista vanhat repot
```
