import { randomBytes } from "node:crypto";
import { SignJWT, exportJWK } from "jose";

const key = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);

const users = new Map();
users.set("admin", randomBytes(16).toString("hex"));

Deno.serve(async (req) => {
  const path = new URL(req.url).pathname;

  if (path == "/login") {
    const body = await req.json();
    if (typeof body.username !== "string" || typeof body.password !== "string") {
      return new Response("Invalid request", { status: 400 });
    }
    if (!users.has(body.username) || users.get(body.username) !== body.password) {
      return new Response("Invalid credentials", { status: 401 });
    }

    const token = await new SignJWT({ username: body.username })
      .setProtectedHeader({ alg: "EdDSA" })
      .setIssuedAt()
      .setExpirationTime("1h")
      .sign(key.privateKey);
    
    return new Response("Login successful", {
      headers: {
        "Set-Cookie": `token=${token}; Path=/; HttpOnly`,
      },
    });
  } else if (path == "/register") {
    const body = await req.json();
    if (typeof body.username !== "string" || typeof body.password !== "string") {
      return new Response("Invalid request", { status: 400 });
    }
    if (users.has(body.username)) {
      return new Response("User already exists", { status: 400 });
    }
    users.set(body.username, body.password);
    return new Response("User created");
  } else if (path == "/.well-known/jwks.json") {
    return new Response(JSON.stringify({
      keys: [{
        ...await exportJWK(key.publicKey),
        use: "sig",
        alg: "EdDSA",
      }]
    }), {
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  return new Response("Not found", { status: 404 });
});