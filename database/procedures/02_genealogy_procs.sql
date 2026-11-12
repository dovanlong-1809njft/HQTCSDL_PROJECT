-- T-SQL Stored Procedures - Thanh vien 2 (genealogy)
SET QUOTED_IDENTIFIER ON;
GO
USE [$(DB_NAME)];
GO

/* =====================================================================
   1. usp_AddChildNode
   Thêm quan hệ cha/mẹ - con vào ParentChild và cập nhật MemberClosure
   trong cùng 1 transaction.
   Mã lỗi: 50100 không lấy được khóa | 50101 cha/mẹ trùng con
           50102 thành viên không tồn tại | 50103 quan hệ đã tồn tại
           50104 tạo chu trình | 50105 vượt quá 2 cha/mẹ
   ===================================================================== */
CREATE OR ALTER PROCEDURE [genealogy].[usp_AddChildNode]
    @ParentId UNIQUEIDENTIFIER,
    @ChildId UNIQUEIDENTIFIER,
    @ParentChildId UNIQUEIDENTIFIER = NULL OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Tuần tự hóa các thao tác ghi vào bảng bao đóng
        DECLARE @LockResult INT;
        EXEC @LockResult = sp_getapplock
            @Resource = N'genealogy.MemberClosure',
            @LockMode = N'Exclusive',
            @LockOwner = N'Transaction',
            @LockTimeout = 10000;
        IF @LockResult < 0
        BEGIN
            THROW 50100, N'Không thể khóa bảng bao đóng, vui lòng thử lại.', 1;
        END;

        IF @ParentId = @ChildId
        BEGIN
            THROW 50101, N'Cha/mẹ và con không thể là cùng một thành viên.', 1;
        END;

        IF NOT EXISTS (SELECT 1 FROM [genealogy].[Members] WHERE [Id] = @ParentId)
           OR NOT EXISTS (SELECT 1 FROM [genealogy].[Members] WHERE [Id] = @ChildId)
        BEGIN
            THROW 50102, N'Thành viên cha/mẹ hoặc con không tồn tại.', 1;
        END;

        IF EXISTS (SELECT 1 FROM [genealogy].[ParentChild] WHERE [ParentId] = @ParentId AND [ChildId] = @ChildId)
        BEGIN
            THROW 50103, N'Quan hệ cha/mẹ - con này đã tồn tại.', 1;
        END;

        -- Chu trình: con đã là tổ tiên của cha/mẹ
        IF EXISTS (SELECT 1 FROM [genealogy].[MemberClosure] WHERE [AncestorId] = @ChildId AND [DescendantId] = @ParentId)
        BEGIN
            THROW 50104, N'Quan hệ tạo ra chu trình huyết thống (con là tổ tiên của cha/mẹ).', 1;
        END;

        IF (SELECT COUNT(*) FROM [genealogy].[ParentChild] WHERE [ChildId] = @ChildId) >= 2
        BEGIN
            THROW 50105, N'Một thành viên chỉ có tối đa 2 cha/mẹ.', 1;
        END;

        -- Đảm bảo cả hai có dòng tự thân (Depth = 0)
        INSERT INTO [genealogy].[MemberClosure] ([AncestorId], [DescendantId], [Depth])
        SELECT v.[Id], v.[Id], 0
        FROM (VALUES (@ParentId), (@ChildId)) AS v([Id])
        WHERE NOT EXISTS
        (
            SELECT 1 FROM [genealogy].[MemberClosure] c
            WHERE c.[AncestorId] = v.[Id] AND c.[DescendantId] = v.[Id]
        );

        -- Thêm quan hệ gốc
        DECLARE @Inserted TABLE ([Id] UNIQUEIDENTIFIER);
        INSERT INTO [genealogy].[ParentChild] ([ParentId], [ChildId])
        OUTPUT inserted.[Id] INTO @Inserted
        VALUES (@ParentId, @ChildId);
        SELECT @ParentChildId = [Id] FROM @Inserted;

        -- Cập nhật bao đóng: (mọi tổ tiên của cha/mẹ, kể cả chính họ)
        --                  x (mọi hậu duệ của con, kể cả chính con)
        ;WITH Src AS
        (
            SELECT a.[AncestorId],
                   d.[DescendantId],
                   a.[Depth] + d.[Depth] + 1 AS [Depth]
            FROM [genealogy].[MemberClosure] a
            CROSS JOIN [genealogy].[MemberClosure] d
            WHERE a.[DescendantId] = @ParentId
              AND d.[AncestorId] = @ChildId
        )
        MERGE [genealogy].[MemberClosure] AS t
        USING Src AS s
            ON t.[AncestorId] = s.[AncestorId] AND t.[DescendantId] = s.[DescendantId]
        WHEN MATCHED AND s.[Depth] < t.[Depth] THEN
            UPDATE SET t.[Depth] = s.[Depth]
        WHEN NOT MATCHED BY TARGET THEN
            INSERT ([AncestorId], [DescendantId], [Depth])
            VALUES (s.[AncestorId], s.[DescendantId], s.[Depth]);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

