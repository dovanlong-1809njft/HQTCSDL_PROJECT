/* Pure reporting helpers. Read existing records; do not create demo business data. */
(function(){'use strict';
const zone='Asia/Ho_Chi_Minh';
function validDay(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const y=Number(s.slice(0,4));if(y<1900||y>9999)return false;const d=new Date(s+'T00:00:00Z');return !Number.isNaN(d.getTime())&&d.toISOString().slice(0,10)===s;}
function dayISO(value){if(typeof value!=='string'||!/(Z|[+-]\d{2}:\d{2})$/i.test(value)||!validDay(value.slice(0,10)))return '';const d=new Date(value);if(Number.isNaN(d.getTime()))return '';const parts=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(d);return ['year','month','day'].map(k=>parts.find(p=>p.type===k).value).join('-');}
function eventDay(value){if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)||!validDay(value.slice(0,10)))return '';const h=Number(value.slice(11,13)),m=Number(value.slice(14));return h<24&&m<60?value.slice(0,10):'';}
function today(){return dayISO(new Date().toISOString());}
function buckets(from,to,group){const rows=[],a=Number(from.slice(0,4)),b=Number(to.slice(0,4));if(group==='year'){for(let y=a;y<=b;y++)rows.push({key:String(y),label:String(y),posts:0,events:0,resources:0});}else if(group==='quarter'){const start=a*4+Math.floor((Number(from.slice(5,7))-1)/3),end=b*4+Math.floor((Number(to.slice(5,7))-1)/3);for(let n=start;n<=end;n++){const y=Math.floor(n/4),q=n%4+1;rows.push({key:y+'-Q'+q,label:'Q'+q+'/'+y,posts:0,events:0,resources:0});}}else{const start=a*12+Number(from.slice(5,7))-1,end=b*12+Number(to.slice(5,7))-1;for(let n=start;n<=end;n++){const y=Math.floor(n/12),m=n%12+1;rows.push({key:y+'-'+String(m).padStart(2,'0'),label:'T'+m+'/'+y,posts:0,events:0,resources:0});}}return rows;}
function groupKey(day,group){if(group==='year')return day.slice(0,4);if(group==='quarter')return day.slice(0,4)+'-Q'+(Math.floor((Number(day.slice(5,7))-1)/3)+1);return day.slice(0,7);}
function build(f,from,to,now=Date.now()){
 const loaded={posts:Array.isArray(f.community?.posts),events:Array.isArray(f.eventData?.items),resources:Array.isArray(f.heritageData?.items)};
 const allPosts=loaded.posts?f.community.posts.filter(p=>p.status!=='hidden'):[],allEvents=loaded.events?f.eventData.items:[],allResources=loaded.resources?f.heritageData.items.filter(r=>r.status!=='hidden'):[];
 const inside=day=>Boolean(day)&&day>=from&&day<=to;
 const posts=allPosts.filter(p=>inside(dayISO(p.createdAt))),resources=allResources.filter(r=>inside(dayISO(r.createdAt)));
 const scheduled=allEvents.filter(e=>!e.cancelled&&inside(eventDay(e.start))),ended=allEvents.filter(e=>!e.cancelled&&inside(eventDay(e.end))&&new Date(e.end+':00+07:00').getTime()<=now),createdEvents=allEvents.filter(e=>!e.cancelled&&inside(dayISO(e.createdAt)));
 const comments=allPosts.flatMap(p=>(p.comments||[]).filter(c=>inside(dayISO(c.createdAt))));
 const gen=new Map();f.members.forEach(m=>gen.set(m.generation,(gen.get(m.generation)||0)+1));
 const generations=[...gen].sort((a,b)=>a[0]-b[0]).map(([g,count])=>({label:'Thế hệ '+g,count}));
 const postTypes={text:'Văn bản',photo:'Ảnh',video:'Video',memory:'Kỷ niệm',poll:'Khảo sát'},eventTypes={birthday:'Sinh nhật',meeting:'Họp mặt',tradition:'Truyền thống',travel:'Du lịch',other:'Khác'},resourceTypes={document:'Tài liệu lịch sử',story:'Câu chuyện',photo:'Ảnh tư liệu',person:'Người nổi bật',archive:'Lưu trữ số',artifact:'Kỷ vật'};
 function classify(records,field,labels){const map=new Map(Object.keys(labels).map(k=>[k,0]));records.forEach(r=>{const key=Object.hasOwn(labels,r[field])?r[field]:'unknown';map.set(key,(map.get(key)||0)+1);});return [...map].map(([key,count])=>({key,label:labels[key]||'Khác / chưa rõ',count}));}
 const attachments=resources.flatMap(r=>r.attachments||[]),fileLabels={image:'Hình ảnh',pdf:'PDF',text:'TXT',docx:'DOCX'},files=classify(attachments,'kind',fileLabels);
 const media={images:posts.reduce((n,p)=>n+(p.images||[]).length,0)+attachments.filter(a=>a.kind==='image').length+scheduled.reduce((n,e)=>n+(e.album||[]).length,0),videos:posts.filter(p=>Boolean(p.video)).length+attachments.filter(a=>a.kind==='video').length};
 const people=new Map(),memberName=id=>id===window.FamilyIdentity.id()?window.FamilyIdentity.name():f.members.find(m=>m.id===id)?.name;
 function credit(id,fallback,key){const who=id||'unknown',row=people.get(who)||{id:who,name:memberName(id)||fallback||'Không rõ người',posts:0,comments:0,resources:0,events:0,total:0};row[key]++;row.total++;people.set(who,row);}
 posts.forEach(p=>credit(p.authorId,p.authorName,'posts'));comments.forEach(c=>credit(c.authorId,c.authorName,'comments'));resources.forEach(r=>credit(r.contributorId,r.contributorName,'resources'));createdEvents.forEach(e=>credit(e.organizer,e.organizerName,'events'));
 const contributors=[...people.values()].sort((a,b)=>b.total-a.total||a.name.localeCompare(b.name,'vi'));
 function timeSeries(group){const rows=buckets(from,to,group),map=new Map(rows.map(r=>[r.key,r]));posts.forEach(p=>{const row=map.get(groupKey(dayISO(p.createdAt),group));if(row)row.posts++;});scheduled.forEach(e=>{const row=map.get(groupKey(eventDay(e.start),group));if(row)row.events++;});resources.forEach(r=>{const row=map.get(groupKey(dayISO(r.createdAt),group));if(row)row.resources++;});return rows;}
 const quality={posts:allPosts.filter(p=>!dayISO(p.createdAt)).length,comments:allPosts.flatMap(p=>p.comments||[]).filter(c=>!dayISO(c.createdAt)).length,resources:allResources.filter(r=>!dayISO(r.createdAt)).length,eventStart:allEvents.filter(e=>!eventDay(e.start)).length,eventEnd:allEvents.filter(e=>!eventDay(e.end)).length,eventCreated:allEvents.filter(e=>!dayISO(e.createdAt)).length};
 return {from,to,loaded,posts,scheduled,ended,resources,comments,generations,postTypes:classify(posts,'type',postTypes),eventTypes:classify(scheduled,'category',eventTypes),resourceTypes:classify(resources,'type',resourceTypes),files,media,contributors,quality,timeSeries,members:f.members.length,cancelled:allEvents.filter(e=>e.cancelled).length};
}
window.ReportMath=Object.freeze({validDay,dayISO,eventDay,today,build,zone});
}());
