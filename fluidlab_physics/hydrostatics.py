"""Constant-density hydrostatic pressure and rectangular plane loading."""
from math import sin, pi
from .core import Result, PhysicalInputError, STANDARD_GRAVITY, check, result, absolute_pressure

def hydrostatic_pressure(depth: float, density: float, surface_pressure: float, *,
                         pressure_basis: str, reference_pressure: float,
                         gravity: float = STANDARD_GRAVITY) -> Result:
    """Pressure at nonnegative depth [m] below a static free surface."""
    check("depth", depth, nonnegative=True)
    check("density", density, positive=True)
    check("gravity", gravity, positive=True)
    p = absolute_pressure(surface_pressure, pressure_basis, reference_pressure) + density*gravity*depth
    return result({"pressure_absolute": (p, "Pa"), "pressure_gauge": (p-reference_pressure, "Pa")},
                  ("p_abs = p_surface_abs + rho*g*h",), ("Static homogeneous fluid; uniform gravity.",))

def rectangular_surface_force(width: float, length: float, top_depth: float,
                              density: float, *, angle: float = pi/2,
                              surface_pressure_absolute: float,
                              opposing_pressure_absolute: float,
                              gravity: float = STANDARD_GRAVITY) -> Result:
    """Net load on wetted rectangle. Angle [rad] is measured from horizontal.

    Length runs downward along the plane from top_depth (which may be negative).
    Dry-area loads are excluded. Opposing pressure is uniform. Resultant distance
    and moment are measured from the original top edge, not the wetted edge.
    """
    for name, value in (("width", width), ("length", length), ("density", density),
                        ("gravity", gravity), ("surface_pressure_absolute", surface_pressure_absolute),
                        ("opposing_pressure_absolute", opposing_pressure_absolute)):
        check(name, value, positive=True)
    check("top_depth", top_depth)
    check("angle", angle)
    if not 0 <= angle <= pi/2:
        raise PhysicalInputError("angle must be in [0, pi/2]")
    slope = sin(angle)
    start = min(length, max(0.0, -top_depth/slope)) if slope else (length if top_depth < 0 else 0.0)
    wet = length-start
    center = start+wet/2
    pressure_center = surface_pressure_absolute-opposing_pressure_absolute+density*gravity*(top_depth+slope*center)
    force = width*wet*pressure_center
    moment = force*center + width*density*gravity*slope*wet**3/12
    location = moment/force if force else None
    warnings = ("Zero resultant: center of pressure undefined; inspect moment.",) if force == 0 else ()
    return result({"wetted_area": (width*wet, "m^2"), "force": (force, "N"),
                   "moment_top_edge": (moment, "N*m"), "resultant_distance": (location, "m")},
                  ("delta_p(s) = p_surface-p_opposing+rho*g*(h_top+s*sin(theta))",
                   "F = integral_wet delta_p dA", "M = integral_wet s*delta_p dA", "s_R = M/F"),
                  ("Static homogeneous liquid; plane rectangle; uniform opposing pressure.",
                   "Positive force acts from liquid toward opposing side; only wetted area included."), warnings)
