#!/usr/bin/env node
/*
 * Kalenteritilaukset (.ics): julkaisuajo kutsuu tätä Jekyllin jälkeen.
 *   TZ=Europe/Helsinki node .github/scripts/kalenteri.js _site
 *
 * Lukee _site/kalenteri/tiedot.json (moskeijan rukousasetukset, tapahtumat ja Ramadan, jos käytössä) ja tekee
 * kansioon _site/kalenteri/ tiedostot jokaiselle valintojen yhdistelmälle, esim.
 *   rukous.ics, rukous-jumua.ics, tapahtumat.ics, rukous-jumua-tapahtumat-ramadan.ics
 * Sivun "Lisää kalenteriin" -kortti valitsee tiedoston rastien mukaan. Puhelin hakee tilatun
 * kalenterin uudelleen muutaman tunnin välein, ja sivu rakennetaan kerran tunnissa, joten
 * uudet tapahtumat ja muuttuneet ajat päivittyvät kalenteriin itsestään.
 *
 * Rukousajat tulevat täsmälleen kuten sivulla (assets/js/sivu.js: ajat()): lähteen tai moskeijan oma
 * aikataulu (CSV), iqamah, Jumua ja päiväkohtaiset muutokset. Aikoja ei lasketa itse: päivä, jolle aikaa
 * ei ole, jää pois. Moskeijan itse kirjoittama Jumua näkyy silloinkin.
 * Ei ulkoisia riippuvuuksia.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const SIVU = process.argv[2] || '_site';
const KANSIO = path.join(SIVU, 'kalenteri');
const NIMET = { rukous: 'Rukousajat', jumua: 'Jumua', tapahtumat: 'Tapahtumat', ramadan: 'Ramadan' };
const RUKOUKSET = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha'];
const RUKOUSNIMI = { fajr: 'Fajr', dhuhr: 'Dhuhr', asr: 'Asr', maghrib: 'Maghrib', isha: 'Isha' };
const CSV = { fajr: 'fajr', sunrise: 'auringonnousu', dhuhr: 'dhuhr', asr: 'asr', maghrib: 'maghrib', isha: 'isha' };
const RUKOUS_PAIVIA = 60;   // rukousajat näin monelta päivältä eteenpäin (ikkuna liukuu joka julkaisussa)
const JUMUA_VIIKKOJA = 26;
const TZ = 'Europe/Helsinki';

const tiedot = JSON.parse(fs.readFileSync(path.join(KANSIO, 'tiedot.json'), 'utf8'));
// Ramadan vain, kun se on käytössä (testimoskeija, ADR-0002): tiedot.json antaa ramadan: null muille (osat/ramadan-tiedot.html),
// joten muille ei tehdä Ramadan-yhdistelmiä (ramadan.ics, rukous-ramadan.ics …)
const LAJIT = ['rukous', 'jumua', 'tapahtumat', ...(tiedot.ramadan ? ['ramadan'] : [])];
const asetus = tiedot.rukous || {};

// ---------------------------------------------------------------- ajat (kuten sivu.js)
const muoto = new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', hourCycle: 'h23' });
function osat(d) { const o = {}; muoto.formatToParts(d).forEach((p) => { o[p.type] = Number(p.value); }); return o; }
function poikkeama(d) { const o = osat(d); return (Date.UTC(o.year, o.month - 1, o.day, o.hour, o.minute) - Math.floor(d.getTime() / 60000) * 60000) / 60000; }
function hki(paiva, hhmm) { // Helsingin seinäkelloaika -> Date
  const m = String(hhmm || '').match(/(\d{1,2})[.:](\d{2})/);
  if (!m) return null;
  const utc = Date.UTC(paiva.getFullYear(), paiva.getMonth(), paiva.getDate(), Number(m[1]), Number(m[2]));
  const t = utc - poikkeama(new Date(utc)) * 60000;
  return new Date(utc - poikkeama(new Date(t)) * 60000);
}
function helsinginPaiva(d, lisaa) { const o = osat(d); return new Date(o.year, o.month - 1, o.day + (lisaa || 0), 12); }
const kk = (p) => `${p.getFullYear()}-${String(p.getMonth() + 1).padStart(2, '0')}`;
const pvm = (p) => `${kk(p)}-${String(p.getDate()).padStart(2, '0')}`;

function ajat(paiva) {
  const tulos = { iqamah: {}, virallinen: false };
  const data = (asetus.aikataulu || {})[kk(paiva)];
  const rivi = data && data.filter((r) => Number(r.pv) === paiva.getDate())[0];
  if (rivi) {
    tulos.virallinen = true;
    Object.keys(CSV).forEach((n) => { tulos[n] = hki(paiva, rivi[CSV[n]]); });
    RUKOUKSET.forEach((n) => { if (rivi['iqamah_' + n]) tulos.iqamah[n] = hki(paiva, rivi['iqamah_' + n]); });
  } else {
    return null; // lähde tai oma aikataulu ei kerro tätä päivää: ei lasketa itse
  }
  if (asetus.iqamah) {
    RUKOUKSET.forEach((n) => {
      const v = asetus.iqamah[n];
      if (typeof v === 'string' && /[.:]/.test(v)) { const k = hki(paiva, v); if (k) tulos.iqamah[n] = k; } else if (!tulos.iqamah[n] && v != null && v !== '' && tulos[n] instanceof Date && !isNaN(tulos[n])) tulos.iqamah[n] = new Date(tulos[n].getTime() + Number(v) * 60000);
    });
  }
  // Jumua: lähteen ilmoittama aika voittaa käsin kirjoitetun
  if (paiva.getDay() === 5 && rivi && rivi.jumua === '1') { tulos.jumua = true; tulos.jumuaLahteesta = true; } else if (paiva.getDay() === 5 && asetus.juma) { const j = hki(paiva, asetus.juma); if (j) { tulos.dhuhr = j; tulos.jumua = true; } }
  const mu = (asetus.muutokset || []).filter((x) => String(x.paiva).slice(0, 10) === pvm(paiva))[0];
  if (mu) {
    RUKOUKSET.forEach((n) => {
      if (mu[n]) { const a = hki(paiva, mu[n]); if (a) tulos[n] = a; }
      if (mu['iqamah_' + n]) { const q = hki(paiva, mu['iqamah_' + n]); if (q) tulos.iqamah[n] = q; }
    });
    tulos.huom = mu.huom || '';
  }
  return tulos;
}
const ok = (d) => d instanceof Date && !isNaN(d);
const klo = (d) => new Intl.DateTimeFormat('fi-FI', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(d).replace(':', '.');

// ---------------------------------------------------------------- tapahtumat lajeittain
const nyt = new Date(), tanaan = helsinginPaiva(nyt);
const tunnus = String(tiedot.tunnus || 'moskeija').replace(/[^a-z0-9-]/gi, '');
const paikka = tiedot.osoite ? `${tiedot.nimi}, ${tiedot.osoite}` : tiedot.nimi;
const MIN = 60000;

function rukous(jumuaErikseen) {
  const t = [];
  for (let i = 0; i < RUKOUS_PAIVIA; i++) {
    const p = helsinginPaiva(nyt, i), a = ajat(p);
    if (!a) continue;
    for (const n of RUKOUKSET) {
      if (!ok(a[n])) continue;
      if (n === 'dhuhr' && a.jumua && jumuaErikseen) continue; // Jumua-kalenterissa omana tapahtumanaan
      const iq = a.iqamah[n];
      const nimi = n === 'dhuhr' && a.jumua ? 'Jumua (perjantairukous)' : RUKOUSNIMI[n];
      t.push({ uid: `rukous-${pvm(p)}-${n}`, alku: a[n], loppu: new Date((ok(iq) && iq > a[n] ? iq.getTime() : a[n].getTime()) + 15 * MIN),
        nimi, kuvaus: [ok(iq) ? `Iqamah ${klo(iq)}` : '', a.huom || '', MAININTA].filter(Boolean).join('\n'), paikka });
    }
  }
  return t;
}
function jumua() {
  const t = [];
  for (let i = 0, viikkoja = 0; viikkoja < JUMUA_VIIKKOJA && i < 7 * JUMUA_VIIKKOJA + 7; i++) {
    const p = helsinginPaiva(nyt, i);
    if (p.getDay() !== 5) continue;
    viikkoja++;
    const a1 = ajat(p);
    // Ilman päivän aikoja (ei lähdettä tai lähde ei ole vielä julkaissut päivää) moskeijan itse kirjoittama Jumua
    const j1 = a1 && a1.jumua ? a1.dhuhr : !a1 && asetus.juma ? hki(p, asetus.juma) : null;
    if (!ok(j1)) continue; // ei Jumua-aikaa
    const mu = (asetus.muutokset || []).filter((x) => String(x.paiva).slice(0, 10) === pvm(p))[0];
    [j1, asetus.juma2 ? hki(p, asetus.juma2) : null].forEach((a, j) => {
      if (!ok(a)) return;
      t.push({ uid: `jumua-${pvm(p)}-${j + 1}`, alku: a, loppu: new Date(a.getTime() + 45 * MIN), nimi: asetus.juma2 ? `Jumua ${j + 1} (perjantairukous)` : 'Jumua (perjantairukous)', kuvaus: [mu && mu.huom ? mu.huom : '', a1 && a1.jumua && j === 0 ? MAININTA : ''].filter(Boolean).join('\n'), paikka }); // lähteen Jumua: lähteen maininta
    });
  }
  return t;
}
function paivaksi(s) { const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? new Date(+m[1], m[2] - 1, +m[3], 12) : null; }
// Toistuva toiminta (toistuu: viikoittain): yksi VEVENT, jossa RRULE ja Helsingin paikallinen aika (kesäaika pysyy oikein)
const ICS_VP = { ma: 'MO', ti: 'TU', ke: 'WE', to: 'TH', pe: 'FR', la: 'SA', su: 'SU' };
const JS_VP = ['su', 'ma', 'ti', 'ke', 'to', 'pe', 'la'];
function paikallinen(p, hhmm) { const m = String(hhmm || '').match(/(\d{1,2})[.:](\d{2})/); return m ? `${paiva8(p)}T${m[1].padStart(2, '0')}${m[2]}00` : null; }
function toistuva(e, p, yhteinen) {
  let vp = (Array.isArray(e.viikonpaivat) ? e.viikonpaivat : []).filter((x) => ICS_VP[x]);
  if (!vp.length) vp = [JS_VP[p.getDay()]];
  // Ensimmäinen esiintymä aloituspäivänä tai sen jälkeen jollakin valitulla viikonpäivällä
  let eka = p;
  for (let i = 0; i < 7; i++) { const d = new Date(p.getFullYear(), p.getMonth(), p.getDate() + i, 12); if (vp.includes(JS_VP[d.getDay()])) { eka = d; break; } }
  const loppuPv = paivaksi(e.paiva_loppuu);
  const rrule = `RRULE:FREQ=WEEKLY;BYDAY=${vp.map((x) => ICS_VP[x]).join(',')}${loppuPv ? `;UNTIL=${paiva8(loppuPv)}T235959Z` : ''}`;
  const uid = `toistuva-${String(e.tunnus || e.nimi).replace(/[^a-z0-9-]/gi, '-').slice(0, 60)}`;
  const alku = paikallinen(eka, e.alkaa);
  if (!alku) return { ...yhteinen, uid, rrule, kokoPaiva: true, alkuPv: eka, loppuPv: new Date(eka.getFullYear(), eka.getMonth(), eka.getDate() + 1, 12) };
  let loppu = paikallinen(eka, e.loppuu);
  if (!loppu || loppu <= alku) { const t = String(e.alkaa).match(/(\d{1,2})[.:](\d{2})/); loppu = paikallinen(eka, `${Math.min(23, Number(t[1]) + 2)}.${Number(t[1]) + 2 > 23 ? '59' : t[2]}`); } // oletuskesto 2 h
  return { ...yhteinen, uid, rrule, paikallinenAlku: alku, paikallinenLoppu: loppu };
}
function tapahtumat() {
  return (tiedot.tapahtumat || []).map((e) => {
    const p = paivaksi(e.paiva);
    if (!p) return null;
    if (e.toistuu === 'viikoittain') return toistuva(e, p, { nimi: e.nimi, kuvaus: [e.kuvaus || '', e.url || ''].filter(Boolean).join('\n\n'), paikka: e.paikka || paikka, url: e.url });
    const loppuPv = paivaksi(e.paiva_loppuu) || p;
    const alku = e.alkaa ? hki(p, e.alkaa) : null;
    const kuvaus = [e.kuvaus || '', e.url || ''].filter(Boolean).join('\n\n');
    const yhteinen = { uid: `tapahtuma-${String(e.tunnus || e.nimi).replace(/[^a-z0-9-]/gi, '-').slice(0, 60)}-${pvm(p)}`, nimi: e.nimi, kuvaus, paikka: e.paikka || paikka, url: e.url };
    if (!alku) return { ...yhteinen, kokoPaiva: true, alkuPv: p, loppuPv: new Date(loppuPv.getFullYear(), loppuPv.getMonth(), loppuPv.getDate() + 1, 12) };
    let loppu = e.loppuu ? hki(loppuPv, e.loppuu) : null;
    if (!loppu || loppu <= alku) loppu = new Date(alku.getTime() + 2 * 60 * MIN);
    return { ...yhteinen, alku, loppu };
  }).filter(Boolean);
}
function ramadan() {
  const r = tiedot.ramadan, t = [];
  if (!r || !r.alkaa) return t;
  const alku = paivaksi(r.alkaa), eid = paivaksi(r.eid), n = Number(r.paivia) || 30;
  if (!alku || !eid || eid < helsinginPaiva(nyt, -1)) return t;
  for (let i = 0; i < n; i++) {
    const p = new Date(alku.getFullYear(), alku.getMonth(), alku.getDate() + i, 12);
    if (p < helsinginPaiva(nyt, -1)) continue;
    // Moskeijan oma Ramadan-aikataulu voittaa; muuten suhur = Fajr ja iftar = Maghrib rukousajoista
    const oma = (r.ajat || {})[pvm(p)] || {}, a = ajat(p) || {};
    const su = oma.s ? hki(p, oma.s) : a.fajr, ift = oma.i ? hki(p, oma.i) : a.maghrib;
    if (ok(su)) t.push({ uid: `ramadan-${pvm(p)}-suhur`, alku: new Date(su.getTime() - 10 * MIN), loppu: su, nimi: `Suhur päättyy ${klo(su)} (Ramadan ${i + 1})`, kuvaus: oma.s ? '' : 'Suhur päättyy Fajrin aikaan.', paikka });
    if (ok(ift)) t.push({ uid: `ramadan-${pvm(p)}-iftar`, alku: ift, loppu: new Date(ift.getTime() + 20 * MIN), nimi: `Iftar ${klo(ift)} (Ramadan ${i + 1})`, kuvaus: oma.i ? '' : 'Iftar Maghribin aikaan.', paikka });
    const tw = oma.t ? hki(p, oma.t) : r.tarawih ? hki(p, r.tarawih) : null;
    if (tw) t.push({ uid: `ramadan-${pvm(p)}-tarawih`, alku: tw, loppu: new Date(tw.getTime() + 60 * MIN), nimi: `Tarawih (Ramadan ${i + 1})`, kuvaus: '', paikka });
  }
  const eidPaikka = r.eid_paikka || paikka;
  const eidAjat = [r.eid_aika, r.eid_aika_2].map((x) => (x ? hki(eid, x) : null)).filter(Boolean);
  if (eidAjat.length) eidAjat.forEach((a, j) => t.push({ uid: `ramadan-${pvm(eid)}-eid-${j + 1}`, alku: a, loppu: new Date(a.getTime() + 60 * MIN), nimi: eidAjat.length > 1 ? `Eid-rukous ${j + 1}` : 'Eid-rukous', kuvaus: 'Eid Mubarak!', paikka: eidPaikka }));
  else t.push({ uid: `ramadan-${pvm(eid)}-eid`, kokoPaiva: true, alkuPv: eid, loppuPv: new Date(eid.getFullYear(), eid.getMonth(), eid.getDate() + 1, 12), nimi: 'Eid al-Fitr', kuvaus: 'Eid Mubarak!', paikka: eidPaikka });
  return t;
}

// ---------------------------------------------------------------- iCalendar
function utc(d) { return d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, ''); }
function paiva8(d) { return pvm(d).replace(/-/g, ''); }
function teksti(s) { return String(s || '').replace(/\\/g, '\\\\').replace(/\r?\n/g, '\\n').replace(/([,;])/g, '\\$1'); }
function taita(rivi) { // RFC 5545: rivit enintään 75 tavua, jatkorivi alkaa välilyönnillä
  const out = []; let nyk = '', tavut = 0;
  for (const merkki of rivi) {
    const b = Buffer.byteLength(merkki);
    if (tavut + b > (out.length ? 74 : 75)) { out.push(nyk); nyk = ''; tavut = 0; }
    nyk += merkki; tavut += b;
  }
  out.push(nyk);
  return out.join('\r\n ');
}
function ics(lajit, tapaht) {
  const leima = utc(nyt);
  const r = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Suomen moskeijat//Kalenteri//FI', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
    `X-WR-CALNAME:${teksti(`${tiedot.nimi} – ${lajit.map((l) => NIMET[l]).join(', ')}`)}`, `X-WR-TIMEZONE:${TZ}`,
    `X-WR-CALDESC:${teksti(`${tiedot.nimi}: ${lajit.map((l) => NIMET[l].toLowerCase()).join(', ')}. Päivittyy automaattisesti. ${tiedot.sivu || ''}${MAININTA ? `\n${MAININTA}` : ''}`)}`,
    'REFRESH-INTERVAL;VALUE=DURATION:PT4H', 'X-PUBLISHED-TTL:PT4H'];
  if (tapaht.some((e) => e.paikallinenAlku)) r.push('BEGIN:VTIMEZONE', `TZID:${TZ}`,
    'BEGIN:DAYLIGHT', 'TZOFFSETFROM:+0200', 'TZOFFSETTO:+0300', 'TZNAME:EEST', 'DTSTART:19700329T030000', 'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU', 'END:DAYLIGHT',
    'BEGIN:STANDARD', 'TZOFFSETFROM:+0300', 'TZOFFSETTO:+0200', 'TZNAME:EET', 'DTSTART:19701025T040000', 'RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU', 'END:STANDARD', 'END:VTIMEZONE');
  for (const e of tapaht) {
    r.push('BEGIN:VEVENT', `UID:${e.uid}@${tunnus}.suomenmoskeijat.fi`, `DTSTAMP:${leima}`);
    if (e.paikallinenAlku) r.push(`DTSTART;TZID=${TZ}:${e.paikallinenAlku}`, `DTEND;TZID=${TZ}:${e.paikallinenLoppu}`);
    else if (e.kokoPaiva) r.push(`DTSTART;VALUE=DATE:${paiva8(e.alkuPv)}`, `DTEND;VALUE=DATE:${paiva8(e.loppuPv)}`, 'TRANSP:TRANSPARENT');
    else r.push(`DTSTART:${utc(e.alku)}`, `DTEND:${utc(e.loppu)}`);
    if (e.rrule) r.push(e.rrule);
    r.push(`SUMMARY:${teksti(e.nimi)}`);
    if (e.kuvaus) r.push(`DESCRIPTION:${teksti(e.kuvaus)}`);
    if (e.paikka) r.push(`LOCATION:${teksti(e.paikka)}`);
    if (e.url) r.push(`URL:${e.url}`);
    r.push('END:VEVENT');
  }
  r.push('END:VCALENDAR');
  return r.map(taita).join('\r\n') + '\r\n';
}

// Lähteen maininta (Masjidboxin ehto: "Prayer times provided by Masjidbox" myös tulostetuissa/linkittömissä näkymissä)
const MAININTA = asetus.lahde === 'masjidbox' ? 'Prayer times provided by Masjidbox' : asetus.lahde === 'mawaqit' ? 'Rukousajat: Mawaqit' : asetus.lahde === 'rukousajat' ? 'Rukousajat: rukousajat.fi' : '';
const LAHTEET = { tapahtumat: tapahtumat(), ramadan: ramadan(), jumua: jumua() };
const rukousKaikki = rukous(false), rukousIlmanJumuaa = rukous(true);
let maara = 0;
for (let maski = 1; maski < 1 << LAJIT.length; maski++) {
  const lajit = LAJIT.filter((_, i) => maski & (1 << i));
  const tapaht = [];
  for (const l of lajit) tapaht.push(...(l === 'rukous' ? (lajit.includes('jumua') && LAHTEET.jumua.length ? rukousIlmanJumuaa : rukousKaikki) : LAHTEET[l]));
  tapaht.sort((a, b) => (a.alku || a.alkuPv) - (b.alku || b.alkuPv));
  fs.writeFileSync(path.join(KANSIO, `${lajit.join('-')}.ics`), ics(lajit, tapaht));
  maara++;
}
console.log(`Kalenterit: ${maara} tiedostoa (rukousajat ${rukousKaikki.length}, Jumua ${LAHTEET.jumua.length}, tapahtumat ${LAHTEET.tapahtumat.length}, Ramadan ${LAHTEET.ramadan.length})`);
