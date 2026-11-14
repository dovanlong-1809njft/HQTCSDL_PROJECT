from fastapi import HTTPException

from app.domains.heritage.repository import execute, assert_access


def rows(db, statement, **params):
    return [dict(row) for row in execute(db, statement, params).mappings().all()]


def scope(db, actor, family_id):
    return rows(db,"""SELECT u.Role,m.BranchId FROM core.Users u
        LEFT JOIN genealogy.Members m ON m.UserId=u.UserId AND m.FamilyId=:family
        WHERE u.UserId=:actor""",family=family_id,actor=actor)[0]


def profile(db, actor):
    user = rows(db, "SELECT UserId AS id,FullName AS full_name,Email AS email,Role AS role FROM core.Users WHERE UserId=:actor", actor=actor)[0]
    members = rows(db, """SELECT m.Id AS id,m.FamilyId AS family_id,f.Name AS family_name,
        b.Name AS branch_name,m.BranchId AS branch_id,m.FullName AS name,m.BirthDate AS birth_date,m.Location AS location
        FROM genealogy.Members m JOIN core.Families f ON f.Id=m.FamilyId
        LEFT JOIN core.Branches b ON b.Id=m.BranchId WHERE m.UserId=:actor""", actor=actor)
    requests = rows(db, """SELECT v.Id AS id,v.Status AS status,v.CreatedAt AS created_at,
        m.FullName AS name,f.Name AS family_name FROM core.MemberVerifications v
        JOIN genealogy.Members m ON m.Id=v.MemberId JOIN core.Families f ON f.Id=m.FamilyId
        WHERE v.UserId=:actor ORDER BY v.CreatedAt DESC,v.Id""", actor=actor)
    return dict(user=user, member=members[0] if members else None, verifications=requests)


def candidates(db, family_name, full_name, birth_date):
    # Exact family/name lookup reveals only the minimum needed to request a link.
    return rows(db, """SELECT TOP (20) m.Id AS id,m.FullName AS name,f.Name AS family_name,b.Name AS branch_name
        FROM genealogy.Members m JOIN core.Families f ON f.Id=m.FamilyId
        LEFT JOIN core.Branches b ON b.Id=m.BranchId
        WHERE m.UserId IS NULL AND f.Name=:family_name AND m.FullName=:full_name
        AND (:birth_date IS NULL OR m.BirthDate=:birth_date) ORDER BY m.Id""",
        family_name=family_name, full_name=full_name, birth_date=birth_date)


def records(db, actor, family_id, resource, q, offset, limit):
    assert_access(db, actor, family_id)
    source, columns, search = {
        "branches": ("core.Branches", "Id AS id,Name AS name", "Name"),
        "members": ("genealogy.Members", "Id AS id,FullName AS name,BranchId AS branch_id,BirthDate AS birth_date,Location AS location,UserId AS user_id", "FullName"),
    }[resource]
    params = dict(family=family_id,q=q,offset=offset,limit=limit)
    where = f"FamilyId=:family AND (:q=N'' OR CHARINDEX(:q,{search})>0)"
    total = execute(db, f"SELECT COUNT_BIG(*) FROM {source} WHERE {where}", params).scalar_one()
    items = rows(db, f"SELECT {columns} FROM {source} WHERE {where} ORDER BY {search},Id OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY", **params)
    actor_scope = scope(db,actor,family_id)
    for item in items:
        branch = item["id"] if resource=="branches" else item["branch_id"]
        item["can_manage"] = actor_scope["Role"]=="admin" or (actor_scope["Role"]=="family_head" and actor_scope["BranchId"] is not None and branch==actor_scope["BranchId"])
    return dict(items=items,total=total)


def mutate(db, actor, family_id, resource, action, identifier, values):
    params = dict(actor=actor,family=family_id,resource=resource,action=action,id=identifier,**values)
    args = "@ActorUserId=:actor,@FamilyId=:family,@Resource=:resource,@Action=:action,@Id=:id"
    names = dict(name="Name",branch_id="BranchId",birth_date="BirthDate",location="Location")
    args += "".join(f",@{names[key]}=:{key}" for key in values)
    return dict(execute(db, "EXEC genealogy.usp_ManageRecord " + args, params).mappings().one())


def relations(db, actor, family_id, member_id):
    assert_access(db, actor, family_id)
    if member_id and not rows(db,"SELECT Id FROM genealogy.Members WHERE Id=:id AND FamilyId=:family",id=member_id,family=family_id):
        raise HTTPException(404,"Không tìm thấy thành viên.")
    params = dict(family=family_id)
    edges = rows(db,"""SELECT p.Id AS id,p.ParentId AS first_id,p.ChildId AS second_id,
        a.FullName AS first_name,b.FullName AS second_name FROM genealogy.ParentChild p
        JOIN genealogy.Members a ON a.Id=p.ParentId JOIN genealogy.Members b ON b.Id=p.ChildId
        WHERE a.FamilyId=:family AND b.FamilyId=:family ORDER BY a.FullName,b.FullName,p.Id""",**params)
    marriages = rows(db,"""SELECT p.Id AS id,p.Spouse1Id AS first_id,p.Spouse2Id AS second_id,
        a.FullName AS first_name,b.FullName AS second_name,p.MarriedDate AS married_date FROM genealogy.Marriages p
        JOIN genealogy.Members a ON a.Id=p.Spouse1Id JOIN genealogy.Members b ON b.Id=p.Spouse2Id
        WHERE a.FamilyId=:family AND b.FamilyId=:family ORDER BY a.FullName,b.FullName,p.Id""",**params)
    ancestors = rows(db,"SELECT MemberId AS id,FullName AS name,GenerationsUp AS depth FROM genealogy.fn_GetAncestors(:id) WHERE FamilyId=:family ORDER BY GenerationsUp,FullName",id=member_id,**params) if member_id else []
    descendants = rows(db,"SELECT MemberId AS id,FullName AS name,GenerationsDown AS depth FROM genealogy.fn_GetDescendants(:id,NULL) WHERE FamilyId=:family ORDER BY GenerationsDown,FullName",id=member_id,**params) if member_id else []
    actor_scope = scope(db,actor,family_id)
    managed = {row["Id"] for row in rows(db,"SELECT Id FROM genealogy.Members WHERE BranchId=:branch AND FamilyId=:family",branch=actor_scope["BranchId"],**params)} if actor_scope["Role"]=="family_head" else set()
    for edge in edges:
        edge["can_manage"] = actor_scope["Role"]=="admin" or edge["second_id"] in managed
    for marriage in marriages:
        marriage["can_manage"] = actor_scope["Role"]=="admin" or marriage["first_id"] in managed or marriage["second_id"] in managed
    return dict(parent_child=edges,marriages=marriages,ancestors=ancestors,descendants=descendants)
