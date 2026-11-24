/* Moskeijalista (hallinta#52): Lisää moskeija -lomake lähettää pyynnön paneeliin (<paneeli>/api/moskeijapyynto). Sama
   käytös kuin moskeijoiden sivujen lomakkeissa (sivupohjan sivu.js): tarkistus ennen lähetystä, piilokenttä ja aika
   roskapostisuojana, Turnstile, viestit data-viesti-kohdissa. text/plain: ei CORS-esipyyntöä. */
(function () {
  var lomake = document.querySelector('[data-moskeijapyynto]');
  if (!lomake) return;
  var avattu = Date.now();
  function viesti(nimi, teksti) {
    Array.prototype.forEach.call(lomake.querySelectorAll('[data-viesti]'), function (p) {
      p.hidden = p.getAttribute('data-viesti') !== nimi;
      if (!p.hidden && teksti) p.textContent = teksti;
    });
  }
  function arvo(n) { var el = lomake.elements[n]; return el ? (el.type === 'checkbox' ? el.checked : el.value.trim()) : ''; }
  lomake.addEventListener('submit', function (e) {
    e.preventDefault();
    lomake.classList.add('on-tarkistettu');
    if (!lomake.checkValidity()) {
      viesti('virhe');
      var eka = lomake.querySelector(':invalid'); if (eka) eka.focus();
      return;
    }
    var nappi = lomake.querySelector('[type="submit"]');
    nappi.disabled = true;
    viesti('lahetetaan');
    var tunnus = lomake.querySelector('[name="cf-turnstile-response"]');
    fetch(lomake.getAttribute('data-api'), { method: 'POST', headers: { 'content-type': 'text/plain;charset=UTF-8' }, body: JSON.stringify({
      nimi: arvo('nimi'), kaupunki: arvo('kaupunki'), nettisivu: arvo('nettisivu'), yhteyshenkilo: arvo('yhteyshenkilo'), sahkoposti: arvo('sahkoposti'),
      puhelin: arvo('puhelin'), viesti: arvo('viesti'), tuonti: arvo('tuonti'), hp: arvo('_sivu'), aika: Date.now() - avattu, turnstile: tunnus ? tunnus.value : '',
    }) })
      .then(function (v) {
        return v.json().catch(function () { return {}; }).then(function (d) {
          if (!v.ok) { var x = new Error(d.virhe || ''); x.palvelin = !!d.virhe && v.status < 500; throw x; }
        });
      })
      .then(function () {
        lomake.reset(); lomake.classList.remove('on-tarkistettu'); avattu = Date.now();
        viesti('kiitos');
        var k = lomake.querySelector('[data-viesti="kiitos"]'); if (k) k.focus();
      })
      .catch(function (x) { if (x && x.palvelin) viesti('palvelin', x.message); else viesti('lahetysvirhe'); })
      .then(function () { nappi.disabled = false; if (window.turnstile) try { window.turnstile.reset(); } catch (e) {} });
  });
})();
