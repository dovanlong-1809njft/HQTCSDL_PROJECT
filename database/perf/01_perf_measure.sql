-- =====================================================================
-- PERF 01: Do STATISTICS IO / STATISTICS TIME cac truy van tren MemberClosure
--
-- Dieu kien: da chay 00_perf_seed.sql (dong ho N'__PERF_TEST__').
-- Chay TOAN BO file trong 1 lan (1 batch, bien se mat neu chon chay tung doan).
--
-- Chay 2 lan: lan 1 nap cache + plan, GHI SO LIEU LAN 2 (warm).
-- Muon so cold-cache thi dat @Cold = 1 (chi tren may dev, can quyen sysadmin).
-- =====================================================================
SET QUOTED_IDENTIFIER ON;
SET NOCOUNT ON;
GO
USE [$(DB_NAME)];
GO

SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
SET STATISTICS XML OFF;

DECLARE @Cold BIT = 0;   -- 1: CHECKPOINT + DBCC DROPCLEANBUFFERS truoc moi truy van

-- ---------------------------------------------------------------------
-- Chuan bi: chon cac thanh vien mau (chua bat STATISTICS)
-- ---------------------------------------------------------------------
DECLARE @FamilyId UNIQUEIDENTIFIER =
    (SELECT [Id] FROM [core].[Families] WHERE [Name] = N'__PERF_TEST__');
IF @FamilyId IS NULL
    THROW 50000, N'Chua co du lieu perf. Chay 00_perf_seed.sql truoc.', 1;

DECLARE @Root UNIQUEIDENTIFIER =
    (SELECT TOP (1) [Id] FROM [genealogy].[Members]
     WHERE [FamilyId] = @FamilyId AND [FullName] = N'PERF-1');

DECLARE @Deep UNIQUEIDENTIFIER, @Other UNIQUEIDENTIFIER,
        @Gen3 UNIQUEIDENTIFIER, @Gen8 UNIQUEIDENTIFIER;

-- @Deep / @Other: hai nut o doi sau nhat (de LCA va truy van to tien dai nhat)
SELECT TOP (1) @Deep  = [DescendantId] FROM [genealogy].[MemberClosure]
WHERE [AncestorId] = @Root ORDER BY [Depth] DESC, [DescendantId] ASC;
SELECT TOP (1) @Other = [DescendantId] FROM [genealogy].[MemberClosure]
WHERE [AncestorId] = @Root ORDER BY [Depth] DESC, [DescendantId] DESC;
-- @Gen3: cay con lon (doi 3); @Gen8: cay con nho (doi 8)
SELECT TOP (1) @Gen3 = [DescendantId] FROM [genealogy].[MemberClosure]
WHERE [AncestorId] = @Root AND [Depth] = 3 ORDER BY [DescendantId];
SELECT TOP (1) @Gen8 = [DescendantId] FROM [genealogy].[MemberClosure]
WHERE [AncestorId] = @Root AND [Depth] = 8 ORDER BY [DescendantId];
SET @Gen3 = ISNULL(@Gen3, @Root);   -- cay qua nho, khong du doi
SET @Gen8 = ISNULL(@Gen8, @Deep);

DECLARE @MemberCount BIGINT  = (SELECT COUNT_BIG(*) FROM [genealogy].[Members] WHERE [FamilyId] = @FamilyId);
DECLARE @ClosureCount BIGINT = (SELECT COUNT_BIG(*) FROM [genealogy].[MemberClosure] WHERE [AncestorId] = @Root);
DECLARE @DeepDepth INT       = (SELECT [Depth] FROM [genealogy].[MemberClosure] WHERE [AncestorId] = @Root AND [DescendantId] = @Deep);
DECLARE @Gen3Size BIGINT     = (SELECT COUNT_BIG(*) FROM [genealogy].[MemberClosure] WHERE [AncestorId] = @Gen3);
DECLARE @Gen8Size BIGINT     = (SELECT COUNT_BIG(*) FROM [genealogy].[MemberClosure] WHERE [AncestorId] = @Gen8);

PRINT N'===== BOI CANH DO =====';
PRINT N'Members trong dong ho perf : ' + CONVERT(NVARCHAR(20), @MemberCount);
PRINT N'Dong closure cua goc       : ' + CONVERT(NVARCHAR(20), @ClosureCount) + N' (ke ca dong tu than)';
PRINT N'Depth cua nut sau nhat     : ' + CONVERT(NVARCHAR(10), @DeepDepth);
PRINT N'Cay con @Gen3 (so nut)     : ' + CONVERT(NVARCHAR(20), @Gen3Size);
PRINT N'Cay con @Gen8 (so nut)     : ' + CONVERT(NVARCHAR(20), @Gen8Size);
PRINT N'Cold cache                 : ' + CONVERT(NVARCHAR(1), @Cold);

