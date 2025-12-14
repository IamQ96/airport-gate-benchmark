from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Any

import yaml

from src.core.types import Gate


@dataclass(frozen=True)
class TurnaroundConfig:
    buffer_minutes: int
    default_turnaround_minutes: Dict[str, int]  # keys: "S","M","L"


@dataclass(frozen=True)
class AirportConfig:
    airport_code: str
    airport_name: str
    timezone: str
    resolution_minutes: int
    turnaround: TurnaroundConfig
    gates: List[Gate]
    model_id: str  # citeable identifier like "WAW-RS-6G-v1"


class ConfigError(ValueError):
    """Raised when the YAML configuration is invalid."""


def _require(d: Dict[str, Any], key: str, ctx: str) -> Any:
    if key not in d:
        raise ConfigError(f"Missing key '{key}' in {ctx}")
    return d[key]


def load_airport_config(path: str | Path) -> AirportConfig:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # --- Parse top-level sections
    airport = _require(cfg, "airport", "root")
    time = _require(cfg, "time", "root")
    turnaround = _require(cfg, "turnaround", "root")
    gates = _require(cfg, "gates", "root")
    export = _require(cfg, "export", "root")

    airport_code = str(_require(airport, "code", "airport")).strip()
    airport_name = str(_require(airport, "name", "airport")).strip()
    timezone = str(_require(time, "timezone", "time")).strip()
    resolution = int(_require(time, "resolution_minutes", "time"))

    buffer_minutes = int(_require(turnaround, "buffer_minutes", "turnaround"))
    default_ta = _require(turnaround, "default_turnaround_minutes", "turnaround")

    model_id = str(_require(export, "recommended_id", "export")).strip()

    # --- Validate aircraft class keys
    allowed_classes = {"S", "M", "L"}
    if set(default_ta.keys()) - allowed_classes:
        raise ConfigError(
            f"default_turnaround_minutes has invalid keys: {set(default_ta.keys()) - allowed_classes}. "
            f"Allowed: {sorted(allowed_classes)}"
        )

    # --- Parse gates
    parsed_gates: List[Gate] = []
    gate_ids: set[str] = set()

    for i, g in enumerate(gates):
        ctx = f"gates[{i}]"
        gate_id = str(_require(g, "gate_id", ctx)).strip()
        if gate_id in gate_ids:
            raise ConfigError(f"Duplicate gate_id '{gate_id}' in {ctx}")
        gate_ids.add(gate_id)

        compat = _require(g, "compatible_classes", ctx)
        if not isinstance(compat, list) or len(compat) == 0:
            raise ConfigError(f"{ctx}.compatible_classes must be a non-empty list")

        compat_set = {str(c).strip() for c in compat}
        if not compat_set.issubset(allowed_classes):
            raise ConfigError(
                f"{ctx}.compatible_classes contains invalid classes: {sorted(compat_set - allowed_classes)}"
            )

        walk_cost = float(_require(g, "walk_cost", ctx))
        parsed_gates.append(Gate(gate_id=gate_id, compatible_classes=sorted(compat_set), walk_cost=walk_cost))

    if resolution <= 0:
        raise ConfigError("time.resolution_minutes must be > 0")
    if buffer_minutes < 0:
        raise ConfigError("turnaround.buffer_minutes must be >= 0")
    if len(parsed_gates) == 0:
        raise ConfigError("At least one gate must be defined")

    ta_cfg = TurnaroundConfig(buffer_minutes=buffer_minutes, default_turnaround_minutes={k: int(v) for k, v in default_ta.items()})

    return AirportConfig(
        airport_code=airport_code,
        airport_name=airport_name,
        timezone=timezone,
        resolution_minutes=resolution,
        turnaround=ta_cfg,
        gates=parsed_gates,
        model_id=model_id,
    )
