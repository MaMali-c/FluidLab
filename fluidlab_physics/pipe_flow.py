"""Darcy (not Fanning) friction for full circular Newtonian-liquid pipes."""
from math import pi, log10
from .core import Result, PhysicalInputError, NumericalError, STANDARD_GRAVITY, check, result

def reynolds_number(velocity: float, diameter: float, density: float, viscosity: float) -> Result:
    """Reynolds number using speed and dynamic viscosity [Pa*s]."""
    check("velocity", velocity)
    for name, value in (("diameter", diameter), ("density", density), ("viscosity", viscosity)):
        check(name, value, positive=True)
    return result({"reynolds": (density*abs(velocity)*diameter/viscosity, "1")},
                  ("Re = rho*abs(V)*D/mu",), ("Newtonian fluid; circular pipe.",))

def friction_factor(reynolds: float, relative_roughness: float = 0.0) -> Result:
    """Darcy friction factor. Transitional predictions are explicitly withheld.

    Supported turbulent envelope: 4000 <= Re <= 1e8, 0 <= epsilon/D <= .05.
    Colebrook is solved for x=1/sqrt(f) by bracketed bisection, tolerance 1e-12
    in its dimensionless residual. Bracket [1,100] covers this envelope.
    """
    check("reynolds", reynolds, nonnegative=True)
    check("relative_roughness", relative_roughness, nonnegative=True)
    if relative_roughness > .05:
        raise PhysicalInputError("Relative roughness exceeds supported envelope 0.05")
    assumptions = ("Fully developed circular-pipe flow; Darcy friction factor.",)
    if reynolds == 0:
        return result({"friction_factor": (None, "1")}, (), assumptions,
                      ("At rest friction factor is undefined; losses are zero.",), "at_rest")
    if reynolds < 2000:
        return result({"friction_factor": (64/reynolds, "1")}, ("f_D = 64/Re",), assumptions)
    if reynolds < 4000:
        return result({"friction_factor": (None, "1")}, (), assumptions,
                      ("Transitional flow: no definitive friction prediction.",), "transitional_not_predicted")
    if reynolds > 1e8:
        raise PhysicalInputError("Re exceeds supported turbulent envelope 1e8")
    def residual(x: float) -> float:
        return x+2*log10(relative_roughness/3.7+2.51*x/reynolds)
    low, high = 1.0, 100.0
    if residual(low)*residual(high) >= 0:
        raise NumericalError("Colebrook root is not bracketed")
    for iteration in range(1, 101):
        x = (low+high)/2
        error = residual(x)
        if abs(error) <= 1e-12:
            return result({"friction_factor": (1/x**2, "1"), "residual": (error, "1"),
                           "iterations": (iteration, "1")},
                          ("1/sqrt(f_D) = -2*log10(epsilon/(3.7D)+2.51/(Re*sqrt(f_D)))",), assumptions)
        if error > 0:
            high = x
        else:
            low = x
    raise NumericalError("Colebrook did not converge in 100 bisection iterations")

def pipe_loss(flow_rate: float, diameter: float, length: float, density: float,
              viscosity: float, roughness: float = 0.0, minor_loss_coefficient: float = 0.0,
              gravity: float = STANDARD_GRAVITY) -> Result:
    """Loss magnitudes for directed nonnegative Q [m³/s]; K uses pipe velocity.

    Pressure loss is rho*g*hL, not a general endpoint pressure difference.
    """
    for name, value in (("flow_rate", flow_rate), ("length", length), ("roughness", roughness),
                        ("minor_loss_coefficient", minor_loss_coefficient)):
        check(name, value, nonnegative=True)
    check("diameter", diameter, positive=True)
    check("gravity", gravity, positive=True)
    velocity = flow_rate/(pi*diameter**2/4)
    re = reynolds_number(velocity, diameter, density, viscosity).values["reynolds"].value
    friction = friction_factor(re, roughness/diameter)
    f = friction.values["friction_factor"].value
    minor = minor_loss_coefficient*velocity**2/(2*gravity)
    major = 0.0 if flow_rate == 0 or length == 0 else (None if f is None else f*length/diameter*velocity**2/(2*gravity))
    total = None if major is None else major+minor
    return result({"velocity": (velocity, "m/s"), "reynolds": (re, "1"),
                   "friction_factor": (f, "1"), "major_head_loss": (major, "m"),
                   "minor_head_loss": (minor, "m"), "total_head_loss": (total, "m"),
                   "pressure_loss": (None if total is None else density*gravity*total, "Pa")},
                  friction.equations+("V = 4Q/(pi*D²)", "Re = rho*V*D/mu", "h_f = f_D*(L/D)*V²/(2g)",
                                      "h_m = K*V²/(2g)", "delta_p_loss = rho*g*(h_f+h_m)"),
                  friction.assumptions+("Steady incompressible single-phase liquid; supplied K referenced to this pipe velocity.",
                                       "Entrance effects excluded; pressure loss excludes elevation and velocity-head changes."),
                  friction.warnings, friction.status)
