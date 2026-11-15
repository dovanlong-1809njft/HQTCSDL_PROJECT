// Run before/after restarting only the separately created upload QA container.
import {readFileSync,writeFileSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {createHash} from "node:crypto";
import assert from "node:assert/strict";
const origin=process.env.UPLOAD_QA_ORIGIN||"http://127.0.0.1:18101",family="e0100000-0000-0000-0000-000000000001";
const video=process.env.UPLOAD_QA_VIDEO;
const checkpoint=join(tmpdir(),video?"familyconnect-video-persistence.json":"familyconnect-upload-persistence.json");
for(let attempt=0;attempt<30;attempt++){
  try{if((await fetch(origin+"/api/auth/me")).status===401)break;}catch{}
  await new Promise(resolve=>setTimeout(resolve,300));
}
async function login(email){
  const response=await fetch(origin+"/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password:"UploadTestOnly!2026"})});
  assert.equal(response.status,200);return (await response.json()).access_token;
}
const token=await login("upload-one@example.com"),headers={Authorization:`Bearer ${token}`};
let url,hash;
if(process.argv[2]==="before"){
  const body=new FormData();body.append("files",new Blob([readFileSync(video||new URL("../../apps/web/public/share.png",import.meta.url))],{type:video?"video/mp4":"image/png"}),video?"ky-niem.mp4":"anh-gia-dinh.png");
  const uploaded=await fetch(origin+`/api/community/uploads?family_id=${family}`,{method:"POST",headers,body});
  assert.equal(uploaded.status,201);url=(await uploaded.json()).items[0].url;
  const post=await fetch(origin+"/api/community/posts",{method:"POST",headers:{...headers,"Content-Type":"application/json"},body:JSON.stringify({family_id:family,content:"Upload persistence QA",media:[{url,type:video?"video":"image"}]})});
  assert.equal(post.status,201);
  const response=await fetch(origin+url,{headers});assert.equal(response.status,200);
  hash=createHash("sha256").update(Buffer.from(await response.arrayBuffer())).digest("hex");
  writeFileSync(checkpoint,JSON.stringify({url,hash}));
}else{
  ({url,hash}=JSON.parse(readFileSync(checkpoint,"utf8")));
  const secondToken=await login("upload-two@example.com");
  const response=await fetch(origin+url,{headers:{Authorization:`Bearer ${secondToken}`}});assert.equal(response.status,200);
  assert.equal(createHash("sha256").update(Buffer.from(await response.arrayBuffer())).digest("hex"),hash);
  const feed=await fetch(origin+`/api/community/posts?family_id=${family}&page_size=100`,{headers});assert.equal(feed.status,200);
  assert.ok((await feed.json()).items.some(post=>post.media_urls.includes(url)));
}
console.log(`PASS ${process.argv[2]}: actual image, authenticated access and SQL post reference verified`);
