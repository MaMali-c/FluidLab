> Frontend and FastAPI adapter added: see [RUNNING.md](RUNNING.md) for application setup.
> The engine scope below describes the independent physics package.

# FluidLab physics engine

Standalone Python package; no frontend, 3D, API framework or network dependency.
Requires Python 3.10+. All arguments use SI; unit strings in results are metadata,
not automatic unit conversion. Callers must supply SI numbers.

Run tests from this directory:

```sh
python -m pip install -e '.[test]'
python -m pytest -q
```

Public functions are exported from `fluidlab_physics`. Each returns a typed Result
containing named Quantity values/units, equations, assumptions, warnings and status.
Undefined values are None with an explanatory status or warning. Invalid inputs raise
PhysicalInputError. Nonfinite outputs raise NumericalError; native floating-point
arithmetic exceptions are not swallowed. No rounding is applied internally.

## Equations and assumptions

- Continuity: V=Q/A, steady incompressible section-mean flow.
- Bernoulli: p1/(rho*g)+alpha1*V1²/(2g)+z1+hp =
  p2/(rho*g)+alpha2*V2²/(2g)+z2+ht+hL. Ideal mode requires alpha=1 and
  zero loss/pump/turbine heads; energy mode uses explicitly supplied heads.
- Pressure: p_abs=p_gauge+p_reference; hydrostatic p=p_surface+rho*g*h.
- Rectangle force: F=integral(delta_p dA); moment M=integral(s*delta_p dA);
  resultant distance=M/F. Integrates exactly over the wetted portion; uniform
  opposing pressure, static constant-density fluid, plane rectangle only.
- Reynolds: Re=rho*abs(V)*D/mu; circular Newtonian pipe.
- Darcy friction: f=64/Re for Re<2000; Colebrook for Re>=4000:
  1/sqrt(f)=-2log10(epsilon/(3.7D)+2.51/(Re*sqrt(f))). No transition prediction.
- Darcy-Weisbach: h_f=f*(L/D)*V²/(2g); h_m=K*V²/(2g);
  pressure loss=rho*g*(h_f+h_m). Fully developed full-pipe steady liquid flow;
  pressure loss is not automatically the endpoint pressure difference.
- Buoyancy: F_B=rho*g*V_displaced; W=mg; F_net=F_B-W.
  Equilibrium displacement=m/rho; prism draft=displacement/base_area.
  Rigid impermeable body; uniform static liquid; air buoyancy/contact/drag excluded.

## Explicit limits

No unit conversion/property database, inverse flow solver, series-pipe orchestration,
curved/circular surface integration, layered fluids, gas compressibility, cavitating
flow, non-Newtonian rheology, transient dynamics or CFD. Buoyancy gives equilibrium
volume for general bodies but draft only for upright constant-area prisms; no sphere
geometry or rotational stability. Exports are not implemented. The separate API/UI adapter exposes a subset of these functions.

Pressure basis and reference are required for pressure calculations. Bernoulli can
check station vapor pressure if supplied; internal cavitation is unresolved. Pipe
loss computes dissipative loss without boundary absolute pressures and therefore
cannot validate cavitation. No material properties are invented or inferred.

Finite validation cannot prevent every floating-point underflow for astronomically
small inputs. Native arithmetic failures propagate; applications should set their
own reviewed operating ranges. Zero resultant forces have no center of pressure;
near-zero signed resultant loads may have very large resultant distances. Neutral
buoyancy classification uses the supplied numbers exactly, without a hidden tolerance.

See REFERENCES.md for independent reference calculations and source provenance.
