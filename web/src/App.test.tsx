import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import App from './App';
import {calculate,getCatalog,normalizeNumber} from './api';
vi.mock('./visualization/ScenePanel',()=>({default:({data}:any)=><div data-testid="scene">{JSON.stringify(data.shapes)}</div>}));
vi.mock('plotly.js-basic-dist-min',()=>({default:{react:vi.fn(),purge:vi.fn(),Plots:{resize:vi.fn()}}}));
// jsdom signals are not Node AbortSignals; the test transport omits the signal.
// Browser cancellation is implemented in production; these tests exercise HTTP and UI.
const nativeFetch=globalThis.fetch;
beforeEach(()=>{globalThis.fetch=((url:any,options:any)=>nativeFetch(new URL(String(url),'http://127.0.0.1:8000'),{...options,signal:undefined})) as typeof fetch;vi.stubGlobal('ResizeObserver',class{observe(){} disconnect(){}});localStorage.clear();location.hash='#/bernoulli'});
afterEach(()=>{cleanup();globalThis.fetch=nativeFetch;vi.unstubAllGlobals()});
describe('real FastAPI integration',()=>{
 it.each(['bernoulli','hydrostatics','pipe-flow','buoyancy'])('calculates %s via HTTP',async id=>{const catalog=await getCatalog(new AbortController().signal);const payload=Object.fromEntries(catalog[id].fields.map(f=>[f.key,f.default]));const response=await calculate(id,payload,new AbortController().signal);expect(Object.keys(response.values).length).toBeGreaterThan(0);expect(response.equations.length).toBeGreaterThan(0);expect(response.assumptions.length).toBeGreaterThan(0)});
 it('switches Persian RTL and English LTR without losing input',async()=>{render(<App/>);const input=await screen.findByLabelText(/Flow rate/);fireEvent.change(input,{target:{value:'.02'}});fireEvent.click(screen.getByRole('button',{name:'Switch language / تغییر زبان'}));expect(document.documentElement.dir).toBe('rtl');expect(document.documentElement.lang).toBe('fa');expect((screen.getByLabelText(/دبی حجمی/) as HTMLInputElement).value).toBe('.02');fireEvent.click(screen.getByRole('button',{name:'Switch language / تغییر زبان'}));expect(document.documentElement.dir).toBe('ltr');await screen.findByText('95,325',{},{timeout:4000});});
 it('clears results for invalid input and updates for valid input',async()=>{render(<App/>);await screen.findByText('99,825',{},{timeout:4000});fireEvent.change(screen.getByLabelText(/Flow rate/),{target:{value:''}});expect(screen.queryByText('99,825')).toBeNull();expect(await screen.findByText('Enter a valid value for every field.')).toBeTruthy();fireEvent.change(screen.getByLabelText(/Flow rate/),{target:{value:'.02'}});await screen.findByText('95,325',{},{timeout:4000});});
 it('renders all four pages using live API',async()=>{render(<App/>);await screen.findByText('99,825',{},{timeout:4000});for(const [id,name,label] of [['hydrostatics','Hydrostatics','Net force'],['pipe-flow','Pipe flow','Reynolds number'],['buoyancy','Buoyancy','Prism draft']]){location.hash='#/'+id;window.dispatchEvent(new HashChangeEvent('hashchange'));await waitFor(()=>expect(screen.getByRole('heading',{level:1}).textContent).toBe(name));await screen.findByText(label,{},{timeout:4000})}});
 it('shows backend physical errors',async()=>{render(<App/>);await screen.findByText('99,825',{},{timeout:4000});fireEvent.change(screen.getByLabelText(/Loss head/),{target:{value:'1'}});expect(await screen.findByRole('alert',{},{timeout:4000})).toBeTruthy();expect(screen.queryByText('99,825')).toBeNull()});
 it('shows connection failure',async()=>{globalThis.fetch=vi.fn().mockRejectedValue(new TypeError('offline'));render(<App/>);expect(await screen.findByRole('alert')).toBeTruthy();expect(screen.getByText('Try again')).toBeTruthy()});
 it.each([
 ['bernoulli','Station 2 area','.008'],
 ['hydrostatics','Top-edge depth','1'],
 ['pipe-flow','Pipe length','20'],
 ['buoyancy','Body mass','750']
 ])('updates %s scene and chart from one input change',async(id,label,changed)=>{
 location.hash='#/'+id;render(<App/>);
 const scene=await screen.findByTestId('scene',{},{timeout:4000});
 const beforeGeometry=scene.textContent;
 const beforeChart=Array.from(document.querySelectorAll('.chart-table')).map(e=>e.textContent).join('');
 fireEvent.change(screen.getByLabelText(new RegExp(label)),{target:{value:changed}});
 expect(screen.queryByTestId('scene')).toBeNull();
 await waitFor(()=>expect(screen.getByTestId('scene').textContent).not.toBe(beforeGeometry),{timeout:4000});
 expect(Array.from(document.querySelectorAll('.chart-table')).map(e=>e.textContent).join('')).not.toBe(beforeChart);
 });
 it('normalizes Persian and Arabic decimal input',()=>{expect(normalizeNumber('۱۲٫۵')).toBe('12.5');expect(normalizeNumber('١٢')).toBe('12')});
});
