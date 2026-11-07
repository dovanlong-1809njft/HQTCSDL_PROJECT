USE [$(DB_NAME)];
GO

/* ---------------------------------------------------------------------
   Function: heritage.fn_CosineSimilarity
   Tính độ tương đồng Cosine giữa 2 mảng Vector lưu ở dạng chuỗi JSON
   (ví dụ: '[0.12, -0.34, 0.56]') bằng hàm chuẩn OPENJSON.
   Giá trị trả về nằm trong khoảng [-1.0, 1.0] (1.0 là giống hệt nhau).
   --------------------------------------------------------------------- */
CREATE OR ALTER FUNCTION [heritage].[fn_CosineSimilarity]
(
    @VecAJson NVARCHAR(MAX),
    @VecBJson NVARCHAR(MAX)
)
RETURNS FLOAT
AS
BEGIN
    IF @VecAJson IS NULL OR @VecBJson IS NULL
       OR ISJSON(@VecAJson) <> 1 OR ISJSON(@VecBJson) <> 1
    BEGIN
        RETURN NULL;
    END;

    DECLARE @Similarity FLOAT;

    SELECT @Similarity =
        SUM(TRY_CAST(a.[value] AS FLOAT) * TRY_CAST(b.[value] AS FLOAT))
        / NULLIF(
            SQRT(SUM(POWER(TRY_CAST(a.[value] AS FLOAT), 2)))
            * SQRT(SUM(POWER(TRY_CAST(b.[value] AS FLOAT), 2))),
            0.0
          )
    FROM OPENJSON(@VecAJson) AS a
    INNER JOIN OPENJSON(@VecBJson) AS b
        ON a.[key] = b.[key];

    RETURN @Similarity;
END;
GO
