-- T-SQL Views & Functions - Thanh vien 4 (heritage & family tree)
USE [$(DB_NAME)];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO
-- Include zero-honor members. Ties share DENSE_RANK, independently per family.
CREATE OR ALTER VIEW heritage.vw_MemberHonorsRanking
AS
    SELECT m.FamilyId, m.Id AS MemberId, m.FullName,
           COUNT_BIG(h.Id) AS HonorCount,
           DENSE_RANK() OVER (PARTITION BY m.FamilyId ORDER BY COUNT_BIG(h.Id) DESC) AS Rank
    FROM genealogy.Members m
    LEFT JOIN heritage.Honors h ON h.MemberId = m.Id
    GROUP BY m.FamilyId, m.Id, m.FullName;
GO
-- Content fingerprints provide optimistic concurrency without altering existing tables.
CREATE OR ALTER VIEW heritage.vw_HeritageItems
AS
    SELECT i.*,
        CONVERT(VARCHAR(64), HASHBYTES('SHA2_256',
            (SELECT i.Id, i.FamilyId, i.CreatedByUserId, i.Type, i.Title,
                    i.Description, i.Content, i.MediaUrl, i.CreatedAt
             FOR JSON PATH, INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER)), 2) AS VersionToken
    FROM heritage.Items i;
GO
CREATE OR ALTER VIEW heritage.vw_Honors
AS
    SELECT h.*, m.FamilyId, m.FullName,
        CONVERT(VARCHAR(64), HASHBYTES('SHA2_256',
            (SELECT h.Id, h.MemberId, h.Title, h.Description, h.DateAwarded, h.CreatedAt
             FOR JSON PATH, INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER)), 2) AS VersionToken
    FROM heritage.Honors h
    INNER JOIN genealogy.Members m ON m.Id = h.MemberId;
GO
