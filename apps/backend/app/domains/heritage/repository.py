"""Bound T-SQL calls; SQL Server owns authorization and mutations."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def execute(db: Session, statement: str, params: dict):
    bound = {key: str(value) if isinstance(value, UUID) else value for key, value in params.items()}
    # Driver versions may omit native error numbers: preserve a private marker.
    return db.execute(text(f"""
        BEGIN TRY
            {statement}
        END TRY
        BEGIN CATCH
            DECLARE @Error NVARCHAR(2048) = CONCAT(N'[TV4_SQL:', ERROR_NUMBER(), N'] ', ERROR_MESSAGE());
            THROW 50000, @Error, 1;
        END CATCH
    """), bound)


def assert_access(db, actor_id, family_id, manage=False):
    execute(db, "EXEC heritage.usp_AssertFamilyAccess @ActorUserId=:actor_id, @FamilyId=:family_id, @Manage=:manage",
            dict(actor_id=actor_id, family_id=family_id, manage=manage)).close()


def families(db, actor_id):
    return execute(db, """
        SELECT f.Id, f.Name FROM core.Families f
        WHERE EXISTS (SELECT 1 FROM core.Users u WHERE u.UserId=:actor_id AND u.IsActive=1
            AND (u.Role=N'admin' OR (u.Role IN (N'member',N'family_head') AND EXISTS
                (SELECT 1 FROM genealogy.Members m WHERE m.UserId=u.UserId AND m.FamilyId=f.Id))))
        ORDER BY f.Name, f.Id
    """, dict(actor_id=actor_id)).mappings().all()


def page(db, resource, family_id, page, page_size, q="", item_type=None):
    # All identifiers are internal constants, never request text.
    sources = {"items": "heritage.vw_HeritageItems", "honors": "heritage.vw_Honors",
               "ranking": "heritage.vw_MemberHonorsRanking", "members": "genealogy.Members"}
    source = sources[resource]
    search = "FullName" if resource in ("ranking", "members") else "Title"
    condition = f"FamilyId=:family_id AND (:q=N'' OR CHARINDEX(:q, {search})>0)"
    if resource == "items":
        condition += " AND (:item_type IS NULL OR Type=:item_type)"
    order = {"items": "CreatedAt DESC, Id", "honors": "CreatedAt DESC, Id",
             "ranking": "Rank, FullName, MemberId", "members": "FullName, Id"}[resource]
    params = dict(family_id=family_id, q=q, item_type=item_type, offset=(page-1)*page_size, limit=page_size)
    count = execute(db, f"SELECT COUNT_BIG(*) FROM {source} WHERE {condition}", params).scalar_one()
    columns = "Id, FullName" if resource == "members" else "*"
    rows = execute(db, f"SELECT {columns} FROM {source} WHERE {condition} ORDER BY {order} "
                      "OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY", params).mappings().all()
    return dict(items=rows, total=count, page=page, page_size=page_size)


def get(db, resource, family_id, identifier):
    source = {"items": "heritage.vw_HeritageItems", "honors": "heritage.vw_Honors"}[resource]
    return execute(db, f"SELECT * FROM {source} WHERE Id=:id AND FamilyId=:family_id",
                   dict(id=identifier, family_id=family_id)).mappings().one_or_none()


def mutate(db, resource, action, actor_id, family_id, values, identifier=None):
    proc = {("items", "create"): "usp_CreateHeritageItem", ("items", "update"): "usp_UpdateHeritageItem",
            ("items", "delete"): "usp_DeleteHeritageItem", ("honors", "create"): "usp_GrantMemberHonor",
            ("honors", "update"): "usp_UpdateMemberHonor", ("honors", "delete"): "usp_DeleteMemberHonor"}[(resource, action)]
    names = {"type": "Type", "title": "Title", "description": "Description", "content": "Content",
             "media_url": "MediaUrl", "member_id": "MemberId", "date_awarded": "DateAwarded",
             "expected_version": "ExpectedVersion"}
    params = dict(actor_id=actor_id, family_id=family_id, **values)
    arguments = ["@ActorUserId=:actor_id", "@FamilyId=:family_id"]
    if identifier is not None:
        params["id"] = identifier
        arguments.append("@Id=:id")
    arguments += [f"@{names[key]}=:{key}" for key in values]
    result = execute(db, f"EXEC heritage.{proc} " + ", ".join(arguments), params)
    if action == "delete":
        result.close()
        return None
    return result.mappings().one()


def family_tree(db, actor_id, family_id):
    return execute(db, "EXEC heritage.usp_GetFamilyTreeJson @ActorUserId=:actor_id, @FamilyId=:family_id",
                   dict(actor_id=actor_id, family_id=family_id)).scalar_one()
