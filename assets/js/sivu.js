/* UUSI ULKOASU – toiminnot: kieli, valikot, rukousajat, tapahtumat, Instagram, lomakkeet. */
(function () {
  'use strict';
  var html = document.documentElement;
  var TZ = 'Europe/Helsinki';
  var LOKAALIT = { fi: 'fi-FI', en: 'en-GB', ar: 'ar-u-nu-latn', so: 'so-SO' };
  function tallenna(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ei tallennusta */ } }
  function kieli() { return LOKAALIT[html.lang] ? html.lang : 'fi'; }
  function muotoile(d, opts, loc) {
    try { return new Intl.DateTimeFormat(loc || LOKAALIT[kieli()], Object.assign({ timeZone: TZ }, opts)).format(d); }
    catch (e) { return new Intl.DateTimeFormat('en-GB', Object.assign({ timeZone: TZ }, opts)).format(d); }
  }
  function kaikki(valitsin, juuri) { return Array.prototype.slice.call((juuri || document).querySelectorAll(valitsin)); }

  /* ---------- 1. Kieli ---------- */
  function asetaKieli(k) {
    html.lang = k;
    html.dir = k === 'ar' ? 'rtl' : 'ltr';
    kaikki('[data-kieli]').forEach(function (b) { b.setAttribute('aria-checked', b.dataset.kieli === k ? 'true' : 'false'); });
    kaikki('[data-kieli-nyt]').forEach(function (e) { e.textContent = k.toUpperCase(); });
    document.dispatchEvent(new CustomEvent('kielivaihto', { detail: k }));
  }
  kaikki('[data-kielivalikko]').forEach(function (v) {
    var nappi = v.querySelector('[data-kieli-avaa]'), lista = v.querySelector('.u-kieli__lista');
    function sulje() { lista.hidden = true; nappi.setAttribute('aria-expanded', 'false'); }
    nappi.addEventListener('click', function (e) {
      e.stopPropagation();
      var auki = lista.hidden;
      lista.hidden = !auki;
      nappi.setAttribute('aria-expanded', auki ? 'true' : 'false');
      if (auki) { var valittu = lista.querySelector('[aria-checked="true"]') || lista.querySelector('button'); if (valittu) valittu.focus(); }
    });
    kaikki('[data-kieli]', v).forEach(function (b) {
      b.addEventListener('click', function () { tallenna('kieli', b.dataset.kieli); asetaKieli(b.dataset.kieli); sulje(); nappi.focus(); });
    });
    document.addEventListener('click', function (e) { if (!v.contains(e.target)) sulje(); });
    v.addEventListener('keydown', function (e) { if (e.key === 'Escape') { sulje(); nappi.focus(); } });
  });
  asetaKieli(kieli());

  /* ---------- 2. Valikko ja yläpalkki ---------- */
  var valikkonappi = document.querySelector('[data-valikko-avaa]');
  if (valikkonappi) {
    var valikko = document.getElementById(valikkonappi.getAttribute('aria-controls'));
    var asetaValikko = function (auki) { valikko.hidden = !auki; valikkonappi.setAttribute('aria-expanded', auki ? 'true' : 'false'); document.body.classList.toggle('on-valikko', auki); };
    valikkonappi.addEventListener('click', function () { asetaValikko(valikko.hidden); });
    valikko.addEventListener('click', function (e) { if (e.target.closest('a')) asetaValikko(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !valikko.hidden) { asetaValikko(false); valikkonappi.focus(); } });
  }
  var yla = document.querySelector('[data-yla]');
  if (yla) {
    var varjo = function () { yla.classList.toggle('u-yla--varjo', window.scrollY > 4); };
    window.addEventListener('scroll', varjo, { passive: true });
    varjo();
  }

  /* Pikanapit piiloon, kun rukousaikataulu tai lomake on näkyvissä (eivät peitä tietoja) */
  var pikanapit = document.querySelector('[data-pikanapit]');
  var suojatut = kaikki('[data-rk], [data-kk], .u-lomake, .u-vierailu, .u-lahjoitustiedot, .u-sivupalkki, .u-ala');
  if (pikanapit && suojatut.length && 'IntersectionObserver' in window) {
    var nakyvat = new Set();
    var io = new IntersectionObserver(function (havainnot) {
      havainnot.forEach(function (h) { if (h.isIntersecting) nakyvat.add(h.target); else nakyvat.delete(h.target); });
      pikanapit.classList.toggle('on-piilossa', nakyvat.size > 0);
    }, { rootMargin: '0px 0px -80px 0px' });
    suojatut.forEach(function (el) { io.observe(el); });
  }
  // Alaspäin luettaessa piiloon, ylöspäin vieritettäessä esiin (aloitusnäytöllä näkyvissä)
  if (pikanapit) {
    var edellinenY = window.scrollY;
    window.addEventListener('scroll', function () {
      var y = window.scrollY, ero = y - edellinenY;
      if (Math.abs(ero) < 8) return;
      pikanapit.classList.toggle('on-alas', ero > 0 && y > 120);
      edellinenY = y;
    }, { passive: true });
  }
  // Ei peitetä aloitusnäytön linkkejä ja nappeja (pienet näytöt): piiloon vain, jos osuisi päälle
  if (pikanapit) {
    var alkuKohteet = kaikki('.u-alku a, .u-alku button');
    var tarkistaPeitto = function () {
      var r = pikanapit.getBoundingClientRect(), siirto = pikanapit.classList.contains('on-piilossa') ? 16 : 0;
      var ylin = r.top - siirto - 8, alin = r.bottom - siirto + 8, vasen = r.left - 8, oikea = r.right + 8;
      var osuu = alkuKohteet.some(function (a) { var q = a.getBoundingClientRect(); return q.width && q.bottom > ylin && q.top < alin && q.right > vasen && q.left < oikea; });
      pikanapit.classList.toggle('on-peitossa', osuu);
    };
    var odottaa = false;
    var ajasta = function () { if (!odottaa) { odottaa = true; requestAnimationFrame(function () { odottaa = false; tarkistaPeitto(); }); } };
    window.addEventListener('scroll', ajasta, { passive: true });
    window.addEventListener('resize', ajasta);
    tarkistaPeitto();
  }

  /* ---------- 3. Tapahtumat: menneet piiloon ---------- */
  var tanaanIso = new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
  kaikki('[data-tulevat]').forEach(function (ul) {
    var maara = parseInt(ul.dataset.maara, 10) || Infinity, naytetty = 0;
    kaikki('[data-paiva]', ul).forEach(function (li) {
      var nayta = li.dataset.paiva >= tanaanIso && naytetty < maara;
      li.hidden = !nayta;
      if (nayta) naytetty++;
    });
    var tyhja = ul.parentNode.querySelector('[data-tyhja]');
    if (tyhja) tyhja.hidden = naytetty > 0;
  });

  /* ---------- 4. Rukousajat ---------- */
  var RUKOUKSET = ['fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha'];
  var VARSINAISET = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha'];
  var CSV = { fajr: 'fajr', sunrise: 'auringonnousu', dhuhr: 'dhuhr', asr: 'asr', maghrib: 'maghrib', isha: 'isha' };
  var ARABIAKSI = { fajr: 'الفجر', sunrise: 'الشروق', dhuhr: 'الظهر', asr: 'العصر', maghrib: 'المغرب', isha: 'العشاء', jumua: 'الجمعة' };
  var NIMET = {
    fi: { fajr: 'Fajr', sunrise: 'Auringonnousu', dhuhr: 'Dhuhr', asr: 'Asr', maghrib: 'Maghrib', isha: 'Isha', jumua: "Jumu'a", huomenna: 'huomenna', klo: 'klo', pv: 'Päivä', nousu: 'Nousu' },
    en: { fajr: 'Fajr', sunrise: 'Sunrise', dhuhr: 'Dhuhr', asr: 'Asr', maghrib: 'Maghrib', isha: 'Isha', jumua: "Jumu'ah", huomenna: 'tomorrow', klo: 'at', pv: 'Day', nousu: 'Sunrise' },
    ar: { fajr: 'الفجر', sunrise: 'الشروق', dhuhr: 'الظهر', asr: 'العصر', maghrib: 'المغرب', isha: 'العشاء', jumua: 'الجمعة', huomenna: 'غداً', klo: 'الساعة', pv: 'اليوم', nousu: 'الشروق' },
    so: { fajr: 'Subax', sunrise: 'Qorrax ka soo bax', dhuhr: 'Duhur', asr: 'Casar', maghrib: 'Maqrib', isha: 'Cishaa', jumua: 'Jimce', huomenna: 'berri', klo: 'saacadda', pv: 'Taariikh', nousu: 'Qorrax' }
  };
  function N() { return NIMET[kieli()] || NIMET.fi; }
  var kello = new Intl.DateTimeFormat('en-GB', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
  function aika(d) { return d instanceof Date && !isNaN(d) ? kello.format(d) : '–'; }
  function osat(d) {
    var o = {};
    new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', hourCycle: 'h23' })
      .formatToParts(d).forEach(function (p) { o[p.type] = Number(p.value); });
    return o;
  }
  // Helsingin kalenteripäivä (paikallinen Date klo 12) riippumatta laitteen aikavyöhykkeestä
  function helsinginPaiva(d, lisaa) { var o = osat(d); return new Date(o.year, o.month - 1, o.day + (lisaa || 0), 12); }
  function poikkeama(d) { var o = osat(d); return (Date.UTC(o.year, o.month - 1, o.day, o.hour, o.minute) - Math.floor(d.getTime() / 60000) * 60000) / 60000; }
  function hki(paiva, hhmm) { // Helsingin seinäkelloaika -> Date
    var m = String(hhmm || '').match(/(\d{1,2})[.:](\d{2})/);
    if (!m) return null;
    var utc = Date.UTC(paiva.getFullYear(), paiva.getMonth(), paiva.getDate(), Number(m[1]), Number(m[2]));
    var t = utc - poikkeama(new Date(utc)) * 60000;
    return new Date(utc - poikkeama(new Date(t)) * 60000);
  }
  function kk(paiva) { return paiva.getFullYear() + '-' + ('0' + (paiva.getMonth() + 1)).slice(-2); }

  var asetus = null;
  try { var dataEl = document.getElementById('rk-data'); if (dataEl) asetus = JSON.parse(dataEl.textContent); } catch (e) { asetus = null; }

  function laskenta() {
    if (typeof adhan === 'undefined' || asetus.lat == null) return null;
    var tapa = adhan.CalculationMethod[asetus.laskentatapa] || adhan.CalculationMethod.MuslimWorldLeague;
    var p = tapa();
    p.madhab = asetus.madhab === 'Hanafi' ? adhan.Madhab.Hanafi : adhan.Madhab.Shafi;
    p.highLatitudeRule = adhan.HighLatitudeRule[asetus.leveysaste] || adhan.HighLatitudeRule.TwilightAngle; // kuten rukousajat.fi
    Object.keys(asetus.saadot || {}).forEach(function (k) { p.adjustments[k] = Number(asetus.saadot[k]) || 0; });
    return { p: p, koord: new adhan.Coordinates(asetus.lat, asetus.lon) };
  }
  var laskin = null;

  // Yhden päivän ajat: { fajr: Date, ..., iqamah: {...}, virallinen, jumua }
  function ajat(paiva) {
    var tulos = { iqamah: {}, virallinen: false };
    var data = (asetus.aikataulu || {})[kk(paiva)];
    var rivi = data && data.filter(function (r) { return Number(r.pv) === paiva.getDate(); })[0];
    if (rivi) {
      tulos.virallinen = true;
      RUKOUKSET.forEach(function (n) { tulos[n] = hki(paiva, rivi[CSV[n]]); });
      VARSINAISET.forEach(function (n) { if (rivi['iqamah_' + n]) tulos.iqamah[n] = hki(paiva, rivi['iqamah_' + n]); });
    } else {
      if (!laskin) laskin = laskenta();
      if (!laskin) return null;
      var pt = new adhan.PrayerTimes(laskin.koord, paiva, laskin.p);
      RUKOUKSET.forEach(function (n) { tulos[n] = pt[n]; });
    }
    if (asetus.iqamah) {
      VARSINAISET.forEach(function (n) {
        var lisa = asetus.iqamah[n];
        if (!tulos.iqamah[n] && lisa != null && tulos[n] instanceof Date && !isNaN(tulos[n])) tulos.iqamah[n] = new Date(tulos[n].getTime() + lisa * 60000);
      });
    }
    if (paiva.getDay() === 5 && asetus.juma) { var j = hki(paiva, asetus.juma); if (j) { tulos.dhuhr = j; tulos.jumua = true; } }
    return tulos;
  }

  function tila(nyt) {
    var tanaan = ajat(helsinginPaiva(nyt));
    if (!tanaan) return null;
    var seuraava = null, edellinen = null;
    for (var i = 0; i < VARSINAISET.length; i++) {
      var t = tanaan[VARSINAISET[i]];
      if (!(t instanceof Date) || isNaN(t)) continue;
      if (t > nyt) { seuraava = { nimi: VARSINAISET[i], aika: t }; break; }
      edellinen = { nimi: VARSINAISET[i], aika: t };
    }
    if (!seuraava) { var h = ajat(helsinginPaiva(nyt, 1)); seuraava = { nimi: 'fajr', aika: h && h.fajr, huomenna: true }; }
    if (!edellinen) { var e = ajat(helsinginPaiva(nyt, -1)); edellinen = { nimi: 'isha', aika: e && e.isha }; }
    return { tanaan: tanaan, seuraava: seuraava, edellinen: edellinen };
  }

  function rukousNimi(n, jumua) { return (n === 'dhuhr' && jumua) ? N().jumua : N()[n]; }
  function kesto(ms) {
    var s = Math.max(0, Math.floor(ms / 1000)), h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
    s = s % 60;
    return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  var nykytila = null;
  function piirraPaiva() {
    var nyt = new Date();
    nykytila = tila(nyt);
    if (!nykytila) return;
    var t = nykytila.tanaan, seur = nykytila.seuraava;
    kaikki('[data-rk]').forEach(function (rk) {
      var pvm = rk.querySelector('[data-rk-pvm]');
      if (pvm) pvm.textContent = muotoile(nyt, { weekday: 'long', day: 'numeric', month: 'numeric' });
      var hijri = rk.querySelector('[data-rk-hijri]');
      if (hijri) {
        var loc = LOKAALIT[kieli()].split('-u-')[0];
        try { hijri.textContent = muotoile(nyt, { day: 'numeric', month: 'long', year: 'numeric' }, loc + '-u-ca-islamic-umalqura' + (kieli() === 'ar' ? '-nu-latn' : '')); } catch (e) { hijri.textContent = ''; }
      }
      var tbody = rk.querySelector('[data-rk-rivit]');
      tbody.textContent = '';
      RUKOUKSET.forEach(function (n) {
        var tr = document.createElement('tr');
        if (n === 'sunrise') tr.className = 'rk__rivi--muu';
        if (!seur.huomenna && n === seur.nimi) { tr.className = 'rk__rivi--seuraava'; tr.setAttribute('aria-current', 'time'); }
        var th = document.createElement('th');
        th.scope = 'row';
        th.textContent = rukousNimi(n, t.jumua);
        var ar = document.createElement('span');
        ar.className = 'rk__ar'; ar.lang = 'ar';
        ar.textContent = (n === 'dhuhr' && t.jumua) ? ARABIAKSI.jumua : ARABIAKSI[n];
        th.appendChild(ar);
        var td1 = document.createElement('td'); td1.textContent = aika(t[n]);
        var td2 = document.createElement('td'); td2.textContent = t.iqamah[n] ? aika(t.iqamah[n]) : '';
        tr.appendChild(th); tr.appendChild(td1); tr.appendChild(td2);
        tbody.appendChild(tr);
      });
    });
    paivitaLaskuri();
  }

  function paivitaLaskuri() {
    if (!nykytila) return;
    var nyt = new Date(), s = nykytila.seuraava, e = nykytila.edellinen;
    if (!(s.aika instanceof Date) || isNaN(s.aika)) return;
    if (s.aika <= nyt) { piirraPaiva(); return; }
    var osuus = (e && e.aika) ? Math.min(1, Math.max(0, (nyt - e.aika) / (s.aika - e.aika))) : 0;
    var nimi = rukousNimi(s.nimi, !s.huomenna && nykytila.tanaan.jumua) + (s.huomenna ? ' (' + N().huomenna + ')' : '');
    kaikki('[data-rk]').forEach(function (rk) {
      rk.querySelector('[data-rk-nimi]').textContent = nimi;
      rk.querySelector('[data-rk-klo]').textContent = N().klo + ' ' + aika(s.aika);
      rk.querySelector('[data-rk-jaljella]').textContent = kesto(s.aika - nyt);
      rk.querySelector('[data-rk-palkki]').style.width = (osuus * 100).toFixed(1) + '%';
    });
    // Etusivun aloitusnäytön laskuri
    var iqa = !s.huomenna && nykytila.tanaan.iqamah ? nykytila.tanaan.iqamah[s.nimi] : null;
    kaikki('[data-laskuri]').forEach(function (l) {
      l.querySelector('[data-laskuri-nimi]').textContent = rukousNimi(s.nimi, !s.huomenna && nykytila.tanaan.jumua);
      var hm = l.querySelector('[data-laskuri-huomenna]'); hm.hidden = !s.huomenna; hm.textContent = N().huomenna;
      l.querySelector('[data-laskuri-aika]').textContent = aika(s.aika);
      l.querySelector('[data-laskuri-jaljella]').textContent = kesto(s.aika - nyt);
      var iq = l.querySelector('[data-laskuri-iqamah]'); iq.hidden = !iqa;
      if (iqa) l.querySelector('[data-laskuri-iqamah-aika]').textContent = aika(iqa);
      l.querySelector('[data-laskuri-palkki]').style.width = (osuus * 100).toFixed(1) + '%';
    });
  }

  // Kuukausitaulukko
  var kkSiirto = 0;
  function piirraKuukausi() {
    kaikki('[data-kk]').forEach(function (kkEl) {
      var nyt = new Date(), tanaan = helsinginPaiva(nyt);
      var eka = new Date(tanaan.getFullYear(), tanaan.getMonth() + kkSiirto, 1, 12);
      kkEl.querySelector('[data-kk-nimi]').textContent = muotoile(eka, { month: 'long', year: 'numeric' });
      var n = N(), taulu = kkEl.querySelector('[data-kk-taulu]');
      var otsikot = ['pv', 'fajr', 'nousu', 'dhuhr', 'asr', 'maghrib', 'isha'];
      var h = '<thead><tr>' + otsikot.map(function (o) { return '<th scope="col">' + n[o] + '</th>'; }).join('') + '</tr></thead><tbody>';
      var kaikkiVirallisia = true;
      for (var d = new Date(eka); d.getMonth() === eka.getMonth(); d = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1, 12)) {
        var a = ajat(d);
        if (!a) continue;
        if (!a.virallinen) kaikkiVirallisia = false;
        var luokat = [];
        if (d.getTime() === tanaan.getTime()) luokat.push('kk__tanaan');
        if (d.getDay() === 5) luokat.push('kk__pe');
        h += '<tr' + (luokat.length ? ' class="' + luokat.join(' ') + '"' : '') + (d.getTime() === tanaan.getTime() ? ' aria-current="date"' : '') + '>' +
          '<th scope="row"><small>' + muotoile(d, { weekday: 'short' }) + '</small> ' + d.getDate() + '</th>' +
          '<td>' + aika(a.fajr) + '</td><td class="kk__nousu">' + aika(a.sunrise) + '</td><td>' + aika(a.dhuhr) + '</td><td>' + aika(a.asr) + '</td><td>' + aika(a.maghrib) + '</td><td>' + aika(a.isha) + '</td></tr>';
      }
      taulu.innerHTML = h + '</tbody>';
      var v = kkEl.querySelector('[data-kk-lahde-virallinen]'), l = kkEl.querySelector('[data-kk-lahde-laskettu]');
      if (v) v.hidden = !kaikkiVirallisia;
      if (l) l.hidden = kaikkiVirallisia;
    });
  }
  kaikki('[data-kk-siirto]').forEach(function (b) {
    b.addEventListener('click', function () {
      kkSiirto = Math.max(-12, Math.min(12, kkSiirto + Number(b.dataset.kkSiirto)));
      piirraKuukausi();
    });
  });

  function kaynnistaRukous() {
    if (!asetus) return;
    piirraPaiva();
    piirraKuukausi();
    setInterval(paivitaLaskuri, 1000);
    setInterval(piirraPaiva, 5 * 60000);
    document.addEventListener('kielivaihto', function () { piirraPaiva(); piirraKuukausi(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', kaynnistaRukous);
  else kaynnistaRukous();

  /* ---------- 5. Instagram: julkaisu isona ---------- */
  kaikki('[data-ig]').forEach(function (g) {
    var data = [];
    try { data = JSON.parse(g.querySelector('[data-ig-json]').textContent); } catch (e) { return; }
    var ikkuna = g.querySelector('[data-ig-ikkuna]');
    if (!ikkuna || typeof ikkuna.showModal !== 'function') return;
    var nyt = 0, kuva = ikkuna.querySelector('[data-ig-kuva]');
    function nayta(i) {
      nyt = (i + data.length) % data.length;
      var j = data[nyt], video = j.tyyppi === 'video';
      kuva.src = j.kuva;
      ikkuna.querySelector('[data-ig-teksti]').textContent = j.teksti || '';
      ikkuna.querySelector('[data-ig-paiva]').textContent = j.paiva ? muotoile(new Date(j.paiva + 'T12:00:00Z'), { day: 'numeric', month: 'long', year: 'numeric' }) : '';
      ikkuna.querySelector('[data-ig-video]').hidden = !video;
      ikkuna.querySelector('[data-ig-linkki-kuva]').hidden = video;
      ikkuna.querySelector('[data-ig-linkki-video]').hidden = !video;
      ikkuna.querySelector('[data-ig-linkki]').href = 'https://www.instagram.com/' + (video ? 'reel/' : 'p/') + j.koodi + '/';
      kaikki('[data-ig-siirry]', ikkuna).forEach(function (b) { b.disabled = data.length < 2; });
      ikkuna.querySelector('.u-ikkuna__teksti').scrollTop = 0;
    }
    function siirry(suunta) { nayta(nyt + suunta * (html.dir === 'rtl' ? -1 : 1)); }
    kaikki('[data-ig-avaa]', g).forEach(function (b) {
      b.addEventListener('click', function () { nayta(Number(b.dataset.igAvaa)); ikkuna.showModal(); html.classList.add('u-lukittu'); });
    });
    ikkuna.addEventListener('close', function () { html.classList.remove('u-lukittu'); });
    ikkuna.querySelector('[data-ig-sulje]').addEventListener('click', function () { ikkuna.close(); });
    ikkuna.addEventListener('click', function (e) { if (e.target === ikkuna) ikkuna.close(); });
    kaikki('[data-ig-siirry]', ikkuna).forEach(function (b) { b.addEventListener('click', function () { siirry(Number(b.dataset.igSiirry)); }); });
    ikkuna.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') siirry(1); if (e.key === 'ArrowLeft') siirry(-1); });
    var alkuX = null, alue = ikkuna.querySelector('.u-ikkuna__kuva');
    alue.addEventListener('touchstart', function (e) { alkuX = e.touches[0].clientX; }, { passive: true });
    alue.addEventListener('touchend', function (e) {
      if (alkuX === null) return;
      var dx = e.changedTouches[0].clientX - alkuX; alkuX = null;
      if (Math.abs(dx) > 40) siirry(dx < 0 ? 1 : -1);
    });
  });

  /* ---------- 6. Lomakkeet (lomakepalvelu tai valmis WhatsApp-/sähköpostiviesti) ---------- */
  function viesti(lomake, nimi) { kaikki('[data-viesti]', lomake).forEach(function (p) { p.hidden = p.dataset.viesti !== nimi; }); }
  function kentanNimi(el) {
    var k = el.closest('.u-kentta') || el.closest('label');
    var fi = k && k.querySelector('[data-l="fi"]');
    return ((fi && fi.textContent) || el.name).replace('*', '').trim();
  }
  kaikki('[data-lomake]').forEach(function (lomake) {
    lomake.addEventListener('submit', function (e) {
      e.preventDefault();
      lomake.classList.add('on-tarkistettu');
      if (!lomake.checkValidity()) {
        viesti(lomake, 'virhe');
        var eka = lomake.querySelector(':invalid'); if (eka) eka.focus();
        return;
      }
      var rivit = [lomake.dataset.aihe, ''], nahty = {};
      Array.prototype.forEach.call(lomake.elements, function (el) {
        if (!el.name || el.name === 'hyvaksyn' || nahty[el.name]) return;
        if (el.type === 'radio') { nahty[el.name] = 1; var v = lomake.querySelector('[name="' + el.name + '"]:checked'); if (v) rivit.push(kentanNimi(el) + ': ' + v.value); return; }
        if (el.value.trim()) rivit.push(kentanNimi(el) + ': ' + el.value.trim());
      });
      var teksti = rivit.join('\n'), osoite = lomake.dataset.osoite;
      if (osoite) {
        viesti(lomake, 'lahetetaan');
        var data = new FormData(lomake); data.append('_subject', lomake.dataset.aihe);
        fetch(osoite, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
          .then(function (v) { if (!v.ok) throw new Error(v.status); viesti(lomake, 'kiitos'); lomake.reset(); lomake.classList.remove('on-tarkistettu'); })
          .catch(function () { viesti(lomake, 'lahetysvirhe'); });
      } else if (lomake.dataset.wa) {
        window.open('https://wa.me/' + lomake.dataset.wa + '?text=' + encodeURIComponent(teksti), '_blank', 'noopener');
        viesti(lomake, 'whatsapp');
      } else if (lomake.dataset.sahkoposti) {
        location.href = 'mailto:' + lomake.dataset.sahkoposti + '?subject=' + encodeURIComponent(lomake.dataset.aihe) + '&body=' + encodeURIComponent(teksti);
        viesti(lomake, 'sahkoposti');
      } else {
        viesti(lomake, 'lahetysvirhe');
      }
    });
  });

  /* ---------- 7. Kopioi-painike ---------- */
  kaikki('[data-kopioi]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (!navigator.clipboard) return;
      navigator.clipboard.writeText(b.dataset.kopioi).then(function () { b.classList.add('on-kopioitu'); setTimeout(function () { b.classList.remove('on-kopioitu'); }, 2000); });
    });
  });

  /* ---------- 8. Sisällön kuvat ja linkit (/tiedostot/...) toimimaan alihakemistossa ---------- */
  var base = (window.SIVU && window.SIVU.baseurl) || '';
  if (base) {
    kaikki('.u-proosa [src^="/tiedostot/"], .u-proosa [href^="/tiedostot/"]').forEach(function (el) {
      var attr = el.hasAttribute('src') ? 'src' : 'href';
      el.setAttribute(attr, base + el.getAttribute(attr));
    });
  }
})();