/* =====================================================================
   2. usp_AddMarriage
   Tự sắp xếp Spouse1Id < Spouse2Id (cùng cách so sánh với CK_Marriages_SpousesOrdered)
   và chặn kết hôn cận huyết trong phạm vi @MaxGenerations đời (mặc định 3).
   Mã lỗi: 50200 không lấy được khóa | 50201 trùng người | 50202 không tồn tại
           50203 hôn nhân đã tồn tại | 50204 cận huyết | 50205 tham số sai
   ===================================================================== */
CREATE OR ALTER PROCEDURE [genealogy].[usp_AddMarriage]
    @MemberAId UNIQUEIDENTIFIER,
    @MemberBId UNIQUEIDENTIFIER,
    @MarriedDate DATE = NULL,
    @MaxGenerations INT = 3,
    @MarriageId UNIQUEIDENTIFIER = NULL OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        IF @MaxGenerations < 1
        BEGIN
            THROW 50205, N'@MaxGenerations phải >= 1.', 1;
        END;

        IF @MemberAId = @MemberBId
        BEGIN
            THROW 50201, N'Không thể kết hôn với chính mình.', 1;
        END;

        BEGIN TRANSACTION;

        DECLARE @LockResult INT;
        EXEC @LockResult = sp_getapplock
            @Resource = N'genealogy.MemberClosure',
            @LockMode = N'Exclusive',
            @LockOwner = N'Transaction',
            @LockTimeout = 10000;
        IF @LockResult < 0
        BEGIN
            THROW 50200, N'Không thể khóa bảng bao đóng, vui lòng thử lại.', 1;
        END;

        IF NOT EXISTS (SELECT 1 FROM [genealogy].[Members] WHERE [Id] = @MemberAId)
           OR NOT EXISTS (SELECT 1 FROM [genealogy].[Members] WHERE [Id] = @MemberBId)
        BEGIN
            THROW 50202, N'Một hoặc cả hai thành viên không tồn tại.', 1;
        END;

        -- Sắp xếp Spouse1Id < Spouse2Id theo chuỗi 36 ký tự (khớp CHECK constraint)
        DECLARE @Spouse1Id UNIQUEIDENTIFIER, @Spouse2Id UNIQUEIDENTIFIER;
        IF CONVERT(CHAR(36), @MemberAId) < CONVERT(CHAR(36), @MemberBId)
            SELECT @Spouse1Id = @MemberAId, @Spouse2Id = @MemberBId;
        ELSE
            SELECT @Spouse1Id = @MemberBId, @Spouse2Id = @MemberAId;

        IF EXISTS (SELECT 1 FROM [genealogy].[Marriages] WHERE [Spouse1Id] = @Spouse1Id AND [Spouse2Id] = @Spouse2Id)
        BEGIN
            THROW 50203, N'Hôn nhân giữa hai thành viên này đã tồn tại.', 1;
        END;

        -- Đảm bảo có dòng tự thân để kiểm tra quan hệ trực hệ
        INSERT INTO [genealogy].[MemberClosure] ([AncestorId], [DescendantId], [Depth])
        SELECT v.[Id], v.[Id], 0
        FROM (VALUES (@Spouse1Id), (@Spouse2Id)) AS v([Id])
        WHERE NOT EXISTS
        (
            SELECT 1 FROM [genealogy].[MemberClosure] c
            WHERE c.[AncestorId] = v.[Id] AND c.[DescendantId] = v.[Id]
        );

        -- Cận huyết: có chung tổ tiên mà cả hai cách tổ tiên <= (@MaxGenerations - 1) bậc,
        -- hoặc một người là tổ tiên trực hệ của người kia (Depth = 0 ở một phía).
        -- Với 3 đời: anh chị em (1,1), chú/bác - cháu (1,2), anh chị em họ (2,2) đều bị chặn.
        IF EXISTS
        (
            SELECT 1
            FROM [genealogy].[MemberClosure] ca
            INNER JOIN [genealogy].[MemberClosure] cb ON cb.[AncestorId] = ca.[AncestorId]
            WHERE ca.[DescendantId] = @Spouse1Id
              AND cb.[DescendantId] = @Spouse2Id
              AND (
                    (ca.[Depth] <= @MaxGenerations - 1 AND cb.[Depth] <= @MaxGenerations - 1)
                    OR ca.[Depth] = 0
                    OR cb.[Depth] = 0
                  )
        )
        BEGIN
            THROW 50204, N'Không được kết hôn giữa những người có quan hệ huyết thống trong phạm vi ba đời.', 1;
        END;

        DECLARE @Inserted TABLE ([Id] UNIQUEIDENTIFIER);
        INSERT INTO [genealogy].[Marriages] ([Spouse1Id], [Spouse2Id], [MarriedDate])
        OUTPUT inserted.[Id] INTO @Inserted
        VALUES (@Spouse1Id, @Spouse2Id, @MarriedDate);
        SELECT @MarriageId = [Id] FROM @Inserted;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

