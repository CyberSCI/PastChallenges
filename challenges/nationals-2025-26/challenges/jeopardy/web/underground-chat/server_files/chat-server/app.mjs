import { randomUUID } from "node:crypto";
import { parseCookie } from "cookie";
import { jwtDecode } from "jwt-decode";

const sockets = new Map();

Deno.serve({ port: 8080 }, (req) => {
  if (!req.headers.get("upgrade") === "websocket") {
    return new Response("Expecting Upgrade: websocket", { status: 426 });
  }

  // verification happens on the reverse proxy we just need the username
  const { username } = jwtDecode(parseCookie(req.headers.get("cookie")).token);
  if (!username) {
    return new Response("Unauthorized", { status: 401 });
  }
  
  const { socket, response } = Deno.upgradeWebSocket(req);

  const id = randomUUID();
  sockets.set(id, socket);

  socket.onmessage = (e) => {
    if (typeof e.data !== "string") {
      return;
    }
    const { message } = JSON.parse(e.data);
    for (const [_, socket] of sockets) {
      socket.send(JSON.stringify({
        username,
        message,
      }));
    }
  };

  socket.onclose = () => {
    sockets.delete(id);
  };

  if (username === "admin") {
    response.headers.set("X-FLAG", Deno.env.get("FLAG") || "CyberSci{test}");
  }

  return response;
});