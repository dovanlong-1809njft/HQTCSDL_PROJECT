// Browser interactions against the real React pages, with deterministic API contracts.
// SQL persistence/concurrency is exercised separately by test_comment_reactions_sql.py.
import {createRequire} from "node:module";
const {test,expect}=createRequire(new URL("../../apps/web/package.json",import.meta.url))("@playwright/test");

async function setup(page){
  const state={post:null,comment:null,fail:false,requests:0};
  await page.addInitScript(()=>{
    localStorage.setItem("familyconnect.token","browser-test-token");
    localStorage.setItem("familyconnect.user",JSON.stringify({id:"user",fullName:"Thành viên",role:"member"}));
  });
  await page.route("**/media/**",route=>route.request().url().includes("missing")?route.fulfill({status:404}):route.fulfill({contentType:"image/svg+xml",body:'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="300"><rect width="600" height="300" fill="#537964"/></svg>'}));
  const summary=value=>({my_reaction:value,reaction_count:value?1:0,reaction_counts:value?{[value]:1}:{}});
  await page.route(url=>url.pathname.startsWith("/api/"),async route=>{
    const path=new URL(route.request().url()).pathname,method=route.request().method();
    let data=[];
    if(path==="/api/settings")data={site_name:"FamilyConnect",logo_url:"/favicon.svg",theme:"forest",registration_enabled:true};
    else if(path.endsWith("/reactions")){
      state.requests++;
      await new Promise(resolve=>setTimeout(resolve,100));
      if(state.fail){state.fail=false;return route.fulfill({status:500,json:{detail:"Không lưu được cảm xúc thử nghiệm."}});}
      const target=path.includes("/comments/")?"comment":"post";
      state[target]=route.request().postDataJSON().type;
      data={type:state[target],...summary(state[target])};
    }else if(path.endsWith("/heritage/families"))data=[{id:"family",name:"Gia đình kiểm thử"}];
    else if(path.endsWith("/community/posts")){
      if(method==="POST")data={};
      else data={items:[{post_id:"post",family_id:"family",author_id:"other",author_name:"Người thân",content:"Nội dung bài kiểm thử",created_at:"2026-11-16T10:00:00Z",comment_count:1,media_urls:Array.from({length:6},(_,i)=>`/media/${i}.png`),...summary(state.post)}],total:1};
    }else if(path.endsWith("/comments"))data=[{id:"comment",user_id:"other",author_name:"Bình luận viên",content:"Bình luận kiểm thử",...summary(state.comment)}];
    else if(path.endsWith("/heritage/items"))data={items:[
      {id:"photo",type:"photo",title:"Ảnh di sản",description:"Mô tả",media_url:"/media/photo.png"},
      {id:"broken",type:"photo",title:"Ảnh thiếu",media_url:"/media/missing.png"},
      {id:"document",type:"document",title:"Tài liệu",media_url:"/media/document.pdf"},
      {id:"story",type:"story",title:"Câu chuyện",content:"Ký ức gia đình",media_url:"/media/story.png"}],total:4};
    else if(path.endsWith("/heritage/family-tree"))data={nodes:[{id:"a",label:"Cha"},{id:"b",label:"Mẹ"},{id:"c",label:"Con"},{id:"d",label:"Người riêng"}],edges:[{id:"ab",source:"a",target:"b",kind:"marriage"},{id:"ac",source:"a",target:"c",kind:"parent_child"},{id:"bc",source:"b",target:"c",kind:"parent_child"}]};
    else if(path.endsWith("/genealogy/relationships"))data={parent_child:[],marriages:[]};
    else if(path.includes("/genealogy/"))data={items:[],total:0};
    await route.fulfill({json:data});
  });
  return state;
}
async function noOverflow(page){expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);}

