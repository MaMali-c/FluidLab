"""Independent reference derivations are recorded in REFERENCES.md."""
import math
import pytest
from fluidlab_physics import *

def value(r, key):
    return r.values[key].value

def energy(**changes):
    args = dict(flow_rate=.01, area1=.01, area2=.005, pressure1=100000,
                elevation1=0, elevation2=0, density=1000,
                pressure_basis="absolute", reference_pressure=100000)
    args.update(changes)
    return bernoulli(**args)

def plate(**changes):
    args = dict(width=1, length=2, top_depth=0, density=1000,
                surface_pressure_absolute=100000, opposing_pressure_absolute=100000)
    args.update(changes)
    return rectangular_surface_force(**args)

def test_continuity():
    assert value(continuity(.01,.005), "velocity") == 2
    assert value(continuity(0,1), "velocity") == 0

def test_bernoulli_reference_and_gauge():
    assert value(energy(), "pressure2_absolute") == 98500
    assert energy(pressure1=0, pressure_basis="gauge").values == energy().values

def test_energy_loss_and_static_limit():
    assert value(energy(mode="energy", loss_head=1), "pressure2_absolute") == pytest.approx(88693.35)
    assert value(energy(flow_rate=0, elevation2=1), "pressure2_absolute") == pytest.approx(90193.35)
    assert value(energy(mode="energy", pump_head=2, turbine_head=1, loss_head=1), "pressure2_absolute") == 98500

def test_hydrostatic_reference():
    r = hydrostatic_pressure(2,1000,0,pressure_basis="gauge",reference_pressure=100000)
    assert value(r,"pressure_gauge") == pytest.approx(19613.3)

def test_plate_reference():
    assert value(plate(),"force") == pytest.approx(19613.3)
    assert value(plate(),"resultant_distance") == pytest.approx(4/3)

def test_partial_and_horizontal_plate():
    assert value(plate(top_depth=-1),"force") == pytest.approx(4903.325)
    assert value(plate(top_depth=-1),"resultant_distance") == pytest.approx(5/3)
    assert value(plate(top_depth=1,angle=0),"resultant_distance") == 1

def test_dry_and_zero_force_couple():
    assert value(plate(top_depth=-3),"wetted_area") == 0
    r = plate(opposing_pressure_absolute=109806.65)
    assert value(r,"force") == pytest.approx(0,abs=1e-10)
    # Use exactly representable g to exercise exact zero resultant with a couple.
    r = plate(gravity=10, opposing_pressure_absolute=110000)
    assert value(r,"resultant_distance") is None
    assert value(r,"moment_top_edge") == pytest.approx(20000/3)

def test_reynolds_and_laminar():
    assert value(reynolds_number(-.01,.1,1000,.001),"reynolds") == 1000
    assert value(friction_factor(1000),"friction_factor") == .064
    q = math.pi*.1**2/4*.01
    r = pipe_loss(q,.1,10,1000,.001)
    # Hagen-Poiseuille, independently from Darcy: 128 mu L Q/(pi D^4).
    assert value(r,"pressure_loss") == pytest.approx(.32)

@pytest.mark.parametrize("re", [2000,3000,3999.99])
def test_transition(re):
    assert friction_factor(re).status == "transitional_not_predicted"
    assert value(friction_factor(re),"friction_factor") is None

def test_colebrook_constructed_exact_reference():
    # f=0.04 -> x=5. Choose Re=12550, making 2.51*x/Re=.001.
    # epsilon/D=3.7*(10^-2.5-.001), so the RHS is exactly 5.
    r = friction_factor(12550,3.7*(10**-2.5-.001))
    assert value(r,"friction_factor") == pytest.approx(.04,rel=1e-11)
    assert abs(value(r,"residual")) <= 1e-12

@pytest.mark.parametrize("re,rough", [(4000,0),(4000,.05),(1e8,0),(1e8,.05)])
def test_colebrook_envelope(re,rough):
    f = value(friction_factor(re,rough),"friction_factor")
    assert abs(1/math.sqrt(f)+2*math.log10(rough/3.7+2.51/(re*math.sqrt(f)))) < 1e-11

def test_rest_and_minor_loss():
    r = pipe_loss(0,.1,10,1000,.001)
    assert value(r,"pressure_loss") == 0
    assert value(r,"friction_factor") is None
    r = pipe_loss(math.pi*.1**2/4,.1,0,1000,.001,minor_loss_coefficient=2)
    assert value(r,"pressure_loss") == pytest.approx(1000)

def test_transitional_loss_withheld():
    r = pipe_loss(.025*math.pi*.1**2/4,.1,10,1000,.001)
    assert value(r,"pressure_loss") is None

def test_buoyancy_and_equilibrium():
    r = buoyancy(.5,1,500,1000)
    assert value(r,"buoyant_force") == 4903.325
    assert value(r,"net_upward_force") == 0
    r = floating_equilibrium(1,500,1000,base_area=2)
    assert value(r,"equilibrium_displacement") == .5
    assert value(r,"draft") == .25

@pytest.mark.parametrize("mass,status", [(0,"floating"),(1000,"neutral"),(1001,"no_equilibrium")])
def test_equilibrium_limits(mass,status):
    r = floating_equilibrium(1,mass,1000)
    assert r.status == status
    if status != "floating":
        assert value(r,"draft") is None

@pytest.mark.parametrize("bad", [float("nan"),float("inf"),-1,True,"1",None])
def test_invalid_density(bad):
    with pytest.raises(PhysicalInputError):
        buoyancy(.5,1,500,bad)

@pytest.mark.parametrize("call", [
    lambda: continuity(1,0), lambda: continuity(-1,1),
    lambda: energy(mode="ideal",loss_head=1), lambda: energy(alpha1=.9),
    lambda: energy(mode="unknown"), lambda: energy(pressure_basis="unknown"),
    lambda: energy(pressure1=1000), lambda: energy(vapor_pressure=99000),
    lambda: energy(reference_pressure=0),
    lambda: hydrostatic_pressure(-1,1000,1,pressure_basis="absolute",reference_pressure=1),
    lambda: plate(angle=2), lambda: plate(width=0),
    lambda: reynolds_number(1,.1,1000,0), lambda: friction_factor(1e9),
    lambda: friction_factor(5000,.06), lambda: pipe_loss(1,.1,-1,1000,.001),
    lambda: pipe_loss(1,.1,1,1000,.001,minor_loss_coefficient=-1),
    lambda: buoyancy(2,1,1,1000), lambda: floating_equilibrium(1,1,1000,base_area=0),
])
def test_invalid_inputs(call):
    with pytest.raises(PhysicalInputError):
        call()

def test_numerical_overflow_not_hidden():
    with pytest.raises((NumericalError,OverflowError,PhysicalInputError)):
        buoyancy(1e308,1e308,1,1e308)

def test_result_contract():
    for r in (energy(),plate(),pipe_loss(0,.1,1,1000,.001),buoyancy(0,1,1,1000)):
        assert r.equations and r.assumptions
        assert all(q.unit for q in r.values.values())
