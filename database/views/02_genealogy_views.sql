-- T-SQL Views & Functions - Thanh vien 2 (genealogy)
SET QUOTED_IDENTIFIER ON;
GO
USE [$(DB_NAME)];
GO

-- Cac ham/view dung bang bao dong genealogy.MemberClosure
-- (AncestorId, DescendantId, Depth; Depth = 0 la chinh no, 1 la cha/me - con, ...)

-- =====================================================================
-- 1. fn_GetAncestors: tat ca to tien cua @MemberId
--    GenerationsUp = 1 la cha/me, 2 la ong ba, 3 la cu, ...
-- =====================================================================
CREATE OR ALTER FUNCTION genealogy.fn_GetAncestors
(
    @MemberId UNIQUEIDENTIFIER
)
RETURNS TABLE
AS
RETURN
(
    SELECT
        m.[Id]        AS MemberId,
        m.[FullName],
        m.[BirthDate],
        m.[Location],
        m.[FamilyId],
        m.[BranchId],
        c.[Depth]     AS GenerationsUp
    FROM genealogy.MemberClosure AS c
    INNER JOIN genealogy.Members AS m
        ON m.[Id] = c.[AncestorId]
    WHERE c.[DescendantId] = @MemberId
      AND c.[Depth] > 0
);
GO

-- =====================================================================
-- 2. fn_GetDescendants: hau due cua @MemberId toi da @MaxDepth doi
--    @MaxDepth NULL = khong gioi han
--    GenerationsDown = 1 la con, 2 la chau, 3 la chat, ...
-- =====================================================================
CREATE OR ALTER FUNCTION genealogy.fn_GetDescendants
(
    @MemberId UNIQUEIDENTIFIER,
    @MaxDepth INT
)
RETURNS TABLE
AS
RETURN
(
    SELECT
        m.[Id]        AS MemberId,
        m.[FullName],
        m.[BirthDate],
        m.[Location],
        m.[FamilyId],
        m.[BranchId],
        c.[Depth]     AS GenerationsDown
    FROM genealogy.MemberClosure AS c
    INNER JOIN genealogy.Members AS m
        ON m.[Id] = c.[DescendantId]
    WHERE c.[AncestorId] = @MemberId
      AND c.[Depth] > 0
      AND (@MaxDepth IS NULL OR c.[Depth] <= @MaxDepth)
);
GO

-- =====================================================================
-- 3. vw_MemberDirectoryProfile: ho so thanh vien + hoc van + cong viec + so doi
--    Depth = so doi cua thanh vien trong gia pha:
--            1 = doi dau (khong co cha/me trong he thong), 2 = con, 3 = chau, ...
--    (lay chuoi to tien dai nhat tu MemberClosure)
-- =====================================================================
CREATE OR ALTER VIEW genealogy.vw_MemberDirectoryProfile
AS
SELECT
    m.[Id]          AS MemberId,
    m.[FamilyId],
    m.[BranchId],
    m.[UserId],
    m.[FullName],
    m.[BirthDate],
    m.[Location],
    m.[CreatedAt],
    anc.[Depth]     AS Depth,
    edu.[EducationCount],
    edu.[Educations],
    wk.[WorkHistoryCount],
    wk.[WorkHistories]
FROM genealogy.Members AS m
OUTER APPLY
(
    SELECT ISNULL(MAX(c.[Depth]), 0) + 1 AS Depth
    FROM genealogy.MemberClosure AS c
    WHERE c.[DescendantId] = m.[Id]
) AS anc
OUTER APPLY
(
    SELECT
        COUNT(*) AS EducationCount,
        STRING_AGG(
            CONVERT(NVARCHAR(MAX),
                e.[Institution]
                + ISNULL(N' - ' + e.[Degree], N'')
                + CASE
                    WHEN e.[StartDate] IS NULL AND e.[EndDate] IS NULL THEN N''
                    ELSE N' (' + ISNULL(CONVERT(NVARCHAR(4), YEAR(e.[StartDate])), N'?')
                         + N'-' + ISNULL(CONVERT(NVARCHAR(4), YEAR(e.[EndDate])), N'nay') + N')'
                  END),
            N'; ') WITHIN GROUP (ORDER BY e.[StartDate]) AS Educations
    FROM genealogy.Educations AS e
    WHERE e.[MemberId] = m.[Id]
) AS edu
OUTER APPLY
(
    SELECT
        COUNT(*) AS WorkHistoryCount,
        STRING_AGG(
            CONVERT(NVARCHAR(MAX),
                w.[Position] + N' @ ' + w.[Company]
                + CASE
                    WHEN w.[StartDate] IS NULL AND w.[EndDate] IS NULL THEN N''
                    ELSE N' (' + ISNULL(CONVERT(NVARCHAR(4), YEAR(w.[StartDate])), N'?')
                         + N'-' + ISNULL(CONVERT(NVARCHAR(4), YEAR(w.[EndDate])), N'nay') + N')'
                  END),
            N'; ') WITHIN GROUP (ORDER BY w.[StartDate]) AS WorkHistories
    FROM genealogy.WorkHistories AS w
    WHERE w.[MemberId] = m.[Id]
) AS wk;
GO