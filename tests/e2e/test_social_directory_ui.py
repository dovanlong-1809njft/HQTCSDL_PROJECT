import json,re
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import parse_qs,urlparse

import pytest
from playwright.sync_api import expect

F='00000000-0000-0000-0000-000000000101'
U='00000000-0000-0000-0000-000000000201'
M='00000000-0000-0000-0000-000000000301'
P='00000000-0000-0000-0000-000000000401'
E='00000000-0000-0000-0000-000000000501'


@pytest.fixture(scope='module')
def social_url(vite_server):
    with vite_server() as url: yield url


@pytest.fixture
def social_ui(e2e_browser,social_url):
    context=e2e_browser.new_context(base_url=social_url,viewport={'width':1440,'height':1000},timezone_id='Asia/Ho_Chi_Minh')
    page=context.new_page();page.set_default_timeout(10000)
    now=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()
    state={'requests':[],'fail':False,'posts':[dict(post_id=P,family_id=F,author_id=U,author_name='Nguyễn An',content='Tin gia đình',created_at=now,comment_count=0,reaction_count=0,media_urls=[],is_announcement=False,my_reaction=None)],'comments':[],
           'member':dict(id=M,name='Nguyễn An',family_id=F,branch_id=None,branch_name=None,birth_date='1990-01-01',location='Hồ Chí Minh',can_edit=True,educations=[],work=[]),
           'events':[dict(event_id=E,family_id=F,title='Gặp mặt gia đình',event_date=now,location='Nhà thờ họ',going_count=0,my_rsvp=None)],'participants':[],'gallery':[],'reminders':[],
           'notifications':[dict(id='notice-one',family_id=F,event_id=E,title='Gặp mặt gia đình',body='Bạn có lịch gặp gia đình.',created_at=now,read_at=None)]}
    def handle(route):
        req=route.request;path=urlparse(req.url).path
        if not path.startswith('/api/'):
            route.continue_();return
        if path=='/api/settings':route.fulfill(json=dict(site_name='FamilyConnect',logo_url='/favicon.svg',theme='forest',registration_enabled=True));return
        params=parse_qs(urlparse(req.url).query);body=req.post_data_json if req.post_data else None
        state['requests'].append((req.method,path,params,body))
        if state['fail']:
            route.fulfill(status=503,json={'detail':'Lỗi máy chủ thử nghiệm'});return
        if path=='/api/heritage/families':route.fulfill(json=[dict(id=F,name='Gia đình kiểm thử')]);return
        if path=='/api/genealogy/branches':route.fulfill(json=dict(items=[],total=0));return
        if path=='/api/genealogy/members':route.fulfill(json=dict(items=[dict(id=M,name='Nguyễn An')],total=1));return
        if path=='/api/genealogy/me':route.fulfill(json=dict(user=dict(id=U,full_name='Nguyễn An',email='ui@example.com',role='admin'),member=state['member'],verifications=[]));return
        if path=='/api/directory':route.fulfill(json=dict(items=[dict(state['member'],generation=2,position='Kỹ sư',company='Đơn vị thử',institution='Trường thử')],total=1));return
        if path=='/api/directory/'+M:route.fulfill(json=state['member']);return
        if path.startswith('/api/directory/'+M+'/'):
            resource=path.split('/')[4];identifier=path.rsplit('/',1)[1]
            if req.method=='POST':state['member'][resource].append(dict(id='history-one',**body));route.fulfill(status=201,json={'id':'history-one'})
            elif req.method=='PUT':state['member'][resource][0].update(body);route.fulfill(json={'id':identifier})
            else:state['member'][resource]=[];route.fulfill(status=204)
            return
        if path=='/api/community/posts':
            if req.method=='GET':route.fulfill(json=dict(items=state['posts'],total=len(state['posts']),page=1,page_size=10))
            else:
                created=dict(state['posts'][0],post_id='post-new',content=body['content'],is_announcement=body.get('is_announcement',False),media_urls=[m['url'] for m in body['media']]);state['posts'].insert(0,created);route.fulfill(status=201,json=created)
            return
        if path=='/api/community/reports':route.fulfill(status=201,json={'status':'pending'});return
        if path.startswith('/api/community/posts/'):
            identifier=path.split('/')[4];post=next(r for r in state['posts'] if r['post_id']==identifier)
            if path.endswith('/reactions'):post['my_reaction']=body['type'];post['reaction_count']=int(bool(body['type']));route.fulfill(json=dict(post_id=identifier,user_id=U,type=body['type'],reaction_count=post['reaction_count']));return
            if path.endswith('/comments'):
                if req.method=='POST':state['comments'].append(dict(id='comment-one',post_id=identifier,user_id=U,author_name='Nguyễn An',content=body['content'],created_at=now));post['comment_count']+=1;route.fulfill(status=201,json=state['comments'][-1])
                else:route.fulfill(json=state['comments'])
                return
            if req.method=='PUT':post.update(content=body['content'],media_urls=[m['url'] for m in body['media']],is_announcement=body['is_announcement']);route.fulfill(json=post)
            elif req.method=='DELETE':state['posts']=[r for r in state['posts'] if r['post_id']!=identifier];route.fulfill(status=204)
            else:route.fulfill(json=post)
            return
        if path=='/api/events':
            if req.method=='GET':route.fulfill(json=state['events'])
            else:state['events'].append(dict(event_id='event-new',going_count=0,my_rsvp=None,**body));route.fulfill(status=201,json=state['events'][-1])
            return
        if path.startswith('/api/events/'):
            identifier=path.split('/')[3];event=next((r for r in state['events'] if r['event_id']==identifier),None)
            if event is None:
                route.fulfill(status=404,json={'detail':'Sự kiện đã được xóa'});return
            if path.endswith('/rsvp'):event['my_rsvp']=body['rsvp_status'];event['going_count']=1;state['participants']=[dict(member_id=M,name='Nguyễn An',branch_name=None,rsvp_status=body['rsvp_status'])];route.fulfill(json=dict(event_id=identifier,member_id=M,rsvp_status=body['rsvp_status'],going_count=1));return
            if '/participants/' in path:state['participants']=[dict(member_id=M,name='Nguyễn An',branch_name=None,rsvp_status=body['rsvp_status'])];route.fulfill(status=204);return
            if path.endswith('/participants'):
                route.fulfill(json=dict(items=state['participants'],total=len(state['participants']),counts={status:sum(r['rsvp_status']==status for r in state['participants']) for status in ('Going','Maybe','Pending','Declined')}));return
            if path.endswith('/gallery'):
                if req.method=='POST':state['gallery'].append(dict(id='photo-one',event_id=identifier,media_url=body['media_url'],uploaded_by=U,created_at=now));route.fulfill(status=201,json=state['gallery'][-1])
                else:route.fulfill(json=state['gallery'])
                return
            if path.endswith('/reminders'):
                if req.method=='POST':state['reminders'].append(dict(id='reminder-one',event_id=identifier,reminder_time=body['reminder_time'],status='pending',user_id=None if body['for_family'] else U));route.fulfill(status=201,json=state['reminders'][-1])
                else:route.fulfill(json=state['reminders'])
                return
            if '/reminders/' in path:state['reminders'][0]['status']='cancelled';route.fulfill(status=204);return
            if req.method=='PUT':event.update(body);route.fulfill(json=event)
            elif req.method=='DELETE':state['events']=[r for r in state['events'] if r['event_id']!=identifier];route.fulfill(status=204)
            else:route.fulfill(json=event)
            return
        if path=='/api/notifications':route.fulfill(json=dict(items=state['notifications'],total=len(state['notifications']),unread=sum(not row['read_at'] for row in state['notifications'])));return
        if path.endswith('/read'):state['notifications'][0]['read_at']=now;route.fulfill(status=204);return
        route.fulfill(status=404,json={'detail':'Unexpected fixture endpoint'})
    page.route('**/api/**',handle)
    context.add_init_script("localStorage.setItem('familyconnect.token','test-token');localStorage.setItem('familyconnect.user',"+json.dumps(json.dumps(dict(id=U,fullName='Nguyễn An',email='ui@example.com',role='admin')))+");")
    try:yield page,state
    finally:context.close()


