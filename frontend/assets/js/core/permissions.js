/* Quyền thao tác trên kho mẫu. Không phải ranh giới bảo mật của hệ thống thật. */
(()=>{'use strict';const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b),omit=(x,keys)=>Object.fromEntries(Object.entries(x||{}).filter(([k])=>!keys.includes(k)));
function authorize(old,next,user,membership){if(membership.status==='active'&&membership.role==='admin')return;
const ignore=['personal','notificationData','aiData','messageDrafts','invitationDrafts','activities','_revision','posts','heritage','memberships'];
if(membership.status!=='active'){
if(!equal(omit(old,ignore),omit(next,ignore)))throw Error('Bạn chưa được duyệt vào gia đình này.');
const before={...old.memberships},after={...next.memberships};delete before[user];delete after[user];if(!equal(before,after))throw Error('Không thể thay đổi tư cách người khác.');const target=next.memberships?.[user];if(!target||!['pending','none'].includes(target.status)||target.role!=='member'||target.memberId)throw Error('Yêu cầu tham gia không hợp lệ.');return;}
for(const key of ['name','description','representative','address','phone','email','foundedDate','photo','members','branches','relations','memberships','announcements','moderationLog','adminData'])if(!equal(old[key],next[key]))throw Error('Thao tác này dành cho quản trị viên gia đình mẫu.');
// Thành viên sửa nội dung của mình; lưu bài, yêu thích, đếm lượt xem là trạng thái riêng/được phép.
for(const [before,after,idKey,allowed]of [[old.community?.posts||[],next.community?.posts||[],'authorId',['saved','reactions','comments','poll']],[old.heritageData?.items||[],next.heritageData?.items||[],'contributorId',['favorite','views']]]){
for(const x of before){const y=after.find(p=>p.id===x.id);if(x[idKey]!==user&&(!y||!equal(omit(x,allowed),omit(y,allowed))))throw Error('Chỉ chỉnh sửa hoặc xóa nội dung do bạn tạo.');if(y&&x[idKey]!==user&&x.poll&&!equal(x.poll.options,y.poll?.options))throw Error('Không sửa lựa chọn bình chọn của người khác.');if(y&&x.authorId){for(const c of x.comments||[]){const n=y.comments?.find(v=>v.id===c.id);if(c.authorId!==user&&(!n||!equal(c,n)))throw Error('Không sửa bình luận của người khác.');}}}
for(const y of after)if(!before.some(p=>p.id===y.id)&&y[idKey]!==user)throw Error('Người tạo nội dung phải là tài khoản hiện tại.');}
for(const x of old.eventData?.items||[]){const y=next.eventData?.items?.find(e=>e.id===x.id);if(x.createdBy!==user&&x.organizer!==user){if(!y||!equal(omit(x,['participants','album']),omit(y,['participants','album'])))throw Error('Chỉ người tổ chức hoặc quản trị viên được sửa sự kiện.');const a={...x.participants},b={...y.participants};delete a[user];delete b[user];if(!equal(a,b))throw Error('Chỉ cập nhật phản hồi tham gia của chính bạn.');}}
}
window.FamilyPermissions=Object.freeze({authorize});})();
