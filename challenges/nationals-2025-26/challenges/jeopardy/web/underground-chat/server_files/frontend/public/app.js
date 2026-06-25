/* =========================================================
   UNDERGROUND :: SPA controller
   - boot sequence
   - auth (login / register) against /login & /register
   - WebSocket chat at /ws (auth via httpOnly cookie)
   ========================================================= */
(() => {
  "use strict";

  // ---------- helpers ----------
  const $  = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const escapeHtml = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  const linkify = (s) =>
    escapeHtml(s).replace(
      /\b(https?:\/\/[^\s<]+)/g,
      (m) => `<a href="${m}" target="_blank" rel="noopener noreferrer">${m}</a>`
    );
  const nowHHMM = () => {
    const d = new Date();
    return `${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}:${String(d.getSeconds()).padStart(2,"0")}`;
  };

  // Decode a JWT payload (no verification — server is the source of truth).
  function decodeJwt(token) {
    try {
      const part = token.split(".")[1];
      const json = atob(part.replace(/-/g, "+").replace(/_/g, "/"));
      return JSON.parse(decodeURIComponent(escape(json)));
    } catch { return null; }
  }
  function readTokenCookie() {
    const m = document.cookie.match(/(?:^|;\s*)token=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : null;
  }
  function currentUsername() {
    const t = readTokenCookie();
    if (!t) return null;
    const p = decodeJwt(t);
    if (!p) return null;
    if (p.exp && p.exp * 1000 < Date.now()) return null;
    return p.username || null;
  }
  function clearTokenCookie() {
    document.cookie = "token=; Path=/; Max-Age=0; SameSite=Lax";
  }

  // ---------- boot sequence ----------
  const BOOT_LINES = [
    { t: "[ <span class='dim'>0.000</span> ] BIOS v0xUC.0001 :: cold boot",                    d: 60 },
    { t: "[ <span class='dim'>0.014</span> ] mounting /dev/grid …                 <span class='ok'>OK</span>", d: 120 },
    { t: "[ <span class='dim'>0.062</span> ] negotiating ed25519 handshake …      <span class='ok'>OK</span>", d: 140 },
    { t: "[ <span class='dim'>0.118</span> ] fetching jwks @ auth-server …        <span class='ok'>OK</span>", d: 140 },
    { t: "[ <span class='dim'>0.184</span> ] tor relay <span class='mag'>onion-3</span> :: <span class='ok'>established</span>", d: 160 },
    { t: "[ <span class='dim'>0.241</span> ] zero-trust ingress @ envoy:8080 …    <span class='ok'>READY</span>", d: 160 },
    { t: "",                                                                                   d: 80 },
    { t: "&gt; <span class='mag'>welcome to the underground.</span>",                          d: 240 },
    { t: "&gt; type slowly. they are listening.",                                              d: 320 },
  ];

  async function runBoot() {
    const log = $("#boot-log");
    for (const line of BOOT_LINES) {
      log.insertAdjacentHTML("beforeend", line.t + "\n");
      await sleep(line.d);
    }
    await sleep(280);
    $("#boot").classList.add("hidden");
    // Decide initial screen based on existing token
    const me = currentUsername();
    if (me) {
      enterChat(me);
    } else {
      showAuth();
    }
  }

  // ---------- screens ----------
  function showAuth() {
    $("#auth").classList.remove("hidden");
    $("#auth").setAttribute("aria-hidden", "false");
    $("#chat").classList.add("hidden");
    $("#chat").setAttribute("aria-hidden", "true");
    $("#username").focus();
  }
  function showChat() {
    $("#auth").classList.add("hidden");
    $("#auth").setAttribute("aria-hidden", "true");
    $("#chat").classList.remove("hidden");
    $("#chat").setAttribute("aria-hidden", "false");
    $("#msg-input").focus();
  }

  // ---------- auth ----------
  let mode = "login"; // "login" | "register"

  function bindAuth() {
    $$(".tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$(".tab").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        mode = btn.dataset.tab;
        $("#submit .btn-label").textContent =
          mode === "login" ? "[ AUTHENTICATE ]" : "[ CREATE IDENTITY ]";
        setMsg("", "");
      });
    });

    $("#auth-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = $("#username").value.trim();
      const password = $("#password").value;
      if (!username || !password) {
        setMsg("missing handle or passphrase.", "err");
        return;
      }
      const submitBtn = $("#submit");
      submitBtn.disabled = true;
      setMsg(mode === "login" ? "▸ authenticating…" : "▸ provisioning identity…", "dim");

      try {
        const path = mode === "login" ? "/login" : "/register";
        const res = await fetch(path, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
          credentials: "same-origin",
        });
        const text = await res.text();
        if (!res.ok) {
          setMsg(`✘ ${text || res.statusText}`, "err");
          return;
        }
        if (mode === "register") {
          setMsg("✔ identity created. logging in…", "ok");
          // auto-login after register
          const loginRes = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
            credentials: "same-origin",
          });
          if (!loginRes.ok) {
            const t = await loginRes.text();
            setMsg(`✘ ${t || loginRes.statusText}`, "err");
            return;
          }
        }
        const me = currentUsername() || username;
        setMsg("✔ uplink established.", "ok");
        await sleep(280);
        enterChat(me);
      } catch (err) {
        setMsg(`✘ network error: ${err.message || err}`, "err");
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  function setMsg(text, kind) {
    const el = $("#auth-msg");
    el.className = "msg" + (kind ? " " + kind : "");
    el.innerHTML = text;
  }

  // ---------- chat ----------
  let ws = null;
  let reconnectAttempts = 0;
  let manualClose = false;

  function setStatus(state, label) {
    const pill = $("#status-pill");
    pill.classList.remove("ok", "err");
    if (state === "ok")  pill.classList.add("ok");
    if (state === "err") pill.classList.add("err");
    $("#status-text").textContent = label;
  }

  function appendMessage({ author, body, kind }) {
    const me = $("#me").textContent;
    const wrap = document.createElement("div");
    wrap.className = "message" + (kind ? " " + kind : (author === me ? " me" : ""));
    wrap.innerHTML = `
      <span class="ts">${nowHHMM()}</span>
      <span class="body"><span class="author">@${escapeHtml(author)}</span> ${linkify(body)}</span>
      <span></span>
    `;
    const list = $("#messages");
    const atBottom = list.scrollTop + list.clientHeight >= list.scrollHeight - 40;
    list.appendChild(wrap);
    if (atBottom) list.scrollTop = list.scrollHeight;
  }

  function systemMessage(text) {
    appendMessage({ author: "system", body: text, kind: "system" });
  }

  function connectWs() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const url   = `${proto}//${location.host}/ws`;
    setStatus("", "connecting…");
    try {
      ws = new WebSocket(url);
    } catch (e) {
      setStatus("err", "ws error");
      systemMessage(`failed to open socket: ${e.message || e}`);
      return;
    }

    ws.addEventListener("open", () => {
      reconnectAttempts = 0;
      setStatus("ok", "online");
      systemMessage("secure channel established.");
    });

    ws.addEventListener("message", (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data && typeof data.message === "string" && typeof data.username === "string") {
          appendMessage({ author: data.username, body: data.message });
          return;
        }
      } catch { /* fallthrough */ }
      appendMessage({ author: "raw", body: String(e.data) });
    });

    ws.addEventListener("close", () => {
      setStatus("err", "disconnected");
      if (manualClose) return;
      reconnectAttempts++;
      const delay = Math.min(8000, 600 * reconnectAttempts);
      systemMessage(`link dropped. retrying in ${Math.round(delay / 100) / 10}s…`);
      setTimeout(() => {
        // Re-validate token before reconnect; if missing, bounce to auth.
        if (!currentUsername()) {
          systemMessage("session expired. returning to login.");
          return logout();
        }
        connectWs();
      }, delay);
    });

    ws.addEventListener("error", () => {
      setStatus("err", "ws error");
    });
  }

  function sendCurrent() {
    const input = $("#msg-input");
    const text = input.value.trim();
    if (!text) return;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      systemMessage("not connected.");
      return;
    }
    ws.send(JSON.stringify({ message: text }));
    input.value = "";
  }

  function bindChat() {
    $("#send").addEventListener("click", sendCurrent);
    $("#msg-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendCurrent();
      }
    });
    $("#logout").addEventListener("click", logout);
  }

  function enterChat(username) {
    manualClose = false;
    $("#me").textContent = username;
    $("#messages").innerHTML = "";
    showChat();
    systemMessage(`identity locked as @${username}. opening secure channel…`);
    connectWs();
  }

  function logout() {
    manualClose = true;
    try { ws && ws.close(); } catch { /* ignore */ }
    clearTokenCookie();
    // best-effort: token is httpOnly so we can't fully clear it client-side.
    // It will expire server-side; meanwhile we just return to auth screen.
    $("#username").value = "";
    $("#password").value = "";
    setMsg("session terminated.", "dim");
    showAuth();
  }

  // ---------- init ----------
  document.addEventListener("DOMContentLoaded", () => {
    bindAuth();
    bindChat();
    runBoot();
  });
})();