def test_directory_search_and_education_crud(social_ui):
    page,state=social_ui;page.goto('/directory')
    page.get_by_label('Nơi ở',exact=True).fill('Hồ Chí Minh');page.get_by_label('Nghề nghiệp / đơn vị',exact=True).fill('Kỹ sư');page.get_by_role('button',name='Tìm thành viên',exact=True).click()
    page.get_by_role('button',name=re.compile('^Nguyễn An')).click()
    page.get_by_role('button',name='Thêm học vấn',exact=True).click()
    page.get_by_label('Trường / cơ sở đào tạo',exact=True).fill('Đại học kiểm thử');page.get_by_label('Bằng cấp',exact=True).fill('Kỹ sư')
    page.get_by_label('Ngày bắt đầu',exact=True).fill('2020-01-01')
    page.get_by_role('button',name='Lưu thông tin',exact=True).click();expect(page.get_by_role('paragraph').filter(has_text='Đại học kiểm thử')).to_be_visible()
    assert any(r[2].get('location')==['Hồ Chí Minh'] for r in state['requests'])
    page.once('dialog',lambda dialog:dialog.accept());page.get_by_role('button',name='Xóa Đại học kiểm thử',exact=True).click();expect(page.get_by_text('Đại học kiểm thử',exact=True)).to_have_count(0)


