import type {Text} from '../types';
export type Vec3=[number,number,number];
export interface PressureField {axis:'x'|'y';values:[number,number]}
export interface PressureScale {min:number;max:number;unit:string;label:Text}
export interface Box {pressure?:PressureField;kind:'box';key:string;size:Vec3;position:Vec3;color:string;opacity:number;angle:number}
export interface Pipe {pressure?:PressureField;kind:'pipe';key:string;start:Vec3;end:Vec3;radius1:number;radius2:number;color:string;opacity:number}
export interface Marker {position:Vec3;label:Text;color:string}
export interface Arrow {origin:Vec3;direction:Vec3;magnitude:number;unit:string;group:string;label:Text;color:string}
export interface Flow {start:Vec3;end:Vec3;radius1:number;radius2:number;active:boolean}
export interface Chart {title:Text;xLabel:Text;yLabel:Text;xUnit:string;yUnit:string;series:{label:Text;x:number[];y:(number|null)[];mode:string}[]}
export interface Visualization {pressureScale?:PressureScale|null;shapes:(Box|Pipe)[];markers:Marker[];arrows:Arrow[];flow:Flow|null;charts:Chart[];notes:Text[]}
