/* Danh tính dùng chung cho bản frontend. Không thay thế xác thực máy chủ. */
(()=>{'use strict';const read=(k,f)=>{try{return JSON.parse(localStorage.getItem(k))||f;}catch{return f;}};
function id(){return window.FamilyDemoAuth?.getSession()?.id||'guest';}
function name(){return read('familyconnect.profile-demo.v1',{}).profile?.name||window.FamilyDemoAuth?.getSession()?.name||'Người dùng mẫu';}
function accounts(){const list=read('familyconnect.demo.accounts.v1',[]);return [{id:'demo',name:'Nguyễn Văn A',email:'demo@familyconnect.local'},...list.map(({id,name,email,username})=>({id,name,email,username}))];}
window.FamilyIdentity=Object.freeze({id,name,accounts});})();
