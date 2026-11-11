"""Thin FastAPI adapter; all scientific calculations remain in fluidlab_physics."""
from dataclasses import asdict
from typing import Literal
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ConfigDict, Field, create_model
from fluidlab_physics import PhysicalInputError
from .catalog import MODELS
from .visualization import visualization

app=FastAPI(title='FluidLab API',version='1.0.0')

@app.exception_handler(PhysicalInputError)
async def physical_error(request: Request, exc: PhysicalInputError):
    return JSONResponse(status_code=422,content={'detail':str(exc),'code':'physical_input'})

@app.exception_handler(ArithmeticError)
async def numerical_error(request: Request, exc: ArithmeticError):
    return JSONResponse(status_code=422,content={'detail':str(exc),'code':'numerical_failure'})

@app.get('/api/v1/models')
def models():
    return {key:{k:v for k,v in m.items() if k!='function'} for key,m in MODELS.items()}

@app.get('/health')
def health():
    return {'status':'ok'}

def register(key, metadata):
    fields={}
    for f in metadata['fields']:
        if f['options']:
            kind=Literal[tuple(o['value'] for o in f['options'])]
            definition=Field(...)
        else:
            kind=float
            bounds={} if f['minimum'] is None else {('gt' if f['exclusive'] else 'ge'):f['minimum']}
            definition=Field(...,allow_inf_nan=False,**bounds)
        fields[f['key']]=(kind,definition)
    schema=create_model(key.replace('-','_')+'Request',__config__=ConfigDict(extra='forbid',strict=True),**fields)
    def calculate(payload: schema):
        inputs=payload.model_dump()
        calculated=metadata['function'](**inputs)
        return {**asdict(calculated), 'visualization': visualization(key, inputs, calculated)}
    app.post('/api/v1/'+key+'/calculate',name=key)(calculate)

for key,metadata in MODELS.items():
    register(key,metadata)
