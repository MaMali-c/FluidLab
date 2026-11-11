import type {Catalog,Result} from './types';
export class ApiError extends Error {constructor(public detail:string,public code:string){super(detail)}}
async function request<T>(url:string, signal:AbortSignal,body?:Record<string,string|number>):Promise<T>{
 const response=await fetch(url,{signal,headers:{'Content-Type':'application/json'},...(body?{method:'POST',body:JSON.stringify(body)}:{})});
 const data=await response.json();
 if(!response.ok)throw new ApiError(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail),data.code||'validation');
 return data;
}
export const getCatalog=(signal:AbortSignal)=>request<Catalog>('/api/v1/models',signal);
export const calculate=(id:string,body:Record<string,string|number>,signal:AbortSignal)=>request<Result>(`/api/v1/${id}/calculate`,signal,body);
export function normalizeNumber(value:string):string{return value.replace(/[۰-۹]/g,c=>String(c.charCodeAt(0)-1776)).replace(/[٠-٩]/g,c=>String(c.charCodeAt(0)-1632)).replace(/٫/g,'.').replace(/−/g,'-')}
