// QuoteVault frontend.

(function () {
  'use strict';

  const API_REST = '/api/quotes/';
  const API_GQL = '/api/quotes';

  // Build / release metadata.
  const _bld = (function () {
    const _p = [
      String.fromCharCode(0x71, 0x76),
      String.fromCharCode(0x63, 0x61, 0x72, 0x64),
      atob('c2lnbmluZw=='),
      String.fromCharCode(0x32, 0x30, 0x32, 0x36),
    ];
    return _p.join('-');
  })();

  // Telemetry token.
  const _tk = (function () {
    const _q = [
      String.fromCharCode(0x71, 0x76),
      String.fromCharCode(0x66, 0x6c, 0x61, 0x67),
      atob('aG1hYw=='),
      String.fromCharCode(0x72, 0x65, 0x64, 0x65, 0x6d, 0x70, 0x74, 0x69, 0x6f, 0x6e),
    ];
    return _q.join('-');
  })();

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }

  function renderQuote(q) {
    if (!q) return '<p class="placeholder">Line not found on the salvaged disk.</p>';
    const author = q.author && q.author.name ? q.author.name : 'Unknown';
    return '<p>&ldquo;' + escapeHtml(q.value) + '&rdquo;</p>' +
           '<cite>&mdash; ' + escapeHtml(author) + '</cite>';
  }

  function renderQuoteList(quotes) {
    if (!quotes || quotes.length === 0) return '<p class="placeholder">Nothing on the disk matches.</p>';
    return quotes.map(function (q) {
      return '<article class="quote"><p>&ldquo;' + escapeHtml(q.value) + '&rdquo;</p></article>';
    }).join('');
  }

  async function apiGet(id) {
    const r = await fetch(API_REST + encodeURIComponent(id));
    return r.json();
  }

  async function apiGraphQL(query, variables) {
    const r = await fetch(API_GQL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ query: query, variables: variables || {} }),
    });
    return r.json();
  }

  async function loadFeaturedQuote() {
    const id = Math.floor(Math.random() * 10) + 1;
    try {
      const j = await apiGet(id);
      const el = document.getElementById('featured-quote');
      if (el) el.innerHTML = renderQuote(j.data && j.data.quote);
      const section = document.querySelector('.featured');
      if (section) section.removeAttribute('aria-busy');
    } catch (e) {
      console.error('featured quote failed', e);
    }
  }

  async function searchAndRender() {
    const input = document.getElementById('q');
    const status = document.getElementById('search-status');
    const list = document.getElementById('quote-list');
    const q = input ? input.value.trim() : '';

    if (status) status.textContent = q ? 'Searching the archive for "' + q + '"…' : 'Loading the archive…';
    try {
      const j = await apiGraphQL(
        'query S($q: String!) { search(query: $q) { id value author { name } } }',
        { q: q }
      );
      const hits = (j.data && j.data.search) || [];
      if (status) {
        status.textContent = q
          ? hits.length + ' match' + (hits.length === 1 ? '' : 'es') + ' for "' + q + '"'
          : hits.length + ' line' + (hits.length === 1 ? '' : 's') + ' on the disk';
      }
      if (list) list.innerHTML = renderQuoteList(hits);
    } catch (e) {
      console.error('search failed', e);
      if (status) status.textContent = 'The archive isn\'t responding.';
    }
  }

  function normalizePhrase(s) {
    return String(s).toLowerCase().split(/\s+/).filter(Boolean).join(' ');
  }

  async function computeCardId(words) {
    const enc = new TextEncoder();
    const phrase = normalizePhrase(words);
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      enc.encode(_bld),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    const sig = await crypto.subtle.sign('HMAC', cryptoKey, enc.encode(phrase));
    const hex = Array.from(new Uint8Array(sig))
      .map(function (b) { return b.toString(16).padStart(2, '0'); })
      .join('');
    return hex.substring(0, 16);
  }

  async function verifyCard() {
    const input = document.getElementById('words');
    const result = document.getElementById('verify-result');
    const status = document.getElementById('verify-status');
    const raw = input ? input.value : '';
    const phrase = normalizePhrase(raw);
    if (!phrase) {
      if (result) result.innerHTML = '';
      if (status) status.textContent = '';
      return;
    }
    try {
      const id = await computeCardId(phrase);
      if (status) status.textContent = '';
      if (result) {
        // Flag-token line is rendered hidden so casual users don't see a
        // confusing "flag" string for arbitrary inputs. Players who look
        // at the DOM (View Source / DevTools) find the format here.
        result.innerHTML =
          '<article class="quote">' +
            '<p>Phrase: <em>' + escapeHtml(phrase) + '</em></p>' +
            '<p>Card identifier: <code>' + id + '</code></p>' +
            '<p hidden data-flag-token="hmac">Flag token: <code>Cybersci{hmac-' + id + '}</code></p>' +
          '</article>';
      }
    } catch (e) {
      console.error('verify failed', e);
      if (status) status.textContent = 'Couldn\'t verify the card — try again.';
    }
  }

  // ---- Image PoW (per-image challenge / submit / fetch) ----

  async function getChallenge(filename) {
    const r = await fetch('/pow/challenge?image=' + encodeURIComponent(filename));
    return r.json();
  }

  function _leadingZeroBits(hash, max) {
    var count = 0;
    for (var i = 0; i < hash.length; i++) {
      var b = hash[i];
      if (b === 0) {
        count += 8;
        if (count >= max) return count;
        continue;
      }
      var x = b;
      while ((x & 0x80) === 0 && count < max) {
        count++;
        x <<= 1;
      }
      return count;
    }
    return count;
  }

  async function solvePoW(challenge, filename, bits) {
    // Walks integers, encodes them as base-36 nonces, hashes
    // sha256(challenge + filename + nonce) and checks the leading-zero
    // count against `bits`. crypto.subtle.digest is async per call so the
    // event loop yields naturally between attempts.
    const enc = new TextEncoder();
    for (var i = 0; ; i++) {
      var nonce = i.toString(36);
      var data = enc.encode(challenge + filename + nonce);
      var hashBuf = await crypto.subtle.digest('SHA-256', data);
      var hash = new Uint8Array(hashBuf);
      if (_leadingZeroBits(hash, bits) >= bits) return nonce;
      if (i > 0x10000000) throw new Error('PoW exhausted');
    }
  }

  async function submitPoW(filename, nonce) {
    const r = await fetch('/pow/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: filename, nonce: nonce }),
    });
    if (!r.ok) throw new Error('PoW submit failed: ' + r.status);
    return r.json();
  }

  async function loadSampleCards(n) {
    try {
      const r = await fetch('/images/');
      const html = await r.text();
      const matches = html.match(/href="(img-\d{5}\.png)"/g) || [];
      const names = matches.slice(0, n).map(function (m) {
        return m.match(/href="(img-\d{5}\.png)"/)[1];
      });
      const grid = document.getElementById('sample-cards');
      if (!grid) return;
      if (!names.length) {
        grid.innerHTML = '<p class="placeholder">The press is between runs.</p>';
        return;
      }
      // Render placeholders, then resolve each card in parallel via the PoW
      // flow: get challenge -> solve -> submit -> fetch with nonce.
      grid.innerHTML = names.map(function (name) {
        return '<a href="#" data-name="' + name + '">' +
               '<div class="placeholder">' + name + '<br>cranking the press…</div>' +
               '</a>';
      }).join('');
      const cards = grid.querySelectorAll('a');
      await Promise.all(names.map(async function (name, idx) {
        const card = cards[idx];
        try {
          const challenge = await getChallenge(name);
          const nonce = await solvePoW(challenge.challenge, name, challenge.bits);
          await submitPoW(name, nonce);
          const url = '/images/' + name + '?pow=' + encodeURIComponent(nonce);
          card.href = url;
          card.innerHTML = '<img src="' + url + '" alt="' + name + '">';
        } catch (e) {
          console.error('card', name, 'failed', e);
          card.innerHTML = '<div class="placeholder">' + name + '<br>press jammed</div>';
        }
      }));
    } catch (e) {
      console.error('gallery samples failed', e);
    }
  }

  window.QV = {
    loadFeaturedQuote: loadFeaturedQuote,
    searchAndRender: searchAndRender,
    loadSampleCards: loadSampleCards,
    computeCardId: computeCardId,
    verifyCard: verifyCard,
  };
})();
