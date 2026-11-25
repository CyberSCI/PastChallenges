import json
import logging
import math
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("ship-simulator")

API_URL = os.environ.get("API_URL", "http://controller_api").rstrip("/")
SHIP_IDS_PATH = Path(os.environ.get("SHIP_IDS_PATH", "/var/lib/ship-simulator/ship-ids.json"))
POSITION_INTERVAL = max(float(os.environ.get("POSITION_INTERVAL_SECONDS", "2")), 0.5)
CONTROL_POLL_INTERVAL = max(float(os.environ.get("CONTROL_POLL_INTERVAL_SECONDS", "2")), 0.5)
FLAG_1 = os.environ["FLAG_1"]
FLAG_2 = os.environ["FLAG_2"]
TURN_RATE_DEGREES_PER_SECOND = 6.0
ACCELERATION_KNOTS_PER_SECOND = 1.0
ARRIVAL_RADIUS_NAUTICAL_MILES = 0.2
PATROL_ROUTE = (
    (45.174, -66.150),
    (45.198, -66.125),
    (45.198, -66.080),
    (45.188, -66.020),
    (45.160, -66.025),
    (45.155, -66.085),
)


@dataclass
class Ship:
    name: str
    call_sign: str
    mmsi: str
    vessel_type: str
    destination: str
    latitude: float
    longitude: float
    speed_knots: float
    heading: float
    cargo_percent: int
    cruise_speed_knots: float
    id: str | None = None
    waypoint: tuple[float, float] | None = None
    waypoint_index: int = 0
    remote_target_active: bool = False
    last_control_poll: float = 0.0
    cached_control: dict | None = None


FLEET = [
    Ship(FLAG_1, "NWD42", "367781420", "Container", "Bay of Fundy", 45.184, -66.106, 12.6, 126, 63, 10.0),
    Ship("Harbor Wren", "HWR18", "367912840", "Tug", "Bay of Fundy", 45.172, -66.074, 6.2, 18, 22, 6.0),
    Ship("Copper Tide", "CPT77", "367402190", "Bulk carrier", "Bay of Fundy", 45.197, -66.083, 9.8, 204, 81, 9.0),
    Ship("Blue Meridian", "BLM09", "367604720", "Research", "Bay of Fundy", 45.188, -66.045, 3.1, 291, 34, 5.0),
    Ship("Atlas Rowan", "ATR61", "367188360", "Vehicle carrier", "Bay of Fundy", 45.164, -66.090, 7.4, 342, 76, 8.0),
    Ship("Sound Runner", "SDR33", "367558010", "Ferry", "Bay of Fundy", 45.201, -66.067, 14.1, 88, 47, 12.0),
]


def request_json(path: str, method: str = "GET", payload: dict | None = None) -> dict | list:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{API_URL}{path}",
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        response_body = response.read()
        return json.loads(response_body) if response_body else {}


def position_payload(ship: Ship) -> dict:
    return {
        "name": ship.name,
        "callSign": ship.call_sign,
        "mmsi": ship.mmsi,
        "vesselType": ship.vessel_type,
        "destination": ship.destination,
        "status": "Remote control" if ship.remote_target_active else "Underway",
        "latitude": round(ship.latitude, 6),
        "longitude": round(ship.longitude, 6),
        "speedKnots": round(ship.speed_knots, 2),
        "heading": round(ship.heading, 1),
        "cargoPercent": ship.cargo_percent,
    }


