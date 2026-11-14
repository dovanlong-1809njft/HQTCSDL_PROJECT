# Đo hiệu năng bảng bao đóng `genealogy.MemberClosure`

Thư mục này chứa bộ script đo **STATISTICS IO / STATISTICS TIME** và hỗ trợ phân tích **Execution Plan** cho các truy vấn trên `MemberClosure` (bảng bao đóng: mọi cặp tổ tiên – hậu duệ, `Depth = 0` là chính nó).

> Các script chưa được chạy thử trên SQL Server thật khi viết. Lần chạy đầu hãy kiểm tra thông báo lỗi; mọi "kỳ vọng" bên dưới là **giả thuyết cần xác nhận bằng số đo**, không phải kết quả.

## 1. Các file

| File | Việc làm |
|---|---|
| `00_perf_seed.sql` | Tạo dòng họ riêng `__PERF_TEST__` (mặc định 100.000 thành viên, cây nhị phân ~17 đời, ~1,7 triệu dòng closure) kèm `ParentChild`, `Educations`, `WorkHistories`. Không đụng dữ liệu seed thật. |
| `01_perf_measure.sql` | Chạy 23 ca đo với `SET STATISTICS IO, TIME ON` (mã `Q1a` … `W2`). |
| `02_perf_plan_and_index_stats.sql` | Kích thước, phân mảnh, mức dùng từng chỉ mục, top statement trong plan cache chạm `MemberClosure` (có cột `PlanXml` bấm mở được), missing index. |
| `03_perf_join_optimization.sql` | Tối ưu hoá JOIN trên closure: so sánh kiểu JOIN, cách viết điều kiện giới hạn đời, cách tính `Generation` trong `usp_SearchDirectory`, kèm kiểm tra kết quả viết lại có tương đương bản gốc (15 ca `J1a` … `J5b`). Chỉ có truy vấn đọc, không tạo/sửa đối tượng DB. |
| `99_perf_cleanup.sql` | Xoá toàn bộ dữ liệu perf theo lô. |

Tham số seed chỉnh ngay đầu `00_perf_seed.sql`: `@Members` (100 … 2.000.000, nên ≤ 500.000) và `@Fanout` (2 … 20; số con tối đa mỗi người, quyết định độ sâu cây).

## 2. Cách chạy

Các file dùng biến `$(DB_NAME)` giống phần còn lại của `database/` (xem `database/README.md`).

```bash
# 1. Nạp dữ liệu (một lần)
sqlcmd -S localhost -E -C -b -I -d FamilyConnect -v DB_NAME="FamilyConnect" -i database/perf/00_perf_seed.sql

# 2. Đo - chạy 2 lần, ghi số liệu của lần 2 (đã nạp cache + plan)
sqlcmd -S localhost -E -C -b -I -d FamilyConnect -v DB_NAME="FamilyConnect" -i database/perf/01_perf_measure.sql -o perf_run1.txt
sqlcmd -S localhost -E -C -b -I -d FamilyConnect -v DB_NAME="FamilyConnect" -i database/perf/01_perf_measure.sql -o perf_run2.txt

# 3. Thống kê chỉ mục + plan cache
sqlcmd -S localhost -E -C -b -I -d FamilyConnect -v DB_NAME="FamilyConnect" -i database/perf/02_perf_plan_and_index_stats.sql

# 4. Tối ưu JOIN (chạy 2 lần như bước 2, ghi số liệu lần 2)
sqlcmd -S localhost -E -C -b -I -d FamilyConnect -v DB_NAME="FamilyConnect" -i database/perf/03_perf_join_optimization.sql -o perf_join_run1.txt

# 5. Dọn dẹp khi xong
sqlcmd -S localhost -E -C -b -I -d FamilyConnect -v DB_NAME="FamilyConnect" -i database/perf/99_perf_cleanup.sql
```

Dùng SSMS: bật **Query → SQLCMD Mode**, thêm `:setvar DB_NAME "FamilyConnect"` ở đầu, bật **Query Options → Results → Grid → Discard results after execution** (để thời gian không bị cộng thêm thời gian hiển thị kết quả), chạy **cả file một lần** (biến chỉ sống trong một batch), đọc số liệu ở tab **Messages**. Mỗi ca có dòng `##### Qxx ... #####` đánh dấu.

