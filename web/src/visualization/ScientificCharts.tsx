import {useEffect,useRef} from 'react';
import type {Lang} from '../types';
import type {Chart} from './types';
export function ScientificChart({chart,lang}:{chart:Chart;lang:Lang}){
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{let active=true;let plot:any;let observer:ResizeObserver|undefined;const element=ref.current;
 import('plotly.js-basic-dist-min').then(module=>{if(!active||!element)return;plot=module.default;plot.react(element,chart.series.map((s,i)=>({type:'scatter',mode:s.mode,x:s.x,y:s.y,name:s.label[lang],connectgaps:false,line:{color:['#209aff','#d96d59'][i%2],width:2},marker:{size:9},hovertemplate:`%{x} ${chart.xUnit}<br>%{y} ${chart.yUnit}<extra>${s.label[lang]}</extra>`})),{height:320,margin:{l:85,r:20,t:25,b:90},paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{family:'Tahoma, Arial',color:'#b9cbea'},xaxis:{title:{text:`${chart.xLabel[lang]} (${chart.xUnit})`},automargin:true,gridcolor:'#243752'},yaxis:{title:{text:`${chart.yLabel[lang]} (${chart.yUnit})`},automargin:true,gridcolor:'#243752'},legend:{orientation:'h',y:-.3},showlegend:chart.series.length>1},{responsive:true,displayModeBar:false});observer=new ResizeObserver(()=>plot.Plots.resize(element));observer.observe(element)});
 return()=>{active=false;observer?.disconnect();if(plot&&element)plot.purge(element)};
 },[chart,lang]);
 return <section className="panel"><h2>{chart.title[lang]}</h2><div dir="ltr" ref={ref} role="img" aria-label={chart.title[lang]}/><details><summary>{lang==='en'?'Chart data (SI)':'داده‌های نمودار (SI)'}</summary><div className="chart-table"><table><thead><tr><th>{chart.xLabel[lang]} ({chart.xUnit})</th>{chart.series.map(s=><th key={s.label.en}>{s.label[lang]} ({chart.yUnit})</th>)}</tr></thead><tbody>{chart.series[0]?.x.map((x,i)=><tr key={i}><td><bdi>{x.toPrecision(5)}</bdi></td>{chart.series.map(s=><td key={s.label.en}><bdi>{s.y[i]===null?'—':s.y[i]?.toPrecision(6)}</bdi></td>)}</tr>)}</tbody></table></div></details></section>
}
