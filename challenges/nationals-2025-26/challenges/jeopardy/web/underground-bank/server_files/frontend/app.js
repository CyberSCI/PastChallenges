/* =====================================================================
   UNDERGROUND//BANK — SPA controller
   ===================================================================== */

const API = "/api";
const TOKEN_KEY = "ub_token";
const USER_KEY  = "ub_user";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const state = {
  token: localStorage.getItem(TOKEN_KEY) || null,
  user:  localStorage.getItem(USER_KEY)  || null,
};

/* ---------- helpers ---------- */
function toast(msg, kind = "ok") {
  const c = $("#toasts");
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(20px)"; el.style.transition = "all 0.3s"; }, 3200);
  setTimeout(() => el.remove(), 3700);
}

async function api(path, { method = "GET", form, auth = true } = {}) {
  const headers = {};
  if (auth && state.token) headers["Authorization"] = `Bearer ${state.token}`;
  let body;
  if (form) {
    body = new URLSearchParams();
    Object.entries(form).forEach(([k, v]) => body.append(k, v));
  }
  const res = await fetch(API + path, { method, headers, body });
  let data = null;
  try { data = await res.json(); } catch {}
  if (!res.ok) {
    const err = (data && (data.detail || data.error)) || `HTTP ${res.status}`;
    throw new Error(typeof err === "string" ? err : JSON.stringify(err));
  }
  return data;
}

function setSession(token, user) {
  state.token = token; state.user = user;
  if (token) localStorage.setItem(TOKEN_KEY, token); else localStorage.removeItem(TOKEN_KEY);
  if (user)  localStorage.setItem(USER_KEY, user);   else localStorage.removeItem(USER_KEY);
  renderStatusBar();
}

function decodeJwtPayload(token) {
  try {
    const p = token.split(".")[1];
    const json = atob(p.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decodeURIComponent(escape(json)));
  } catch { return {}; }
}

/* ---------- status bar ---------- */
function renderStatusBar() {
  $("#session").innerHTML = `SESSION: <b>${state.user ? state.user.toUpperCase() : "ANON"}</b>`;
  $("#logoutBtn").hidden = !state.token;
}

function tickClock() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  $("#clock").textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
setInterval(tickClock, 1000); tickClock();

$("#logoutBtn").addEventListener("click", () => {
  setSession(null, null);
  toast("disconnected", "ok");
  mount();
});

/* ---------- routes ---------- */
function mountTemplate(id) {
  const tpl = document.getElementById(id);
  const node = tpl.content.cloneNode(true);
  const app = $("#app");
  app.innerHTML = "";
  app.appendChild(node);
}

function mount() {
  renderStatusBar();
  if (state.token) mountDashboard();
  else mountAuth();
}

/* ---------- AUTH screen ---------- */
function mountAuth() {
  mountTemplate("tpl-auth");

  $$(".tab").forEach((t) => {
    t.addEventListener("click", () => {
      $$(".tab").forEach((x) => x.classList.toggle("active", x === t));
      const target = t.dataset.tab;
      $("#loginForm").classList.toggle("active", target === "login");
      $("#registerForm").classList.toggle("active", target === "register");
    });
  });

  $("#loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const username = fd.get("username");
    const password = fd.get("password");
    try {
      const res = await api("/login", { method: "POST", form: { username, password }, auth: false });
      if (!res.token) throw new Error(res.error || "auth failed");
      setSession(res.token, username);
      const payload = decodeJwtPayload(res.token);
      toast(`welcome, ${payload.username || username}`, "ok");
      mountDashboard();
    } catch (err) { toast(err.message, "error"); }
  });

  $("#registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const username = fd.get("username");
    const password = fd.get("password");
    try {
      const res = await api("/register", { method: "POST", form: { username, password }, auth: false });
      if (!res.success) throw new Error(res.error || "registration failed");
      toast("identity forged. authenticating...", "ok");
      const lr = await api("/login", { method: "POST", form: { username, password }, auth: false });
      if (!lr.token) throw new Error(lr.error || "auth failed");
      setSession(lr.token, username);
      mountDashboard();
    } catch (err) { toast(err.message, "error"); }
  });
}

