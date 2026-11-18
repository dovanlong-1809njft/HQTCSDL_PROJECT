import io
import os
from uuid import uuid4

import pytest
from PIL import Image

from test_community_events_api import client, session, FakeResult, FAMILY_ID, USER_ID


def image(fmt="PNG", size=(32,16)):
    output=io.BytesIO()
    Image.new("RGB",size,"green").save(output,format=fmt)
    return output.getvalue()


@pytest.fixture(autouse=True)
def media_storage(tmp_path,monkeypatch):
    monkeypatch.setenv("MEDIA_ROOT",str(tmp_path))
    return tmp_path


def upload(client, files=None):
    return client.post("/api/community/uploads",params={"family_id":str(FAMILY_ID)},files=files or [("files",("a.png",image(),"image/png"))])


@pytest.mark.parametrize("fmt",["PNG","JPEG","WEBP"])
def test_upload_content_detection_private_read_and_safe_filename(client,media_storage,fmt):
    response=upload(client,[("files",("../../payload.php",image(fmt),"text/html"))])
    assert response.status_code==201,response.text
    url=response.json()["items"][0]["url"]
    assert "payload" not in url and ".." not in url
    assert len(list(media_storage.rglob("*.*")))==1
    response=client.get(url)
    assert response.status_code==200
    assert response.headers["cache-control"]=="private, no-store"
    with Image.open(io.BytesIO(response.content)) as decoded:
        assert decoded.format==fmt


def test_multiple_files_and_atomic_rejection(client,media_storage):
    result=upload(client,[("files",("a.jpg",image("JPEG"),"image/jpeg")),("files",("b.webp",image("WEBP"),"image/webp"))])
    assert result.status_code==201 and len(result.json()["items"])==2
    before=set(media_storage.rglob("*.*"))
    assert upload(client,[("files",("good.png",image(),"image/png")),("files",("fake.jpg",b"<script>alert(1)</script>","image/jpeg"))]).status_code==415
    assert set(media_storage.rglob("*.*"))==before


@pytest.mark.parametrize("content",[b"",b"broken",b"<svg xmlns='http://www.w3.org/2000/svg'/>",image("GIF")])
def test_invalid_or_unsupported_images(client,content):
    assert upload(client,[("files",("a.jpg",content,"image/jpeg"))]).status_code==415


def test_oversized_file_and_dimensions(client):
    assert upload(client,[("files",("big.png",b"x"*(8*1024*1024+1),"image/png"))]).status_code==413
    assert upload(client,[("files",("wide.png",image(size=(8193,1)),"image/png"))]).status_code==413


def test_too_many_files(client):
    assert upload(client,[("files",("a.png",image(),"image/png"))]*21).status_code==400


def test_post_cannot_use_failed_upload_url(client):
    missing=f"/media/uploads/{FAMILY_ID}/{USER_ID}/{uuid4().hex}.png"
    response=client.post("/api/community/posts",json={"family_id":str(FAMILY_ID),"content":"test","media":[{"url":missing}]})
    assert response.status_code==422


def test_upload_and_read_require_family_membership(client,session):
    url=upload(client).json()["items"][0]["url"]
    session.is_member=False
    assert upload(client).status_code==403
    assert client.get(url).status_code==403


def test_draft_private_until_attached_to_post(client,session):
    url=upload(client).json()["items"][0]["url"]
    session.user.id=uuid4()
    assert client.get(url).status_code==404
    original=session.execute
    session.execute=lambda statement,params=None: FakeResult(scalar=1) if "FROM community.PostMedia m" in str(statement) else original(statement,params)
    assert client.get(url).status_code==200


def test_no_token_denied_before_multipart_parsing(client):
    from app.main import app
    from app.core.dependencies import get_current_user
    app.dependency_overrides.pop(get_current_user)
    assert upload(client).status_code==401


def test_uploads_survive_new_app_client(client):
    from fastapi.testclient import TestClient
    from app.main import app
    url=upload(client).json()["items"][0]["url"]
    with TestClient(app) as reloaded:
        assert reloaded.get(url).status_code==200


def test_strip_metadata_and_polyglot_tail(client):
    output=io.BytesIO()
    source=Image.new("RGB",(8,8),"blue")
    exif=Image.Exif();exif[270]="private GPS/camera metadata"
    source.save(output,"JPEG",exif=exif)
    response=upload(client,[("files",("a.jpg",output.getvalue()+b"<script>payload</script>","image/jpeg"))])
    assert response.status_code==201
    data=client.get(response.json()["items"][0]["url"]).content
    assert b"payload" not in data and b"private GPS" not in data
    assert not Image.open(io.BytesIO(data)).getexif()


def test_streaming_and_declared_request_limit(client,monkeypatch,media_storage):
    from app.domains.community import uploads
    monkeypatch.setattr(uploads,"MAX_REQUEST_BYTES",128)
    assert upload(client).status_code==413
    body=b'--qa\r\nContent-Disposition: form-data; name="files"; filename="a.png"\r\nContent-Type: image/png\r\n\r\n'+b'x'*400+b'\r\n--qa--\r\n'
    response=client.post(f"/api/community/uploads?family_id={FAMILY_ID}",content=iter([body]),headers={"Content-Type":"multipart/form-data; boundary=qa"})
    assert response.status_code==413,response.text
    assert not list(media_storage.rglob("*.*"))


def test_draft_reference_not_usable_by_another_author(client,session):
    url=upload(client).json()["items"][0]["url"]
    session.user.id=uuid4()
    response=client.post("/api/community/posts",json={"family_id":str(FAMILY_ID),"content":"test","media":[{"url":url}]})
    assert response.status_code==403


def test_animated_webp_rejected(client):
    output=io.BytesIO()
    Image.new("RGB",(16,16),"red").save(output,"WEBP",save_all=True,append_images=[Image.new("RGB",(16,16),"blue")],duration=100,loop=0)
    assert upload(client,[("files",("animated.webp",output.getvalue(),"image/webp"))]).status_code==415


def test_valid_image_larger_than_multipart_default_field_limit(client):
    output=io.BytesIO()
    Image.frombytes("RGB",(1024,1024),os.urandom(1024*1024*3)).save(output,"PNG")
    assert 1024*1024<len(output.getvalue())<8*1024*1024
    assert upload(client,[("files",("large.png",output.getvalue(),"image/png"))]).status_code==201
