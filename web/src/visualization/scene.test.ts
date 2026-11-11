import {describe,it,expect} from 'vitest';
import {buildScene,pressureColor} from './scene';
import type {Visualization} from './types';
const nativeFetch=globalThis.fetch;
describe('scene adapter with real API geometry',()=>{
 it.each(['bernoulli','hydrostatics','pipe-flow','buoyancy'])('builds and disposes %s',async id=>{
  const catalog=await (await nativeFetch('http://127.0.0.1:8000/api/v1/models')).json();
  const payload=Object.fromEntries(catalog[id].fields.map((f:any)=>[f.key,f.default]));
  const response=await (await nativeFetch(`http://127.0.0.1:8000/api/v1/${id}/calculate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})).json();
  const data:Visualization=response.visualization;const built=buildScene(data);
  expect(built.group.children.length).toBeGreaterThan(1);expect(Number.isFinite(built.radius)).toBe(true);
  for(const shape of data.shapes)expect(built.group.getObjectByName(shape.key)).toBeTruthy();
  built.animate(1);built.dispose();expect(built.group.children).toHaveLength(0);
 });
 it('changes geometry when the server receives different area inputs',async()=>{
  const catalog=await (await nativeFetch('http://127.0.0.1:8000/api/v1/models')).json();
  const body=Object.fromEntries(catalog.bernoulli.fields.map((f:any)=>[f.key,f.default]));
  const geometry=async(area2:number)=>{const data=await (await nativeFetch('http://127.0.0.1:8000/api/v1/bernoulli/calculate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,area2})})).json();return buildScene(data.visualization)};
  const a=await geometry(.005),b=await geometry(.009);
  const pipeA:any=a.group.getObjectByName('pipe'),pipeB:any=b.group.getObjectByName('pipe');
  expect(pipeA.geometry.parameters.radiusTop).not.toBe(pipeB.geometry.parameters.radiusTop);a.dispose();b.dispose();
 });
});


describe('pressure surface colors',()=>{
 const scale={min:-10,max:10,unit:'Pa',label:{en:'Net pressure',fa:'فشار خالص'}};
 it('maps minimum to blue, maximum to red, and constant pressure to blue',()=>{
  expect(pressureColor(-10,scale).getHexString()).toBe('164bff');
  expect(pressureColor(10,scale).getHexString()).toBe('ef2424');
  expect(pressureColor(0,{...scale,min:0,max:0}).getHexString()).toBe('164bff');
 });
 it('attaches finite distinct vertex colors to the live hydrostatic wet surface only',async()=>{
  const catalog=await (await nativeFetch('http://127.0.0.1:8000/api/v1/models')).json();
  const body=Object.fromEntries(catalog.hydrostatics.fields.map((f:any)=>[f.key,f.default]));
  const response=await (await nativeFetch('http://127.0.0.1:8000/api/v1/hydrostatics/calculate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,top_depth:-1})})).json();
  const built=buildScene(response.visualization);
  const wet:any=built.group.getObjectByName('surface-pressure');
  const dry:any=built.group.getObjectByName('surface');
  expect(wet.geometry.getAttribute('color')).toBeTruthy();
  expect(dry.geometry.getAttribute('color')).toBeUndefined();
  const colors=Array.from(wet.geometry.getAttribute('color').array) as number[];
  expect(colors.every(Number.isFinite)).toBe(true);
  expect(new Set(colors).size).toBeGreaterThan(4);
  built.dispose();
 });
});
