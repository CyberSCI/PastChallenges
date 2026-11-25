import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    flag_1: str = field(repr=False)
    flag_2: str = field(repr=False)
    flag_3: str = field(repr=False)
    public_origin: str
    session_ttl_seconds: int = 1800
    receipt_ttl_seconds: int = 900
    sweep_interval_seconds: int = 60
    max_sessions: int = 2000
    max_ws_per_session: int = 3
    max_ws_total: int = 500
    max_ws_message_bytes: int = 4096
    ws_idle_seconds: float = 300
    max_inflight_redeems_per_session: int = 4
    max_inflight_redeems_total: int = 100
    redeem_rate_per_minute: int = 20
    reset_cooldown_seconds: int = 2
    audit_delay_seconds: float = 0.15


def load_settings_from_env() -> Settings:
    names = ("DAMWATCH_FLAG_1", "DAMWATCH_FLAG_2", "DAMWATCH_FLAG_3")
    flags = []
    for name in names:
        value = os.environ.get(name, "").strip()
        if not value:
            raise ValueError(f"{name} is required")
        flags.append(value)
    if len(set(flags)) != 3:
        raise ValueError("DamWatch flags must be distinct")

    origin = os.environ.get("DAMWATCH_PUBLIC_ORIGIN", "").strip().rstrip("/")
    if not origin.startswith(("https://", "http://")):
        raise ValueError("DAMWATCH_PUBLIC_ORIGIN must be an HTTP(S) origin")
    return Settings(*flags, public_origin=origin)
