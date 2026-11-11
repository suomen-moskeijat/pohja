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
| **Kaikki moskeijat ja niiden tila** | https://suomen-moskeijat.github.io/pohja/ | kaikille |
| **Nämä ohjeet** | https://suomen-moskeijat.github.io/pohja/ohjeet/ | kaikille |
| **Moskeijan sivu** | `https://suomen-moskeijat.github.io/<moskeija>/` (tai oma verkkotunnus) | kävijöille |
| **Sivun muokkaus** | https://app.pagescms.org → valitse moskeija | moskeijan muokkaajille |
| **Uusi moskeija, muokkaajat, ehdotussivut** | https://github.com/suomen-moskeijat/pohja/actions | ylläpitäjille |
| **Moskeijalista** | `moskeijat.csv` pohja-repossa | ylläpitäjille |
| **Esimerkkisivut** | https://suomen-moskeijat.github.io/pohja/masjid-sunnah/ ja `/pohja/hyvinkaa/` | esittelyyn |

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
| Haluan näyttää moskeijalle, millainen sivu heille tulisi | ylläpitäjä | Katso hakemistosta, onko heillä ehdotussivu. Jos ei, lisää heidät `moskeijat.csv`:hen ja aja **Luo ehdotussivut listasta** (Osa 2, kohta 3a). Lähetä linkki. |
| Moskeija haluaa lähteä mukaan | ylläpitäjä | 1) Pages CMS → Moskeijan tiedot → poista **Ehdotus**. 2) Jos heillä on vanha nettisivu: kysy lupa ja tuo tiedot (Osa 2, kohta 3b). 3) Kysy muokkaajien GitHub-tunnukset → **Lisää muokkaaja**. Sivu on nyt luonnos. |
| Moskeija on tarkistanut sivun ja hyväksyy sen | muokkaaja tai ylläpitäjä | Pages CMS → Moskeijan tiedot → poista **Luonnos** → Save. Sivu on julkinen noin 2 minuutissa. |
| Moskeija ei halua sivua | ylläpitäjä | Arkistoi repo (repo → Settings → Archive) tai poista se, ja merkitse `moskeijat.csv`:hen tila `ei`. Sivu poistuu hakemistosta. |
| Uusi moskeija, joka ei ole listalla | ylläpitäjä | **Lisää moskeija** -lomake (nimi, kaupunki, Mawaqit- tai Masjidbox-linkki, nettisivu luvalla). |
| Moskeija haluaa muokata tekstejä tai lisätä tapahtuman | muokkaaja | Pages CMS (Osa 1). |
| Uusi henkilö haluaa muokkausoikeuden | ylläpitäjä | GitHub-tunnus → Actions → **Lisää muokkaaja** (repo + tunnus). |
| Henkilö lopettaa | ylläpitäjä | moskeijan repo → Settings → Collaborators → Remove. |
| Rukousajat ovat väärin | muokkaaja | Tarkista Masjidbox tai Mawaqit. Jos moskeija ei käytä kumpaakaan, ylläpitäjä valitsee lähteen (Osa 2, kohta 7). |
| Moskeija ottaa Mawaqitin tai Masjidboxin käyttöön | ylläpitäjä | Pages CMS → Moskeijan tiedot → Rukousajat: lähde ja tunnus. |
| Moskeija haluaa oman osoitteen (esim. moskeija.fi) | ylläpitäjä | Osa 2, kohta 8. Tee vasta, kun sivu on julkaistu. |
| Sivu ei päivity tai näyttää rikkinäiseltä | ylläpitäjä | Osa 2, kohta 10 (Actions-loki). |
| Haluan muuttaa ulkoasua kaikille | ylläpitäjä | Muutos pohjaan → tarkista esittelysivulta → kaikki päivittyvät tunnin sisällä. |
| Avain `MOSKEIJA_AVAIN` vanhenee | ylläpitäjä | Tee uusi (Osa 2, kohta 2) ja korvaa salaisuus. |

---

<a id="osa-1"></a>

## Osa 1: Moskeijan muokkaajalle

### 1. Mitä tarvitset

