// Ulkoasun esikatselu (/esikatselu/): värit ja etusivun tausta iframeen ennen valintaa.
(function () {
  var juuri = document.querySelector('[data-esik]'), kehys = juuri.querySelector('[data-esik-kehys]');
  var kuva = juuri.getAttribute('data-kuva'), vari = null, tausta = null;
  function doc() { try { return kehys.contentDocument; } catch (e) { return null; } }
  function kayta() {
    var d = doc(); if (!d || !d.documentElement) return;
    var r = d.documentElement.style;
    if (vari === 'oma') { ['--paa', '--teksti', '--paa-tumma', '--kulta', '--kulta-vaalea', '--kulta-teksti'].forEach(function (x) { r.removeProperty(x); }); }
    else if (vari) {
      r.setProperty('--paa', vari.paa); r.setProperty('--teksti', vari.pt); r.setProperty('--paa-tumma', vari.pt);
      r.setProperty('--kulta', vari.k); r.setProperty('--kulta-vaalea', vari.kv);
      r.setProperty('--kulta-teksti', 'color-mix(in srgb, ' + vari.k + ' 45%, ' + vari.paa + ')');
    }
    var alku = d.querySelector('.u-alku');
    if (alku && tausta) {
      alku.classList.remove('u-alku--kuva', 'u-alku--vari');
      if (tausta === 'kuva' && kuva) { alku.classList.add('u-alku--kuva'); alku.style.setProperty('--alku-kuva', 'url("' + kuva + '")'); }
      if (tausta === 'vari') alku.classList.add('u-alku--vari');
    }
  }
  kehys.addEventListener('load', kayta);
  juuri.querySelectorAll('[data-vari]').forEach(function (b) {
    b.addEventListener('click', function () {
      vari = b.dataset.vari === 'oma' ? 'oma' : { paa: b.dataset.paa, pt: b.dataset.pt, k: b.dataset.k, kv: b.dataset.kv };
      juuri.querySelectorAll('[data-vari]').forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
      var vv = juuri.querySelector('[data-esik-valittu-vari]'); vv.textContent = ''; vv.appendChild(document.createElement('b')).textContent = b.dataset.nimi;
      kayta();
    });
  });
  juuri.querySelectorAll('[data-tausta]').forEach(function (b) {
    b.addEventListener('click', function () {
      tausta = b.dataset.tausta;
      juuri.querySelectorAll('[data-tausta]').forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
      var vt = juuri.querySelector('[data-esik-valittu-tausta]'); vt.textContent = ''; vt.appendChild(document.createElement('b')).textContent = b.querySelector('b').textContent; if (tausta === 'kuva') vt.appendChild(document.createTextNode(' (ja kuva kohtaan Taustakuva)'));
      kayta();
    });
  });
})();
