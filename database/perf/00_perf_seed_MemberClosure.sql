-- =====================================================================
-- PERF 00: Sinh du lieu lon de do hieu nang bang bao dong MemberClosure
--
-- Tao 1 dong ho rieng ten N'__PERF_TEST__' gom @Members thanh vien xep thanh
-- cay @Fanout-phan (moi nguoi 1 cha/me), kem ParentChild, MemberClosure,
-- Educations, WorkHistories. Khong dong cham den du lieu seed that.
-- Don dep bang 99_perf_cleanup.sql.
--
-- Chinh 2 tham so ngay duoi (khong dung bien SQLCMD de chay duoc ca 2 cach).
--   @Members = so thanh vien           (100 .. 2.000.000)
--   @Fanout  = so con toi da moi nguoi (2..20; 2 -> ~17 doi voi 100k nguoi,
--                                       3 -> ~11 doi)
-- So dong closure ~ SUM(Depth + 1) ~ @Members * (so doi trung binh + 1)
-- (100k nguoi, Fanout 2 -> ~1,7 trieu dong). Nen giu @Members <= 500.000.
-- =====================================================================
SET QUOTED_IDENTIFIER ON;
SET NOCOUNT ON;
SET XACT_ABORT ON;
GO
USE [$(DB_NAME)];
GO

DECLARE @Members INT = 100000;
DECLARE @Fanout  INT = 2;
DECLARE @FamilyName NVARCHAR(200) = N'__PERF_TEST__';

-- Fanout >= 2: Fanout = 1 la 1 chuoi dai @Members doi -> closure ~ @Members^2 / 2 dong.
IF @Members NOT BETWEEN 100 AND 2000000 OR @Fanout NOT BETWEEN 2 AND 20
    THROW 50000, N'Tham so ngoai khoang cho phep (Members 100..2000000, Fanout 2..20).', 1;

IF EXISTS (SELECT 1 FROM [core].[Families] WHERE [Name] = @FamilyName)
    THROW 50000, N'Du lieu perf da ton tai. Chay 99_perf_cleanup.sql truoc khi seed lai.', 1;

