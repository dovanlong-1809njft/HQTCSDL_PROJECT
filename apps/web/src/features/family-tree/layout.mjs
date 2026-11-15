// Stable spouse units and parent barycenters; never changes source relations.
export function layoutTree(tree) {
  const members=[...new Map(tree.nodes.map(n=>[n.id,n])).values()].sort((a,b)=>a.id.localeCompare(b.id));
  const ids=new Set(members.map(n=>n.id));
  const edges=[...new Map(tree.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&e.source!==e.target).map(e=>[`${e.kind}:${e.kind==="marriage"?[e.source,e.target].sort().join(":"):`${e.source}:${e.target}`}`,e])).values()];
  const parents=new Map(members.map(n=>[n.id,[]])),spouses=new Map(members.map(n=>[n.id,[]]));
  for(const e of edges)if(e.kind==="parent_child")parents.get(e.target).push(e.source);
  for(const e of edges)if(e.kind==="marriage"){spouses.get(e.source).push(e.target);spouses.get(e.target).push(e.source);}
  function units(groupSpouses){
    const owner=new Map(),groups=new Map();
    for(const n of members){
      if(owner.has(n.id))continue;
      const group=[],queue=[n.id];owner.set(n.id,n.id);
      for(let i=0;i<queue.length;i++){
        const id=queue[i];group.push(id);
        if(groupSpouses)for(const other of [...spouses.get(id)].sort())if(!owner.has(other)){owner.set(other,n.id);queue.push(other);}
      }
      groups.set(n.id,group);
    }
    return {owner,groups};
  }
  function rank({owner,groups}){
    const next=new Map([...groups.keys()].map(id=>[id,new Set()])),degree=new Map([...groups.keys()].map(id=>[id,0])),levels=new Map([...groups.keys()].map(id=>[id,0]));
    for(const e of edges)if(e.kind==="parent_child"){
      const a=owner.get(e.source),b=owner.get(e.target);
      if(!next.get(a).has(b)){next.get(a).add(b);degree.set(b,degree.get(b)+1);}
    }
    const queue=[...groups.keys()].filter(id=>degree.get(id)===0);
    for(let i=0;i<queue.length;i++)for(const child of next.get(queue[i])){
      levels.set(child,Math.max(levels.get(child),levels.get(queue[i])+1));
      degree.set(child,degree.get(child)-1);if(degree.get(child)===0)queue.push(child);
    }
    return {levels,cyclic:queue.length!==groups.size};
  }
  let grouping=units(true),ranking=rank(grouping),hasConflict=false;
  if(ranking.cyclic){grouping=units(false);ranking=rank(grouping);hasConflict=!ranking.cyclic;}
  const rows=new Map(),positions=new Map();
  for(const [id,group]of grouping.groups){const level=ranking.levels.get(id);if(!rows.has(level))rows.set(level,[]);rows.get(level).push({id,group});}
  for(const [level,row]of [...rows].sort((a,b)=>a[0]-b[0])){
    const desired=unit=>{
      const ancestors=[...new Set(unit.group.flatMap(id=>parents.get(id)))].map(id=>positions.get(id)).filter(Boolean);
      return ancestors.length?ancestors.reduce((sum,p)=>sum+p.x,0)/ancestors.length:Infinity;
    };
    row.sort((a,b)=>desired(a)-desired(b)||a.id.localeCompare(b.id));
    let right=-Infinity;
    for(const unit of row){
      const center=desired(unit),width=(unit.group.length-1)*230;
      const left=Math.max(Number.isFinite(center)?center-width/2:(Number.isFinite(right)?right:0),Number.isFinite(right)?right:0);
      unit.group.forEach((id,i)=>positions.set(id,{x:left+i*230,y:level*200}));right=left+width+270;
    }
    const anchored=row.filter(unit=>Number.isFinite(desired(unit)));
    const shift=anchored.length?anchored.reduce((sum,unit)=>sum+desired(unit)-(positions.get(unit.group[0]).x+(unit.group.length-1)*115),0)/anchored.length:0;
    for(const unit of row)for(const id of unit.group)positions.get(id).x+=shift;
  }
  const nodes=members.map(n=>({id:n.id,type:"member",data:{label:n.label,birthDate:n.birth_date,avatar:n.avatar_url},position:positions.get(n.id),style:{width:190,height:86,borderRadius:12,padding:0,border:"1px solid #62836c",background:"#fff"}}));
  const result={nodes,edges:edges.map(edge=>{
    const marriage=edge.kind==="marriage",realParents=parents.get(edge.target);
    const sameRank=realParents.length===2&&positions.get(realParents[0]).y===positions.get(realParents[1]).y;
    const joint=sameRank?{x:(positions.get(realParents[0]).x+positions.get(realParents[1]).x)/2+95,y:positions.get(realParents[0]).y+120}:null;
    const left=positions.get(edge.source).x<=positions.get(edge.target).x;
    return {...edge,type:marriage?"marriage":"family",sourceHandle:marriage?(left?"right":"left"):"children",targetHandle:marriage?(left?"left":"right"):"parents",data:{joint},label:marriage?"H\u00f4n nh\u00e2n":undefined,style:marriage?{stroke:"#b7791f",strokeDasharray:"6 4"}:{stroke:"#62836c"}};
  }),hasCycle:ranking.cyclic};
  if(hasConflict)result.hasConflict=true;
  if(tree.edges.some(e=>!ids.has(e.source)||!ids.has(e.target)||e.source===e.target))result.hasInvalidRelations=true;
  return result;
}
