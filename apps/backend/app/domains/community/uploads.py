"""Private, family-scoped images. Storage is mounted independently of SQL Server."""
import io
import os
import re
import warnings
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.family_access import require_family_access
from app.domains.identity.models import User
from app.domains.community.video import normalize_video, MAX_VIDEO_BYTES

MAX_FILES = 20
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_BATCH_BYTES = 100 * 1024 * 1024
MAX_REQUEST_BYTES = MAX_BATCH_BYTES + 1024 * 1024
MAX_PIXELS = 20_000_000
PREFIX = "/media/uploads/"
FILE_NAME = re.compile(r"[a-f0-9]{32}\.(jpg|png|webp|mp4)")
router = APIRouter(prefix="/community", tags=["community media"])
media_router = APIRouter(prefix="/media/uploads", tags=["private media"])
Actor = Annotated[User, Depends(get_current_user)]
Db = Annotated[Session, Depends(get_db)]


def storage_root() -> Path:
    return Path(os.environ.get("MEDIA_ROOT", "/var/lib/familyconnect/media")).resolve()


def image_path(family_id: UUID, owner_id: UUID, filename: str) -> Path:
    if not FILE_NAME.fullmatch(filename):
        raise HTTPException(404, "Không tìm thấy ảnh.")
    root = storage_root()
    path = (root / str(family_id) / str(owner_id) / filename).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(404, "Không tìm thấy ảnh.")
    return path


def referenced(db, family_id, url) -> bool:
    return bool(db.execute(text("""SELECT TOP 1 1 FROM community.PostMedia m
        JOIN community.Posts p ON p.Id=m.PostId
        WHERE p.FamilyId=:family AND m.MediaUrl=:url
        UNION ALL SELECT TOP 1 1 FROM heritage.Items h WHERE h.FamilyId=:family AND h.MediaUrl=:url"""), {"family":str(family_id),"url":url}).scalar())


def validate_media(db, actor, family_id, media):
    """Prevent forging a private upload URL when creating or editing a post."""
    for item in media:
        if not item.url.startswith(PREFIX):
            continue
        try:
            family, owner, filename = item.url[len(PREFIX):].split("/")
            family, owner = UUID(family), UUID(owner)
            path = image_path(family, owner, filename)
        except (ValueError, TypeError):
            raise HTTPException(422, "Đường dẫn ảnh tải lên không hợp lệ.") from None
        if family != UUID(str(family_id)) or not path.is_file():
            raise HTTPException(422, "Ảnh tải lên không tồn tại hoặc thuộc gia đình khác.")
        if owner != actor.id and not referenced(db, family, item.url):
            raise HTTPException(403, "Không được sử dụng ảnh nháp của người khác.")
        item.url = f"{PREFIX}{family}/{owner}/{filename}"
        if hasattr(item,"type"):
            item.type = "video" if filename.endswith(".mp4") else "image"


