// Real browser -> nginx -> FastAPI -> SQL Server + Docker media volume.
import {createRequire} from "node:module";
import {readFileSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
const {test,expect}=createRequire(new URL("../../apps/web/package.json",import.meta.url))("@playwright/test");
const png=readFileSync(new URL("../../apps/web/public/share.png",import.meta.url));
const family="e0100000-0000-0000-0000-000000000001";
async function login(page,email="upload-one@example.com"){
  const result=await page.request.post("/api/auth/login",{data:{email,password:"UploadTestOnly!2026"}});
  expect(result.status()).toBe(200);
  const session=await result.json();
  await page.addInitScript(session=>{
    localStorage.setItem("familyconnect.token",session.access_token);
    localStorage.setItem("familyconnect.user",JSON.stringify({...session.user,fullName:session.user.full_name}));
  },session);
  return session.access_token;
}
test("select, preview, upload, publish and read as another member after refresh",async({page,browser})=>{
  const token=await login(page);await page.goto("/community");
  const text=`Ảnh thật E2E ${Date.now()}`;
  await page.getByRole("textbox",{name:"Nội dung",exact:true}).fill(text);
  await page.getByLabel("Chọn các tệp ảnh").setInputFiles([
    {name:"gia-dinh.png",mimeType:"image/png",buffer:png},
    {name:"ky-niem.png",mimeType:"image/png",buffer:png},
  ]);
  await expect(page.getByRole("img",{name:"Ảnh từ máy tính 1",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Xóa ảnh từ máy tính 2",exact:true}).click();
  await expect(page.getByText("1 ảnh đã thêm",{exact:true})).toBeVisible();
  const uploaded=page.waitForResponse(r=>r.url().includes("/api/community/uploads")&&r.request().method()==="POST");
  const posted=page.waitForResponse(r=>r.url().endsWith("/api/community/posts")&&r.request().method()==="POST");
  await page.getByRole("button",{name:"Đăng bài",exact:true}).click();
  const uploadResponse=await uploaded;expect(uploadResponse.status()).toBe(201);
  const url=(await uploadResponse.json()).items[0].url;
  expect((await posted).status()).toBe(201);
  const card=page.locator("article").filter({hasText:text});
  await expect(card.getByRole("img")).toBeVisible();
  await page.reload();await expect(card.getByRole("img")).toBeVisible();
  expect(await card.getByRole("img").getAttribute("src")).toMatch(/^blob:/);
  expect((await page.request.get(url,{headers:{Authorization:`Bearer ${token}`}})).status()).toBe(200);
  const context=await browser.newContext({baseURL:"http://127.0.0.1:18101"}),other=await context.newPage();
  const otherToken=await login(other,"upload-two@example.com");
  expect((await other.request.get(url,{headers:{Authorization:`Bearer ${otherToken}`}})).status()).toBe(200);
  await other.goto("/community");await expect(other.locator("article").filter({hasText:text}).getByRole("img")).toBeVisible();
  await context.close();
  expect((await page.request.get(url)).status()).toBe(401);
});
test("upload failure never creates a post; local limits keep composer usable",async({page})=>{
  await login(page);await page.goto("/community");
  await page.getByRole("textbox",{name:"Nội dung",exact:true}).fill("Bài này không được lưu");
  await page.getByLabel("Chọn các tệp ảnh").setInputFiles({name:"fake.png",mimeType:"image/png",buffer:Buffer.from("not an image")});
  let writes=0;page.on("request",r=>{if(r.method()==="POST"&&new URL(r.url()).pathname==="/api/community/posts")writes++;});
  await page.getByRole("button",{name:"Đăng bài",exact:true}).click();
  await expect(page.getByRole("alert")).toContainText("không phải ảnh hợp lệ");expect(writes).toBe(0);
  await page.getByRole("button",{name:"Xóa ảnh từ máy tính 1",exact:true}).click();
  await page.getByLabel("Chọn các tệp ảnh").setInputFiles({name:"big.png",mimeType:"image/png",buffer:Buffer.alloc(8*1024*1024+1)});
  await expect(page.getByRole("alert")).toContainText("8 MB");
  await expect(page.getByRole("button",{name:"Đăng bài",exact:true})).toBeEnabled();
});
test("API and private media reject outsiders and corrupt content",async({page})=>{
  const token=await login(page),headers={Authorization:`Bearer ${token}`};
  const data={name:"a.png",mimeType:"image/png",buffer:png};
  const result=await page.request.post(`/api/community/uploads?family_id=${family}`,{headers,multipart:{files:data}});
  expect(result.status()).toBe(201);const url=(await result.json()).items[0].url;
  const outsider=await page.request.post("/api/auth/login",{data:{email:"upload-outsider@example.com",password:"UploadTestOnly!2026"}});
  const unauthorizedHeaders={Authorization:`Bearer ${(await outsider.json()).access_token}`};
  expect((await page.request.get(url,{headers:unauthorizedHeaders})).status()).toBe(403);
  expect((await page.request.post(`/api/community/uploads?family_id=${family}`,{headers:unauthorizedHeaders,multipart:{files:data}})).status()).toBe(403);
  expect((await page.request.post(`/api/community/uploads?family_id=${family}`,{headers,multipart:{files:{...data,buffer:Buffer.from("<html>fake</html>")}}})).status()).toBe(415);
});
test("failed post retains uploaded draft for retry without uploading twice",async({page})=>{
  await login(page);await page.goto("/community");
  let fail=true,uploads=0;
  page.on("request",r=>{if(r.method()==="POST"&&new URL(r.url()).pathname==="/api/community/uploads")uploads++;});
  await page.route(url=>url.pathname==="/api/community/posts",async route=>{
    if(route.request().method()==="POST"&&fail){fail=false;return route.fulfill({status:500,json:{detail:"Thử nghiệm lỗi lưu bài."}});}
    await route.continue();
  });
  const text=`Thử lại bài ảnh ${Date.now()}`;
  await page.getByRole("textbox",{name:"Nội dung",exact:true}).fill(text);
  await page.getByLabel("Chọn các tệp ảnh").setInputFiles({name:"retry.png",mimeType:"image/png",buffer:png});
  await page.getByRole("button",{name:"Đăng bài",exact:true}).click();
  await expect(page.getByRole("alert")).toContainText("Thử nghiệm lỗi lưu bài");
  await page.getByRole("button",{name:"Đăng bài",exact:true}).click();
  await expect(page.locator("article").filter({hasText:text}).getByRole("img")).toBeVisible();
  expect(uploads).toBe(1);
});
function videoFile(){return {name:"ky-niem.mp4",mimeType:"video/mp4",buffer:readFileSync(process.env.UPLOAD_QA_VIDEO||join(tmpdir(),"familyconnect-qa-video.mp4"))};}
async function playVideo(video){
  await expect.poll(()=>video.evaluate(v=>v.readyState)).toBeGreaterThanOrEqual(2);
  await video.evaluate(async v=>{v.muted=true;await v.play();});
  await expect.poll(()=>video.evaluate(v=>v.currentTime)).toBeGreaterThan(0);
}
test("heritage uploads a photo from disk and shares it with another member",async({page,browser})=>{
  await login(page);await page.goto("/heritage");
  await page.getByRole("button",{name:"Thêm di sản",exact:true}).click();
  const form=page.getByRole("form",{name:"Thêm mới"}),title=`Di sản ảnh ${Date.now()}`;
  await form.getByRole("combobox",{name:"Loại",exact:true}).selectOption("photo");
  await form.getByRole("textbox",{name:"Tiêu đề",exact:true}).fill(title);
  await form.getByLabel("Chọn các tệp ảnh").setInputFiles({name:"di-san.png",mimeType:"image/png",buffer:png});
  await form.getByRole("button",{name:"Lưu",exact:true}).click();
  const card=page.locator("article").filter({hasText:title});await expect(card.getByRole("img")).toBeVisible();
  await page.reload();await expect(card.getByRole("img")).toBeVisible();
  const context=await browser.newContext({baseURL:"http://127.0.0.1:18101"}),other=await context.newPage();
  await login(other,"upload-two@example.com");await other.goto("/heritage");
  await expect(other.locator("article").filter({hasText:title}).getByRole("img")).toBeVisible();await context.close();
  await card.getByRole("button",{name:"Sửa",exact:true}).click();
  const edit=page.getByRole("form",{name:"Chỉnh sửa"});await edit.getByRole("textbox",{name:"Tiêu đề",exact:true}).fill(title+" sửa");
  await edit.getByRole("button",{name:"Lưu",exact:true}).click();await expect(page.locator("article").filter({hasText:title+" sửa"}).getByRole("img")).toBeVisible();
});
test("heritage uploads video, plays after refresh and filters video",async({page})=>{
  await login(page);await page.goto("/heritage");await page.getByRole("button",{name:"Thêm di sản",exact:true}).click();
  const form=page.getByRole("form",{name:"Thêm mới"}),title=`Di sản video ${Date.now()}`;
  await form.getByRole("combobox",{name:"Loại",exact:true}).selectOption("video");
  await form.getByRole("textbox",{name:"Tiêu đề",exact:true}).fill(title);
  await form.getByLabel("Chọn các tệp video").setInputFiles(videoFile());
  await expect(form.locator("video")).toBeVisible();await form.getByRole("button",{name:"Lưu",exact:true}).click();
  const card=page.locator("article").filter({hasText:title});await playVideo(card.locator("video"));
  await page.reload();await playVideo(card.locator("video"));
  await page.getByRole("combobox",{name:"Loại",exact:true}).selectOption("video");await expect(card.locator("video")).toBeVisible();
});
test("feed uploads mixed photo/video, preserves it and plays for another member",async({page,browser})=>{
  await login(page);await page.goto("/community");const text=`Bài video thật ${Date.now()}`;
  await page.getByRole("textbox",{name:"Nội dung",exact:true}).fill(text);
  await page.getByLabel("Chọn các tệp ảnh").setInputFiles({name:"photo.png",mimeType:"image/png",buffer:png});
  await page.getByLabel("Chọn các tệp video").setInputFiles(videoFile());
  await page.getByRole("button",{name:"Đăng bài",exact:true}).click();
  const card=page.locator("article").filter({hasText:text});await expect(card.getByRole("img")).toBeVisible();await playVideo(card.locator("video"));
  await page.reload();await playVideo(card.locator("video"));
  const context=await browser.newContext({baseURL:"http://127.0.0.1:18101"}),other=await context.newPage();
  await login(other,"upload-two@example.com");await other.goto("/community");await playVideo(other.locator("article").filter({hasText:text}).locator("video"));await context.close();
});
