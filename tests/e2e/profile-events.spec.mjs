import {createRequire} from "node:module";
const {test,expect}=createRequire(new URL("../../apps/web/package.json",import.meta.url))("@playwright/test");

async function setup(page,{linked=true,editable=true,role="member"}={}){
  const state={educations:[],work:[]};
  await page.addInitScript(role=>{
    localStorage.setItem("familyconnect.token","test-token");
    localStorage.setItem("familyconnect.user",JSON.stringify({id:"user",role,fullName:"Tester"}));
  },role);
  await page.route(url=>url.pathname.startsWith("/api/"),async route=>{
    const path=new URL(route.request().url()).pathname,method=route.request().method();let data=[];
    if(path==="/api/settings")data={site_name:"FamilyConnect",logo_url:"/favicon.svg",theme:"forest",registration_enabled:true};
    else if(path==="/api/genealogy/me")data={user:{id:"user",full_name:"Tester",email:"test@example.com",role},member:linked?{id:"member",family_id:"family",name:"Tester",family_name:"Family",birth_date:"2000-01-01",location:"City"}:null,verifications:[]};
    else if(path==="/api/heritage/families")data=[{id:"family",name:"Family"}];
    else if(path==="/api/directory/member")data={id:"member",name:"Tester",can_edit:editable,...state};
    else if(path.startsWith("/api/directory/member/")){
      const [,resource,id]=path.split("/member/")[1].match(/^(work|educations)(?:\/(.*))?$/)||[];
      if(!resource)throw new Error(path);
      if(method==="POST")state[resource].push({...route.request().postDataJSON(),id:String(Date.now())});
      if(method==="PUT")state[resource]=state[resource].map(row=>row.id===id?{...row,...route.request().postDataJSON()}:row);
      if(method==="DELETE")state[resource]=state[resource].filter(row=>row.id!==id);
      data={};
    }else if(path==="/api/events")data=[{event_id:"e",family_id:"family",title:"Ended event",event_date:"2020-01-01T00:00:00",end_date:"2020-01-01T01:00:00",going_count:0}];
    else if(path==="/api/notifications")data={items:[{id:"n",family_id:"family",event_id:"e",title:"Sự kiện đã kết thúc",body:"Family event ended",notification_type:"event_ended",created_at:"2020-01-01T01:00:00",read_at:null}],unread:1,total:1};
    await route.fulfill({json:data});
  });return state;
}
for(const width of [1440,768,390])test(`profile shared history CRUD ${width}px`,async({page})=>{
  await page.setViewportSize({width,height:1000});await setup(page);await page.goto("/profile");
  await page.getByRole("button",{name:"Thêm học vấn",exact:true}).click();
  await page.getByLabel("Trường / cơ sở đào tạo").fill("SchoolOne");await page.getByLabel("Bằng cấp").fill("Degree");
  await page.getByLabel("Ngày bắt đầu",{exact:true}).fill("2020-01-01");await page.getByRole("button",{name:"Lưu thông tin"}).click();
  await expect(page.locator("p").filter({hasText:/^SchoolOne$/})).toBeVisible();
  await page.getByRole("button",{name:"Sửa SchoolOne"}).click();await page.getByLabel("Bằng cấp").fill("Updated degree");await page.getByRole("button",{name:"Lưu thông tin"}).click();
  await expect(page.getByText("Updated degree",{exact:true})).toBeVisible();
  for(const company of ["CompanyOne","CompanyTwo"]){
    await page.getByRole("button",{name:"Thêm công việc",exact:true}).click();await page.getByLabel("Công ty / đơn vị").fill(company);await page.getByLabel("Chức danh / nghề nghiệp").fill("Engineer");
    await page.getByLabel("Ngày bắt đầu",{exact:true}).fill("2021-01-01");await page.getByRole("button",{name:"Lưu thông tin"}).click();await expect(page.locator("p").filter({hasText:company}).first()).toBeVisible();
  }
  await page.reload();await expect(page.locator("p").filter({hasText:/^CompanyTwo$/})).toBeVisible();
  page.on("dialog",dialog=>dialog.accept());await page.getByRole("button",{name:"Xóa SchoolOne"}).click();await expect(page.locator("p").filter({hasText:/^SchoolOne$/})).toHaveCount(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test("unlinked and read-only profiles cannot edit history",async({page})=>{
  await setup(page,{linked:false});await page.goto("/profile");await expect(page.getByText("Liên kết hồ sơ gia phả trước khi thêm học vấn và nghề nghiệp.")).toBeVisible();await expect(page.getByRole("button",{name:"Thêm công việc",exact:true})).toHaveCount(0);
});
test("event end validation and ended notification link",async({page})=>{
  await setup(page,{role:"admin"});await page.goto("/events");await expect(page.getByText("Đã kết thúc",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Tạo sự kiện",exact:true}).click();await page.getByLabel("Tên sự kiện").fill("Test");
  await page.locator('[name="event_date"]').fill("2030-01-01T12:00");await page.locator('[name="end_date"]').fill("2030-01-01T11:00");await page.getByLabel("Địa điểm").fill("City");
  await page.getByRole("button",{name:"Lưu sự kiện"}).click();await expect(page.getByRole("alert")).toContainText("Kết thúc phải sau bắt đầu");
  await page.goto("/notifications");await expect(page.getByRole("link",{name:"Xem sự kiện"})).toHaveAttribute("href","/events?family=family&event=e");
});