def normalize_image(data: bytes):
    """Decode and re-encode; never trust extension/MIME or retain EXIF/polyglots."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as original:
                fmt = original.format
                if fmt not in ("JPEG", "PNG", "WEBP"):
                    raise HTTPException(415, "Chỉ chấp nhận ảnh JPG, PNG hoặc WebP.")
                if original.width * original.height > MAX_PIXELS or max(original.size) > 8192:
                    raise HTTPException(413, "Ảnh vượt quá 20 triệu điểm ảnh hoặc cạnh dài 8192px.")
                if getattr(original, "n_frames", 1) != 1:
                    raise HTTPException(415, "Vui lòng chọn ảnh tĩnh JPG, PNG hoặc WebP.")
                original.verify()
            with Image.open(io.BytesIO(data)) as original:
                oriented = ImageOps.exif_transpose(original)
                mode = "RGBA" if fmt != "JPEG" and ("A" in oriented.getbands() or "transparency" in oriented.info) else "RGB"
                clean = Image.new(mode, oriented.size)
                clean.paste(oriented.convert(mode))
                output = io.BytesIO()
                clean.save(output, format=fmt)
                encoded = output.getvalue()
                if len(encoded) > MAX_FILE_BYTES:
                    raise HTTPException(413, "Ảnh sau xử lý vượt quá 8 MB.")
                return encoded, {"JPEG":"jpg","PNG":"png","WEBP":"webp"}[fmt]
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise HTTPException(415, "Tệp không phải ảnh hợp lệ hoặc ảnh bị hỏng.") from None
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(413, "Ảnh có kích thước giải nén quá lớn.") from None


@router.post("/uploads", status_code=201)
async def upload_images(family_id: UUID, request: Request, actor: Actor, db: Db):
    require_family_access(db, actor, family_id)
    if request.headers.get("content-type", "").split(";")[0].lower() != "multipart/form-data":
        raise HTTPException(415, "Cần gửi ảnh/video bằng multipart/form-data.")
    try:
        length = int(request.headers.get("content-length", "0"))
        if length < 0:
            raise ValueError()
    except ValueError:
        raise HTTPException(400, "Kích thước yêu cầu không hợp lệ.") from None
    if length > MAX_REQUEST_BYTES:
        raise HTTPException(413, "Mỗi lần tải lên tối đa 100 MB.")
    receive, received, exceeded = request._receive, 0, False

    async def bounded_receive():
        nonlocal received, exceeded
        message = await receive()
        received += len(message.get("body", b""))
        if received > MAX_REQUEST_BYTES:
            exceeded = True
            raise MultiPartException("Upload request exceeds the size limit")
        return message

    request._receive = bounded_receive
    saved = []
    try:
        async with request.form(max_files=MAX_FILES, max_fields=0) as form:
            files = form.getlist("files")
            if not files or len(files) != len(form.multi_items()) or any(not isinstance(f, UploadFile) for f in files):
                raise HTTPException(422, "Chọn từ 1 đến 20 ảnh trong trường files.")
            normalized, total, encoded_total = [], 0, 0
            for file in files:
                data = await file.read(MAX_VIDEO_BYTES + 1)
                video = (len(data)>12 and data[4:8]==b"ftyp") or data[:4]==b"\x1aE\xdf\xa3"
                if len(data) > (MAX_VIDEO_BYTES if video else MAX_FILE_BYTES):
                    raise HTTPException(413, "Mỗi ảnh tối đa 8 MB, mỗi video tối đa 50 MB.")
                total += len(data)
                if total > MAX_BATCH_BYTES:
                    raise HTTPException(413, "Mỗi lần tải lên tối đa 100 MB.")
                image = await run_in_threadpool(normalize_video if video else normalize_image, data)
                encoded_total += len(image[0])
                if encoded_total > MAX_BATCH_BYTES:
                    raise HTTPException(413, "Tổng tệp sau xử lý vượt quá 100 MB.")
                normalized.append(image)
            result = []
            for data, extension in normalized:
                filename = f"{uuid4().hex}.{extension}"
                path = image_path(family_id, actor.id, filename)
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with path.open("xb") as destination:
                    saved.append(path)
                    destination.write(data)
                result.append({"url":f"{PREFIX}{family_id}/{actor.id}/{filename}","type":"video" if extension=="mp4" else "image","size":len(data)})
            return {"items":result}
    except Exception as exc:
        for path in saved:
            path.unlink(missing_ok=True)
        if exceeded:
            raise HTTPException(413, "Mỗi lần tải lên tối đa 100 MB.") from None
        if isinstance(exc, OSError):
            raise HTTPException(503, "Không lưu được ảnh. Vui lòng thử lại sau.") from None
        from starlette.exceptions import HTTPException as StarletteHTTPException
        if isinstance(exc, StarletteHTTPException) and exc.status_code == 400:
            raise HTTPException(400, "Dữ liệu tải lên không hợp lệ; chọn tối đa 20 ảnh, không thêm trường biểu mẫu khác.") from None
        raise


@media_router.get("/{family_id}/{owner_id}/{filename}")
def read_image(family_id: UUID, owner_id: UUID, filename: str, actor: Actor, db: Db):
    require_family_access(db, actor, family_id)
    path = image_path(family_id, owner_id, filename)
    url = f"{PREFIX}{family_id}/{owner_id}/{filename}"
    if not path.is_file() or (actor.id != owner_id and not referenced(db, family_id, url)):
        raise HTTPException(404, "Không tìm thấy ảnh.")
    return FileResponse(path, media_type={"jpg":"image/jpeg","png":"image/png","webp":"image/webp","mp4":"video/mp4"}[path.suffix[1:]],
        headers={"Cache-Control":"private, no-store", "X-Content-Type-Options":"nosniff", "Content-Security-Policy":"default-src 'none'; sandbox"})