Muốn xuất **Actual Execution Plan**: trong SSMS bấm `Ctrl+M` trước khi chạy, hoặc bỏ comment dòng `SET STATISTICS XML ON;` trong `01_perf_measure.sql`. Nên lưu plan thành file `.sqlplan` (chuột phải → Save Execution Plan As) theo tên ca, ví dụ `plans/Q2a_before.sqlplan`, để so sánh trước/sau khi đổi chỉ mục hoặc câu truy vấn.

`@Cold = 1` trong `01_perf_measure.sql` chạy `CHECKPOINT` + `DBCC DROPCLEANBUFFERS` trước mỗi ca để có số physical/read-ahead reads. **Chỉ dùng trên máy dev** (cần quyền sysadmin, ảnh hưởng cả instance).

## 3. Các ca đo

| Mã | Truy vấn | Điều cần xem |
|---|---|---|
| Q1a | `fn_GetAncestors` tổ tiên của nút sâu nhất | Seek trên `IX_MemberClosure_Descendant_Depth`; reads có tỉ lệ theo độ sâu, không theo tổng số dòng |
| Q1b | Đệ quy trên `ParentChild` (không dùng closure) | Mốc so sánh với Q1a |
| Q2a | `fn_GetDescendants(@root, NULL)` toàn bộ cây | Kiểu join với `Members` (Hash/Merge/Nested Loops), Estimated so với Actual rows |
| Q2b | `fn_GetDescendants(@root, 3)` dùng lại plan của Q2a | Plan cache theo tham số sniff: kết quả nhỏ nhưng plan có thể được xây cho cả cây |
| Q2c, Q2d | Hậu duệ của nút đời 3 (cây vừa) và đời 8 (cây nhỏ) | Reads có tăng theo kích thước cây con không |
| Q2e | Đệ quy trên `ParentChild` cho cây của Q2c | Mốc so sánh với Q2c |
| Q3 | Đếm hậu duệ theo từng đời | Chỉ chạm closure, Stream Aggregate không cần Sort |
| Q4 | Kiểm tra chu trình (`EXISTS` theo khoá chính) | Seek trên PK, vài logical reads |
| Q5 | Tổ tiên chung gần nhất (LCA), mẫu trong `usp_AddMarriage` | Hai seek + join trên `AncestorId` |
| Q6a, Q6b | `vw_MemberDirectoryProfile` cho 1 người và cho trang đầu 50 người | **Number of Executions** của seek vào closure ở `OUTER APPLY`: 50 hay hàng chục nghìn? |
| Q7a – Q7d | `usp_SearchDirectory` (chỉ dòng họ / theo cây con / theo đời / theo từ khoá) | Như Q6b; từ khoá dùng `CHARINDEX` nên không seek được |
| Q8a – Q8e | Ép từng chỉ mục bằng hint để so sánh | Chỉ mục nào thực sự cần, chỉ mục nào thừa (Q8a dự kiến phải quét) |
| W1, W2 | `usp_AddChildNode` thêm lá mới (W1) và thêm tổ tiên mới trên đỉnh gốc (W2, xấu nhất), mỗi ca rollback | Chi phí `MERGE` closure + trigger `trg_ParentChild_PreventCycle`; cái giá của việc có thêm chỉ mục phụ |

### Các ca đo JOIN (`03_perf_join_optimization.sql`)

Chạy sau `00_perf_seed.sql`, cùng cách chạy và cùng quy ước "chạy 2 lần, ghi lần 2" như `01`.

