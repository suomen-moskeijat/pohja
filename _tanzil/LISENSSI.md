# Tanzil: Koraanin teksti ja käännökset

Koraanin jae -osio (hallinta#36) näyttää Koraanin arabiankielisen tekstin ja valitun käännöksen näistä tiedostoista.
Tiedostot on ladattu Tanzil-projektilta 21.11.2026, ja ne ovat **muuttamattomina** (tekijänoikeusilmoitukset mukana).
Älä muokkaa niitä käsin. Hakua varten sivupohja käyttää niistä johdettuja tiedostoja `_data/koraani/`
(tee uudelleen: `python3 .github/scripts/koraani.py`). Johdetuissa tiedostoissa on sama tekijänoikeusilmoitus, ja testi
(hallinta `testi/koraani-tanzil.mjs`) varmistaa, että jokainen jae on tavu tavulta sama kuin tässä kansiossa.

| Tiedosto | Mikä | Lähde |
| --- | --- | --- |
| `quran-uthmani.txt` | Koraanin teksti, Uthmani (Tanzil Quran Text, Version 1.1), oletusasetukset, tekstimuoto jaenumeroin | https://tanzil.net/download/ |
| `quran-data.xml` | Suurien tiedot (nimet ja jakeiden määrä) | https://tanzil.net/docs/Quran_Metadata |
| `en.sahih.txt` | Saheeh International (englanti, oletus) | https://tanzil.net/trans/ |
| `en.pickthall.txt` | Mohammed Marmaduke William Pickthall (englanti) | https://tanzil.net/trans/ |
| `en.yusufali.txt` | Abdullah Yusuf Ali (englanti) | https://tanzil.net/trans/ |
| `so.abduh.txt` | Mahmud Muhammad Abduh (somali) | https://tanzil.net/trans/ |

## Käyttöehdot (Tanzil, sellaisinaan)

**Koraanin teksti** (https://tanzil.net/docs/Text_License):

> Permission is granted to copy and distribute verbatim copies of the Quran text provided here, but changing the text is
> not allowed. The text can be used in any website or application, provided that its source (Tanzil Project) is clearly
> indicated, and a link is made to tanzil.net to enable users to keep track of changes.
>
> This copyright notice shall be included in all verbatim copies of the text, and shall be reproduced appropriately in
> all files derived from or containing substantial portion of this text.

**Käännökset** (https://tanzil.net/trans/):

> The translations provided at this page are for non-commercial purposes only. If used otherwise, you need to obtain
> necessary permission from the translator or the publisher.
>
> If you are using more than three of the following translations in a website or application, we require you to put a
> link back to this page to make sure that subsequent users have access to the latest updates.
>
> Redistributing the following list in another website is not allowed, unless direct permission is granted by the
> Tanzil Project.

## Miten ehdot täytetään

- Moskeijoiden sivut ovat ilmaisia eikä niissä ole mainoksia: käyttö on ei-kaupallista.
- Arabiankielistä tekstiä ja käännöksiä ei muuteta: sivu näyttää jakeen sellaisenaan, eikä paneelissa voi muokata niitä.
- Jokaisessa Koraanin jae -osiossa lukee lähde (Tanzil Project) ja linkki jakeeseen Tanzilissa (esim.
  https://tanzil.net/#4:94); käännöksen kohdalla kääntäjän nimi ja linkki samaan jakeeseen käännöksessä
  (esim. https://tanzil.net/#trans/en.sahih/4:94).
- Tanzilin käännöslistaa ei kopioida: pohjassa on vain yllä olevat käännökset. Uusi käännös lisätään lataamalla se
  Tanzilista tähän kansioon ja ajamalla skripti (vain käännökset, joiden ehdot sallivat ei-kaupallisen käytön).
  Esimerkiksi The Clear Quran (Khattab) ei ole Tanzilissa ja vaatii julkaisijan luvan, joten sitä ei ole.