SET STATISTICS IO ON;
SET STATISTICS TIME ON;
-- SET STATISTICS XML ON;

-- =====================================================================
-- NHOM 1: TO TIEN
-- =====================================================================
PRINT N'';
PRINT N'##### Q1a  To tien cua nut sau nhat - fn_GetAncestors (dung closure) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC sp_executesql
    N'SELECT * FROM [genealogy].[fn_GetAncestors](@id)',
    N'@id UNIQUEIDENTIFIER', @id = @Deep;

PRINT N'';
PRINT N'##### Q1b  To tien cua nut sau nhat - de quy tren ParentChild (khong closure, de so sanh) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
;WITH Up AS
(
    SELECT pc.[ParentId] AS AncestorId, 1 AS Depth
    FROM [genealogy].[ParentChild] pc
    WHERE pc.[ChildId] = @Deep
    UNION ALL
    SELECT pc.[ParentId], u.Depth + 1
    FROM Up u
    INNER JOIN [genealogy].[ParentChild] pc ON pc.[ChildId] = u.AncestorId
)
SELECT m.[Id] AS MemberId, m.[FullName], m.[BirthDate], m.[Location], m.[FamilyId], m.[BranchId], u.Depth AS GenerationsUp
FROM Up u
INNER JOIN [genealogy].[Members] m ON m.[Id] = u.AncestorId
OPTION (MAXRECURSION 200, RECOMPILE);

-- =====================================================================
-- NHOM 2: HAU DUE
-- =====================================================================
PRINT N'';
PRINT N'##### Q2a  Hau due cua GOC, khong gioi han doi - fn_GetDescendants(@root, NULL) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC sp_executesql
    N'SELECT * FROM [genealogy].[fn_GetDescendants](@id, @max)',
    N'@id UNIQUEIDENTIFIER, @max INT', @id = @Root, @max = NULL;

PRINT N'';
PRINT N'##### Q2b  Hau due cua GOC toi da 3 doi - plan da cache o Q2a duoc dung lai (parameter sniffing) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC sp_executesql
    N'SELECT * FROM [genealogy].[fn_GetDescendants](@id, @max)',
    N'@id UNIQUEIDENTIFIER, @max INT', @id = @Root, @max = 3;

PRINT N'';
PRINT N'##### Q2c  Hau due cua nut @Gen3 (cay con vua), khong gioi han doi #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC sp_executesql
    N'SELECT * FROM [genealogy].[fn_GetDescendants](@id, @max)',
    N'@id UNIQUEIDENTIFIER, @max INT', @id = @Gen3, @max = NULL;

PRINT N'';
PRINT N'##### Q2d  Hau due cua nut @Gen8 (cay con nho), khong gioi han doi #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC sp_executesql
    N'SELECT * FROM [genealogy].[fn_GetDescendants](@id, @max)',
    N'@id UNIQUEIDENTIFIER, @max INT', @id = @Gen8, @max = NULL;

PRINT N'';
PRINT N'##### Q2e  Hau due cua nut @Gen3 - de quy tren ParentChild (khong closure, de so sanh) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
;WITH Down AS
(
    SELECT pc.[ChildId] AS DescendantId, 1 AS Depth
    FROM [genealogy].[ParentChild] pc
    WHERE pc.[ParentId] = @Gen3
    UNION ALL
    SELECT pc.[ChildId], d.Depth + 1
    FROM Down d
    INNER JOIN [genealogy].[ParentChild] pc ON pc.[ParentId] = d.DescendantId
)
SELECT m.[Id] AS MemberId, m.[FullName], m.[BirthDate], m.[Location], m.[FamilyId], m.[BranchId], d.Depth AS GenerationsDown
FROM Down d
INNER JOIN [genealogy].[Members] m ON m.[Id] = d.DescendantId
OPTION (MAXRECURSION 200, RECOMPILE);

PRINT N'';
PRINT N'##### Q3  Dem hau due theo tung doi cua GOC (chi can closure, khong cham Members) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
SELECT c.[Depth], COUNT_BIG(*) AS Members
FROM [genealogy].[MemberClosure] c
WHERE c.[AncestorId] = @Root
GROUP BY c.[Depth]
ORDER BY c.[Depth]
OPTION (RECOMPILE);