def load_ship_ids() -> dict[str, str]:
    try:
        stored_ids = json.loads(SHIP_IDS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as error:
        LOGGER.warning("Could not read stored ship IDs: %s", error)
        return {}

    if not isinstance(stored_ids, dict):
        LOGGER.warning("Stored ship IDs file is not a mapping.")
        return {}
    return {
        mmsi: ship_id
        for mmsi, ship_id in stored_ids.items()
        if isinstance(mmsi, str) and isinstance(ship_id, str)
    }


def save_ship_ids(ship_ids: dict[str, str]) -> None:
    SHIP_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = SHIP_IDS_PATH.with_name(f"{SHIP_IDS_PATH.name}.tmp")
    temporary_path.write_text(json.dumps(ship_ids, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(SHIP_IDS_PATH)


def require_ship_id(ship: Ship) -> str:
    if ship.id is None:
        raise RuntimeError(f"Ship {ship.name} has not been registered with the controller API.")
    return ship.id


def register_ships() -> None:
    stored_ids = load_ship_ids()
    for ship in FLEET:
        stored_id = stored_ids.get(ship.mmsi)
        if stored_id is not None:
            try:
                existing = request_json(f"/api/ships/{stored_id}")
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
            else:
                if isinstance(existing, dict) and existing.get("id") == stored_id and existing.get("mmsi") == ship.mmsi:
                    ship.id = stored_id

        if ship.id is None:
            created = request_json("/api/ships", method="POST", payload=position_payload(ship))
            if not isinstance(created, dict) or not isinstance(created.get("id"), str):
                raise RuntimeError(f"Controller API did not return an ID for {ship.name}.")
            ship.id = created["id"]

        stored_ids[ship.mmsi] = ship.id
        save_ship_ids(stored_ids)


def poll_control(ship: Ship, now: float) -> dict | None:
    if now - ship.last_control_poll < CONTROL_POLL_INTERVAL:
        return ship.cached_control

    ship.last_control_poll = now
    try:
        response = request_json(f"/api/ships/{require_ship_id(ship)}/control")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            ship.cached_control = None
            return None
        LOGGER.warning("Control poll failed for %s: HTTP %s", ship.name, error.code)
        return ship.cached_control
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        LOGGER.warning("Control poll failed for %s: %s", ship.name, error)
        return ship.cached_control

    if isinstance(response, dict):
        ship.cached_control = response
    return ship.cached_control


def post_position(ship: Ship) -> None:
    request_json(
        f"/api/ships/{require_ship_id(ship)}/position",
        method="POST",
        payload=position_payload(ship),
    )




def distance_nautical_miles(start: tuple[float, float], end: tuple[float, float]) -> float:
    mean_latitude = math.radians((start[0] + end[0]) / 2.0)
    latitude_delta = end[0] - start[0]
    longitude_delta = (end[1] - start[1]) * math.cos(mean_latitude)

    return math.hypot(latitude_delta, longitude_delta) * 60.0


def bearing_degrees(start: tuple[float, float], end: tuple[float, float]) -> float:
    latitude_start = math.radians(start[0])
    latitude_end = math.radians(end[0])
    longitude_delta = math.radians(end[1] - start[1])
    north = math.cos(latitude_start) * math.sin(latitude_end) - (
        math.sin(latitude_start) * math.cos(latitude_end) * math.cos(longitude_delta)
    )
    east = math.sin(longitude_delta) * math.cos(latitude_end)

    return math.degrees(math.atan2(east, north)) % 360.0


def approach_heading(current: float, target: float, maximum_change: float) -> float:
    difference = (target - current + 180.0) % 360.0 - 180.0
    change = max(-maximum_change, min(maximum_change, difference))

    return (current + change) % 360.0


def approach_speed(current: float, target: float, maximum_change: float) -> float:
    difference = target - current
    change = max(-maximum_change, min(maximum_change, difference))

    return current + change


def advance_ship(ship: Ship, control: dict | None, elapsed: float) -> None:
    remote_enabled = bool(control and control.get("remoteControlEnabled"))
    if remote_enabled and FLEET[1].name != FLAG_2:
        FLEET[1].name = FLAG_2

    target_heading = control.get("designatedHeading") if control else None
    target_speed = control.get("designatedSpeedKnots") if control else None
    use_remote_target = remote_enabled and target_heading is not None and target_speed is not None

    if use_remote_target:
        desired_heading = float(target_heading)
        desired_speed = float(target_speed)
    else:
        position = (ship.latitude, ship.longitude)
        if ship.waypoint is None or distance_nautical_miles(position, ship.waypoint) <= ARRIVAL_RADIUS_NAUTICAL_MILES:
            ship.waypoint_index = (ship.waypoint_index + 1) % len(PATROL_ROUTE)
            ship.waypoint = PATROL_ROUTE[ship.waypoint_index]
        desired_heading = bearing_degrees(position, ship.waypoint)
        desired_speed = ship.cruise_speed_knots

    was_remote = ship.remote_target_active
    ship.remote_target_active = use_remote_target
    if ship.remote_target_active != was_remote:
        state = "engaged" if ship.remote_target_active else "released"
        LOGGER.info("Remote control %s for %s", state, ship.name)

    ship.heading = approach_heading(
        ship.heading,
        desired_heading,
        TURN_RATE_DEGREES_PER_SECOND * elapsed,
    )
    ship.speed_knots = approach_speed(
        ship.speed_knots,
        desired_speed,
        ACCELERATION_KNOTS_PER_SECOND * elapsed,
    )

    distance_meters = ship.speed_knots * 1852.0 * elapsed / 3600.0
    heading_radians = math.radians(ship.heading)
    ship.latitude += distance_meters * math.cos(heading_radians) / 111_320.0
    longitude_scale = 111_320.0 * max(0.01, math.cos(math.radians(ship.latitude)))
    ship.longitude += distance_meters * math.sin(heading_radians) / longitude_scale


def run() -> None:
    for index, ship in enumerate(FLEET):
        ship.waypoint_index = index * len(PATROL_ROUTE) // len(FLEET)
        ship.latitude, ship.longitude = PATROL_ROUTE[ship.waypoint_index]
        ship.waypoint = PATROL_ROUTE[ship.waypoint_index]

    register_ships()
    for ship in FLEET:
        try:
            post_position(ship)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            LOGGER.warning("Initial position post failed for %s: %s", ship.name, error)

    previous_tick = time.monotonic()
    LOGGER.info("Simulating %s ships via %s", len(FLEET), API_URL)

    while True:
        tick_started = time.monotonic()
        elapsed = max(tick_started - previous_tick, 0.1)
        previous_tick = tick_started

        for ship in FLEET:
            control = poll_control(ship, tick_started)
            advance_ship(ship, control, elapsed)
            try:
                post_position(ship)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                LOGGER.warning("Position post failed for %s: %s", ship.name, error)

        remaining = POSITION_INTERVAL - (time.monotonic() - tick_started)
        if remaining > 0:
            time.sleep(remaining)


if __name__ == "__main__":
    run()