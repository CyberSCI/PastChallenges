#!/usr/bin/env node
/**
 * Solver for the "maze" CTF challenge.
 *
 * The server hides a random binary tree (1023 nodes) behind an encrypted
 * JWT state cookie. /go?direction=left|right is a navigation oracle:
 *   - "OK" + new cookie  -> child is an internal node
 *   - "dead end!"        -> child is a leaf, but not the solution
 *   - flag               -> child is the solution leaf
 *
 * Cookies are stateless and reusable until their 5-minute expiry, so we
 * treat each one as a node handle and explore the tree with a concurrent
 * DFS: keep parent cookies for backtracking, try left then right at every
 * node, stop when the flag appears.
 *
 * Usage: node solve.js [baseURL] [concurrency]
 *   e.g. node solve.js http://localhost:8000 24
 */

const BASE = (process.argv[2] ?? "http://localhost:8000").replace(/\/$/, "");
const CONCURRENCY = Math.max(1, Number(process.argv[3] ?? 24));
const DIRECTIONS = ["left", "right"];

const stats = { requests: 0, deadEnds: 0, nodes: 0, retries: 0 };
let flag = null;

function stateCookie(res) {
  const m = /(?:^|,\s*)state=([^;]*)/.exec(res.headers.get("set-cookie") ?? "");
  return m ? m[1] : null;
}

async function start() {
  const res = await fetch(`${BASE}/start`, { cache: "no-store" });
  const cookie = stateCookie(res);
  if (!cookie) throw new Error(`no state cookie from /start (${res.status})`);
  return cookie;
}

async function go(cookie, direction) {
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(`${BASE}/go?direction=${direction}`, {
        headers: { cookie: `state=${cookie}` },
        cache: "no-store",
      });
      stats.requests++;
      return {
        status: res.status,
        body: await res.text(),
        cookie: stateCookie(res),
      };
    } catch (err) {
      if (attempt >= 5 || flag) throw err;
      stats.retries++;
      await new Promise((r) => setTimeout(r, 250 * (attempt + 1)));
    }
  }
}

// Work queue: items are { cookie, depth, path }. Workers pop nodes and push
// newly discovered internal children. `pending` counts in-flight nodes so
// workers don't exit while another worker can still enqueue more.
const queue = [];
const waiters = new Set();
let pending = 0;
const wake = () => {
  for (const r of waiters) r();
  waiters.clear();
};

async function worker() {
  for (;;) {
    if (flag) return;
    let item;
    while (!(item = queue.pop())) {
      if (flag || pending === 0) return;
      await new Promise((r) => waiters.add(r));
    }
    pending++;
    try {
      for (const dir of DIRECTIONS) {
        if (flag) return;
        const r = await go(item.cookie, dir);
        if (r.status === 200 && r.body === "OK" && r.cookie) {
          stats.nodes++;
          queue.push({ cookie: r.cookie, depth: item.depth + 1, path: item.path + dir[0] });
          wake();
        } else if (r.status === 200) {
          flag = r.body; // any other 200 body is the flag
          return;
        } else {
          stats.deadEnds++; // 400: dead end / invalid / expired
          if (r.body === "session expired!")
            console.error(`warning: cookie expired at depth ${item.depth} (path ${item.path})`);
        }
      }
    } finally {
      pending--;
    }
  }
}

const started = Date.now();
const root = await start();
stats.nodes = 1;
queue.push({ cookie: root, depth: 0, path: "" });
await Promise.all(Array.from({ length: CONCURRENCY }, worker));

const secs = ((Date.now() - started) / 1000).toFixed(1);
if (flag) {
  console.log(`flag: ${flag}`);
} else {
  console.log("no flag found (tree exhausted or cookies expired)");
}
console.log(
  `${stats.requests} requests, ${stats.nodes} internal nodes, ` +
    `${stats.deadEnds} dead ends, ${stats.retries} retries, ${secs}s`
);
