// Testisivun välikerros (hallinta#48, J8; ADR-0008): testisivun näkee vain paneeliin kirjautunut testaaja tai ylläpitäjä.
//
// Rakennuskomento (rakenna_sivu.py --sivulupa <paneeli>) kopioi tämän tiedoston testisivun juureen nimellä _worker.js ja
// vaihtaa paneelin osoitteen paikalleen. Cloudflare Pages ajaa sen jokaisessa pyynnössä kaikissa projektin osoitteissa
// (advanced mode: wrangler pages deploy lataa kansion _worker.js:n välikerrokseksi eikä tarjoa sitä tiedostona).
// Välikerros on vain testisivujen projekteissa, joten muiden sivujen pyynnöt eivät kuluta Workers-rajaa.
//
// Kulku:
// 1. Pyyntö ilman kelvollista evästettä → paneelin sivulupa-reitti (<paneeli>/api/sivulupa?paluu=<osoite>).
// 2. Paneeli tarkistaa istunnon ja roolin ja ohjaa takaisin osoitteeseen /__sivulupa?lupa=<lupa>&paluu=<polku>.
//    Lupa on lyhytikäinen (2 min) ja allekirjoitettu (HMAC-SHA256, yhteinen avain SIVULUPA_AVAIN) ja koskee vain tätä osoitetta.
// 3. Välikerros vaihtaa luvan omaksi evästeekseen (__Host-sivulupa: HttpOnly, Secure, SameSite=Lax, vain tälle osoitteelle,
//    1 h) ja ohjaa pyydettyyn polkuun. Vanhentunut tai väärennetty lupa hylätään (403), eväste ei synny.
// 4. Kelvollisella evästeellä sivun tiedostot tulevat Pagesista (env.ASSETS).
// robots.txt (Disallow: /) on kaikille. Kaikissa vastauksissa on X-Robots-Tag: noindex: Pages ei lisää _headers-tiedoston
// otsakkeita välikerroksen vastauksiin. Jos avainta ei ole, mitään muuta ei näytetä (503).
//
// Merkki (lupa ja eväste): base64url(JSON) + "." + base64url(HMAC-SHA256(avain, "sivulupa.v1." + base64url(JSON))).
// JSON: { t: "lupa" | "evaste", h: osoitteen host, e: vanhenemishetki (Unix-sekunnit) }. Paneeli tekee luvan samalla tavalla
// (hallinta src/sivulupa.js). Allekirjoitus tarkistetaan crypto.subtle.verify-kutsulla (vakioaikainen vertailu).
// Moduulissa on vain oletusvienti: Workers-ajoympäristö hylkää muut nimetyt viennit (vakiot), joten testit ajavat tämän sellaisenaan.

const PANEELI = "__SIVULUPA_PANEELI__";
const EVASTE = "__Host-sivulupa";
const LUPA_POLKU = "/__sivulupa";
const EVASTE_IKA = 3600;
const AVAIN_VAHINTAAN = 32;
const PIILOON = {
  "x-robots-tag": "noindex, nofollow, noarchive, noai, noimageai",
  "referrer-policy": "no-referrer",
};

const enc = new TextEncoder();
const b64u = (tavut) => btoa(String.fromCharCode(...tavut)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
function b64uTavut(s) {
  const t = s.replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(t + "=".repeat((4 - (t.length % 4)) % 4)), (c) => c.charCodeAt(0));
}
const avain = (salaisuus) => crypto.subtle.importKey("raw", enc.encode(salaisuus), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);

async function allekirjoita(salaisuus, sisalto) {
  const osa = b64u(enc.encode(JSON.stringify(sisalto)));
  const allekirjoitus = new Uint8Array(await crypto.subtle.sign("HMAC", await avain(salaisuus), enc.encode("sivulupa.v1." + osa)));
  return `${osa}.${b64u(allekirjoitus)}`;
}

/** Merkin sisältö, jos allekirjoitus, tyyppi, osoite ja voimassaolo ovat kunnossa; muuten null. */
async function tarkista(salaisuus, merkki, tyyppi, host, nyt = Math.floor(Date.now() / 1000)) {
  if (typeof merkki !== "string" || merkki.length > 2000 || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(merkki)) return null;
  const [osa, allekirjoitus] = merkki.split(".");
  let d;
  try {
    if (!(await crypto.subtle.verify("HMAC", await avain(salaisuus), b64uTavut(allekirjoitus), enc.encode("sivulupa.v1." + osa)))) return null;
    d = JSON.parse(new TextDecoder().decode(b64uTavut(osa)));
  } catch {
    return null;
  }
  if (!d || d.t !== tyyppi || d.h !== host || !Number.isFinite(d.e) || d.e < nyt) return null;
  return d;
}

