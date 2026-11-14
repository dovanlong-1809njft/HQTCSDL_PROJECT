import re

from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError


def run(db, operation, write=False):
    try:
        result = operation()
        if write:
            db.commit()
        return result
    except DBAPIError as exc:
        db.rollback()
        marker = re.search(r"\[TV4_SQL:(\d+)\]", str(exc.orig))
        code = int(marker[1]) if marker else 0
        if code == 51403:
            status, message = 403,"Bạn không có quyền thao tác trong gia đình này."
        elif code in (51404,50102,50202):
            status, message = 404,"Không tìm thấy dữ liệu."
        elif code in (51509,2601,2627,547,50103,50203):
            status, message = 409,"Dữ liệu bị trùng hoặc còn liên kết. Hãy kiểm tra trước khi thay đổi."
        elif code in (50100,50200,1205,1222):
            status, message = 503,"Gia phả đang được xử lý. Vui lòng thử lại."
        elif code in (51522,50101,50104,50105,50201,50204,50205,50001,50002):
            status, message = 422,"Dữ liệu không hợp lệ: kiểm tra chi nhánh, ngày sinh, chu trình, tối đa hai cha/mẹ và quy tắc huyết thống ba đời."
        else:
            status, message = 500,"Không thể xử lý dữ liệu gia phả."
        raise HTTPException(status,message) from None
    except Exception:
        if write:
            db.rollback()
        raise
