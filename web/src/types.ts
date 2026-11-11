export type Lang='en'|'fa';
export type Text=Record<Lang,string>;
export interface Field {key:string;label:Text;unit:string;default:string|number;minimum:number|null;exclusive:boolean;options:null|{value:string;en:string;fa:string}[]}
export interface Model {title:Text;description:Text;fields:Field[]}
export type Catalog=Record<string,Model>;
export interface Result {visualization?:import("./visualization/types").Visualization;values:Record<string,{value:number|null;unit:string}>;equations:string[];assumptions:string[];warnings:string[];status:string}
