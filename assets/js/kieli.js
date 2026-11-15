// Näkyvän kielen valinta ennen sivun piirtämistä (ladataan <head>issä ilman deferiä).
// Sivuston kielet ja RTL-tieto tulevat #kieli-data-elementistä (_data/kielet.json); ensimmäinen kieli on pääkieli.
(function () {
  var data = {};
  try { data = JSON.parse(document.getElementById('kieli-data').textContent) || {}; } catch (e) {}
  var sallitut = Object.keys(data), k = null;
  if (!sallitut.length) return;
  try { k = localStorage.getItem('kieli'); } catch (e) {}
  // Hakukone- ja tekoälybotit näkevät sivun pääkielellä (suomi), eivät selaimensa kielellä
  var botti = /bot|crawl|spider|slurp|bingpreview|facebookexternalhit|embedly|google-inspectiontool|chrome-lighthouse/i.test(navigator.userAgent || '');
  if (sallitut.indexOf(k) < 0) { var n = botti ? '' : (navigator.language || '').slice(0, 2); k = sallitut.indexOf(n) >= 0 ? n : sallitut[0]; }
  // Kieliversio omassa osoitteessa (/en/ …): osoitteen kieli voittaa ja tallentuu valinnaksi.
  // Pääkielen sivulla kävijä, jonka kieli on muu, ohjataan oman kielensä osoitteeseen (ei botteja).
  var urlKieli = document.documentElement.getAttribute('data-url-kieli');
  if (urlKieli && sallitut.indexOf(urlKieli) >= 0) { k = urlKieli; try { localStorage.setItem('kieli', k); } catch (e) {} }
  else if (!botti && k !== sallitut[0] && window.top === window) {
    var alt = document.querySelector('link[rel="alternate"][hreflang="' + k + '"]');
    var polku = alt ? new URL(alt.href).pathname : null;
    if (polku && polku !== location.pathname) { location.replace(polku + location.search + location.hash); }
  }
  document.documentElement.lang = k;
  document.documentElement.dir = data[k] && data[k].rtl ? 'rtl' : 'ltr';
})();