> **Uusi sivu on aluksi luonnos** (keltainen palkki ylhäällä). Kun sivu on kunnossa,
> poista Pages CMS:ssä kohdasta **Moskeijat** valinta **Luonnos**, niin sivu on julkinen.


1. **GitHub-tunnus** (ilmainen): https://github.com/signup
2. Kerro tunnuksesi ylläpitäjälle. Saat sähköpostiin **kutsun** moskeijasi sivuun: hyväksy se.
   Oikeus koskee vain oman moskeijasi sivua.
3. Muokkaaminen tapahtuu osoitteessa **https://app.pagescms.org**. Kirjaudu GitHub-tunnuksella.

> Toimii puhelimella ja tietokoneella. Tallennuksen jälkeen sivu päivittyy noin 2 minuutissa.

### 2. Mistä mitäkin muokataan

Kun olet kirjautunut ja valinnut moskeijasi, vasemmalla on valikko:

| Valikossa | Mitä siellä tehdään |
|---|---|
| **Moskeijan tiedot** | moskeijan tiedot: yhteystiedot, Jumua, tekstit eri kielillä, etusivun tausta ja napit, valikko, lahjoitustiedot, somet, värit ja logo |
| **Tapahtumat** | tulevat tapahtumat (menneet katoavat sivulta itsestään) |
| **Artikkelit** | moskeijan omat kirjoitukset ja tiedotteet |
| **Omat sivut** | lisäsivut, esim. kirjasto, hyvät lähteet, viikko-ohjelma |
| **Media** | kuvat ja tiedostot (myös PDF) |

Muokkaa kenttää ja paina lopuksi **Save** (Tallenna).

### 3. Tapahtuman lisääminen

1. **Tapahtumat → Add an entry**
2. Täytä **nimi**, **päivämäärä** ja halutessasi **alkaa / päättyy klo** (esim. `18.00`), paikka, kuva ja kuvaus.
3. **Save.** Tapahtuma näkyy etusivulla ja Tapahtumat-sivulla. Se katoaa, kun päivä on mennyt.

### 4. Artikkelin tai tiedotteen kirjoittaminen

1. **Artikkelit → Add an entry**
2. **Otsikko**, **päivämäärä** ja **aihe**. Valitse aihe listasta, esim. *Tiedotteet* tai *Islamin perusteet*.
   Jos sopivaa ei ole, kirjoita uusi aihe. Se tulee artikkelisivulle omaksi napikseen.
3. **Lyhyt kuvaus** näkyy listassa, ja **teksti** on varsinainen kirjoitus. Lisää halutessasi kuva.
4. **Save.** Kolme uusinta näkyy etusivulla, ja kaikki löytyvät Artikkelit-sivulta haun ja aiheiden kautta.

**Yhteiset artikkelit:** sivulla on valmiina noin 110 suomenkielistä artikkelia islaminusko.fi:stä
(lähde mainitaan jokaisessa). Ne saa pois tai takaisin kohdasta **Moskeijan tiedot → Yhteiset artikkelit**.

### 5. Oma sivu (kirjasto, lähteet, viikko-ohjelma …)

1. **Omat sivut → Add an entry**
2. **Sivun nimi.** Tiedoston nimestä tulee osoite, esim. `hyvat-lahteet` → `/hyvat-lahteet/`.
3. Kirjoita **sisältö** ja lisää halutessasi **linkit kortteina** (nimi, kuvaus, osoite tai PDF-tiedosto, kuvake).
4. **Näytä valikossa** päälle, niin sivu tulee valikkoon. **Järjestys** määrää paikan valikossa.

### 6. Kokeile ulkoasua ennen valintaa: /esikatselu/

Avaa oma sivusi ja lisää osoitteen perään **`/esikatselu/`**, esim.
`https://suomen-moskeijat.github.io/hyvinkaa-islam-keskus/esikatselu/`.
Napauta värimaailmaa ja taustaa: etusivu vaihtuu heti puhelimen kokoisessa ikkunassa.
Sivu kertoo myös, mistä saman valinnan tekee Pages CMS:ssä. Esikatselu ei muuta mitään.