/* =====================================================================
   3. usp_SearchDirectory
   Tìm kiếm / lọc danh bạ theo Nghề nghiệp, Học vấn, Chi nhánh, Thế hệ.
   - @Generation: đời thứ n (1 = đời đầu tiên).
       + Nếu có @RootMemberId: tính từ người đó (1 = chính người đó, 2 = con, ...),
         và chỉ lấy hậu duệ của người đó.
       + Nếu không: tính theo chuỗi tổ tiên dài nhất trong ParentChild.
   - @Occupation: khớp một phần Position hoặc Company (@OnlyCurrentJob = 1: chỉ công việc hiện tại).
   - @Education : khớp một phần Institution hoặc Degree.
   ===================================================================== */
CREATE OR ALTER PROCEDURE [genealogy].[usp_SearchDirectory]
    @FamilyId UNIQUEIDENTIFIER = NULL,
    @Keyword NVARCHAR(200) = NULL,
    @Occupation NVARCHAR(200) = NULL,
    @OnlyCurrentJob BIT = 0,
    @Education NVARCHAR(200) = NULL,
    @BranchId UNIQUEIDENTIFIER = NULL,
    @Generation INT = NULL,
    @RootMemberId UNIQUEIDENTIFIER = NULL,
    @PageNumber INT = 1,
    @PageSize INT = 50
AS
BEGIN
    SET NOCOUNT ON;

    SET @Keyword = NULLIF(LTRIM(RTRIM(@Keyword)), N'');
    SET @Occupation = NULLIF(LTRIM(RTRIM(@Occupation)), N'');
    SET @Education = NULLIF(LTRIM(RTRIM(@Education)), N'');
    IF @PageNumber IS NULL OR @PageNumber < 1 SET @PageNumber = 1;
    IF @PageSize IS NULL OR @PageSize < 1 SET @PageSize = 50;
    IF @PageSize > 200 SET @PageSize = 200;

    ;WITH Base AS
    (
        SELECT m.[Id],
               m.[FamilyId],
               m.[BranchId],
               m.[FullName],
               m.[BirthDate],
               m.[Location],
               CASE WHEN @RootMemberId IS NULL
                    THEN ISNULL(g.[GenDepth], 0) + 1
                    ELSE g.[GenDepth] + 1
               END AS [Generation]
        FROM [genealogy].[Members] m
        OUTER APPLY
        (
            SELECT CASE WHEN @RootMemberId IS NULL
                        THEN MAX(c.[Depth])
                        ELSE MAX(CASE WHEN c.[AncestorId] = @RootMemberId THEN c.[Depth] END)
                   END AS [GenDepth]
            FROM [genealogy].[MemberClosure] c
            WHERE c.[DescendantId] = m.[Id]
        ) g
        WHERE (@FamilyId IS NULL OR m.[FamilyId] = @FamilyId)
          AND (@BranchId IS NULL OR m.[BranchId] = @BranchId)
          AND (@Keyword IS NULL OR CHARINDEX(@Keyword, m.[FullName]) > 0)
          AND (@RootMemberId IS NULL OR g.[GenDepth] IS NOT NULL)
          AND (@Occupation IS NULL OR EXISTS
               (
                   SELECT 1 FROM [genealogy].[WorkHistories] w
                   WHERE w.[MemberId] = m.[Id]
                     AND (CHARINDEX(@Occupation, w.[Position]) > 0 OR CHARINDEX(@Occupation, w.[Company]) > 0)
                     AND (@OnlyCurrentJob = 0 OR w.[EndDate] IS NULL)
               ))
          AND (@Education IS NULL OR EXISTS
               (
                   SELECT 1 FROM [genealogy].[Educations] e
                   WHERE e.[MemberId] = m.[Id]
                     AND (CHARINDEX(@Education, e.[Institution]) > 0 OR CHARINDEX(@Education, ISNULL(e.[Degree], N'')) > 0)
               ))
    )
    SELECT b.[Id],
           b.[FullName],
           b.[BirthDate],
           b.[Location],
           b.[FamilyId],
           b.[BranchId],
           b.[Generation],
           job.[Position] AS [LatestPosition],
           job.[Company] AS [LatestCompany],
           edu.[Institution] AS [LatestInstitution],
           edu.[Degree] AS [LatestDegree],
           COUNT(*) OVER () AS [TotalCount]
    FROM Base b
    OUTER APPLY
    (
        SELECT TOP (1) w.[Position], w.[Company]
        FROM [genealogy].[WorkHistories] w
        WHERE w.[MemberId] = b.[Id]
        ORDER BY CASE WHEN w.[EndDate] IS NULL THEN 0 ELSE 1 END, w.[StartDate] DESC
    ) job
    OUTER APPLY
    (
        SELECT TOP (1) e.[Institution], e.[Degree]
        FROM [genealogy].[Educations] e
        WHERE e.[MemberId] = b.[Id]
        ORDER BY e.[EndDate] DESC, e.[StartDate] DESC
    ) edu
    WHERE (@Generation IS NULL OR b.[Generation] = @Generation)
    ORDER BY b.[Generation], b.[BirthDate], b.[FullName]
    OFFSET (@PageNumber - 1) * @PageSize ROWS
    FETCH NEXT @PageSize ROWS ONLY;
END;
GO