def test_community_create_react_comment_edit_and_report(social_ui):
    page,state=social_ui;page.goto('/community')
    page.get_by_label('Nội dung',exact=True).fill('Tin mới của gia đình');page.get_by_role('button',name='Đăng bài',exact=True).click()
    card=page.get_by_role('article').filter(has=page.get_by_text('Tin mới của gia đình',exact=True));expect(card).to_be_visible()
    card.get_by_role('button',name='Chọn cảm xúc cho bài của Nguyễn An',exact=True).click()
    card.get_by_role('button',name='Yêu thích',exact=True).click()
    expect(card.get_by_role('button',name='Yêu thích cho bài của Nguyễn An',exact=True)).to_have_attribute('aria-pressed','true')
    card.get_by_role('button',name='Bình luận · 0',exact=True).click();card.get_by_label('Viết bình luận',exact=True).fill('Cả nhà cùng xem nhé');card.get_by_role('button',name='Gửi bình luận',exact=True).click();expect(card.get_by_text('Cả nhà cùng xem nhé',exact=True)).to_be_visible()
    card.get_by_role('button',name='Báo cáo bài',exact=True).click();card.get_by_label('Lý do báo cáo',exact=True).fill('Lý do kiểm thử');card.get_by_role('button',name='Gửi báo cáo',exact=True).click()
    expect(card.get_by_label('Lý do báo cáo',exact=True)).to_have_count(0)
    assert next(r for r in state['requests'] if r[1]=='/api/community/reports')[3]['reason']=='Lý do kiểm thử'


def test_event_rsvp_manager_status_and_reminder(social_ui):
    page,state=social_ui;page.goto('/events');page.get_by_role('button',name=re.compile('.*Gặp mặt gia đình')).click()
    page.get_by_role('button',name='Tham dự',exact=True).click();expect(page.get_by_role('button',name='Tham dự',exact=True)).to_have_attribute('aria-pressed','true')
    page.get_by_role('combobox',name='Trạng thái của Nguyễn An',exact=True).select_option('Maybe')
    expect(page.get_by_role('combobox',name='Trạng thái của Nguyễn An',exact=True)).to_have_value('Maybe')
    target=(datetime.now(timezone.utc)+timedelta(days=1)).astimezone(timezone(timedelta(hours=7))).strftime('%Y-%m-%dT%H:%M')
    page.get_by_label('Thời gian nhắc (giờ trên thiết bị)',exact=True).fill(target);page.get_by_role('button',name='Đặt nhắc lịch',exact=True).click();expect(page.get_by_role('button',name='Hủy nhắc',exact=True)).to_be_visible()
    page.get_by_role('button',name='Hủy nhắc',exact=True).click();expect(page.get_by_text(re.compile('.*Đã hủy'))).to_be_visible()
    writes=[r for r in state['requests'] if '/participants/' in r[1]];assert writes[-1][3]['rsvp_status']=='Maybe'
    assert next(r for r in state['requests'] if r[0]=='POST' and r[1].endswith('/reminders'))[3]['reminder_time'].endswith('Z')


def test_notification_read_and_event_deep_link(social_ui):
    page,_=social_ui;page.goto('/notifications');page.get_by_role('button',name='Đánh dấu đã đọc',exact=True).click();expect(page.get_by_role('button',name='Đánh dấu đã đọc',exact=True)).to_have_count(0)
    page.get_by_role('link',name='Xem sự kiện',exact=True).click();expect(page.get_by_role('heading',name='Gặp mặt gia đình',exact=True)).to_be_visible()


def test_create_update_and_delete_event(social_ui):
    page,state=social_ui;page.goto('/events');page.get_by_role('button',name='Tạo sự kiện',exact=True).click()
    page.get_by_label('Tên sự kiện',exact=True).fill('Sự kiện mới')
    page.get_by_label('Thời gian (giờ trên thiết bị)',exact=True).fill('2026-11-25T18:00')
    page.get_by_label('Địa điểm',exact=True).fill('Nhà thờ họ')
    page.get_by_role('button',name='Lưu sự kiện',exact=True).click()
    page.get_by_role('button',name=re.compile('.*Sự kiện mới')).click()
    page.get_by_role('button',name='Sửa sự kiện',exact=True).click();page.get_by_label('Tên sự kiện',exact=True).fill('Sự kiện đã sửa')
    page.get_by_role('button',name='Lưu sự kiện',exact=True).click();expect(page.get_by_role('heading',name='Sự kiện đã sửa',exact=True)).to_be_visible()
    page.once('dialog',lambda dialog:dialog.accept());page.get_by_role('button',name='Xóa sự kiện',exact=True).click();expect(page.get_by_role('heading',name='Sự kiện đã sửa',exact=True)).to_have_count(0)
    body=next(r[3] for r in state['requests'] if r[0]=='POST' and r[1]=='/api/events')
    assert body['event_date']=='2026-11-25T11:00:00.000Z'