-- =====================================================================
-- NHOM 3: KIEM TRA QUAN HE (cac truy van con trong usp_AddChildNode / usp_AddMarriage)
-- =====================================================================
PRINT N'';
PRINT N'##### Q4  Kiem tra chu trinh: con co phai to tien cua cha/me (tra cuu theo khoa chinh) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
SELECT CASE WHEN EXISTS
       (SELECT 1 FROM [genealogy].[MemberClosure] WHERE [AncestorId] = @Deep AND [DescendantId] = @Root)
       THEN 1 ELSE 0 END AS HasCycle
OPTION (RECOMPILE);

PRINT N'';
PRINT N'##### Q5  To tien chung gan nhat (LCA) cua 2 nut sau nhat - mau trong usp_AddMarriage #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
SELECT TOP (1) ca.[AncestorId], ca.[Depth] AS DepthA, cb.[Depth] AS DepthB, ca.[Depth] + cb.[Depth] AS Distance
FROM [genealogy].[MemberClosure] ca
INNER JOIN [genealogy].[MemberClosure] cb ON cb.[AncestorId] = ca.[AncestorId]
WHERE ca.[DescendantId] = @Deep
  AND cb.[DescendantId] = @Other
ORDER BY ca.[Depth] + cb.[Depth]
OPTION (RECOMPILE);

-- =====================================================================
-- NHOM 4: VIEW / PROC THU MUC (dung MemberClosure qua OUTER APPLY)
-- =====================================================================
PRINT N'';
PRINT N'##### Q6a  vw_MemberDirectoryProfile - 1 thanh vien (tra theo MemberId) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC sp_executesql
    N'SELECT * FROM [genealogy].[vw_MemberDirectoryProfile] WHERE [MemberId] = @id',
    N'@id UNIQUEIDENTIFIER', @id = @Deep;

PRINT N'';
PRINT N'##### Q6b  vw_MemberDirectoryProfile - trang dau 50 nguoi cua dong ho, sap theo ten #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC sp_executesql
    N'SELECT TOP (50) * FROM [genealogy].[vw_MemberDirectoryProfile] WHERE [FamilyId] = @fam ORDER BY [FullName]',
    N'@fam UNIQUEIDENTIFIER', @fam = @FamilyId;

PRINT N'';
PRINT N'##### Q7a  usp_SearchDirectory - chi theo dong ho, trang 1 #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC [genealogy].[usp_SearchDirectory] @FamilyId = @FamilyId, @PageNumber = 1, @PageSize = 50;

PRINT N'';
PRINT N'##### Q7b  usp_SearchDirectory - loc theo cay con cua goc (@RootMemberId) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC [genealogy].[usp_SearchDirectory] @FamilyId = @FamilyId, @RootMemberId = @Root, @PageNumber = 1, @PageSize = 50;

PRINT N'';
PRINT N'##### Q7c  usp_SearchDirectory - cay con cua goc + loc doi (@Generation = 5) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC [genealogy].[usp_SearchDirectory] @FamilyId = @FamilyId, @RootMemberId = @Root, @Generation = 5, @PageNumber = 1, @PageSize = 50;

PRINT N'';
PRINT N'##### Q7d  usp_SearchDirectory - tim theo tu khoa ten (CHARINDEX, khong sargable) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
EXEC [genealogy].[usp_SearchDirectory] @FamilyId = @FamilyId, @Keyword = N'PERF-1000', @PageNumber = 1, @PageSize = 50;

-- =====================================================================
-- NHOM 5: SO SANH CHI MUC (ep chi muc bang hint, chi de do - KHONG dua vao code that)
--   Q8a/Q8b: tim to tien theo DescendantId
--   Q8c/Q8d/Q8e: tim hau due <= 3 doi theo AncestorId
-- =====================================================================
PRINT N'';
PRINT N'##### Q8a  To tien - ep PK_MemberClosure (khoa dau la AncestorId -> du kien phai quet) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
SELECT c.[AncestorId], c.[Depth]
FROM [genealogy].[MemberClosure] c WITH (INDEX([PK_MemberClosure]))
WHERE c.[DescendantId] = @Deep AND c.[Depth] > 0
OPTION (RECOMPILE);

PRINT N'';
PRINT N'##### Q8b  To tien - ep IX_MemberClosure_Descendant_Depth #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
SELECT c.[AncestorId], c.[Depth]
FROM [genealogy].[MemberClosure] c WITH (INDEX([IX_MemberClosure_Descendant_Depth]))
WHERE c.[DescendantId] = @Deep AND c.[Depth] > 0
OPTION (RECOMPILE);

