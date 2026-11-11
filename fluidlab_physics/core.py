"""Shared SI result contracts and validation; no API dependencies."""
from dataclasses import dataclass
from math import isfinite
from typing import Mapping

STANDARD_GRAVITY = 9.80665  # Conventional standard gravity, m/s².

class PhysicalInputError(ValueError):
    """Input violates the supported physical model."""

class NumericalError(ArithmeticError):
    """A finite, converged numerical result could not be obtained."""

@dataclass(frozen=True)
class Quantity:
    """An SI quantity; None denotes an explicitly undefined result."""
    value: float | None
    unit: str

@dataclass(frozen=True)
class Result:
    """Calculation outputs, model provenance and applicability notices."""
    values: Mapping[str, Quantity]
    equations: tuple[str, ...]
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    status: str = "valid"

def check(name: str, value: float, *, positive: bool = False,
          nonnegative: bool = False) -> float:
    """Reject booleans, nonnumeric, nonfinite and out-of-domain inputs."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PhysicalInputError(f"{name} must be a finite number in SI units")
    if not isfinite(value) or (positive and value <= 0) or (nonnegative and value < 0):
        raise PhysicalInputError(f"Invalid {name}: {value}")
    return value

def result(values: dict[str, tuple[float | None, str]], equations: tuple[str, ...],
           assumptions: tuple[str, ...], warnings: tuple[str, ...] = (),
           status: str = "valid") -> Result:
    """Build a result without hiding overflow, NaN or infinity."""
    for name, (value, _) in values.items():
        if value is not None and not isfinite(value):
            raise NumericalError(f"Nonfinite calculated {name}")
    return Result({k: Quantity(*v) for k, v in values.items()}, equations,
                  assumptions, warnings, status)

def absolute_pressure(value: float, basis: str, reference: float) -> float:
    """Convert gauge/absolute pressure to positive absolute pressure (Pa)."""
    check("pressure", value)
    check("reference_pressure", reference, positive=True)
    if basis not in ("absolute", "gauge"):
        raise PhysicalInputError("pressure_basis must be absolute or gauge")
    absolute = value + reference if basis == "gauge" else value
    check("absolute_pressure", absolute, positive=True)
    return absolute
