"""Verify scene geometry and chart samples share the actual calculation inputs."""
import math
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.catalog import MODELS
client=TestClient(app)

def calculate(module, **changes):
    payload={f['key']:f['default'] for f in MODELS[module]['fields']}
    payload.update(changes)
    response=client.post(f'/api/v1/{module}/calculate',json=payload)
    assert response.status_code==200,response.text
    return response.json()

def test_bernoulli_updates_geometry_and_station_charts():
    first=calculate('bernoulli')
    second=calculate('bernoulli',area2=.02,elevation2=1)
    a=second['visualization']
    assert a['shapes'][0]['radius2']==pytest.approx(math.sqrt(.02/math.pi))
    assert a['shapes'][0]['end'][1]==1
    assert a['charts'][0]['series'][0]['mode']=='markers'
    assert a['charts'][0]['series'][0]['y'][1]==second['values']['pressure2_absolute']['value']
    assert a['charts'][1]['series'][0]['y'][1]==.5
    assert a!=first['visualization']
    assert not calculate('bernoulli',flow_rate=0)['visualization']['flow']['active']

def test_hydrostatic_distribution_and_resultant():
    a=calculate('hydrostatics')['visualization']
    assert a['charts'][0]['series'][0]['y'][-1]==pytest.approx(19613.3)
    cp=next(m for m in a['markers'] if m['label']['en']=='Center of pressure')
    assert cp['position'][1]==pytest.approx(-4/3)
    force=next(v for v in a['arrows'] if v['group']=='force')
    assert force['magnitude']==pytest.approx(19613.3)
    partial=calculate('hydrostatics',top_depth=-1)['visualization']
    assert partial['charts'][0]['series'][0]['x'][0]==pytest.approx(1)
    assert partial['charts'][0]['series'][0]['y'][-1]==pytest.approx(9806.65)
    dry=calculate('hydrostatics',top_depth=-3)['visualization']
    assert dry['arrows']==[]
    assert dry['charts'][0]['series'][0]['x']==[]

def test_pipe_loss_chart_and_minor_jump():
    r=calculate('pipe-flow',minor_loss_coefficient=2)
    chart=r['visualization']['charts'][0]['series'][0]
    assert chart['x'][-2:]==[10,10]
    assert chart['y'][-1]==r['values']['pressure_loss']['value']
    assert chart['y'][-1]>chart['y'][-2]
    changed=calculate('pipe-flow',length=20)
    assert changed['visualization']['flow']['end'][0]==10
    larger=calculate('pipe-flow',diameter=.08)
    assert larger['visualization']['flow']['radius1']>r['visualization']['flow']['radius1']
    rest=calculate('pipe-flow',flow_rate=0)
    assert set(rest['visualization']['charts'][0]['series'][0]['y'])=={0}
    transitional=calculate('pipe-flow',flow_rate=2500*.001/1000/.05*math.pi*.05**2/4)
    assert transitional['status']=='transitional_not_predicted'
    assert all(y is None for y in transitional['visualization']['charts'][0]['series'][0]['y'])

def test_buoyancy_force_equilibrium_and_sinking():
    r=calculate('buoyancy')
    a=r['visualization']
    assert [v['magnitude'] for v in a['arrows']]==[4903.325,4903.325]
    assert a['charts'][0]['series'][0]['y'][-1]==9806.65
    changed=calculate('buoyancy',mass=750)['visualization']
    body=next(s for s in changed['shapes'] if s['key']=='body')
    assert body['position'][1]==-.25
    sink=calculate('buoyancy',mass=1500)
    assert sink['status']=='no_equilibrium'
    assert sink['visualization']['arrows'][0]['magnitude']>sink['visualization']['arrows'][1]['magnitude']
    assert 'not a predicted equilibrium' in sink['visualization']['notes'][-1]['en']


def test_surface_pressure_map_matches_independent_hydrostatic_values():
    """rho=1000, g=10, h=1..3 m gives net p=10000..30000 Pa."""
    v=calculate('hydrostatics',top_depth=1,gravity=10)['visualization']
    surface=next(s for s in v['shapes'] if s['key']=='surface-pressure')
    assert surface['pressure']=={'axis':'x','values':[10000,30000]}
    assert (v['pressureScale']['min'],v['pressureScale']['max'])==(10000,30000)
    assert surface['pressure']['values']==[v['charts'][0]['series'][0]['y'][i] for i in (0,-1)]


def test_partial_dry_horizontal_and_signed_pressure_maps():
    partial=calculate('hydrostatics',top_depth=-1,gravity=10)['visualization']
    wet=next(s for s in partial['shapes'] if s['key']=='surface-pressure')
    assert wet['size'][0]==pytest.approx(1)
    assert wet['pressure']['values']==[0,10000]
    dry=calculate('hydrostatics',top_depth=-3)['visualization']
    assert dry['pressureScale'] is None
    assert not any('pressure' in s for s in dry['shapes'])
    horizontal=calculate('hydrostatics',angle=0,top_depth=1,gravity=10)['visualization']
    assert horizontal['pressureScale']['min']==horizontal['pressureScale']['max']==10000
    signed=calculate('hydrostatics',gravity=10,opposing_pressure_absolute=111325)['visualization']
    assert signed['pressureScale']['min']==-10000
    assert signed['pressureScale']['max']==10000


def test_floating_pressure_values_and_wetted_geometry():
    """500 kg / (1000 kg/m³ * 1 m²) = .5 m draft; Δp=5000 Pa at g=10."""
    v=calculate('buoyancy',gravity=10)['visualization']
    wet=next(s for s in v['shapes'] if s['key']=='body-pressure')
    assert wet['size'][1]==.5
    assert wet['position'][1]==-.25
    assert wet['pressure']['values']==[5000,0]
    assert v['pressureScale']['max']==5000
    changed=calculate('buoyancy',gravity=10,mass=750)['visualization']
    assert changed['pressureScale']['max']==7500


def test_only_solved_bernoulli_stations_are_colored():
    r=calculate('bernoulli')
    v=r['visualization']
    assert 'pressure' not in v['shapes'][0]
    bands=[s for s in v['shapes'] if 'pressure' in s]
    assert len(bands)==2
    assert bands[1]['pressure']['values']==[r['values']['pressure2_absolute']['value']]*2


def test_pipe_pressure_color_uses_major_loss_not_unknown_absolute_pressure():
    r=calculate('pipe-flow',minor_loss_coefficient=2)
    v=r['visualization']
    major=v['charts'][0]['series'][0]['y'][-2]
    assert v['shapes'][0]['pressure']['values'][0]==0
    assert v['shapes'][-1]['pressure']['values'][-1]==pytest.approx(-major)
    assert v['pressureScale']['min']==-major
    assert major<r['values']['pressure_loss']['value']
    rest=calculate('pipe-flow',flow_rate=0)['visualization']
    assert rest['pressureScale']['min']==rest['pressureScale']['max']==0
    transitional=calculate('pipe-flow',flow_rate=2500*.001/1000/.05*math.pi*.05**2/4)['visualization']
    assert transitional['pressureScale'] is None
    assert not any('pressure' in s for s in transitional['shapes'])