**Värimaailmat** (valitaan nimellä, värikoodeja ei tarvita): Kulta-ruskea, Smaragdinvihreä,
Metsänvihreä ja kulta, Turkoosi, Sininen, Yönsininen ja kulta, Persiansininen, Violetti,
Viininpunainen, Terrakotta, Oliivinvihreä, Grafiitti ja kulta, sekä *Nykyiset värit (logon mukaan)*.
Valinta: **Moskeijan tiedot → Ulkoasu: värit ja logo → Värit**.

**Taustakuviot alueittain** (hallintapaneeli → Ulkoasu): kuvio valitaan erikseen sivujen yläosaan,
alapalkkiin ja nostoihin (lahjoitus, lasten opetus), tai "Ei kuviota". Kuvion väri tulee värimaailmasta.

**Lomakkeiden lähetys ja WhatsApp-napit** (hallintapaneeli → Sivut ja osiot → Yhteystiedot):
lomakkeiden viestit sähköpostiin, WhatsAppiin tai kävijän valinnan mukaan, ja WhatsApp-napit
näkyviin, ilman kulman pikanappia tai kokonaan piiloon.

### 6b. Etusivun yläosa: tausta ja napit

**Moskeijan tiedot → Etusivun yläosa**

| Tausta | Miltä näyttää |
|---|---|
| `kuvio` | vaalea kuviotausta (oletus) |
| `kuva` | oma valokuva, joka tummennetaan automaattisesti, jotta teksti erottuu. Lisää kuva kenttään **Taustakuva**. |
| `vari` | moskeijan oma pääväri |

**Napit** (enintään 2, ensimmäinen korostetaan):

| Valinta | Nappi |
|---|---|
| `lapsi` | Ilmoita lapsesi opetukseen |
| `toiminta` | Tutustu toimintaamme |
| `rukousajat` | Katso rukousajat |
| `lahjoita` | Lahjoita nyt |
| `yhteys` | Ota yhteyttä |
| `oma` | oma teksti ja linkki (kenttä *Oma nappi*), esim. "Liity jäseneksi" |
| oman sivun nimi | esim. `hyvat-lahteet` |

**Taustakuvan vinkit:** vaakakuva, vähintään 1600 px leveä, esim. rukoussali tai moskeija ulkoa.

### 7. Valikko

**Moskeijan tiedot → Piilota valikosta**: valitse sivut, joita moskeijallanne ei ole, esim. *tapahtumat*.
**Lahjoita** on piilossa automaattisesti, kunnes lahjoitustiedot on lisätty.

### 8. Tekstit eri kielillä

Sivu on neljällä kielellä: suomi, englanti, arabia ja somali. Kävijä valitsee kielen yläpalkista.
Kentissä on rivi jokaiselle kielelle. Jos jokin kieli puuttuu, näytetään englanti tai suomi.
Arabia näkyy automaattisesti oikealta vasemmalle.

### 9. Kuvat ja logo

- **Logo:** Moskeijan tiedot → Ulkoasu → Logo. Jos logossa on tummaa tekstiä, lisää myös **vaalea logo**
  alapalkkia varten (tumma tausta).
- **Kuvagalleria:** Moskeijan tiedot → Kuvagalleria. Käytä omia valokuvia. Kuvapankkien kuvia saa käyttää vain luvalla.
- Lapsista ja ihmisistä otettuihin kuviin kysytään lupa.
- Mawaqitissa olevat moskeijan kuvat tulevat sivulle automaattisesti.

### 10. Rukousajat

Rukousajat tulevat automaattisesti, eikä niitä tarvitse muokata sivulla:

| Lähde | Mitä tulee |
|---|---|
| **Masjidbox** | adhan, iqamah ja perjantaina Jumuah. Kun muutat aikoja Masjidboxissa, sivu seuraa perässä. |
| **Mawaqit** | adhan, iqamah, Jumuah ja moskeijan kuvat |
| **rukousajat.fi** | Helsinki, Espoo ja Vantaa, jos moskeijalla ei ole omaa palvelua |
| **laskenta** | muualla sijainnista samalla tavalla kuin rukousajat.fi |

Ajat päivittyvät kerran tunnissa. **Iqamah:** jos lähde ei kerro iqamahia, käytetään moskeijan
oletusminuutteja (Moskeijan tiedot → Rukousajat → Iqamah oletus).

### 11. Somet

