import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import Database from "better-sqlite3";

function formatShip(row) {
  return {
    id: row.id,
    name: row.name,
    callSign: row.call_sign,
    mmsi: row.mmsi,
    vesselType: row.vessel_type,
    destination: row.destination,
    status: row.status,
    latitude: Number(row.latitude),
    longitude: Number(row.longitude),
    speedKnots: Number(row.speed_knots),
    heading: Number(row.heading),
    cargoPercent: Number(row.cargo_percent),
    updatedAt: row.updated_at,
    remoteControlEnabled: Boolean(row.remote_control_enabled),
    designatedHeading: row.designated_heading === null ? null : Number(row.designated_heading),
    designatedSpeedKnots: row.designated_speed_knots === null
      ? null
      : Number(row.designated_speed_knots),
  };
}

function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00");
}

function positionValues(id, position) {
  return {
    id,
    name: position.name,
    call_sign: position.callSign,
    mmsi: position.mmsi,
    vessel_type: position.vesselType,
    destination: position.destination,
    status: position.status,
    latitude: position.latitude,
    longitude: position.longitude,
    speed_knots: position.speedKnots,
    heading: position.heading,
    cargo_percent: position.cargoPercent,
    updated_at: utcTimestamp(),
  };
}

export class ShipStore {
  constructor(databasePath) {
    if (databasePath !== ":memory:") {
      mkdirSync(dirname(resolve(databasePath)), { recursive: true });
    }

    this.database = new Database(databasePath);
    this.database.pragma("busy_timeout = 5000");
    this.database.pragma("journal_mode = WAL");
    this.database.exec(`
      CREATE TABLE IF NOT EXISTS ships (
        id TEXT NOT NULL PRIMARY KEY,
        name TEXT NOT NULL,
        call_sign TEXT NOT NULL,
        mmsi TEXT NOT NULL UNIQUE,
        vessel_type TEXT NOT NULL,
        destination TEXT NOT NULL,
        status TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        speed_knots REAL NOT NULL,
        heading REAL NOT NULL,
        cargo_percent INTEGER NOT NULL,
        updated_at TEXT NOT NULL,
        remote_control_enabled INTEGER NOT NULL DEFAULT 0,
        designated_heading REAL DEFAULT NULL,
        designated_speed_knots REAL DEFAULT NULL
      )
    `);
  }

  getAll() {
    return this.database.prepare("SELECT * FROM ships ORDER BY id").all().map(formatShip);
  }

  getShip(id) {
    const row = this.database.prepare("SELECT * FROM ships WHERE id = ?").get(id);
    return row === undefined ? null : formatShip(row);
  }

  getControl(id) {
    const ship = this.getShip(id);
    if (ship === null) {
      return null;
    }

    return {
      id: ship.id,
      remoteControlEnabled: ship.remoteControlEnabled,
      designatedHeading: ship.designatedHeading,
      designatedSpeedKnots: ship.designatedSpeedKnots,
    };
  }

  createShip(id, position) {
    const insertion = this.database.prepare(`
      INSERT INTO ships (
        id, name, call_sign, mmsi, vessel_type, destination, status,
        latitude, longitude, speed_knots, heading, cargo_percent, updated_at
      ) VALUES (
        @id, @name, @call_sign, @mmsi, @vessel_type, @destination, @status,
        @latitude, @longitude, @speed_knots, @heading, @cargo_percent, @updated_at
      )
      ON CONFLICT(mmsi) DO NOTHING
    `).run(positionValues(id, position));

    const row = this.database.prepare(
      "SELECT * FROM ships WHERE mmsi = ?",
    ).get(position.mmsi);
    return {
      created: insertion.changes === 1,
      ship: formatShip(row),
    };
  }

  recordPosition(id, position) {
    this.database.prepare(`
      UPDATE ships SET
        name = @name,
        call_sign = @call_sign,
        mmsi = @mmsi,
        vessel_type = @vessel_type,
        destination = @destination,
        status = @status,
        latitude = @latitude,
        longitude = @longitude,
        speed_knots = @speed_knots,
        heading = @heading,
        cargo_percent = @cargo_percent,
        updated_at = @updated_at
      WHERE id = @id
    `).run(positionValues(id, position));

    return this.getShip(id);
  }

  setRemoteControl(id, enabled) {
    this.database.prepare(
      "UPDATE ships SET remote_control_enabled = ? WHERE id = ?",
    ).run(Number(enabled), id);
    return this.getControl(id);
  }

  setDesignation(id, heading, speedKnots) {
    this.database.prepare(`
      UPDATE ships
      SET designated_heading = ?, designated_speed_knots = ?
      WHERE id = ?
    `).run(heading, speedKnots, id);
    return this.getControl(id);
  }

  clearDesignation(id) {
    this.database.prepare(`
      UPDATE ships
      SET designated_heading = NULL, designated_speed_knots = NULL
      WHERE id = ?
    `).run(id);
    return this.getControl(id);
  }

  close() {
    this.database.close();
  }
}