/* Kho dữ liệu DEMO của giao diện, hoàn toàn không phải database hay phân quyền.
   Chỉ dùng localStorage cùng origin. Không lưu mật khẩu/token/dữ liệu gia đình thật. */
(function () {
  'use strict';
  const KEY = 'familyconnect.family-demo.v1';
  const ACTIVE = 'familyconnect.active-family';
  let writable = true;
  function seed(key) {
    const le = key === 'le';
    const surname = le ? 'Lê' : 'Nguyễn';
    const branches = [
      { id: key + '-hcm', name: 'Chi nhánh TP.HCM', location: 'TP. Hồ Chí Minh', description: 'Kết nối người thân đang sinh sống tại TP. Hồ Chí Minh.' },
      { id: key + '-dn', name: 'Chi nhánh Đà Nẵng', location: 'Đà Nẵng', description: 'Gìn giữ nếp nhà và chia sẻ những câu chuyện miền Trung.' }
    ];
    if (!le) branches.push({id:key+'-hn',name:'Chi nhánh Hà Nội',location:'Hà Nội',description:'Gắn kết người thân tại Hà Nội.'});
    const names = ['Văn Bình', 'Minh Tuấn', 'Thị Hương', 'Anh Khoa', 'Thị Mai', 'Văn An', 'Ngọc Hà', 'Minh Anh', 'Văn Nam', 'Thị Lan', 'Quốc Bảo', 'Thu Thảo', 'Hoàng Minh', 'Thanh Tâm', 'Gia Huy', 'Bảo Ngọc'];
    const members = Array.from({length: le ? 32 : 48}, (_, i) => ({
      id: key + '-person-' + (i + 1),
      name: surname + ' ' + names[i % names.length] + (i >= names.length ? ' ' + (Math.floor(i / names.length) + 1) : ''),
      generation: i === 0 ? 1 : (i < 4 ? (i === 3 ? 3 : 2) : (le ? 2 + i % 2 : 2 + i % 3)),
      branchId: le ? (i < 18 ? branches[0].id : (i < 30 ? branches[1].id : '')) : branches[i % 3].id,
      role: i === 0 ? 'Trưởng họ' : (i === 1 || i === 2 ? 'Đại diện chi nhánh' : 'Thành viên'),
      occupation: ['Nghỉ hưu', 'Kỹ sư', 'Giáo viên', 'Sinh viên'][i % 4],
      quote: ['Giữ gìn truyền thống là giữ gìn cội nguồn.', 'Kết nối và phát triển gia đình trong thời đại mới.', 'Cùng nhau xây dựng một gia đình đoàn kết, yêu thương.', 'Luôn hướng về cội nguồn và kết nối thế hệ trẻ.'][i % 4],
      featured: i < 4
    }));
    return { id: key, name:'Gia đình '+surname, description:'Kết nối các thế hệ, lưu giữ cội nguồn và cùng nhau phát triển.',
      representative: surname+' Văn Bình', address:'TP. Hồ Chí Minh · địa chỉ mẫu', phone:'', email:le?'giadinhle@example.com':'giadinhnguyen@example.com',
      foundedDate:'2026-10-15', createdDate:'2026-10-15', photo:'', posts:0, heritage:0,
      branches, members, activities:[
        {id:key+'-a1',type:'member',text:surname+' Thị Mai đã được thêm vào gia đình.',at:'2026-10-15T02:00:00Z'},
        {id:key+'-a2',type:'event',text:'Sự kiện “Gặp mặt cuối năm 2026” đã được tạo.',at:'2026-10-14T22:00:00Z'},
        {id:key+'-a3',type:'heritage',text:'Đã thêm tư liệu “Gia phả họ '+surname+'”.',at:'2026-10-14T02:00:00Z'}
      ] };
  }
  const fresh = () => ({version:1, families:{le:seed('le'),nguyen:seed('nguyen')}});
  function validFamily(f) {
    return f && typeof f.name==='string' && typeof f.description==='string' && typeof f.representative==='string'
      && ['address','phone','email','foundedDate','createdDate','photo'].every(k=>typeof f[k]==='string')
      && Number.isFinite(f.posts) && Number.isFinite(f.heritage)
      && (f.photo==='' || /^data:image\/(png|jpeg);base64,/.test(f.photo))
      && Array.isArray(f.branches) && f.branches.every(b=>b && ['id','name','location','description'].every(k=>typeof b[k]==='string'))
      && Array.isArray(f.members) && f.members.every(m=>m && ['id','name','branchId','role','occupation','quote'].every(k=>typeof m[k]==='string') && Number.isInteger(m.generation) && m.generation>0 && m.generation<=20 && typeof m.featured==='boolean')
      && Array.isArray(f.activities) && f.activities.every(a=>a && ['id','type','text','at'].every(k=>typeof a[k]==='string'));
  }
  let state,corrupt=false;
  try {
    const raw = localStorage.getItem(KEY);
    const loaded = raw ? JSON.parse(raw) : null;
    if(raw&&!loaded){corrupt=true;throw Error('Dữ liệu rỗng');}
    if(raw&&!validState(loaded))corrupt=true;state = validState(loaded) ? loaded : fresh();
  } catch (error) { state=fresh();corrupt=corrupt||error.name==='SyntaxError';writable=false; }
  function validState(s){return s?.version===1&&s.families&&Object.keys(s.families).length>0&&Object.values(s.families).every(validFamily);}
  function active() {const user=window.FamilyIdentity?.id()||'guest',keys=Object.keys(state.families),accessible=keys.filter(id=>state.families[id].memberships?.[user]?.status==='active'||user==='demo'&&['le','nguyen'].includes(id)&&!state.families[id].memberships?.demo);try{const k=localStorage.getItem(ACTIVE);return accessible.includes(k)?k:accessible[0]||keys[0];}catch{return accessible[0]||keys[0];}}
  let activeId=active();
  const clone=obj=>JSON.parse(JSON.stringify(obj));
  let diskVersion;try{diskVersion=localStorage.getItem(KEY);}catch{diskVersion=null;}
  function checkDisk(){if(corrupt)throw Error('Dữ liệu lưu bị hỏng. Hãy xuất bản sao bằng công cụ trình duyệt trước khi xóa/khôi phục; ứng dụng không tự ghi đè.');let current;try{current=localStorage.getItem(KEY);}catch{return;}if(current!==diskVersion)throw Error('Dữ liệu đã đổi ở tab khác. Tải lại trang trước khi lưu để tránh ghi đè.');}
  function save(next){checkDisk();state=next;try{const raw=JSON.stringify(state);localStorage.setItem(KEY,raw);diskVersion=raw;writable=true;}catch{writable=false;}changed();return writable;}
  function setActive(key){if(!state.families[key])return;activeId=key;try{localStorage.setItem(ACTIVE,key);}catch{writable=false;}changed();}
  // Additive migration: keep all previously edited family/member fields.
  function prepare(f) {
    if (!Array.isArray(f.relations)) {
      // Explicit example edges only for original seed IDs and matching levels.
      const edges=[[0,1],[0,2],[0,4],[0,6],[1,3],[1,5],[8,3],[8,5],[6,7],[6,9]];
      const id=i=>f.id+'-person-'+(i+1), person=i=>f.members.find(m=>m.id===id(i));
      f.relations=edges.filter(([a,b])=>person(a)&&person(b)&&person(a).generation<person(b).generation)
        .map(([a,b])=>({id:'demo-'+a+'-'+b,type:'parent',from:id(a),to:id(b)}));
      if(person(1)&&person(8))f.relations.push({id:'demo-spouse',type:'spouse',from:id(1),to:id(8)});
    }
    const ids=new Set(f.members.map(m=>m.id));
    f.relations=f.relations.filter(r=>r && typeof r.id==='string' && ['parent','spouse'].includes(r.type)&&ids.has(r.from)&&ids.has(r.to)&&r.from!==r.to);
    if(Array.isArray(f.messageDrafts))f.messageDrafts=f.messageDrafts.filter(d=>d&&ids.has(d.memberId));
    return f;
  }
  const who=()=>window.FamilyIdentity?.id()||'guest';
  function membership(f,user=who()){return f.memberships?.[user]||{status:['le','nguyen'].includes(f.id)&&user==='demo'?'active':'none',role:user==='demo'?'admin':'member',memberId:''};}
  function catalog(f){
    // Mọi trang nhận cùng một tập dữ liệu; không phụ thuộc thứ tự mở trang.
    f.community ||= {version:1,posts:[]};f.heritageData ||= {version:1,items:[],collections:[]};f.eventData ||= {version:1,items:[],reminders:[]};
    f.posts=f.community.posts.filter(p=>p.status!=='hidden').length;f.heritage=f.heritageData.items.filter(r=>r.status!=='hidden').length;
    f.memberships ||= {};if(['le','nguyen'].includes(f.id)&&!f.memberships.demo)f.memberships.demo={status:'active',role:'admin',memberId:''};f.announcements ||= [];f.personal ||= {};
    // Nội dung từ phiên bản preview cũ thuộc tài khoản demo, không gán cho tài khoản mới.
    const rename=v=>v==='preview-user'?'demo':v;
    for(const p of f.community.posts){p.authorId=rename(p.authorId);for(const c of p.comments||[])c.authorId=rename(c.authorId);for(const key of ['reactions'])if(p[key]?.['preview-user']){p[key].demo=p[key]['preview-user'];delete p[key]['preview-user'];}if(p.poll?.votes&&Object.hasOwn(p.poll.votes,'preview-user')){p.poll.votes.demo=p.poll.votes['preview-user'];delete p.poll.votes['preview-user'];}}
    for(const e of f.eventData.items){e.organizer=rename(e.organizer);e.participants||={};if(e.participants['preview-user']){e.participants.demo=e.participants['preview-user'];delete e.participants['preview-user'];}}
    for(const r of f.heritageData.items)r.contributorId=rename(r.contributorId);
    return f;
  }
  function project(raw){const f=catalog(prepare(clone(raw))),u=who();f.personal[u] ||= clone(u==='demo'?{notificationData:f.notificationData,aiData:f.aiData,messageDrafts:f.messageDrafts,invitationDrafts:f.invitationDrafts}:{});const personal=f.personal[u];for(const k of ['notificationData','aiData','messageDrafts','invitationDrafts'])f[k]=clone(personal[k]||({notificationData:{version:1,readIds:[],hiddenIds:[]},aiData:{version:1,chats:[]},messageDrafts:[],invitationDrafts:[]}[k]));for(const p of f.community.posts)p.saved=Boolean(personal.savedPosts?.includes(p.id)||(u==='demo'&&personal.savedPosts===undefined&&p.saved));for(const r of f.heritageData.items)r.favorite=Boolean(personal.favoriteResources?.includes(r.id)||(u==='demo'&&personal.favoriteResources===undefined&&r.favorite));f._revision=raw._revision||0;return f;}
  function get(key=activeId){if(!state.families[key])throw Error('Không tìm thấy gia đình.');return project(state.families[key]);}
  function update(family){
    if(!validFamily(family)||!state.families[family.id])throw Error('Dữ liệu mẫu không hợp lệ.');
    if((family._revision||0)!==(state.families[family.id]._revision||0))throw Error('Dữ liệu đã được cập nhật. Tải lại trang trước khi lưu.');
    const next=clone(state),f=catalog(prepare(clone(family))),u=who();
    window.FamilyDataValidation?.reconcile(f,catalog(prepare(clone(state.families[f.id]))));
    window.FamilyDataValidation?.validate(f);
    window.FamilyPermissions?.authorize(project(state.families[f.id]),f,u,membership(state.families[f.id],u));
    f.personal[u]={...f.personal[u],...Object.fromEntries(['notificationData','aiData','messageDrafts','invitationDrafts'].map(k=>[k,f[k]])),savedPosts:f.community.posts.filter(p=>p.saved).map(p=>p.id),favoriteResources:f.heritageData.items.filter(r=>r.favorite).map(r=>r.id)};
    for(const k of ['notificationData','aiData','messageDrafts','invitationDrafts'])delete f[k];for(const p of f.community.posts)delete p.saved;for(const r of f.heritageData.items)delete r.favorite;
    for(const personal of Object.values(f.personal)){if(personal.messageDrafts)personal.messageDrafts=personal.messageDrafts.filter(d=>f.members.some(m=>m.id===d.memberId));}
    for(const e of f.eventData.items)for(const key of Object.keys(e.participants))if(!f.members.some(m=>m.id===key)&&!window.FamilyIdentity.accounts().some(u=>u.id===key))delete e.participants[key];
    for(const r of f.heritageData.items)if(r.personId&&!f.members.some(m=>m.id===r.personId))r.personId='';
    for(const m of Object.values(f.memberships))if(m.memberId&&!f.members.some(p=>p.id===m.memberId))m.memberId='';
    f._revision=(family._revision||0)+1;next.families[f.id]=f;const ok=save(next);family._revision=f._revision;return ok;
  }
  function create(name,description=''){if(!name.trim()||name.trim().length>100)throw Error('Tên gia đình cần từ 1–100 ký tự.');const id='family-'+uid(),f=catalog({id,name:name.trim(),description,representative:window.FamilyIdentity.name(),address:'',phone:'',email:'',foundedDate:'',createdDate:new Date().toISOString().slice(0,10),photo:'',posts:0,heritage:0,members:[],branches:[],relations:[],activities:[],memberships:{[who()]:{status:'active',role:'admin',memberId:''}},_revision:0});const next=clone(state);next.families[id]=f;save(next);setActive(id);return id;}
  function list(){return Object.values(state.families).map(raw=>({id:raw.id,name:raw.name,...membership(raw)}));}
  function reset(key=activeId){if(membership(state.families[key]).role!=='admin'||membership(state.families[key]).status!=='active')throw Error('Chỉ quản trị viên gia đình được khôi phục mẫu.');const next=clone(state);if(!['le','nguyen'].includes(key))throw Error('Chỉ khôi phục được hai gia đình minh họa ban đầu.');next.families[key]=seed(key);next.families[key]._revision=(state.families[key]._revision||0)+1;return save(next);}
  function changed(){if(typeof window.dispatchEvent==='function'&&typeof window.CustomEvent==='function')window.dispatchEvent(new window.CustomEvent('familyconnect:change'));}
  function refresh(){if(!writable)return false;try{const raw=localStorage.getItem(KEY);if(!raw)return false;const next=JSON.parse(raw);if(!validState(next))return false;state=next;diskVersion=raw;if(!state.families[activeId])activeId=Object.keys(state.families)[0];changed();return true;}catch{return false;}}
  function uid(){return window.crypto?.randomUUID?crypto.randomUUID():Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);}
  window.FamilyStore=Object.freeze({get,update,reset,setActive,refresh,create,list,membership,has:key=>Boolean(state.families[key]),getActive:()=>activeId,uid,isPersistent:()=>writable});
}());