- **Instagram, YouTube ja Telegram:** uusimmat julkaisut näkyvät sivulla automaattisesti ("Seuraa meitä").
- **Facebook, TikTok, X, Snapchat, WhatsApp-kanava:** näkyvät kuvakkeina.
- Lisää osoitteet kohtaan **Moskeijan tiedot → Some**.

### 12. Lahjoitukset ja lomakkeet

- **Lahjoitustiedot:** Moskeijan tiedot → Lahjoitus (saaja, tilinumero, viite, MobilePay tai verkkomaksun linkki).
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
| En näe moskeijaani Pages CMS:ssä | Hyväksy kutsu sähköpostista, tai pyydä ylläpitäjää lisäämään sinut. |
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
> | 📋 Moskeijalista | Suomen moskeijat (moskeijat.csv): lisää moskeija, luo ehdotussivut napista |
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
2. **Pages CMS -sovellus** organisaatioon: kirjaudu https://app.pagescms.org ja asenna sovellus
   organisaatiolle `suomen-moskeijat` (kaikki repot).
3. **Organisaation oikeudet:** Settings → Member privileges → Base permissions: **No permission**.
   Muokkaajia ei lisätä organisaation jäseniksi.
4. **Pohjan Pages:** pohja → Settings → Pages → Source: **GitHub Actions** (esittely ja ohjeet).

### 3. Uuden moskeijan prosessi: luonnos → hyväksyntä → julkinen

1. **Lisää moskeija** (kohta 3c) tai poista ehdotussivulta Ehdotus-valinta. Sivu on nyt **luonnos**: ylhäällä on keltainen palkki
   "Luonnos – sivua ei ole vielä julkaistu", eikä Google näytä sivua.
2. **Tarkista** sivu itse tarkistuslistalla (alla).
3. **Lähetä linkki moskeijalle**, esim. `https://suomen-moskeijat.github.io/<moskeija>/`.
   He katsovat sivun puhelimella ja kertovat korjaukset, tai korjaavat itse Pages CMS:ssä.
4. **Hyväksyntä:** Pages CMS → Moskeijan tiedot → poista valinta **Luonnos** → Save.
   Palkki katoaa noin 2 minuutissa, ja Google saa näyttää sivun.
5. Myöhemmin halutessa **oma verkkotunnus** (kohta 8).

> Luonnos ei ole salainen: kuka tahansa, jolla on linkki, voi avata sen. Se ei kuitenkaan näy
> Googlessa eikä missään listassa.

### 3a. Ehdotussivut listasta (moskeijat, jotka eivät vielä ole mukana)

1. Lisää moskeija tiedostoon **`moskeijat.csv`** (pohja-repo → tiedosto → kynä → muokkaa → *Commit*).
   Sarakkeet: nimi, kaupunki, osoite, puhelin, sähköposti, nettisivu, facebook, **repo** (sivun osoite,
   esim. `masjid-al-nuur`), **tila** (tyhjä = tee ehdotus, `ei` = ei sivua), lähde, huomautus.
2. **Actions → Luo ehdotussivut listasta → Run workflow.** Kenttä *vain* tyhjäksi = kaikki listan moskeijat,
   joilla ei vielä ole sivua. Voit myös kirjoittaa yhden repon nimen.
3. Sivut syntyvät **ehdotuksina**, ja niissä on vain listan julkiset tiedot: nimi, osoite, yhteystiedot ja linkit.
   Rukousajat tulevat rukousajat.fi:stä (Helsinki, Espoo ja Vantaa) tai lasketaan sijainnista.
4. Hakemisto https://suomen-moskeijat.github.io/pohja/ päivittyy. Lähetä moskeijalle linkki heidän sivuunsa.

> Moskeijan omaa nettisivua (logo, kuvat, tekstit) **ei** tuoda ehdotukseen. Se tuodaan vasta, kun moskeija
> on lähtenyt mukaan ja antanut luvan (kohta 3b).

### 3b. Mukaan lähtevän moskeijan tiedot heidän vanhalta sivultaan