@pytest.mark.parametrize('label,invalid',[('Tên sự kiện',''),('Tên sự kiện','   '),('Thời gian (giờ trên thiết bị)',''),('Địa điểm',''),('Địa điểm','   ')])
def test_event_requires_complete_information(social_ui,label,invalid):
    page,state=social_ui
    page.goto('/events')
    page.get_by_role('button',name='Tạo sự kiện',exact=True).click()
    for name,value in [('Tên sự kiện','Test event'),('Thời gian (giờ trên thiết bị)','2027-01-01T10:00'),('Địa điểm','Test place')]:
        page.get_by_label(name,exact=True).fill(value)
    control=page.get_by_label(label,exact=True)
    control.fill(invalid)
    page.get_by_role('button',name='Lưu sự kiện',exact=True).click()
    assert control.evaluate('field => !field.validity.valid')
    assert not any(row[0]=='POST' for row in state['requests'])


@pytest.mark.parametrize('label,invalid',[('Trường / cơ sở đào tạo',''),('Trường / cơ sở đào tạo','   '),('Bằng cấp',''),('Bằng cấp','   '),('Ngày bắt đầu','')])
def test_education_requires_complete_information(social_ui,label,invalid):
    page,state=social_ui
    page.goto('/directory')
    page.get_by_role('button',name=re.compile('^Nguyễn An')).click()
    page.get_by_role('button',name='Thêm học vấn',exact=True).click()
    for name,value in [('Trường / cơ sở đào tạo','Test school'),('Bằng cấp','Test degree'),('Ngày bắt đầu','2020-01-01')]:
        page.get_by_label(name,exact=True).fill(value)
    control=page.get_by_label(label,exact=True)
    control.fill(invalid)
    page.get_by_role('button',name='Lưu thông tin',exact=True).click()
    assert control.evaluate('field => !field.validity.valid')
    assert not any(row[0]=='POST' for row in state['requests'])


@pytest.mark.parametrize('target',['post','comment','report'])
def test_community_rejects_whitespace_before_request(social_ui,target):
    page,state=social_ui
    page.goto('/community')
    if target=='post':
        control=page.get_by_label('Nội dung',exact=True)
        button=page.get_by_role('button',name='Đăng bài',exact=True)
    elif target=='comment':
        page.get_by_role('button',name='Bình luận · 0',exact=True).click()
        control=page.get_by_label('Viết bình luận',exact=True)
        button=page.get_by_role('button',name='Gửi bình luận',exact=True)
    else:
        page.get_by_role('button',name='Báo cáo bài',exact=True).click()
        control=page.get_by_label('Lý do báo cáo',exact=True)
        button=page.get_by_role('button',name='Gửi báo cáo',exact=True)
    control.fill('   ')
    button.click()
    assert control.evaluate('field => !field.validity.valid')
    assert not any(row[0]=='POST' for row in state['requests'])


@pytest.mark.parametrize('path,title',[('/directory','Danh bạ gia đình'),('/community','Bảng tin gia đình'),('/events','Lịch gia đình'),('/notifications','Thông báo')])
@pytest.mark.parametrize('width',[1440,1024,768,390])
def test_new_pages_at_four_widths(social_ui,path,title,width):
    page,_=social_ui;page.set_viewport_size({'width':width,'height':900 if width>=1024 else 844});page.goto(path)
    expect(page.get_by_role('heading',name=title,exact=True,level=1)).to_be_visible()
    expect(page.get_by_text('Đang tải dữ liệu…',exact=True)).to_have_count(0)
    if path=='/directory': expect(page.get_by_role('button',name=re.compile('^Nguy\u1ec5n An'))).to_be_visible()
    elif path=='/community': expect(page.get_by_role('article')).to_have_count(1)
    elif path=='/events': expect(page.get_by_role('button',name=re.compile('.*G\u1eb7p m\u1eb7t gia \u0111\u00ecnh'))).to_be_visible()
    else: expect(page.get_by_role('link',name='Xem s\u1ef1 ki\u1ec7n',exact=True)).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    output=Path(__file__).resolve().parents[2]/'apps/web/.taste-skill/shots';output.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(output/(path.strip('/')+f'-{width}.png')),full_page=True)