| Mã | Nội dung | Điều cần xem |
|---|---|---|
| J1a – J1d | JOIN closure → `Members` cho cây con **lớn** (cả cây của gốc): optimizer tự chọn / ép HASH / MERGE / LOOP | Kiểu join mà optimizer tự chọn có trùng với kiểu rẻ nhất không; LOOP có `scan count` = số nút không |
| J2a – J2c | Như trên cho cây con **nhỏ** (nút đời 8): tự chọn / HASH / LOOP | Hash có tốn memory grant và scan cả `Members` chỉ để lấy vài dòng không |
| J3a – J3d | Điều kiện `@max IS NULL OR Depth <= @max` và bản viết lại `Depth <= ISNULL(@max, 2147483647)`, qua `sp_executesql`, plan bị cache theo `@max = NULL` rồi chạy lại với `@max = 3` | So reads của J3b với J3d: plan cache của điều kiện gốc có đọc thừa khi giới hạn đời không |
| J4a, J4b | `usp_SearchDirectory` có `@RootMemberId`: `OUTER APPLY MAX(CASE …)` từng thành viên so với `INNER JOIN` closure theo khoá chính | Number of Executions của seek vào closure; logical reads của `Members` và `MemberClosure` |
| J5a, J5b | `usp_SearchDirectory` không có `@RootMemberId`: `OUTER APPLY` từng thành viên so với `LEFT JOIN` bảng gộp sẵn `GROUP BY DescendantId` | N lần seek so với một lần quét; ảnh hưởng của việc dòng họ chiếm bao nhiêu phần bảng |
| Kiểm tra cuối file | `EXCEPT` hai chiều giữa bản gốc và bản viết lại cho J3, J4, J5 | Mỗi dòng in `OK` hoặc `LECH`; chỉ tin số đo của cách viết lại khi `OK` |

J4/J5 chỉ lặp lại phần `Base` của `usp_SearchDirectory` (lọc, tính `Generation`, `COUNT(*) OVER ()`, `ORDER BY`, `OFFSET/FETCH`); hai `OUTER APPLY` lấy công việc và học vấn bị bỏ vì không dùng closure.

Các hint `HASH/MERGE/LOOP JOIN` ở J1, J2 chỉ để xem optimizer có chọn đúng không. **Không đưa hint vào hàm/proc thật**; nếu chọn sai thì sửa thống kê hoặc cách viết trước. Phần "đề xuất sửa" ở cuối `03_perf_join_optimization.sql` để trong comment, chưa áp dụng vào `views/` hay `procedures/` (đó là code của thành viên phụ trách domain `genealogy`), chỉ làm khi số đo xác nhận và được nhóm đồng ý.

## 4. Cách đọc `STATISTICS IO` và `STATISTICS TIME`

`STATISTICS IO`, mỗi bảng một dòng:

- **logical reads** – số trang 8 KB đọc từ buffer pool. Đây là chỉ số chính, ổn định giữa các lần chạy, dùng để so sánh trước/sau.
- **scan count** – số lần bảng/chỉ mục bị truy cập. Ở nhánh trong của Nested Loops, giá trị này bằng số lần seek (ví dụ 100000 nghĩa là 100.000 lần seek lặp lại).
- **physical reads / read-ahead reads** – đọc từ đĩa; chỉ khác 0 khi cold cache.
- **Worktable / Workfile** – spool, sort, hash dùng tempdb; Workfile có số lớn thường là hash spill.
- **lob logical reads** – xuất hiện ở view có `NVARCHAR(MAX)` / `STRING_AGG`.

`STATISTICS TIME`:

- **CPU time** có thể lớn hơn **elapsed time** nếu plan chạy song song.
- **parse and compile time** chỉ xuất hiện khi biên dịch plan; bỏ qua ở lần chạy thứ 2 (riêng ca dùng `OPTION (RECOMPILE)` luôn có).
- Elapsed của ca trả nhiều dòng (Q2a) gồm cả thời gian chuyển kết quả; tắt hiển thị kết quả như hướng dẫn ở mục 2.

## 5. Checklist phân tích Execution Plan

