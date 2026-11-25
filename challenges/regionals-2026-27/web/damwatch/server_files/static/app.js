const page = document.body.dataset.page;
const byId = (id) => document.getElementById(id);

async function request(url, options = {}) {
  const response = await fetch(url, { credentials: "same-origin", ...options });
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The console returned an unreadable response.");
  }
  if (response.status === 401) {
    await fetch("/", { credentials: "same-origin" });
    throw new Error("Your observer session expired. A fresh ticket is ready; reload this view.");
  }
  if (!response.ok) {
    throw new Error(data.message || "The request could not be completed.");
  }
  return data;
}

async function post(url, body) {
  return request(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

function showMessage(id, message) {
  byId(id).textContent = message;
}

function startLive() {
  let reconnectTimer;
  function connect() {
    const scheme = location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${scheme}//${location.host}/ws/telemetry`);
    socket.addEventListener("open", () => {
      socket.send(JSON.stringify({ action: "subscribe", topic: "water/level" }));
      showMessage("live-message", "Public telemetry connected.");
    });
    socket.addEventListener("message", (event) => {
      let frame;
      try { frame = JSON.parse(event.data); } catch { return; }
      if (frame.topic !== "water/level" || frame.type !== "snapshot") return;
      byId("waterline").textContent = frame.waterline_cm;
      byId("baseline").textContent = frame.baseline_cm;
      byId("water-fill").style.height = `${Math.max(0, Math.min(100, frame.waterline_cm / frame.baseline_cm * 100))}%`;
      byId("water-fill").parentElement.setAttribute("aria-label", `Reservoir level ${frame.waterline_cm} centimeters; reference ${frame.baseline_cm} centimeters`);
      byId("public-status").textContent = frame.public_status;
      byId("updated").textContent = `Sample received ${new Date().toLocaleTimeString()}`;
    });
    socket.addEventListener("close", () => {
      showMessage("live-message", "Telemetry disconnected. Reconnecting to the public feed…");
      reconnectTimer = window.setTimeout(connect, 3000);
    });
  }
  connect();
  window.addEventListener("beforeunload", () => window.clearTimeout(reconnectTimer));
}

async function startReports() {
  try {
    const { reports } = await request("/api/archive/public");
    const list = byId("report-list");
    list.replaceChildren();
    for (const report of reports) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = report.title;
      button.addEventListener("click", async () => {
        showMessage("report-message", "Opening record…");
        try {
          const opened = await request(`/api/archive/read?path=${encodeURIComponent(report.path)}`);
          byId("record-path").textContent = opened.path;
          byId("record-title").textContent = opened.title;
          byId("record-body").textContent = opened.body;
          showMessage("report-message", "Record opened.");
        } catch (error) {
          showMessage("report-message", error.message);
        }
      });
      item.append(button);
      list.append(item);
    }
  } catch (error) {
    showMessage("report-message", error.message);
  }
}

async function startOverride() {
  let ticket;
  let receipts = {};
  const message = (value) => showMessage("override-message", value);

  function render(state) {
    ticket = state.ticket;
    receipts = state.receipts || {};
    byId("ticket").textContent = ticket;
    byId("generation").textContent = `GEN ${state.generation}`;
    byId("ticket-note").textContent = state.ticket_used
      ? "This ticket is spent. Issue a new one to try again."
      : "A ticket is spent after one redemption. A failed attempt can be reset.";
    byId("slot-a").textContent = receipts.A ? "Receipt recorded" : "Awaiting receipt";
    byId("slot-b").textContent = receipts.B ? "Receipt recorded" : "Awaiting receipt";
    byId("lock-state").textContent = state.locked ? "Engaged" : "Standby";
  }

  async function refresh() {
    render(await request("/api/override/state"));
  }

  document.querySelectorAll("[data-slot]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      message(`Reviewing slot ${button.dataset.slot}…`);
      try {
        await post("/api/approvals/redeem", { ticket, slot: button.dataset.slot });
        await refresh();
        message(`Slot ${button.dataset.slot} has a receipt.`);
      } catch (error) {
        message(error.message);
      } finally {
        button.disabled = false;
      }
    });
  });

  byId("reset").addEventListener("click", async () => {
    try {
      await post("/api/approvals/reset", {});
      await refresh();
      byId("flag-result").hidden = true;
      message("New ticket issued. Previous receipts were cleared.");
    } catch (error) {
      message(error.message);
    }
  });

  byId("authorize").addEventListener("click", async () => {
    try {
      const result = await post("/api/override/authorize", { receipts });
      byId("lock-state").textContent = "Engaged";
      byId("flag-result").textContent = result.flag;
      byId("flag-result").hidden = false;
      message(result.message);
    } catch (error) {
      message(error.message);
    }
  });

  try { await refresh(); } catch (error) { message(error.message); }
}

if (page === "live") startLive();
if (page === "reports") startReports();
if (page === "override") startOverride();