function piiloon(vastaus, lisat = {}) {
  const r = new Response(vastaus.body, vastaus);
  for (const [a, b] of Object.entries({ ...PIILOON, ...lisat })) r.headers.set(a, b);
  return r;
}

function ohjaa(osoite, lisat = {}) {
  return new Response(null, { status: 302, headers: { location: osoite, "cache-control": "no-store", ...PIILOON, ...lisat } });
}

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

/** Lyhyt ilmoitussivu suomeksi ja englanniksi (ei sivun sisältöä). */
function ilmoitus(tila, fi, en, linkki) {
  const nappi = linkki ? `<p><a href="${esc(linkki)}">Kirjaudu uudelleen</a> · <a href="${esc(linkki)}" lang="en">Sign in again</a></p>` : "";
  const html = `<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Testisivu – Test site</title></head>
<body style="font-family:system-ui,sans-serif;max-width:34rem;margin:3rem auto;padding:0 1rem;line-height:1.5;color:#222">
<h1 style="font-size:1.25rem">Testisivu</h1><p>${esc(fi)}</p><p lang="en">${esc(en)}</p>${nappi}</body></html>`;
  return new Response(html, { status: tila, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", ...PIILOON } });
}

const sivulupaOsoite = (osoite) => `${PANEELI}/api/sivulupa?paluu=${encodeURIComponent(osoite)}`;

/** Paluupolku saman osoitteen sisällä ("/…"); muu (toinen osoite, //, \) → "/". */
function polku(paluu, origin) {
  if (typeof paluu !== "string" || !paluu.startsWith("/") || paluu.startsWith("//") || /[\\\u0000-\u001f]/.test(paluu)) return "/";
  try {
    const u = new URL(paluu, origin);
    return u.origin === origin ? u.pathname + u.search : "/";
  } catch {
    return "/";
  }
}

function lueEvaste(request) {
  const m = (request.headers.get("cookie") || "").match(new RegExp(`(?:^|;\\s*)${EVASTE}=([A-Za-z0-9_.-]{1,2000})`));
  return m ? m[1] : null;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/robots.txt") return piiloon(await env.ASSETS.fetch(request));
    const salaisuus = String(env.SIVULUPA_AVAIN || "").trim();
    if (salaisuus.length < AVAIN_VAHINTAAN) {
      return ilmoitus(503, "Testisivun kirjautumista ei ole vielä otettu käyttöön.", "Sign-in for this test site has not been set up yet.");
    }
    const nyt = Math.floor(Date.now() / 1000);
    if (url.pathname === LUPA_POLKU) {
      const lupa = await tarkista(salaisuus, url.searchParams.get("lupa"), "lupa", url.host, nyt);
      if (!lupa) {
        return ilmoitus(403, "Kirjautumislupa on vanhentunut tai virheellinen.", "The sign-in permit has expired or is invalid.", sivulupaOsoite(`${url.origin}/`));
      }
      const evaste = await allekirjoita(salaisuus, { t: "evaste", h: url.host, e: nyt + EVASTE_IKA });
      return ohjaa(url.origin + polku(url.searchParams.get("paluu"), url.origin), {
        "set-cookie": `${EVASTE}=${evaste}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${EVASTE_IKA}`,
      });
    }
    const evaste = lueEvaste(request);
    if (evaste && (await tarkista(salaisuus, evaste, "evaste", url.host, nyt))) {
      return piiloon(await env.ASSETS.fetch(request), { "cache-control": "private, no-cache" });
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      return ilmoitus(403, "Testisivu näkyy vain kirjautuneille testaajille.", "This test site is only visible to signed-in testers.");
    }
    // Ei kelvollista evästettä: paneeliin kirjautumaan (vanhentunut tai väärennetty eväste poistetaan)
    return ohjaa(sivulupaOsoite(url.href), evaste ? { "set-cookie": `${EVASTE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0` } : {});
  },
};
