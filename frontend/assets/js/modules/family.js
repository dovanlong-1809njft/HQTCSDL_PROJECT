/* Gia đình của tôi — tất cả thao tác là demo ở trình duyệt, không có API. */
(function () {
  'use strict';
  const S=window.FamilyStore;
  if (!S || !document.getElementById('family-name')) return;
  const $=id=>document.getElementById(id);
  const make=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;};
  let family=S.get(), editingMember=null, editingBranch=null, detailMember=null, draftPhoto='', photoVersion=0, confirmAction=null;
  const dialogIds=['family-dialog','member-dialog','members-dialog','detail-dialog','branch-dialog','confirm-dialog','activities-dialog'];
  function toast(text){ window.FamilyUI?.toast(text); }
  function initials(name){return name.trim().split(/\s+/).slice(-2).map(w=>w.charAt(0)).join('').toUpperCase();}
  function date(text){const d=new Date(text);return Number.isNaN(d.getTime())?'Chưa có':d.toLocaleDateString('vi-VN');}
  function generations(members){return new Set(members.map(m=>m.generation)).size;}
  function branchName(id){return family.branches.find(b=>b.id===id)?.name || 'Chưa phân nhánh';}
  function error(id,message){$(id).textContent=message;$(id).hidden=!message;}
  function activity(type,text){family.activities.unshift({id:S.uid(),type,text,at:new Date().toISOString()});family.activities=family.activities.slice(0,100);}
  function persist(message){const saved=S.update(family);family=S.get();render();toast(saved?message:message+' Chưa lưu được trên trình duyệt; tải lại sẽ mất.');}
  function show(id){$(id).showModal();if(id==='family-dialog')document.body.classList.add('family-edit-open');}
  function close(id){$(id).close();}
  dialogIds.forEach(id=>{
    $(id).addEventListener('close',()=>{if(id==='family-dialog'){document.body.classList.remove('family-edit-open');photoVersion++;}if(id==='confirm-dialog')confirmAction=null;});
  });
  document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>close(b.dataset.close)));
  function photo(node,src){node.replaceChildren();if(src){const img=make('img');img.src=src;img.alt='Ảnh đại diện '+family.name;node.append(img);}else node.append(make('span','',family.id==='le'?'LÊ':'NG'));}
  function openEdit(){
    draftPhoto=family.photo;photoVersion++;
    $('family-edit-name').value=family.name;$('family-edit-description').value=family.description;
    $('family-edit-representative').value=family.representative;$('family-edit-address').value=family.address;
    $('family-edit-phone').value=family.phone;$('family-edit-email').value=family.email;$('family-edit-date').value=family.foundedDate;
    $('photo-file').value='';$('save-family').disabled=false;
    $('description-counter').textContent=family.description.length+'/500';photo($('edit-photo-preview'),draftPhoto);error('family-error','');show('family-dialog');
  }
  ['edit-family','edit-contact','edit-photo-open'].forEach(id=>$(id).addEventListener('click',openEdit));
  $('family-edit-description').addEventListener('input',e=>$('description-counter').textContent=e.target.value.length+'/500');
  $('choose-photo').addEventListener('click',()=>$('photo-file').click());
  $('remove-photo').addEventListener('click',()=>{photoVersion++;draftPhoto='';$('photo-file').value='';$('save-family').disabled=false;photo($('edit-photo-preview'),'');});
  $('photo-file').addEventListener('change',async e=>{
    const file=e.target.files[0];if(!file)return;
    if(!['image/jpeg','image/png'].includes(file.type)||file.size>5*1024*1024){error('family-error','Chọn ảnh JPG hoặc PNG không quá 5 MB.');e.target.value='';return;}
    const version=++photoVersion;error('family-error','');$('save-family').disabled=true;
    try {
      const url=URL.createObjectURL(file);
      try {
        const img=new Image();img.src=url;await img.decode();
        // Thu nhỏ ảnh do người dùng chọn để tránh vượt dung lượng localStorage.
        const canvas=document.createElement('canvas');canvas.width=canvas.height=320;
        const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,320,320);
        const side=Math.min(img.naturalWidth,img.naturalHeight);ctx.drawImage(img,(img.naturalWidth-side)/2,(img.naturalHeight-side)/2,side,side,0,0,320,320);
        if(version===photoVersion && $('family-dialog').open){draftPhoto=canvas.toDataURL('image/jpeg',0.85);photo($('edit-photo-preview'),draftPhoto);}
      } finally {URL.revokeObjectURL(url);}
    } catch(_){if(version===photoVersion)error('family-error','Không đọc được ảnh. Hãy chọn tệp JPG/PNG hợp lệ.');}
    finally{if(version===photoVersion)$('save-family').disabled=false;}
  });
  $('family-form').addEventListener('submit',e=>{
    e.preventDefault();const name=$('family-edit-name').value.trim(),rep=$('family-edit-representative').value.trim(),phone=$('family-edit-phone').value.trim();
    if(!name||!rep){error('family-error','Vui lòng nhập tên gia đình và người đại diện.');return;}
    if(phone&&!/^[+\d\s().-]{6,30}$/.test(phone)){error('family-error','Số điện thoại cần từ 6–30 ký tự, gồm số và dấu +, khoảng trắng, (), dấu chấm hoặc gạch nối.');return;}
    Object.assign(family,{name,representative:rep,description:$('family-edit-description').value.trim(),address:$('family-edit-address').value.trim(),phone,email:$('family-edit-email').value.trim(),foundedDate:$('family-edit-date').value,photo:draftPhoto});
    activity('family','Đã cập nhật thông tin gia đình.');persist('Đã lưu thông tin gia đình trên trình duyệt.');close('family-dialog');
  });
  function branchOptions(node,all=false){const previous=node.value;node.replaceChildren(make('option','',all?'Tất cả chi nhánh':'Chưa phân nhánh'));node.options[0].value=all?'all':'';family.branches.forEach(b=>{const o=make('option','',b.name);o.value=b.id;node.append(o);});if(all){const o=make('option','','Chưa phân nhánh');o.value='unassigned';node.append(o);}if([...node.options].some(o=>o.value===previous))node.value=previous;}
  function openMember(member=null){
    editingMember=member?.id || null;$('member-form').reset();branchOptions($('member-branch'));
    $('member-dialog-title').textContent=member?'Chỉnh sửa thành viên':'Thêm thành viên';
    $('member-name').value=member?.name||'';$('member-generation').value=member?.generation||3;
    $('member-branch').value=member?.branchId||'';$('member-role').value=member?.role||'Thành viên';
    $('member-occupation').value=member?.occupation||'';$('member-quote').value=member?.quote||'';$('member-featured').checked=!!member?.featured;
    error('member-error','');show('member-dialog');
  }
  $('add-member').addEventListener('click',()=>openMember());
  $('member-form').addEventListener('submit',e=>{
    e.preventDefault();const name=$('member-name').value.trim(),generation=Number($('member-generation').value),branchId=$('member-branch').value;
    if(!name){error('member-error','Vui lòng nhập họ tên.');return;}
    if(!Number.isInteger(generation)||generation<1||generation>20){error('member-error','Thế hệ phải là số nguyên từ 1 đến 20.');return;}
    if(branchId&&!family.branches.some(b=>b.id===branchId)){error('member-error','Chi nhánh không còn tồn tại.');return;}
    const member={...(family.members.find(m=>m.id===editingMember)||{}),id:editingMember||S.uid(),name,generation,branchId,role:$('member-role').value,occupation:$('member-occupation').value.trim(),quote:$('member-quote').value.trim(),featured:$('member-featured').checked};
    if(editingMember && (family.relations||[]).some(r=>r.type==='parent' && ((r.from===editingMember && generation>=family.members.find(m=>m.id===r.to)?.generation)||(r.to===editingMember && generation<=family.members.find(m=>m.id===r.from)?.generation)))){error('member-error','Thế hệ phải phù hợp với quan hệ cha mẹ–con đã có trong Cây gia phả.');return;}
    if(editingMember)family.members[family.members.findIndex(m=>m.id===editingMember)]=member;else family.members.push(member);
    activity('member',(editingMember?'Đã cập nhật hồ sơ ':'Đã thêm thành viên ')+name+'.');persist(editingMember?'Đã cập nhật thành viên mẫu.':'Đã thêm thành viên mẫu.');close('member-dialog');
  });
  function openDetail(member){
    detailMember=member.id;const target=$('member-detail');target.replaceChildren();
    const header=make('div','member-detail');header.append(make('span','member-avatar',initials(member.name)));
    const name=make('div');name.append(make('h3','',member.name),make('p','small',member.role));header.append(name);target.append(header);
    const dl=make('dl');[['Thế hệ',member.generation],['Chi nhánh',branchName(member.branchId)],['Nghề nghiệp',member.occupation||'Chưa cập nhật'],['Lời nhắn',member.quote||'Chưa cập nhật']].forEach(([label,value])=>dl.append(make('dt','',label),make('dd','',String(value))));target.append(dl);show('detail-dialog');
  }
  $('edit-member-detail').addEventListener('click',()=>{const member=family.members.find(m=>m.id===detailMember);close('detail-dialog');if(member)openMember(member);});
  $('delete-member-detail').addEventListener('click',()=>{const member=family.members.find(m=>m.id===detailMember);close('detail-dialog');if(!member)return;confirm('Xóa thành viên mẫu?', 'Xóa hồ sơ '+member.name+' cùng các quan hệ liên quan khỏi gia đình mẫu trên trình duyệt?',()=>{family.members=family.members.filter(m=>m.id!==member.id);activity('member','Đã xóa hồ sơ '+member.name+'.');persist('Đã xóa thành viên mẫu.');});});
  function normalize(s){return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase();}
  function renderMembers(){
    const query=normalize($('member-search').value.trim()),filter=$('member-branch-filter').value;
    const members=family.members.filter(m=>normalize(m.name).includes(query)&&(filter==='all'||(filter==='unassigned'?!m.branchId:m.branchId===filter)));
    $('member-results').textContent='Hiển thị '+members.length+' / '+family.members.length+' thành viên';const list=$('all-members');list.replaceChildren();
    members.forEach(m=>{const row=make('div','member-list-row'),copy=make('div','member-list-copy');copy.append(make('strong','member-name',m.name),make('p','',branchName(m.branchId)+' · Thế hệ '+m.generation));const button=make('button','btn-link','Xem hồ sơ');button.type='button';button.setAttribute('aria-label','Xem hồ sơ '+m.name);button.addEventListener('click',()=>{close('members-dialog');openDetail(m);});row.append(make('span','member-avatar',initials(m.name)),copy,button);list.append(row);});
    if(!members.length)list.append(make('p','empty-state','Không có thành viên phù hợp.'));
  }
  function openMembers(branch='all'){$('member-search').value='';branchOptions($('member-branch-filter'),true);$('member-branch-filter').value=branch;renderMembers();show('members-dialog');}
  $('view-members').addEventListener('click',()=>openMembers());$('member-search').addEventListener('input',renderMembers);$('member-branch-filter').addEventListener('change',renderMembers);
  function openBranch(branch=null){editingBranch=branch?.id||null;$('branch-form').reset();$('branch-dialog-title').textContent=branch?'Chỉnh sửa chi nhánh':'Thêm chi nhánh';$('branch-name').value=branch?.name||'';$('branch-location').value=branch?.location||'';$('branch-description').value=branch?.description||'';error('branch-error','');show('branch-dialog');}
  $('add-branch').addEventListener('click',()=>openBranch());
  $('branch-form').addEventListener('submit',e=>{
    e.preventDefault();const name=$('branch-name').value.trim();if(!name){error('branch-error','Vui lòng nhập tên chi nhánh.');return;}
    if(family.branches.some(b=>b.id!==editingBranch&&normalize(b.name)===normalize(name))){error('branch-error','Tên chi nhánh đã tồn tại trong gia đình.');return;}
    const branch={id:editingBranch||S.uid(),name,location:$('branch-location').value.trim(),description:$('branch-description').value.trim()};
    if(editingBranch)family.branches[family.branches.findIndex(b=>b.id===editingBranch)]=branch;else family.branches.push(branch);
    activity('branch',(editingBranch?'Đã cập nhật ':'Đã tạo ')+name+'.');persist('Đã lưu chi nhánh mẫu.');close('branch-dialog');
  });
  function confirm(title,message,action){$('confirm-title').textContent=title;$('confirm-message').textContent=message;confirmAction=action;show('confirm-dialog');}
  $('confirm-action').addEventListener('click',()=>{const action=confirmAction;close('confirm-dialog');if(action)action();});
  function deleteBranch(branch){
    if(family.members.some(m=>m.branchId===branch.id)){toast('Chi nhánh còn thành viên. Hãy chuyển họ sang nhánh khác trước khi xóa.');return;}
    confirm('Xóa chi nhánh?', 'Xóa “'+branch.name+'” khỏi gia đình mẫu?',()=>{family.branches=family.branches.filter(b=>b.id!==branch.id);activity('branch','Đã xóa '+branch.name+'.');persist('Đã xóa chi nhánh mẫu.');});
  }
  function renderHistory(node,limit){node.replaceChildren();family.activities.slice(0,limit).forEach(a=>{const li=make('li'),symbol=make('span','history-icon',a.type==='member'?'＋':'•');symbol.setAttribute('aria-hidden','true');const copy=make('div','history-copy');const time=make('time','',new Date(a.at).toLocaleString('vi-VN'));time.dateTime=a.at;copy.append(make('p','',a.text),time);li.append(symbol,copy);node.append(li);});}
  $('view-activities').addEventListener('click',()=>{renderHistory($('all-activities'),100);show('activities-dialog');});
  $('reset-family').addEventListener('click',()=>confirm('Khôi phục dữ liệu mẫu?', 'Thông tin, ảnh, thành viên và chi nhánh bạn đã sửa của gia đình này sẽ trở về ban đầu. Gia đình còn lại không bị thay đổi.',()=>{S.reset();family=S.get();render();toast('Đã khôi phục gia đình mẫu.');}));
  $('family-select').value=S.getActive();
  $('family-select').addEventListener('change',e=>{S.setActive(e.target.value);family=S.get();render();toast('Đã chuyển gia đình mẫu.');});
  function render(){
    $('family-name').textContent=family.name;document.title=family.name+' | FamilyConnect';$('family-description').textContent=family.description||'Chưa cập nhật mô tả.';photo($('family-photo'),family.photo);
    [...$('family-select').options].forEach(o=>o.textContent=S.get(o.value).name+' · mẫu');
    const data={members:family.members.length,branches:family.branches.length,posts:family.posts,heritage:family.heritage};Object.entries(data).forEach(([k,v])=>$('family-stat-'+k).textContent=String(v));
    const meta=$('family-meta');meta.replaceChildren();[family.members.length+' thành viên',generations(family.members)+' thế hệ',family.branches.length+' chi nhánh','Tạo ngày '+date(family.createdDate)].forEach(text=>meta.append(make('span','chip',text)));
    const featured=$('featured-members');featured.replaceChildren();const featuredPeople=family.members.filter(m=>m.featured);
    featuredPeople.slice(0,4).forEach(m=>{const card=make('button','member-card');card.type='button';card.setAttribute('aria-label','Xem hồ sơ '+m.name);const top=make('div','member-top'),copy=make('div','member-info'),badges=make('div','member-badges');badges.append(make('span','member-badge',m.role),make('span','member-badge blue','Thế hệ '+m.generation));copy.append(make('strong','member-name',m.name),badges);top.append(make('span','member-avatar',initials(m.name)),copy);card.append(top,make('p','member-location',branchName(m.branchId)),make('p','member-quote',m.quote||'Cùng kết nối và gìn giữ câu chuyện gia đình.'));card.addEventListener('click',()=>openDetail(m));featured.append(card);});
    if(!featuredPeople.length)featured.append(make('p','empty-state','Chưa chọn thành viên nổi bật. Bạn có thể chọn khi thêm/sửa hồ sơ.'));
    $('featured-title').textContent=featuredPeople.length>4?'Thành viên nổi bật · hiển thị 4/'+featuredPeople.length:'Thành viên nổi bật';
    const branches=$('branches-list');branches.replaceChildren();family.branches.forEach(b=>{const members=family.members.filter(m=>m.branchId===b.id);const card=make('article','branch-card'),head=make('div','branch-header'),copy=make('div','branch-copy');copy.append(make('h3','',b.name),make('p','branch-count',members.length+' thành viên · '+generations(members)+' thế hệ'),make('p','branch-location',b.location||'Chưa cập nhật địa điểm'));head.append(make('span','branch-symbol','⌂'),copy);card.append(head);if(b.description)card.append(make('p','small',b.description));const actions=make('div','branch-actions');[['Xem thành viên',()=>openMembers(b.id)],['Sửa',()=>openBranch(b)],['Xóa',()=>deleteBranch(b)]].forEach(([text,fn])=>{const button=make('button','btn-link'+(text==='Xóa'?' danger-link':''),text);button.type='button';button.setAttribute('aria-label',text+' · '+b.name);button.addEventListener('click',fn);actions.append(button);});card.append(actions);branches.append(card);});
    if(!family.branches.length)branches.append(make('p','empty-state','Chưa có chi nhánh. Thêm chi nhánh đầu tiên cho gia đình.'));
    const contact=$('family-contact');contact.replaceChildren();[['Người đại diện',family.representative],['Ngày thành lập',family.foundedDate?date(family.foundedDate):'Chưa cập nhật'],['Địa chỉ',family.address],['Số điện thoại',family.phone],['Email',family.email]].forEach(([label,value])=>{const box=make('div');box.append(make('dt','',label),make('dd','',value||'Chưa cập nhật'));contact.append(box);});
    renderHistory($('family-history'),4);$('family-storage-note').textContent=S.isPersistent()?'Bản xem trước · Thay đổi được lưu trên trình duyệt này, chưa gửi đến máy chủ.':'Trình duyệt chưa lưu được dữ liệu. Thay đổi chỉ giữ trong tab này và sẽ mất khi tải lại.';
  }
  render();
}());
