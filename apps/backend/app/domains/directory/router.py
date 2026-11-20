from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.domains.genealogy.repository import rows, scope
from app.domains.genealogy.services import run
from app.domains.heritage.repository import assert_access, execute
from app.domains.identity.models import User

router=APIRouter(prefix="/directory",tags=["directory"])
DB=Annotated[Session,Depends(get_db)]
Actor=Annotated[User,Depends(get_current_user)]
Resource=Literal["educations","work"]


class HistoryFields(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    institution: str | None=Field(default=None,max_length=200)
    degree: str | None=Field(default=None,max_length=200)
    company: str | None=Field(default=None,max_length=200)
    position: str | None=Field(default=None,max_length=200)
    start_date: date
    end_date: date | None=None

    @model_validator(mode="after")
    def dates(self):
        if self.start_date and self.end_date and self.end_date<self.start_date:
            raise ValueError("Ngày kết thúc phải sau ngày bắt đầu.")
        return self


@router.get("")
def search(family_id: UUID,db: DB,actor: Actor,q: str=Query(default="",max_length=200),
           occupation: str=Query(default="",max_length=200),education: str=Query(default="",max_length=200),
           location: str=Query(default="",max_length=300),branch_id: UUID | None=None,
           generation: int | None=Query(default=None,ge=1,le=1000),current_job: bool=False,
           page: int=Query(default=1,ge=1),page_size: int=Query(default=12,ge=1,le=200)):
    def operation():
        assert_access(db,actor.id,family_id)
        params=dict(family=family_id,q=q,occupation=occupation,education=education,location=location,
                    branch=branch_id,generation=generation,current=current_job,page=page,limit=page_size)
        statement="""EXEC genealogy.usp_SearchDirectory @FamilyId=:family,@Keyword=:q,
            @Occupation=:occupation,@Education=:education,@Location=:location,@BranchId=:branch,
            @Generation=:generation,@OnlyCurrentJob=:current,@PageNumber=:page,@PageSize=:limit"""
        result=rows(db,statement,**params)
        total=result[0]["TotalCount"] if result else 0
        if not result and page>1:
            first=rows(db,statement,**dict(params,page=1,limit=1))
            total=first[0]["TotalCount"] if first else 0
        names=dict(Id="id",FullName="name",BirthDate="birth_date",Location="location",FamilyId="family_id",
                   BranchId="branch_id",Generation="generation",LatestPosition="position",LatestCompany="company",
                   LatestInstitution="institution",LatestDegree="degree")
        return dict(items=[{alias:row[key] for key,alias in names.items()} for row in result],total=total,page=page,page_size=page_size)
    return run(db,operation)


@router.get("/{member_id}")
def detail(member_id: UUID,family_id: UUID,db: DB,actor: Actor):
    def operation():
        assert_access(db,actor.id,family_id)
        found=rows(db,"""SELECT m.Id AS id,m.FullName AS name,m.BirthDate AS birth_date,m.Location AS location,
            m.BranchId AS branch_id,m.UserId AS user_id,b.Name AS branch_name
            FROM genealogy.Members m LEFT JOIN core.Branches b ON b.Id=m.BranchId
            WHERE m.Id=:id AND m.FamilyId=:family""",id=member_id,family=family_id)
        if not found: raise HTTPException(404,"Không tìm thấy thành viên trong gia đình này.")
        member=found[0]
        own_scope=scope(db,actor.id,family_id)
        member["can_edit"]=own_scope["Role"]=="admin" or str(member["user_id"])==str(actor.id) or (
            own_scope["Role"]=="family_head" and own_scope["BranchId"] is not None and member["branch_id"]==own_scope["BranchId"])
        member.pop("user_id")
        member["educations"]=rows(db,"""SELECT Id AS id,Institution AS institution,Degree AS degree,StartDate AS start_date,EndDate AS end_date
            FROM genealogy.Educations WHERE MemberId=:id ORDER BY StartDate DESC,Id""",id=member_id)
        member["work"]=rows(db,"""SELECT Id AS id,Company AS company,Position AS position,StartDate AS start_date,EndDate AS end_date
            FROM genealogy.WorkHistories WHERE MemberId=:id ORDER BY StartDate DESC,Id""",id=member_id)
        return member
    return run(db,operation)


def save_history(db,actor,member_id,resource,action,identifier=None,payload=None):
    values=payload.model_dump() if payload else {}
    required=("institution","degree") if resource=="educations" else ("company","position")
    if action in ("create","update") and any(not values.get(field) for field in required):
        raise HTTPException(422,"Cần nhập đầy đủ thông tin học vấn hoặc công việc.")
    names=dict(institution="Institution",degree="Degree",company="Company",position="Position",start_date="StartDate",end_date="EndDate")
    statement="EXEC genealogy.usp_ManageHistory @ActorUserId=:actor,@MemberId=:member,@Resource=:resource,@Action=:action,@Id=:id"
    statement+="".join(f",@{names[key]}=:{key}" for key in values)
    return run(db,lambda: dict(execute(db,statement,dict(actor=actor.id,member=member_id,resource=resource,action=action,id=identifier,**values)).mappings().one()),write=True)


@router.post("/{member_id}/{resource}",status_code=201)
def create(member_id: UUID,resource: Resource,payload: HistoryFields,db: DB,actor: Actor):
    return save_history(db,actor,member_id,resource,"create",payload=payload)


@router.put("/{member_id}/{resource}/{identifier}")
def update(member_id: UUID,resource: Resource,identifier: UUID,payload: HistoryFields,db: DB,actor: Actor):
    return save_history(db,actor,member_id,resource,"update",identifier,payload)


@router.delete("/{member_id}/{resource}/{identifier}",status_code=204)
def remove(member_id: UUID,resource: Resource,identifier: UUID,db: DB,actor: Actor):
    save_history(db,actor,member_id,resource,"delete",identifier)
