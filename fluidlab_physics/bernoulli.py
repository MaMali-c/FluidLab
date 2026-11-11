"""Steady incompressible continuity and two-station energy balances."""
from .core import Result, PhysicalInputError, STANDARD_GRAVITY, check, result, absolute_pressure

def continuity(flow_rate: float, area: float) -> Result:
    """Return mean velocity for nonnegative directed flow Q [m³/s], A [m²]."""
    check("flow_rate", flow_rate, nonnegative=True)
    check("area", area, positive=True)
    return result({"velocity": (flow_rate / area, "m/s")}, ("V = Q/A",),
                  ("Steady incompressible flow; section-mean velocity.",))

def bernoulli(flow_rate: float, area1: float, area2: float, pressure1: float,
              elevation1: float, elevation2: float, density: float, *,
              pressure_basis: str, reference_pressure: float,
              mode: str = "ideal", loss_head: float = 0.0,
              pump_head: float = 0.0, turbine_head: float = 0.0,
              alpha1: float = 1.0, alpha2: float = 1.0,
              gravity: float = STANDARD_GRAVITY,
              vapor_pressure: float | None = None) -> Result:
    """Solve downstream pressure. All inputs SI; heads/elevations in metres.

    Ideal mode uses uniform section velocities and prohibits loss/machine heads.
    Energy mode accepts explicit heads; it does not infer friction or pump curves.
    """
    for name, value in (("density", density), ("gravity", gravity)):
        check(name, value, positive=True)
    for name, value in (("elevation1", elevation1), ("elevation2", elevation2)):
        check(name, value)
    for name, value in (("loss_head", loss_head), ("pump_head", pump_head),
                        ("turbine_head", turbine_head), ("alpha1", alpha1), ("alpha2", alpha2)):
        check(name, value, nonnegative=True)
    if alpha1 < 1 or alpha2 < 1:
        raise PhysicalInputError("Kinetic energy correction factors must be >= 1")
    if mode not in ("ideal", "energy"):
        raise PhysicalInputError("mode must be ideal or energy")
    if mode == "ideal" and (loss_head or pump_head or turbine_head or alpha1 != 1 or alpha2 != 1):
        raise PhysicalInputError("Ideal mode requires zero losses/machine heads and alpha=1")
    v1 = continuity(flow_rate, area1).values["velocity"].value
    v2 = continuity(flow_rate, area2).values["velocity"].value
    p1 = absolute_pressure(pressure1, pressure_basis, reference_pressure)
    p2 = p1 + density * gravity * (elevation1 - elevation2 + pump_head - turbine_head - loss_head) + density * (alpha1*v1*v1-alpha2*v2*v2)/2
    check("calculated_absolute_pressure2", p2, positive=True)
    warnings = ()
    if vapor_pressure is None:
        warnings = ("Cavitation not checked: vapor pressure unavailable.",)
    else:
        check("vapor_pressure", vapor_pressure, positive=True)
        if min(p1, p2) <= vapor_pressure:
            raise PhysicalInputError("Station pressure at/below vapor pressure: single-phase model invalid")
        warnings = ("Cavitation checked only at stations; interior pressure is unresolved.",)
    return result({"velocity1": (v1, "m/s"), "velocity2": (v2, "m/s"),
                   "pressure2_absolute": (p2, "Pa"),
                   "pressure2_gauge": (p2-reference_pressure, "Pa")},
                  ("Q = A1 V1 = A2 V2", "p1/(rho*g)+alpha1*V1²/(2g)+z1+hp = p2/(rho*g)+alpha2*V2²/(2g)+z2+ht+hL"),
                  ("Steady constant-density single-phase flow.",
                   "Ideal: inviscid along a streamline, uniform section velocity." if mode == "ideal" else "Section-averaged energy balance with explicitly supplied heads and correction factors."), warnings)
