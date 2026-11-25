import { jwtVerify, SignJWT } from "jose";
import { randomSeeded, randomIntegerBetween, sample } from "@std/random";
import { getCookies } from "@std/http/cookie";
import { encrypt, decrypt } from "./crypto.ts";

const FRONTEND = Deno.readFileSync(new URL("./index.html", import.meta.url));
const TOTAL_NODES = 1023; 

const secret = crypto.getRandomValues(new Uint8Array(32));
const key = await crypto.subtle.importKey(
  "raw",
  secret,
  "AES-GCM",
  false,
  ["encrypt", "decrypt"]
);

const clearState = {
  "set-cookie": "state=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax",
  "cache-control": "no-store",
};
const stateCookie = (token: string) => `state=${token}; Path=/; HttpOnly; SameSite=Lax`;

type State = {
  maze: string,
  state: string
}

type Node = [number, number] | null;
type Tree = Array<Node>;

async function encodeState(s: State) {
  return await new SignJWT(s)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("5min")
    .sign(secret);
}

async function decodeState(token: string) {
  const { payload } = await jwtVerify(token, secret);
  if (!payload?.maze || typeof payload.maze !== "string") {
    return;
  }
  if (!payload?.state || typeof payload.state !== "string") {
    return;
  }
  return {
    maze: payload.maze,
    state: payload.state,
  };
}

function randomFullTree(n: number, seed: bigint): Tree {
  if (n <= 0 || n % 2 !== 1) {
    throw new Error("n must be a positive odd number");
  }

  const prng = randomSeeded(seed);
  const tree: Tree = [null];

  while (tree.length < n) {
    const v = randomIntegerBetween(0, tree.length - 1, { prng });
    const a = tree.length;
    const b = a + 1;

    tree.push(tree[v], null);
    tree[v] = prng() < 0.5 ? [a, b] : [b, a];
  }

  return tree;
}

function getSolutions(tree: Tree, minDepth = 20): number[] {
  const leaves: number[] = [];
  const visit = (index: number, depth: number) => {
    const node = tree[index];
    if (node === null) {
      if (depth >= minDepth) leaves.push(index);
    } else {
      visit(node[0], depth + 1);
      visit(node[1], depth + 1);
    }
  };
  if (tree.length) visit(0, 0);

  return leaves;
}

Deno.serve(async (req) => {
  const url = new URL(req.url, "http://127.0.0.1");

  if (url.pathname == "/start") {
    let maze = crypto.getRandomValues(new BigUint64Array(1))[0];
    while (!getSolutions(randomFullTree(TOTAL_NODES, maze)).length) {
      maze = crypto.getRandomValues(new BigUint64Array(1))[0];
    }
    const state = 0n;
    return new Response("OK", {
      headers: {
        "set-cookie": stateCookie(await encodeState({
          maze: await encrypt(maze, key),
          state: await encrypt(state, key)
        })),
        "cache-control": "no-store",
      }
    });
  } else if (url.pathname == "/go") {
    const cookie = getCookies(req.headers)?.state;
    if (!cookie || typeof cookie !== "string") {
      return new Response("start the maze!", { status: 400, headers: clearState });
    }
    let state: State | undefined;
    try {
      state = await decodeState(cookie);
    } catch {
      return new Response("session expired!", { status: 400, headers: clearState });
    }
    if (!state) {
      return new Response("invalid state!", { status: 400, headers: clearState })
    }
    const mazeSeed = await decrypt(state.maze, key)
    const maze = randomFullTree(TOTAL_NODES, mazeSeed);
    const solution = sample(getSolutions(maze), { prng: randomSeeded(mazeSeed) }); 
    const current = maze[Number(await decrypt(state.state, key))];
    if (current === null) {
      return new Response("dead end!", { status: 400, headers: clearState });
    }

    const direction = url.searchParams.get("direction");

    let next: number;
    if (direction === "left") {
      next = current[0];
    } else if (direction === "right") {
      next = current[1];
    } else {
      return new Response("invalid direction!", { status: 400, headers: { "cache-control": "no-store" } });
    }

    if (next === solution) {
      return new Response(Deno.env.get("flag") ?? 'test_flag', { headers: clearState });
    }

    if (maze[next] === null) {
      return new Response("dead end!", { status: 400, headers: clearState });
    }

    return new Response("OK", {
      headers: {
        "set-cookie": stateCookie(await encodeState({
          maze: state.maze,
          state: await encrypt(BigInt(next), key),
        })),
        "cache-control": "no-store",
      }
    });
  } else if (url.pathname === "/") {
    return new Response(FRONTEND, { headers: { "content-type": "text/html; charset=utf-8" }})
  }

  return new Response("not found", { status: 404 });
});
