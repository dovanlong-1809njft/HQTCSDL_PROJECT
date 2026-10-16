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
      foundedDate:'2026-10-15', createdDate:'2026-10-15', photo:'', posts:le?18:26, heritage:le?8:12,
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
  let state;
  try {
    const raw = localStorage.getItem(KEY);
    const loaded = raw ? JSON.parse(raw) : null;
    state = loaded?.version === 1 && validFamily(loaded.families?.le) && validFamily(loaded.families?.nguyen) ? loaded : fresh();
  } catch (error) { state=fresh(); if(error.name!=='SyntaxError')writable=false; }
  function active() { try { const key=localStorage.getItem(ACTIVE); return key==='nguyen'?'nguyen':'le'; } catch (_) { return 'le'; } }
  let activeId = active();
  const clone = obj => JSON.parse(JSON.stringify(obj));
  function save(next) {
    // Giao diện vẫn chạy trong RAM nếu trình duyệt không cho lưu. Luôn báo rõ trạng thái.
    state=next;
    try { localStorage.setItem(KEY,JSON.stringify(state)); writable=true; } catch (_) { writable=false; }
    changed();
    return writable;
  }
  function setActive(key) {
    if (!(key in state.families)) return;
    activeId=key;
    try { localStorage.setItem(ACTIVE,key); } catch (_) { writable=false; }
    changed();
  }
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
  function get(key=activeId) { return prepare(clone(state.families[key])); }
  function update(family) {
    if (!validFamily(family) || !['le','nguyen'].includes(family.id)) throw Error('Dữ liệu mẫu không hợp lệ.');
    const next=clone(state); next.families[family.id]=prepare(clone(family)); return save(next);
  }
  function reset(key=activeId) { const next=clone(state);next.families[key]=seed(key);return save(next); }
  function changed(){if(typeof window.dispatchEvent==='function'&&typeof window.CustomEvent==='function')window.dispatchEvent(new window.CustomEvent('familyconnect:change'));}
  function refresh(){if(!writable)return false;try{const raw=localStorage.getItem(KEY);if(!raw)return false;const next=JSON.parse(raw);if(next?.version!==1||!validFamily(next.families?.le)||!validFamily(next.families?.nguyen))return false;state=next;changed();return true;}catch(_){return false;}}
  function uid() { return window.crypto?.randomUUID ? crypto.randomUUID() : Date.now().toString(36)+'-'+Math.random().toString(36).slice(2); }
  window.FamilyStore=Object.freeze({get,update,reset,setActive,refresh,getActive:()=>activeId,uid,isPersistent:()=>writable});
}());
