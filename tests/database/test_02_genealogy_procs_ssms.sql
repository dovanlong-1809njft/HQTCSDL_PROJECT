
USE [$(DB_NAME)];
GO

DECLARE @FamilyId UNIQUEIDENTIFIER;
SELECT TOP 1 @FamilyId = Id FROM core.Families;

-- Khoi tao ID kiem thu
DECLARE @A UNIQUEIDENTIFIER = NEWID(),
        @B UNIQUEIDENTIFIER = NEWID(),
        @C UNIQUEIDENTIFIER = NEWID(),
        @D UNIQUEIDENTIFIER = NEWID(),
        @E UNIQUEIDENTIFIER = NEWID(),
        @F UNIQUEIDENTIFIER = NEWID();

-- Du lieu thanh vien gia pha
INSERT INTO genealogy.Members (Id, FamilyId, FullName)
VALUES
(@A, @FamilyId, N'Test Ancestor A'),
(@B, @FamilyId, N'Test Ancestor B'),
(@C, @FamilyId, N'Test Child C'),
(@D, @FamilyId, N'Test Grandchild D'),
(@E, @FamilyId, N'Test Member E'),
(@F, @FamilyId, N'Test Member F');

-- Khoi tao MemberClosure
INSERT INTO genealogy.MemberClosure (AncestorId, DescendantId, Depth)
VALUES (@A,@A,0),(@B,@B,0),(@C,@C,0),
       (@D,@D,0),(@E,@E,0),(@F,@F,0);

-- Tao quan he gia pha ban dau
EXEC genealogy.usp_AddChildNode @ParentId=@A, @ChildId=@C;
EXEC genealogy.usp_AddChildNode @ParentId=@B, @ChildId=@C;
EXEC genealogy.usp_AddChildNode @ParentId=@C, @ChildId=@D;

-- TC01: Them quan he cha/me - con hop le
EXEC genealogy.usp_AddChildNode @ParentId=@D, @ChildId=@E;

-- TC02: Them lai quan he da ton tai (du kien bao loi)
-- EXEC genealogy.usp_AddChildNode @ParentId=@A, @ChildId=@C;

-- TC03: Tao quan he voi chinh minh (du kien bao loi)
-- EXEC genealogy.usp_AddChildNode @ParentId=@A, @ChildId=@A;

-- TC04: Tao chu trinh huyet thong (du kien bao loi)
-- EXEC genealogy.usp_AddChildNode @ParentId=@D, @ChildId=@A;

-- Kiem tra quan he va khoang cach the he
SELECT * FROM genealogy.ParentChild;
SELECT * FROM genealogy.MemberClosure;

-- TC05: Them hon nhan hop le
EXEC genealogy.usp_AddMarriage
    @MemberAId=@A, @MemberBId=@F,
    @MarriedDate='2026-01-01', @MaxGenerations=3;

-- TC06: Ket hon voi chinh minh (du kien bao loi)
-- EXEC genealogy.usp_AddMarriage @MemberAId=@A, @MemberBId=@A;

-- TC07: Ket hon voi hau due truc he (du kien bao loi)
-- EXEC genealogy.usp_AddMarriage
--     @MemberAId=@A, @MemberBId=@D, @MaxGenerations=3;

-- TC08: Kiem tra du lieu hon nhan
SELECT * FROM genealogy.Marriages;

-- Du lieu hoc van va cong tac
INSERT INTO genealogy.Educations (MemberId, Institution, Degree)
VALUES (@A, N'University of Technology', N'Bachelor');

INSERT INTO genealogy.WorkHistories (MemberId, Company, Position)
VALUES (@A, N'ABC Company', N'Software Engineer');

-- TC09: Tim kiem theo ten
EXEC genealogy.usp_SearchDirectory @Keyword=N'Test Ancestor A';

-- TC10: Tim kiem theo nghe nghiep
EXEC genealogy.usp_SearchDirectory @Occupation=N'Engineer';

-- TC11: Tim kiem theo hoc van
EXEC genealogy.usp_SearchDirectory @Education=N'University of Technology';

-- TC12: Tim kiem hau due theo thanh vien goc
EXEC genealogy.usp_SearchDirectory @RootMemberId=@A;

-- TC13: Tim kiem khong co ket qua
EXEC genealogy.usp_SearchDirectory @Keyword=N'NotExist999';

-- TC14: Kiem tra phan trang
EXEC genealogy.usp_SearchDirectory
    @FamilyId=@FamilyId, @PageNumber=1, @PageSize=3;

-- Xoa du lieu kiem thu
DELETE FROM genealogy.Marriages
WHERE Spouse1Id IN (@A,@B,@C,@D,@E,@F)
   OR Spouse2Id IN (@A,@B,@C,@D,@E,@F);

DELETE FROM genealogy.ParentChild
WHERE ParentId IN (@A,@B,@C,@D,@E,@F)
   OR ChildId IN (@A,@B,@C,@D,@E,@F);

DELETE FROM genealogy.Educations WHERE MemberId IN (@A,@B,@C,@D,@E,@F);
DELETE FROM genealogy.WorkHistories WHERE MemberId IN (@A,@B,@C,@D,@E,@F);
DELETE FROM genealogy.MemberClosure
WHERE AncestorId IN (@A,@B,@C,@D,@E,@F)
   OR DescendantId IN (@A,@B,@C,@D,@E,@F);
DELETE FROM genealogy.Members WHERE Id IN (@A,@B,@C,@D,@E,@F);
GO  