/* ---------- DASHBOARD ---------- */
function mountDashboard() {
  mountTemplate("tpl-dashboard");

  // account panel
  $("#acctHandle").textContent = state.user || "--";

  $("#requestForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    try {
      const res = await api("/request-money", {
        method: "POST",
        form: { request_from: fd.get("request_from"), amount: fd.get("amount") },
      });
      if (res.errors) throw new Error(res.errors[0]?.message || "request failed");
      toast(`request transmitted (id=${res?.data?.requestMoney?.id?.slice(0,8) || "??"})`, "ok");
      form.reset();
    } catch (err) { toast(err.message, "error"); }
  });

  $("#webhookForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    try {
      const res = await api("/set-webhook", { method: "POST", form: { webhook: fd.get("webhook") } });
      if (res.errors) throw new Error(res.errors[0]?.message || "set-webhook failed");
      toast("webhook bound", "ok");
      form.reset();
    } catch (err) { toast(err.message, "error"); }
  });

  $("#refreshBtn").addEventListener("click", loadRequests);
  loadRequests();
}

async function loadRequests() {
  const list = $("#requestsList");
  if (!list) return;
  list.innerHTML = `<p class="empty">// scanning ledger ...</p>`;
  try {
    const res = await api("/requests");
    const items = res?.data?.requests || [];
    if (!items.length) {
      list.innerHTML = `<p class="empty">// no incoming requests detected</p>`;
      return;
    }
    list.innerHTML = "";
    for (const r of items) {
      const row = document.createElement("div");
      row.className = "request-row" + (r.amount === null ? " amt-null" : "");
      const amt = r.amount === null ? "Infinity ☠" : Number(r.amount).toFixed(2);
      row.innerHTML = `
        <span class="rid">id: ${r.id}</span>
        <span class="ramt">⟶ ${amt}</span>
        <button class="neon-btn small accept-btn">ACCEPT</button>
      `;
      row.querySelector(".accept-btn").addEventListener("click", async () => {
        try {
          const ar = await api("/accept-request", { method: "POST", form: { id: r.id } });
          if (ar?.data?.acceptRequest) { toast("request accepted", "ok"); loadRequests(); }
          else { toast("transfer rejected (insufficient funds?)", "error"); }
        } catch (err) { toast(err.message, "error"); }
      });
      list.appendChild(row);
    }
  } catch (err) {
    if (/401|Not authenticated/i.test(err.message)) {
      setSession(null, null); mountAuth();
    }
    list.innerHTML = `<p class="empty">// link severed: ${err.message}</p>`;
  }
}

/* ---------- Matrix-rain background ---------- */
(function matrixRain() {
  const canvas = document.getElementById("matrix");
  const ctx = canvas.getContext("2d");
  const chars = "アイウエオカキクケコサシスセソタチツテトナニヌネノ01@#$%&*ABCDEFGHIJ0123456789".split("");
  let cols, drops;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    cols = Math.floor(canvas.width / 14);
    drops = Array(cols).fill(1).map(() => Math.random() * canvas.height);
  }
  resize();
  window.addEventListener("resize", resize);

  function draw() {
    ctx.fillStyle = "rgba(5, 6, 10, 0.08)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = "14px Share Tech Mono";
    for (let i = 0; i < drops.length; i++) {
      const txt = chars[Math.floor(Math.random() * chars.length)];
      const x = i * 14;
      const y = drops[i];
      // green head, faded body
      ctx.fillStyle = y < 18 ? "#aafff0" : "#00ffd1";
      ctx.fillText(txt, x, y);
      drops[i] = (y > canvas.height + Math.random() * 200) ? 0 : y + 14;
    }
  }
  setInterval(draw, 55);
})();

/* ---------- boot ---------- */
mount();
