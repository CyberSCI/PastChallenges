import express from "express";
import methodOverride from "method-override";
import { randomUUID } from "node:crypto";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { ShipStore } from "./ship-store.js";

const POSITION_ERROR = "Expected valid ship metadata and GPS position fields.";
const REMOTE_CONTROL_ERROR = "The enabled field must be a boolean.";
const DESIGNATION_PAYLOAD_ERROR = "Expected a JSON object with heading and speedKnots.";
const DESIGNATION_RANGE_ERROR = "Heading must be in [0, 360) and speedKnots in [0, 40].";
const UUID_PATTERN = /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i;

function jsonObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value
    : null;
}

function numberInRange(payload, field, minimum, maximum) {
  const value = payload[field];
  return typeof value === "number"
    && Number.isFinite(value)
    && value >= minimum
    && value <= maximum
    ? value
    : null;
}

function queryBoolean(value) {
  if (typeof value !== "string") {
    return value;
  }

  switch (value.trim().toLowerCase()) {
    case "1":
    case "true":
    case "on":
    case "yes":
      return true;
    case "0":
    case "false":
    case "off":
    case "no":
      return false;
    default:
      return value;
  }
}

function queryNumber(value) {
  if (typeof value !== "string") {
    return value;
  }

  const normalized = value.trim();
  if (!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(normalized)) {
    return value;
  }

  const number = Number(normalized);
  return Number.isFinite(number) ? number : value;
}

function mutationPayload(request) {
  if (request.originalMethod !== "GET") {
    return jsonObject(request.body);
  }

  const payload = { ...request.query };
  if ("enabled" in payload) {
    payload.enabled = queryBoolean(payload.enabled);
  }
  for (const field of ["heading", "speedKnots"]) {
    if (field in payload) {
      payload[field] = queryNumber(payload[field]);
    }
  }
  return payload;
}

function isValidPosition(payload) {
  for (const field of ["name", "callSign", "mmsi", "vesselType", "destination", "status"]) {
    if (typeof payload[field] !== "string" || payload[field].trim() === "") {
      return false;
    }
  }

  const heading = numberInRange(payload, "heading", 0, 360);
  return numberInRange(payload, "latitude", -90, 90) !== null
    && numberInRange(payload, "longitude", -180, 180) !== null
    && numberInRange(payload, "speedKnots", 0, 60) !== null
    && heading !== null
    && heading < 360
    && Number.isInteger(payload.cargoPercent)
    && payload.cargoPercent >= 0
    && payload.cargoPercent <= 100;
}

function badRequest(response, message) {
  return response.status(400).json({ error: message });
}

function invalidJsonMessage(request) {
  if (request.path === "/api/ships" || /^\/api\/ships\/[^/]+\/position$/.test(request.path)) {
    return POSITION_ERROR;
  }
  if (/^\/api\/ships\/[^/]+\/remote-control$/.test(request.path)) {
    return REMOTE_CONTROL_ERROR;
  }
  if (/^\/api\/ships\/[^/]+\/designation$/.test(request.path)) {
    return DESIGNATION_PAYLOAD_ERROR;
  }
  return "Invalid JSON request body.";
}

export function createApp(ships, generateShipId = randomUUID) {
  const app = express();
  app.use(express.json({
    limit: "100kb",
    type: (request) => !request.is("application/x-www-form-urlencoded"),
  }));
  app.use(express.urlencoded({ extended: false, limit: "100kb" }));
  app.use(methodOverride(
    (request) => request.body?._method ?? request.query?._method,
    { methods: ["GET", "POST"] },
  ));

  app.param("id", (request, response, next, value) => {
    if (!UUID_PATTERN.test(value)) {
      return response.status(404).json({ error: "Ship not found." });
    }
    request.shipId = value.toLowerCase();
    return next();
  });

  app.get("/healthz", (_request, response) => {
    response.json({ status: "ok" });
  });

  app.get("/api/ships", (_request, response) => {
    response.json(ships.getAll());
  });

  app.post("/api/ships", (request, response) => {
    const payload = jsonObject(request.body);
    if (payload === null || !isValidPosition(payload)) {
      return badRequest(response, POSITION_ERROR);
    }

    let result;
    try {
      result = ships.createShip(generateShipId(), payload);
    } catch (error) {
      if (error.code === "SQLITE_CONSTRAINT_PRIMARYKEY") {
        return response.status(409).json({ error: "Ship ID conflict." });
      }
      throw error;
    }

    return response
      .status(result.created ? 201 : 200)
      .location(`/api/ships/${result.ship.id}`)
      .json(result.ship);
  });

  app.get("/api/ships/:id", (request, response) => {
    const ship = ships.getShip(request.shipId);
    return ship === null
      ? response.status(404).json({ error: "Ship not found." })
      : response.json(ship);
  });

  app.post("/api/ships/:id/position", (request, response) => {
    const payload = jsonObject(request.body);
    if (payload === null || !isValidPosition(payload)) {
      return badRequest(response, POSITION_ERROR);
    }
    const ship = ships.recordPosition(request.shipId, payload);
    return ship === null
      ? response.status(404).json({ error: "Ship not found." })
      : response.json(ship);
  });

  app.get("/api/ships/:id/control", (request, response) => {
    const control = ships.getControl(request.shipId);
    return control === null
      ? response.status(404).json({ error: "Ship not found." })
      : response.json(control);
  });

  app.put("/api/ships/:id/remote-control", (request, response) => {
    const payload = mutationPayload(request);
    if (payload === null || typeof payload.enabled !== "boolean") {
      return badRequest(response, REMOTE_CONTROL_ERROR);
    }

    const control = ships.setRemoteControl(request.shipId, payload.enabled);
    return control === null
      ? response.status(404).json({ error: "Ship not found." })
      : response.json(control);
  });

  app.put("/api/ships/:id/designation", (request, response) => {
    const payload = mutationPayload(request);
    if (payload === null) {
      return badRequest(response, DESIGNATION_PAYLOAD_ERROR);
    }

    const heading = numberInRange(payload, "heading", 0, 360);
    const speedKnots = numberInRange(payload, "speedKnots", 0, 40);
    if (heading === null || heading >= 360 || speedKnots === null) {
      return badRequest(response, DESIGNATION_RANGE_ERROR);
    }

    const control = ships.setDesignation(request.shipId, heading, speedKnots);
    return control === null
      ? response.status(404).json({ error: "Ship not found." })
      : response.json(control);
  });

  app.delete("/api/ships/:id/designation", (request, response) => {
    const control = ships.clearDesignation(request.shipId);
    return control === null
      ? response.status(404).json({ error: "Ship not found." })
      : response.json(control);
  });

  app.use((error, request, response, _next) => {
    if (error.type === "entity.parse.failed") {
      return badRequest(response, invalidJsonMessage(request));
    }
    if (error.type === "entity.too.large") {
      return response.status(413).json({ error: "Request body too large." });
    }
    console.error("Unhandled API error:", error);
    return response.status(500).json({ error: "Internal server error." });
  });

  return app;
}

function startServer() {
  const databasePath = process.env.DATABASE_PATH ?? "./data/ships.sqlite";
  const port = Number(process.env.PORT ?? 80);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error("PORT must be an integer between 1 and 65535.");
  }

  const ships = new ShipStore(databasePath);
  const server = createApp(ships).listen(port, "0.0.0.0", () => {
    console.log(`Controller API listening on port ${port}`);
  });

  const shutdown = () => {
    server.close(() => {
      ships.close();
      process.exit(0);
    });
  };
  process.once("SIGINT", shutdown);
  process.once("SIGTERM", shutdown);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  startServer();
}