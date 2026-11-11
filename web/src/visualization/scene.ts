/** Geometry adapter only. Scientific coordinates and magnitudes arrive from Python. */
import * as THREE from 'three';
import type {Visualization,Vec3,PressureScale} from './types';
/** Color mapping only; scalar pressures are supplied by the backend. */
export const pressurePalette=['#164bff','#00cfff','#ffe04a','#ef2424'];
export function pressureColor(value:number, scale:PressureScale):THREE.Color {
 const fraction=scale.max===scale.min?0:Math.max(0,Math.min(1,(value-scale.min)/(scale.max-scale.min)));
 const index=Math.min(2,Math.floor(fraction*3));
 return new THREE.Color(pressurePalette[index]).lerp(new THREE.Color(pressurePalette[index+1]),fraction*3-index);
}
export function buildScene(data:Visualization){
 const group=new THREE.Group();
 // Normalize before allocating Float32 geometry, and use a consistent isotropic scale.
 const extent=Math.max(...data.shapes.flatMap(s=>s.kind==='box'?[...s.size,...s.position.map(Math.abs)]:[...s.start.map(Math.abs),...s.end.map(Math.abs),s.radius1,s.radius2]),Number.MIN_VALUE);
 const unit=4/extent;
 const vector=(p:Vec3)=>new THREE.Vector3(...p.map(v=>v*unit) as Vec3);
 for(const shape of data.shapes){
  let geometry:THREE.BufferGeometry;
  const colored=Boolean(shape.pressure&&data.pressureScale);
  const material=colored?new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide,toneMapped:false,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1}):new THREE.MeshStandardMaterial({color:shape.color,transparent:shape.opacity<1,opacity:shape.opacity,side:THREE.DoubleSide,depthWrite:shape.opacity>=1,roughness:.7});
  function applyPressure(geometry:THREE.BufferGeometry, span:number){
   if(!shape.pressure||!data.pressureScale)return;
   const position=geometry.getAttribute('position');const colors=new Float32Array(position.count*3);
   for(let i=0;i<position.count;i++){
    const coordinate=shape.pressure.axis==='x'?position.getX(i):position.getY(i);
    const fraction=Math.max(0,Math.min(1,coordinate/span+.5));
    const [a,b]=shape.pressure.values;
    pressureColor(a+(b-a)*fraction,data.pressureScale).toArray(colors,i*3);
   }
   geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));
  }
  if(shape.kind==='box'){
   geometry=new THREE.BoxGeometry(shape.size[0]*unit,shape.size[1]*unit,shape.size[2]*unit,colored&&shape.pressure?.axis==='x'?32:1,colored&&shape.pressure?.axis==='y'?32:1,1);
   applyPressure(geometry,shape.size[shape.pressure?.axis==='x'?0:1]*unit);
   const mesh=new THREE.Mesh(geometry,material);mesh.name=shape.key;mesh.position.copy(vector(shape.position));mesh.rotation.z=shape.angle;group.add(mesh);
   const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geometry),new THREE.LineBasicMaterial({color:shape.color,transparent:true,opacity:.8}));edges.position.copy(mesh.position);edges.rotation.copy(mesh.rotation);group.add(edges);
  }else{
   const a=vector(shape.start),b=vector(shape.end),direction=b.clone().sub(a);
   geometry=new THREE.CylinderGeometry(shape.radius2*unit,shape.radius1*unit,direction.length(),32,colored?8:1,true);
   applyPressure(geometry,direction.length());
   const mesh=new THREE.Mesh(geometry,material);mesh.name=shape.key;mesh.position.copy(a).add(b).multiplyScalar(.5);mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),direction.normalize());group.add(mesh);
   for(const [point,radius] of [[a,shape.radius1],[b,shape.radius2]] as const){if(data.flow&&!point.equals(vector(data.flow.start))&&!point.equals(vector(data.flow.end)))continue;const ring=new THREE.Mesh(new THREE.TorusGeometry(radius*unit,.012,6,32),new THREE.MeshBasicMaterial({color:'#547c8b'}));ring.position.copy(point);ring.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),direction);group.add(ring)}
  }
 }
 for(const marker of data.markers){const mesh=new THREE.Mesh(new THREE.SphereGeometry(.075,12,8),new THREE.MeshBasicMaterial({color:marker.color}));mesh.name=marker.label.en;mesh.position.copy(vector(marker.position));group.add(mesh)}
 for(const arrow of data.arrows){
  if(arrow.magnitude===0)continue;
  const max=Math.max(...data.arrows.filter(a=>a.group===arrow.group).map(a=>Math.abs(a.magnitude)));
  const direction=new THREE.Vector3(...arrow.direction).normalize().multiplyScalar(Math.sign(arrow.magnitude));
  const length=1.3*Math.abs(arrow.magnitude)/max;
  const helper=new THREE.ArrowHelper(direction,vector(arrow.origin),length,arrow.color,Math.min(.18,length*.25),Math.min(.1,length*.15));helper.name=arrow.label.en;group.add(helper);
 }
 let particleGeometry:THREE.BufferGeometry|undefined;
 let animate:(time:number)=>void=()=>{};
 if(data.flow){
  const flow=data.flow;const a=vector(flow.start),b=vector(flow.end);const axis=b.clone().sub(a).normalize();
  const normal=new THREE.Vector3(0,0,1);if(Math.abs(axis.dot(normal))>.95)normal.set(0,1,0);
  const u=normal.cross(axis).normalize(),v=axis.clone().cross(u).normalize();
  const count=48;const positions=new Float32Array(count*3);particleGeometry=new THREE.BufferGeometry();particleGeometry.setAttribute('position',new THREE.BufferAttribute(positions,3));
  const points=new THREE.Points(particleGeometry,new THREE.PointsMaterial({color:'#124a64',size:.06,sizeAttenuation:true}));points.name='Illustrative flow particles';group.add(points);
  animate=(time)=>{for(let i=0;i<count;i++){
   // Fixed display speed, not computed fluid velocity or a CFD trajectory.
   const fraction=(i/count+(flow.active?time*.12:0))%1;
   const radius=(flow.radius1+(flow.radius2-flow.radius1)*fraction)*unit*.6;
   const phase=i*2.399963229728653; // Golden-angle spacing, purely visual.
   const point=a.clone().lerp(b,fraction).addScaledVector(u,Math.cos(phase)*radius).addScaledVector(v,Math.sin(phase)*radius);
   point.toArray(positions,i*3);
  }particleGeometry!.attributes.position.needsUpdate=true};animate(0);
 }
 const bounds=new THREE.Box3().setFromObject(group);const center=bounds.getCenter(new THREE.Vector3());const radius=Math.max(bounds.getSize(new THREE.Vector3()).length()/2,1);
 function dispose(){group.traverse(object=>{const drawable=object as THREE.Mesh;if(drawable.geometry)drawable.geometry.dispose();if(drawable.material){for(const m of Array.isArray(drawable.material)?drawable.material:[drawable.material])m.dispose()}});group.clear()}
 return {group,center,radius,animate,dispose};
}