DECLARE @t0 DATETIME2(3) = SYSDATETIME();
DECLARE @FamilyId UNIQUEIDENTIFIER;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Trigger kiem tra chu trinh se di bo ca cay cho moi dong chen vao -> tat trong luc nap.
    -- Cay sinh ra chac chan khong co chu trinh va moi nut chi co 1 cha/me.
    -- Neu ROLLBACK thi DISABLE cung bi hoan tac; COMMIT thi da ENABLE lai o cuoi.
    DISABLE TRIGGER [genealogy].[trg_ParentChild_PreventCycle] ON [genealogy].[ParentChild];

    -- 1. Dong ho + 4 chi nhanh
    DECLARE @F TABLE ([Id] UNIQUEIDENTIFIER);
    INSERT INTO [core].[Families] ([Name])
    OUTPUT inserted.[Id] INTO @F
    VALUES (@FamilyName);
    SELECT @FamilyId = [Id] FROM @F;

    DECLARE @B TABLE ([Id] UNIQUEIDENTIFIER, [Name] NVARCHAR(200));
    INSERT INTO [core].[Branches] ([FamilyId], [Name])
    OUTPUT inserted.[Id], inserted.[Name] INTO @B
    VALUES (@FamilyId, N'PERF-BRANCH-0'), (@FamilyId, N'PERF-BRANCH-1'),
           (@FamilyId, N'PERF-BRANCH-2'), (@FamilyId, N'PERF-BRANCH-3');

    -- 2. Cay nut trong bang tam: nut Seq co cha la (Seq - 2) / Fanout + 1 (Seq = 1 la goc)
    CREATE TABLE #Nodes
    (
        [Seq] INT NOT NULL PRIMARY KEY,
        [Id] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWSEQUENTIALID(),
        [ParentSeq] INT NULL
    );
    CREATE INDEX [IX_Nodes_ParentSeq] ON #Nodes ([ParentSeq]);

    -- a x b cua sys.all_objects ~ vai trieu dong (>= 2.000.000 khi bang co >= 1415 dong).
    -- TOP + WHERE n <= @Members: dung som sau @Members dong va luon ra dung tap 1..@Members.
    INSERT INTO #Nodes ([Seq], [ParentSeq])
    SELECT TOP (@Members)
           CAST(x.[n] AS INT),
           CASE WHEN x.[n] = 1 THEN NULL ELSE CAST((x.[n] - 2) / @Fanout + 1 AS INT) END
    FROM
    (
        SELECT ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS [n]
        FROM sys.all_objects a
        CROSS JOIN sys.all_objects b
    ) x
    WHERE x.[n] <= @Members;

    IF (SELECT COUNT(*) FROM #Nodes) <> @Members
        THROW 50000, N'Khong sinh du so nut yeu cau (sys.all_objects qua it dong).', 1;

    -- 3. Members
    INSERT INTO [genealogy].[Members] ([Id], [FamilyId], [BranchId], [FullName], [BirthDate], [Location])
    SELECT n.[Id],
           @FamilyId,
           b.[Id],
           N'PERF-' + CAST(n.[Seq] AS NVARCHAR(10)),
           DATEADD(DAY, -((CHECKSUM(n.[Seq]) & 0x7FFFFFFF) % 25000), CAST('2000-01-01' AS DATE)),
           CHOOSE(n.[Seq] % 5 + 1, N'Ha Noi', N'TP HCM', N'Da Nang', N'Hue', N'Can Tho')
    FROM #Nodes n
    INNER JOIN @B b ON b.[Name] = N'PERF-BRANCH-' + CAST(n.[Seq] % 4 AS NVARCHAR(10))
    ORDER BY n.[Id];

    -- 4. ParentChild
    INSERT INTO [genealogy].[ParentChild] ([ParentId], [ChildId])
    SELECT p.[Id], n.[Id]
    FROM #Nodes n
    INNER JOIN #Nodes p ON p.[Seq] = n.[ParentSeq]
    ORDER BY n.[Id];

    -- 5. Hoc van (moi nguoi thu 2) va cong tac (moi nguoi thu 3): de view/proc thu muc co du lieu that
    INSERT INTO [genealogy].[Educations] ([MemberId], [Institution], [Degree], [StartDate], [EndDate])
    SELECT n.[Id], N'PERF University ' + CAST(n.[Seq] % 50 AS NVARCHAR(5)), N'Bachelor',
           CAST('2010-09-01' AS DATE), CAST('2014-06-30' AS DATE)
    FROM #Nodes n
    WHERE n.[Seq] % 2 = 0;

    INSERT INTO [genealogy].[WorkHistories] ([MemberId], [Company], [Position], [StartDate], [EndDate])
    SELECT n.[Id], N'PERF Company ' + CAST(n.[Seq] % 100 AS NVARCHAR(5)),
           CASE WHEN n.[Seq] % 2 = 0 THEN N'Engineer' ELSE N'Teacher' END,
           CAST('2015-01-01' AS DATE),
           CASE WHEN n.[Seq] % 6 = 0 THEN NULL ELSE CAST('2022-12-31' AS DATE) END
    FROM #Nodes n
    WHERE n.[Seq] % 3 = 0;

    -- 6. Bao dong tinh san trong bang tam theo tung doi (cay 1 cha/me -> khong trung cap)
    CREATE TABLE #Closure
    (
        [Depth] INT NOT NULL,
        [AncestorSeq] INT NOT NULL,
        [DescSeq] INT NOT NULL,
        PRIMARY KEY CLUSTERED ([Depth], [AncestorSeq], [DescSeq])
    );

    INSERT INTO #Closure ([Depth], [AncestorSeq], [DescSeq])
    SELECT 0, [Seq], [Seq] FROM #Nodes;

    DECLARE @d INT = 0;
    DECLARE @rows INT = 1;
    WHILE @rows > 0
    BEGIN
        INSERT INTO #Closure ([Depth], [AncestorSeq], [DescSeq])
        SELECT @d + 1, c.[AncestorSeq], n.[Seq]
        FROM #Closure c
        INNER JOIN #Nodes n ON n.[ParentSeq] = c.[DescSeq]
        WHERE c.[Depth] = @d;

        SET @rows = @@ROWCOUNT;
        SET @d += 1;
    END;

    -- Chen theo dung thu tu khoa cum (AncestorId, DescendantId) de chi muc moi nap it phan manh
    INSERT INTO [genealogy].[MemberClosure] ([AncestorId], [DescendantId], [Depth])
    SELECT a.[Id], d.[Id], c.[Depth]
    FROM #Closure c
    INNER JOIN #Nodes a ON a.[Seq] = c.[AncestorSeq]
    INNER JOIN #Nodes d ON d.[Seq] = c.[DescSeq]
    ORDER BY a.[Id], d.[Id];

    ENABLE TRIGGER [genealogy].[trg_ParentChild_PreventCycle] ON [genealogy].[ParentChild];

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;

-- 7. Thong ke day du de so do khong bi anh huong boi thong ke cu
UPDATE STATISTICS [genealogy].[Members]       WITH FULLSCAN;
UPDATE STATISTICS [genealogy].[ParentChild]   WITH FULLSCAN;
UPDATE STATISTICS [genealogy].[MemberClosure] WITH FULLSCAN;
UPDATE STATISTICS [genealogy].[Educations]    WITH FULLSCAN;
UPDATE STATISTICS [genealogy].[WorkHistories] WITH FULLSCAN;

-- PRINT khong cho phep subquery -> gan ra bien truoc
DECLARE @MemberCount BIGINT = (SELECT COUNT_BIG(*) FROM [genealogy].[Members] WHERE [FamilyId] = @FamilyId);
DECLARE @ClosureCount BIGINT, @MaxDepth INT;
SELECT @ClosureCount = COUNT_BIG(*), @MaxDepth = MAX(c.[Depth])
FROM [genealogy].[MemberClosure] c
WHERE EXISTS (SELECT 1 FROM [genealogy].[Members] m
              WHERE m.[Id] = c.[AncestorId] AND m.[FamilyId] = @FamilyId);

PRINT N'--- PERF seed xong ---';
PRINT N'FamilyId       : ' + CONVERT(NVARCHAR(36), @FamilyId);
PRINT N'Members        : ' + CONVERT(NVARCHAR(20), @MemberCount);
PRINT N'Closure rows   : ' + CONVERT(NVARCHAR(20), @ClosureCount);
PRINT N'Max Depth      : ' + CONVERT(NVARCHAR(10), @MaxDepth);
PRINT N'Thoi gian (s)  : ' + CONVERT(NVARCHAR(20), DATEDIFF(SECOND, @t0, SYSDATETIME()));
GO