PRINT N'';
PRINT N'##### Q8c  Hau due <= 3 doi cua @Gen3 - ep PK_MemberClosure #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
SELECT c.[DescendantId], c.[Depth]
FROM [genealogy].[MemberClosure] c WITH (INDEX([PK_MemberClosure]))
WHERE c.[AncestorId] = @Gen3 AND c.[Depth] BETWEEN 1 AND 3
OPTION (RECOMPILE);

PRINT N'';
PRINT N'##### Q8d  Hau due <= 3 doi cua @Gen3 - ep IX_MemberClosure_Ancestor_Depth #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
SELECT c.[DescendantId], c.[Depth]
FROM [genealogy].[MemberClosure] c WITH (INDEX([IX_MemberClosure_Ancestor_Depth]))
WHERE c.[AncestorId] = @Gen3 AND c.[Depth] BETWEEN 1 AND 3
OPTION (RECOMPILE);

PRINT N'';
PRINT N'##### Q8e  Hau due <= 3 doi cua @Gen3 - de optimizer tu chon (khong hint) #####';
IF @Cold = 1 BEGIN CHECKPOINT; DBCC DROPCLEANBUFFERS WITH NO_INFOMSGS; END;
SELECT c.[DescendantId], c.[Depth]
FROM [genealogy].[MemberClosure] c
WHERE c.[AncestorId] = @Gen3 AND c.[Depth] BETWEEN 1 AND 3
OPTION (RECOMPILE);

-- =====================================================================
-- NHOM 6: DUONG GHI - usp_AddChildNode (cap nhat closure bang MERGE)
--   Moi ca chay trong transaction roi ROLLBACK -> khong de lai du lieu.
--   Chi so STATISTICS cua cau lenh EXEC duoc hien (INSERT chuan bi tat STATISTICS).
-- =====================================================================
PRINT N'';
PRINT N'##### W1  Them 1 la moi duoi nut sau nhat (them ~ Depth + 2 dong closure) #####';
BEGIN TRY
    BEGIN TRANSACTION;

    SET STATISTICS IO OFF; SET STATISTICS TIME OFF;
    DECLARE @NewLeaf UNIQUEIDENTIFIER = NEWID();
    DECLARE @PcLeaf UNIQUEIDENTIFIER;
    INSERT INTO [genealogy].[Members] ([Id], [FamilyId], [FullName])
    VALUES (@NewLeaf, @FamilyId, N'PERF-WRITE-LEAF');
    SET STATISTICS IO ON; SET STATISTICS TIME ON;

    EXEC [genealogy].[usp_AddChildNode] @ParentId = @Deep, @ChildId = @NewLeaf, @ParentChildId = @PcLeaf OUTPUT;

    SET STATISTICS IO OFF; SET STATISTICS TIME OFF;
    ROLLBACK TRANSACTION;
    SET STATISTICS IO ON; SET STATISTICS TIME ON;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    SET STATISTICS IO ON; SET STATISTICS TIME ON;
    PRINT N'W1 loi: ' + ERROR_MESSAGE();
END CATCH;

PRINT N'';
PRINT N'##### W2  Them to tien moi tren dinh GOC (xau nhat: closure them ~ @Members dong, trigger de quy ca cay) #####';
BEGIN TRY
    BEGIN TRANSACTION;

    SET STATISTICS IO OFF; SET STATISTICS TIME OFF;
    DECLARE @NewTop UNIQUEIDENTIFIER = NEWID();
    DECLARE @PcTop UNIQUEIDENTIFIER;
    INSERT INTO [genealogy].[Members] ([Id], [FamilyId], [FullName])
    VALUES (@NewTop, @FamilyId, N'PERF-WRITE-TOP');
    SET STATISTICS IO ON; SET STATISTICS TIME ON;

    EXEC [genealogy].[usp_AddChildNode] @ParentId = @NewTop, @ChildId = @Root, @ParentChildId = @PcTop OUTPUT;

    SET STATISTICS IO OFF; SET STATISTICS TIME OFF;
    ROLLBACK TRANSACTION;
    SET STATISTICS IO ON; SET STATISTICS TIME ON;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    SET STATISTICS IO ON; SET STATISTICS TIME ON;
    PRINT N'W2 loi: ' + ERROR_MESSAGE();
END CATCH;

SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
SET STATISTICS XML OFF;
PRINT N'';
PRINT N'===== XONG. Ghi so lieu lan chay thu 2 vao bang ket qua trong README.md =====';
GO