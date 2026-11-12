/* =====================================================================
   database/views/03_community_views.sql
   TV3 - Cong dong & Su kien: view bang tin va ham lich su kien theo thang
   Chay sau schema/*.sql (init.sh chay thu muc views/ sau schema/)
   ===================================================================== */
USE [$(DB_NAME)];
GO

/* ---------------------------------------------------------------------
   1. vw_NewsfeedPosts
   Moi dong la mot bai viet kem tac gia, so binh luan, so cam xuc va
   danh sach anh (cac MediaUrl noi bang dau phay, theo thu tu tai len).
   --------------------------------------------------------------------- */
CREATE OR ALTER VIEW [community].[vw_NewsfeedPosts]
AS
    SELECT
        p.[Id]        AS [PostId],
        p.[FamilyId],
        p.[UserId]    AS [AuthorId],
        u.[FullName]  AS [AuthorName],
        p.[Content],
        p.[CreatedAt],
        ISNULL(c.[CommentCount],  0) AS [CommentCount],
        ISNULL(r.[ReactionCount], 0) AS [ReactionCount],
        m.[MediaUrls]
    FROM [community].[Posts] AS p
    LEFT JOIN [core].[Users] AS u
        ON u.[UserId] = p.[UserId]
    OUTER APPLY (SELECT COUNT_BIG(*) AS [CommentCount]
                 FROM [community].[Comments] AS cm
                 WHERE cm.[PostId] = p.[Id]) AS c
    OUTER APPLY (SELECT COUNT_BIG(*) AS [ReactionCount]
                 FROM [community].[Reactions] AS rc
                 WHERE rc.[PostId] = p.[Id]) AS r
    OUTER APPLY (SELECT STRING_AGG(CAST(pm.[MediaUrl] AS NVARCHAR(MAX)), N',')
                          WITHIN GROUP (ORDER BY pm.[CreatedAt]) AS [MediaUrls]
                 FROM [community].[PostMedia] AS pm
                 WHERE pm.[PostId] = p.[Id]) AS m;
GO

/* ---------------------------------------------------------------------
   2. fn_GetMonthlyEvents(@FamilyId, @Year, @Month)
   Tra ve cac su kien trong thang cua mot gia dinh, kem so nguoi
   da tra loi "Going". Dung de ve lich thang tren mobile.
   Vi du: SELECT * FROM community.fn_GetMonthlyEvents(@FamilyId, 2026, 11);
   --------------------------------------------------------------------- */
CREATE OR ALTER FUNCTION [community].[fn_GetMonthlyEvents]
(
    @FamilyId UNIQUEIDENTIFIER,
    @Year     INT,
    @Month    INT
)
RETURNS TABLE
AS
RETURN
(
    SELECT
        e.[Id]        AS [EventId],
        e.[FamilyId],
        e.[Title],
        e.[EventDate],
        e.[Location],
        (SELECT COUNT_BIG(*)
         FROM [community].[EventParticipants] AS ep
         WHERE ep.[EventId] = e.[Id]
           AND ep.[RsvpStatus] = N'Going') AS [GoingCount]
    FROM [community].[Events] AS e
    WHERE e.[FamilyId] = @FamilyId
      AND @Month BETWEEN 1 AND 12
      AND e.[EventDate] >= DATEFROMPARTS(@Year, @Month, 1)
      AND e.[EventDate] <  DATEADD(MONTH, 1, DATEFROMPARTS(@Year, @Month, 1))
);
GO