1. **Seek hay Scan?** Với seek, `Depth` nằm ở *Seek Predicates* (tốt) hay *Predicate* (bộ lọc thừa sau khi đọc)?
2. **Estimated so với Actual rows** lệch hơn 10 lần: thống kê cũ, parameter sniffing hoặc biến cục bộ.
3. **Number of Executions** của nhánh trong Nested Loops: nếu bằng số dòng của nhánh ngoài thì tổng reads = số dòng × độ sâu chỉ mục.
4. **Key Lookup / RID Lookup** trên `MemberClosure`: không nên có vì hai chỉ mục phụ đã `INCLUDE`; nếu có, thường là do truy vấn lấy cột `CreatedAt` (không nằm trong chỉ mục phụ).
5. **Kiểu join** hợp lý với số dòng: Nested Loops cho vài trăm dòng, Hash Match cho hàng chục nghìn trở lên.
6. **Cảnh báo (tam giác vàng):** Sort/Hash spill, implicit conversion (`PlanAffectingConvert`), missing index, thiếu join predicate. Xem thêm *Memory Grant* granted/used.
7. **Parallelism** (`Gather Streams`) ở truy vấn nhỏ kiểu OLTP là dấu hiệu estimate sai.
8. **Chi phí tương đối** của từng operator (thanh %), và độ dày mũi tên (số dòng thực tế).
9. So sánh Q1b/Q2e (đệ quy) với Q1a/Q2c (closure): lợi thế của closure thể hiện ở tổng logical reads và số lần seek, không chỉ ở thời gian.

Riêng khi đọc plan của các ca JOIN (J1 … J5):

10. **Nhánh build/probe của Hash Match**: bảng nhỏ hơn nên là build. Xem *Memory Grant* và *Spill Level* của Hash Match; spill nghĩa là ước lượng dòng thấp hơn thực tế.
11. **Merge Join** có kèm **Sort** không? Closure sắp theo `(AncestorId, DescendantId)` trong khi `Members` sắp theo `Id`; nếu cột join không đúng thứ tự khoá thì phải sort thêm, và Sort đó thường là phần đắt nhất.
12. **Nested Loops**: đọc *Number of Executions* của nhánh trong; tổng reads ≈ số lần thực thi × độ sâu chỉ mục (3 – 4 trang cho một lần seek vào `Members`).
13. **Số lần quét `MemberClosure`**: ở J4/J5, mục tiêu là đưa từ "N seek" xuống "1 seek (J4b) hoặc 1 lần quét (J5b)", đo bằng `scan count` của `MemberClosure` trong `STATISTICS IO`.
14. **Bước nào tính `Generation` trước `ORDER BY`**: vì `ORDER BY Generation` và `COUNT(*) OVER ()` cần tính cho mọi dòng, việc tính cho toàn bộ dòng họ là không tránh được; chỉ có thể làm cho phép tính đó rẻ hơn.

## 6. Giả thuyết cần kiểm chứng

Chỉ coi là kết luận khi số đo xác nhận.

- **Q2b**: `fn_GetDescendants` có điều kiện `@MaxDepth IS NULL OR c.Depth <= @MaxDepth`. Plan được cache theo giá trị tham số đầu tiên (`NULL` ở Q2a), nên với `@MaxDepth = 3` plan có thể đọc cả khoảng `AncestorId` và lọc ở bước sau thay vì seek theo `Depth`. Nếu đúng, thử viết lại `c.Depth <= ISNULL(@MaxDepth, 2147483647)` hoặc tách hai hàm.
- **Q7b, Q7c**: trong `usp_SearchDirectory`, `OUTER APPLY` tính `MAX(c.Depth)` cho từng dòng `Members`. Khi có `@RootMemberId`, giá trị này chính là `Depth` của đúng một dòng closure `(AncestorId = @RootMemberId, DescendantId = m.Id)`. Nếu Number of Executions của seek closure bằng số thành viên của dòng họ, hãy thử join trực tiếp theo khoá chính hoặc đi từ closure xuống `Members`.
- **Q6b**: `TOP (50) ... ORDER BY FullName` có thể sắp xếp xong rồi mới `OUTER APPLY` (50 lần), hoặc `OUTER APPLY` hết rồi mới sắp xếp (hàng chục nghìn lần). Xem plan để biết cái nào.
- **J1, J2** (kiểu JOIN): với cây con lớn, mong đợi optimizer chọn Hash hoặc Merge thay vì Nested Loops; với cây con nhỏ thì ngược lại. Nếu `LOOP JOIN` ép ở J1d tốn hơn rõ rệt nhưng optimizer vẫn chọn nó ở J1a, nguyên nhân là ước lượng dòng sai chứ không phải thiếu hint.
- **J4**: chỉ cần một seek vào closure thay vì N seek; kỳ vọng reads của `MemberClosure` giảm mạnh, còn reads của `Members` gần như không đổi (vẫn phải đọc `FamilyId = @FamilyId`).
- **J5**: chưa thể dự đoán bên nào thắng; quét một lần cả closure có thể rẻ hơn N seek khi dòng họ lớn, nhưng đắt hơn khi dòng họ nhỏ so với toàn bảng. Đó là lý do cần đo thêm trên DB có nhiều dòng họ.
- **Q8c – Q8e**: khoá cụm `(AncestorId, DescendantId)` đã chứa `Depth`, nên `IX_MemberClosure_Ancestor_Depth` chỉ hơn ở chỗ hẹp hơn và sắp theo `Depth`. Nếu reads gần bằng nhau, chỉ mục này chỉ làm `MERGE` ở W1/W2 chậm hơn.
- **Seed so với dữ liệu thật**: seed nạp closure theo thứ tự khoá nên chỉ mục gần như không phân mảnh, còn dữ liệu thật đi qua `MERGE` từng bước. Chạy mục B của `02_perf_plan_and_index_stats.sql`, và nếu cần đo lại sau `ALTER INDEX ALL ON genealogy.MemberClosure REBUILD`.

