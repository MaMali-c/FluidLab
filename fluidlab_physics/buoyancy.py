"""Archimedes force and fixed-orientation prismatic floating equilibrium."""
from .core import Result, PhysicalInputError, STANDARD_GRAVITY, check, result

def buoyancy(displaced_volume: float, body_volume: float, mass: float,
             fluid_density: float, gravity: float = STANDARD_GRAVITY) -> Result:
    """Prescribed immersion; volumes [m³], mass [kg], density [kg/m³]."""
    check("displaced_volume", displaced_volume, nonnegative=True)
    check("body_volume", body_volume, positive=True)
    check("mass", mass, nonnegative=True)
    check("fluid_density", fluid_density, positive=True)
    check("gravity", gravity, positive=True)
    if displaced_volume > body_volume:
        raise PhysicalInputError("Displacement exceeds body volume")
    force = fluid_density*gravity*displaced_volume
    weight = mass*gravity
    return result({"buoyant_force": (force, "N"), "weight": (weight, "N"),
                   "net_upward_force": (force-weight, "N")},
                  ("F_B = rho_f*g*V_displaced", "W = m*g", "F_net_up = F_B-W"),
                  ("Rigid impermeable body; homogeneous static liquid; uniform gravity.",
                   "Air buoyancy, capillarity, contact forces and drag excluded."))

def floating_equilibrium(body_volume: float, mass: float, fluid_density: float, *,
                         base_area: float | None = None,
                         gravity: float = STANDARD_GRAVITY) -> Result:
    """Find equilibrium displacement; optional upright prism base area gives draft.

    Neutral buoyancy does not determine depth; no rotational stability is implied.
    """
    full = buoyancy(body_volume, body_volume, mass, fluid_density, gravity)
    if base_area is not None:
        check("base_area", base_area, positive=True)
    required = mass/fluid_density
    if required > body_volume:
        status = "no_equilibrium"
        displacement = fraction = draft = None
        warnings = ("Weight exceeds maximum buoyancy; no free floating equilibrium or sinking speed predicted.",)
    elif required == body_volume:
        status = "neutral"
        displacement, fraction, draft = required, 1.0, None
        warnings = ("Neutral when fully submerged; vertical position is not unique.",)
    else:
        status = "floating"
        displacement, fraction = required, required/body_volume
        draft = None if base_area is None else required/base_area
        warnings = ("Massless zero-displacement limiting case.",) if mass == 0 else ()
    return result({"equilibrium_displacement": (displacement, "m^3"),
                   "submerged_fraction": (fraction, "1"), "draft": (draft, "m"),
                   "maximum_buoyant_force": (full.values["buoyant_force"].value, "N")},
                  ("V_equilibrium = m/rho_f", "fraction = V_equilibrium/V_body", "draft = V_equilibrium/A_base (upright prism only)"),
                  full.assumptions+("Fixed orientation; large tank with fixed free surface; rotational stability not assessed.",),
                  warnings, status)