for(const [width,height]of [[1920,1080],[1366,768],[768,1024],[390,844]]){
  test(`gallery and reactions at ${width}px`,async({page})=>{
    await page.setViewportSize({width,height});await setup(page);await page.goto("/community");
    await expect(page.getByText("Nội dung bài kiểm thử")).toBeVisible();
    await expect(page.getByText("+2",{exact:true})).toBeVisible();
    await page.getByRole("button",{name:"Xem Ảnh bài viết 1",exact:true}).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByRole("button",{name:"Ảnh tiếp →"}).click();await expect(page.getByText("2 / 6")).toBeVisible();
    await page.keyboard.press("Escape");await expect(page.getByRole("dialog")).toHaveCount(0);
    await page.getByRole("button",{name:"Thích cho bài của Người thân",exact:true}).click();
    await expect(page.getByRole("button",{name:"Thích cho bài của Người thân",exact:true})).toHaveAttribute("aria-pressed","true");
    await page.getByRole("button",{name:"Chọn cảm xúc cho bài của Người thân",exact:true}).click();
    const palette=page.getByRole("group",{name:"Chọn cảm xúc"});await expect(palette).toBeVisible();
    const box=await palette.boundingBox();expect(box.x).toBeGreaterThanOrEqual(0);expect(box.x+box.width).toBeLessThanOrEqual(width);
    await palette.getByRole("button",{name:"Yêu thích",exact:true}).click();
    await expect(page.getByRole("button",{name:"Yêu thích cho bài của Người thân",exact:true})).toBeVisible();
    await page.getByRole("button",{name:"Bình luận · 1",exact:true}).click();
    await page.getByRole("button",{name:"Thích cho bình luận của Bình luận viên",exact:true}).click();
    await expect(page.getByRole("button",{name:"Thích cho bình luận của Bình luận viên",exact:true})).toHaveAttribute("aria-pressed","true");
    await noOverflow(page);
    await page.reload();await expect(page.getByRole("button",{name:"Yêu thích cho bài của Người thân",exact:true})).toBeVisible();
    await page.getByRole("button",{name:"Bình luận · 1",exact:true}).click();
    await expect(page.getByRole("button",{name:"Thích cho bình luận của Bình luận viên",exact:true})).toHaveAttribute("aria-pressed","true");
    await page.getByRole("button",{name:"Thích cho bình luận của Bình luận viên",exact:true}).click();
    await expect(page.getByRole("button",{name:"Thích cho bình luận của Bình luận viên",exact:true})).toHaveAttribute("aria-pressed","false");
  });
  test(`heritage image, document and missing file at ${width}px`,async({page})=>{
    await page.setViewportSize({width,height});await setup(page);await page.goto("/heritage");
    await expect(page.getByRole("img",{name:"Ảnh di sản 1",exact:true})).toBeVisible();
    await expect(page.getByText("Không tải được ảnh. Bạn có thể mở liên kết gốc.")).toBeVisible();
    await expect(page.getByRole("link",{name:"📄 Mở tài liệu PDF"})).toBeVisible();
    await expect(page.getByText("Ký ức gia đình")).toBeVisible();await noOverflow(page);
  });
  test(`tree selection, controls and parents at ${width}px`,async({page})=>{
    await page.setViewportSize({width,height});await setup(page);await page.goto("/family-tree");
    await expect(page.locator(".react-flow__node")).toHaveCount(4);
    const cha=page.locator('.react-flow__node[data-id="a"]'),me=page.locator('.react-flow__node[data-id="b"]'),con=page.locator('.react-flow__node[data-id="c"]');
    const a=await cha.boundingBox(),b=await me.boundingBox(),c=await con.boundingBox();
    expect(Math.abs(a.y-b.y)).toBeLessThan(1);expect(c.y).toBeGreaterThan(a.y+a.height);
    await cha.click();await expect(page.getByRole("status")).toContainText("Cha");
    await expect(page.locator('.react-flow__node[data-id="d"]')).toHaveCSS("opacity","0.45");
    await page.getByRole("button",{name:"zoom in",exact:true}).click();
    await page.getByRole("button",{name:"fit view",exact:true}).click();await noOverflow(page);
  });
}
test("composer previews/removes attachments and rejects unsafe URLs",async({page})=>{
  await setup(page);await page.goto("/community");
  const media=page.getByRole("textbox",{name:"Ảnh đính kèm"});
  await media.fill("/media/a.png\n/media/b.png");await expect(page.getByText("2 ảnh đã thêm")).toBeVisible();
  await page.getByRole("button",{name:"Xóa ảnh 1",exact:true}).click();await expect(media).toHaveValue("/media/b.png");
  await media.fill("javascript:alert(1)");await expect(page.getByRole("alert")).toContainText("URL ảnh không hợp lệ");
});
test("API failure preserves state; repeated clicks cannot duplicate writes",async({page})=>{
  const state=await setup(page);await page.goto("/community");
  const like=page.getByRole("button",{name:"Thích cho bài của Người thân",exact:true});
  await expect(like).toBeVisible();state.fail=true;await like.click();
  await expect(page.getByRole("alert")).toContainText("Không lưu được");await expect(like).toHaveAttribute("aria-pressed","false");
  const before=state.requests;await like.evaluate(button=>{for(let i=0;i<10;i++)button.click();});
  await expect(like).toHaveAttribute("aria-pressed","true");expect(state.requests-before).toBe(1);
});
test("touch opens palette, changes reaction and Escape closes it",async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const page=await context.newPage();await setup(page);await page.goto("http://127.0.0.1:5179/community");
  await page.getByRole("button",{name:"Chọn cảm xúc cho bài của Người thân",exact:true}).tap();
  await page.getByRole("group",{name:"Chọn cảm xúc"}).getByRole("button",{name:"Ngạc nhiên",exact:true}).tap();
  await expect(page.getByRole("button",{name:"Ngạc nhiên cho bài của Người thân",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Chọn cảm xúc cho bài của Người thân",exact:true}).tap();
  await page.keyboard.press("Escape");await expect(page.getByRole("group",{name:"Chọn cảm xúc"})).toHaveCount(0);
  await context.close();
});