## 7. Bảng ghi kết quả

Môi trường: SQL Server ____ (phiên bản/edition) · CPU/RAM ____ · MAXDOP ____ · `@Members` ____ / `@Fanout` ____ · Closure rows ____ · Max Depth ____ · Cold/Warm ____ · Ngày đo ____

| Mã | Dòng trả về | Logical reads (bảng chính) | Scan count | CPU ms | Elapsed ms | Operator chính trong plan | Ghi chú (Est/Actual, cảnh báo) |
|---|---|---|---|---|---|---|---|
| Q1a | | | | | | | |
| Q1b | | | | | | | |
| Q2a | | | | | | | |
| Q2b | | | | | | | |
| Q2c | | | | | | | |
| Q2d | | | | | | | |
| Q2e | | | | | | | |
| Q3 | | | | | | | |
| Q4 | | | | | | | |
| Q5 | | | | | | | |
| Q6a | | | | | | | |
| Q6b | | | | | | | |
| Q7a | | | | | | | |
| Q7b | | | | | | | |
| Q7c | | | | | | | |
| Q7d | | | | | | | |
| Q8a | | | | | | | |
| Q8b | | | | | | | |
| Q8c | | | | | | | |
| Q8d | | | | | | | |
| Q8e | | | | | | | |
| W1 | | | | | | | |
| W2 | | | | | | | |
| J1a | | | | | | | |
| J1b | | | | | | | |
| J1c | | | | | | | |
| J1d | | | | | | | |
| J2a | | | | | | | |
| J2b | | | | | | | |
| J2c | | | | | | | |
| J3a | | | | | | | |
| J3b | | | | | | | |
| J3c | | | | | | | |
| J3d | | | | | | | |
| J4a | | | | | | | |
| J4b | | | | | | | |
| J5a | | | | | | | |
| J5b | | | | | | | |

Kiểm tra tương đương cuối `03`: J3 (`@max = 3`) ____ · J3 (`@max = NULL`) ____ · J4 ____ · J5 ____ (`OK`/`LECH`)

## 8. An toàn

- Chỉ chạy trên máy dev. Seed bật/tắt trigger `trg_ParentChild_PreventCycle` bên trong một transaction (rollback thì tự trả lại trạng thái cũ).
- W1/W2 rollback toàn bộ; nếu script bị ngắt giữa chừng, chạy `99_perf_cleanup.sql` để chắc chắn không còn dữ liệu `PERF-WRITE-*`.
- W2 là ca xấu nhất (closure thêm cỡ `@Members` dòng, trigger đệ quy qua cả cây); với 100.000 thành viên có thể mất vài chục giây.