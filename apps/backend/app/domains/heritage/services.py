import json
import re

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.domains.heritage import repository as repo
from app.domains.heritage.schemas import (
    FamilyTree, HonorFields, HonorResponse, ItemFields, ItemResponse,
    FamilyResponse, MemberResponse, RankingResponse,
)

ERRORS = {
    51403: (403, "Bạn không có quyền truy cập hoặc thao tác trong gia đình này."),
    51404: (404, "Không tìm thấy dữ liệu trong gia đình đã chọn."),
    51409: (409, "Dữ liệu đã thay đổi. Hãy tải lại trước khi lưu hoặc xóa."),
    51410: (409, "Tư liệu đã được AI lập chỉ mục. Cần phối hợp TV5 trước khi thay đổi."),
    51422: (422, "Nội dung di sản hoặc vinh danh chưa hợp lệ."),
    1205: (503, "Dữ liệu đang được xử lý. Vui lòng thử lại."),
    1222: (503, "Dữ liệu đang bị khóa. Vui lòng thử lại."),
}
MODELS = {"items": ItemResponse, "honors": HonorResponse,
          "ranking": RankingResponse, "members": MemberResponse}


def run(db, operation, write=False):
    try:
        result = operation()
        if write:
            db.commit()
        return result
    except DBAPIError as exc:
        db.rollback()
        message = str(exc.orig)
        marker = re.search(r"\[TV4_SQL:(\d+)\]", message)
        codes = [int(marker[1])] if marker else [int(n) for n in re.findall(r"\((\d{4,5})\)", message)]
        status, detail = next((ERRORS[c] for c in codes if c in ERRORS),
                              (500, "Không thể xử lý dữ liệu TV4. Kiểm tra cấu hình SQL Server."))
        raise HTTPException(status, detail) from None
    except Exception:
        if write:
            db.rollback()
        raise


def families(db, actor):
    return run(db, lambda: [FamilyResponse.model_validate(r) for r in repo.families(db, actor.id)])


def list_resource(db, actor, family_id, resource, **filters):
    def operation():
        repo.assert_access(db, actor.id, family_id)
        result = repo.page(db, resource, family_id, **filters)
        result["items"] = [MODELS[resource].model_validate(r) for r in result["items"]]
        return result
    return run(db, operation)


def read(db, actor, family_id, resource, identifier):
    def operation():
        repo.assert_access(db, actor.id, family_id)
        row = repo.get(db, resource, family_id, identifier)
        if row is None:
            raise HTTPException(404, "Không tìm thấy dữ liệu trong gia đình đã chọn.")
        return MODELS[resource].model_validate(row)
    return run(db, operation)


def mutate(db, actor, family_id, resource, action, payload=None, identifier=None, expected_version=None):
    def operation():
        repo.assert_access(db, actor.id, family_id, manage=resource == "honors")
        values = payload.model_dump(exclude_unset=True) if payload is not None else {}
        if action == "update":
            current = repo.get(db, resource, family_id, identifier)
            if current is None:
                raise HTTPException(404, "Không tìm thấy dữ liệu trong gia đình đã chọn.")
            model = MODELS[resource].model_validate(current)
            fields = ItemFields if resource == "items" else HonorFields
            merged = {key: getattr(model, key) for key in fields.model_fields}
            merged.update({key: value for key, value in values.items() if key != "expected_version"})
            try:
                checked = fields.model_validate(merged)
            except ValidationError:
                raise HTTPException(422, "Nội dung sau cập nhật chưa hợp lệ.") from None
            values = dict(**checked.model_dump(), expected_version=values["expected_version"])
        elif action == "delete":
            values = dict(expected_version=expected_version)
        result = repo.mutate(db, resource, action, actor.id, family_id, values, identifier)
        return MODELS[resource].model_validate(result) if result is not None else None
    return run(db, operation, write=True)


def tree(db, actor, family_id):
    def operation():
        data = json.loads(repo.family_tree(db, actor.id, family_id))
        return FamilyTree.model_validate(data)
    return run(db, operation)
