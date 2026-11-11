"""Exercise actual HTTP handlers against the independent scientific engine."""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.catalog import MODELS
from dataclasses import asdict
client=TestClient(app)

@pytest.mark.parametrize('module',MODELS)
def test_real_calculation(module):
    model=MODELS[module]
    payload={f['key']:f['default'] for f in model['fields']}
    response=client.post('/api/v1/'+module+'/calculate',json=payload)
    assert response.status_code==200,response.text
    assert {k:v for k,v in response.json().items() if k != "visualization"}==__import__('json').loads(__import__('json').dumps(asdict(model['function'](**payload))))
    payload['density' if 'density' in payload else 'fluid_density']=-1
    assert client.post('/api/v1/'+module+'/calculate',json=payload).status_code==422

def test_catalog_bilingual_and_openapi():
    data=client.get('/api/v1/models').json()
    assert len(data)==4
    for key,model in data.items():
        assert model['title']['fa'] and model['title']['en']
        for field in model['fields']:
            assert field['label']['en'] and field['label']['fa']
    assert len(client.get('/openapi.json').json()['paths'])==6

def test_missing_extra_boolean_and_physical_errors():
    assert client.post('/api/v1/bernoulli/calculate',json={}).status_code==422
    body={f['key']:f['default'] for f in MODELS['bernoulli']['fields']}
    body['loss_head']=1
    response=client.post('/api/v1/bernoulli/calculate',json=body)
    assert response.status_code==422
    assert response.json()['code']=='physical_input'
    body['loss_head']=0
    body['density']=True
    assert client.post('/api/v1/bernoulli/calculate',json=body).status_code==422
    body['density']=1000
    body['extra']=1
    assert client.post('/api/v1/bernoulli/calculate',json=body).status_code==422