Kun moskeija lähtee mukaan ja antaa luvan, voit tuoda heidän vanhalta sivultaan logon, kuvat ja tekstit:
- **Uusi repo:** Lisää moskeija -lomake ja kenttä **nettisivu**.
- **Ehdotussivu on jo olemassa:** täydennä tiedot Pages CMS:ssä, tai pyydä Claudea tuomaan ne (`tuo_sivusto.py`).

### 3c. Uuden moskeijan lisääminen lomakkeella (noin 2 minuuttia)

**pohja → Actions → Lisää moskeija → Run workflow**

| Kenttä | Selitys |
|---|---|
| **nettisivu** | Moskeijan nykyinen sivu. Sieltä haetaan logo, värit, osoite, sähköposti, puhelin, WhatsApp, somet, Jumuan aika, Meistä-teksti ja valokuvat. WordPress-sivuilta tulevat myös sivut ja kirjoitukset. |
| **mawaqit / masjidbox** | Linkin tai upotuskoodin voi liittää sellaisenaan. Rukousajat, iqamah ja Jumuah tulevat niistä automaattisesti. |
| **nimi, kaupunki, osoite** | Voi jättää tyhjiksi, jos nettisivu, Mawaqit tai Masjidbox kertoo ne. |
| **instagram, whatsapp, youtube, telegram** | valinnaisia |
| **muokkaajat** | GitHub-tunnukset pilkulla eroteltuina. Kutsu vain tähän moskeijaan. |
| **repo** | valinnainen, oletuksena nimestä |

**Lisäyksen jälkeen tarkista** (Pages CMS:ssä tai repossa):
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

Vanha tapa (GitHub-tunnus ja Pages CMS) toimii yhä:

- **Uusi moskeija:** kenttä *muokkaajat* lomakkeessa.
- **Myöhemmin:** pohja → Actions → **Lisää muokkaaja** (repo ja tunnukset), tai
  moskeijan repo → Settings → Collaborators → Add people → **Write**.
- Muokkaaja näkee ja voi muokata vain oman moskeijansa sivua.
- Poistaminen: moskeijan repo → Settings → Collaborators → Remove.

### 5. Mitä tapahtuu automaattisesti

| Mitä | Milloin | Missä |
|---|---|---|
| Moskeijan sivun julkaisu: rukousajat, Instagram, YouTube, Telegram, Mawaqitin kuvat | kerran tunnissa ja aina kun tietoja muutetaan | moskeijan repo → Actions → *Julkaise sivusto* |
| Yhteiset artikkelit (islaminusko.fi) | maanantaisin | pohja → Actions → *Päivitä yhteiset artikkelit* |
| Esittelysivu ja nämä ohjeet | pohjan muutoksesta ja 6 tunnin välein | pohja → Actions → *Esittelysivu* |

Jokaisen ajon voi käynnistää myös käsin: Actions → työnkulku → **Run workflow**.

### 6. Pohjan muuttaminen

- Ulkoasu: `assets/css/sivu.css`. Toiminnot: `assets/js/sivu.js`.
- Sivut: juuren `*.html`. Osat: `_includes/osat/`. Käännökset: `_data/kaannokset.yml`.
- Uuden moskeijan malli: `malli/` (myös Pages CMS:n kentät `malli/.pages.yml`).
- **Testaa esittelysivulla**: https://suomen-moskeijat.github.io/pohja/. Esimerkit ovat kansiossa `esittely/`.
- Jos lisäät Pages CMS -kenttiä, kopioi `malli/.pages.yml` myös olemassa oleviin moskeijoihin.

### 7. Rukousaikojen lähteet

Moskeijan tiedostossa `_moskeijat/<slug>.md`:

```yaml
rukousajat:
  lahde: masjidbox        # masjidbox | mawaqit | rukousajat | taulukko | laskenta
  tunnus: masjid-sunnah-helsinki
  iqamah_oletus: { fajr: 10, dhuhr: 10, asr: 10, maghrib: 5, isha: 10 }
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
  malli/                     ← uuden moskeijan tiedostot
  esittely/                  ← esimerkkimoskeijat (esittelysivu)
  .github/scripts/           ← haut ja automaatiot (Python, ei riippuvuuksia)
  .github/workflows/         ← julkaisu, Lisää moskeija, Lisää muokkaaja, artikkelit, esittely
```
