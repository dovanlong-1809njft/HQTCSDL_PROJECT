import subprocess

import pytest

from test_image_uploads import client, session, media_storage, upload


@pytest.fixture(scope="module")
def video_data(tmp_path_factory):
    output=tmp_path_factory.mktemp("video")/"test.mp4"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=green:s=160x90:d=1",
        "-c:v","libx264","-pix_fmt","yuv420p","-metadata","title=private metadata",str(output)],check=True)
    return output.read_bytes()


def test_real_video_upload_normalizes_and_serves_ranges(client,video_data,media_storage):
    response=upload(client,[("files",("../../unsafe.exe",video_data,"application/octet-stream"))])
    assert response.status_code==201,response.text
    item=response.json()["items"][0]
    assert item["type"]=="video" and item["url"].endswith(".mp4")
    response=client.get(item["url"],headers={"Range":"bytes=0-99"})
    assert response.status_code==206 and len(response.content)==100
    assert response.headers["content-type"]=="video/mp4"
    assert b"private metadata" not in client.get(item["url"]).content


def test_corrupt_video_rejected_without_saving(client,media_storage):
    assert upload(client,[("files",("fake.mp4",b"\x00\x00\x00\x18ftypisom"+b"junk"*10,"video/mp4"))]).status_code==415
    assert not list(media_storage.rglob("*.*"))


def test_video_over_duration_rejected(client,tmp_path):
    path=tmp_path/"long.mp4"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=green:s=16x16:r=1:d=301","-c:v","libx264",str(path)],check=True)
    assert upload(client,[("files",("long.mp4",path.read_bytes(),"video/mp4"))]).status_code==415


def test_mixed_video_and_image_batch(client,video_data):
    from test_image_uploads import image
    response=upload(client,[("files",("photo.png",image(),"image/png")),("files",("movie.mp4",video_data,"video/mp4"))])
    assert response.status_code==201,response.text
    assert [item["type"] for item in response.json()["items"]]==["image","video"]


def test_webm_is_normalized_to_playable_mp4(client,tmp_path):
    path=tmp_path/"test.webm"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=blue:s=64x64:r=5:d=1","-c:v","libvpx-vp9","-threads","2",str(path)],check=True)
    result=upload(client,[("files",("clip.webm",path.read_bytes(),"video/webm"))])
    assert result.status_code==201,result.text
    assert result.json()["items"][0]["url"].endswith(".mp4")


def test_video_size_limit(client,monkeypatch,video_data):
    from app.domains.community import uploads
    monkeypatch.setattr(uploads,"MAX_VIDEO_BYTES",128)
    assert upload(client,[("files",("large.mp4",video_data,"video/mp4"))]).status_code==413
