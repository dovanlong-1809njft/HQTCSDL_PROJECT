# Thiết kế cơ sở dữ liệu — SQL Server / T-SQL

TRẠNG THÁI: thiết kế đề xuất v2, CHƯA có DDL tạo bảng. 27 bảng dưới đây là danh mục triển khai, chưa phải từ điển dữ liệu cuối cùng. DBA chốt kiểu/độ dài/nullability/default/index trước khi code.

| Bảng | Nghĩa | Khóa và thuộc tính dự kiến |
|---|---|---|
| USERS | Tài khoản | UserID PK; Email UNIQUE; PasswordHash; FullName; Status; CreatedAt |
| USER_SESSIONS | Phiên đăng nhập | SessionID PK; UserID FK; TokenJti UNIQUE; ExpiresAt; RevokedAt NULL |
| ROLES | Vai trò hệ thống | RoleID PK; RoleName UNIQUE |
| USER_ROLES | Gán vai trò hệ thống | (UserID,RoleID) PK/FK |
| FAMILIES | Gia đình | FamilyID PK; FamilyName; CreatedBy FK; CreatedAt |
| FAMILY_BRANCHES | Nhánh gia đình | BranchID PK; FamilyID FK; BranchName |
| FAMILY_MEMBERS | Người trong gia phả | MemberID PK; FamilyID FK; BranchID NULL FK; UserID NULL FK; FullName; BirthDate NULL; DeathDate NULL; Gender |
| FAMILY_MEMBERSHIPS | Tư cách/quyền trong gia đình | (FamilyID,UserID) PK/FK; RoleInFamily; Status; ReviewedBy NULL; ReviewedAt NULL |
| PARENT_CHILD | Quan hệ cha/mẹ-con | (FamilyID,ParentMemberID,ChildMemberID) PK; RelationshipType |
| MARRIAGES | Hôn nhân | MarriageID PK; FamilyID; Member1ID; Member2ID; StartDate NULL; EndDate NULL |
| MEMBER_PROFILES | Hồ sơ nghề nghiệp/học vấn | MemberID PK/FK; Occupation; Education; LocationText; Biography |
| POSTS | Bài đăng/tin gia đình | PostID PK; FamilyID FK; AuthorUserID FK; Content; PostType; Status; CreatedAt |
| COMMENTS | Bình luận | CommentID PK; PostID FK; AuthorUserID FK; Content; Status; CreatedAt |
| REACTIONS | Phản ứng | (PostID,UserID) PK/FK; ReactionType; CreatedAt |
| EVENTS | Sự kiện | EventID PK; FamilyID FK; OrganizerUserID FK; Title; StartAt; EndAt; Location; Capacity NULL; Status |
| EVENT_PARTICIPANTS | RSVP/tham gia | (EventID,UserID) PK/FK; RSVPStatus; UpdatedAt |
| HERITAGE_ITEMS | Tư liệu/câu chuyện/người tiêu biểu | HeritageID PK; FamilyID FK; ItemType; Title; Content; FeaturedMemberID NULL; Status; CreatedAt; UpdatedAt |
| MEDIA_FILES | Thông tin tệp | MediaID PK; FamilyID FK; UploadedBy FK; StorageKey UNIQUE; OriginalName; MimeType; SizeBytes; Status |
| POST_MEDIA | Ảnh/tệp bài đăng | (PostID,MediaID) PK/FK; cùng FamilyID theo ràng buộc hoặc thủ tục |
| EVENT_MEDIA | Album sự kiện | (EventID,MediaID) PK/FK; cùng FamilyID |
| HERITAGE_MEDIA | Tệp di sản | (HeritageID,MediaID) PK/FK; cùng FamilyID |
| NOTIFICATIONS | Thông báo và nhắc lịch | NotificationID PK; FamilyID FK; RecipientUserID FK; EventID NULL; ReminderKey NULL; Message; IsRead; CreatedAt |
| AI_DOCUMENT_CHUNKS | Đoạn tư liệu và embedding | ChunkID PK; FamilyID FK; HeritageID FK; ChunkText; EmbeddingJson; ModelName; ModelRevision; Dimension; SourceUpdatedAt |
| AI_CHAT_HISTORY | Lịch sử hỏi đáp | ChatID PK; FamilyID FK; UserID FK; Question; Answer; SourcesJson; CreatedAt |
| AUDIT_LOGS | Nhật ký thao tác | AuditID PK; FamilyID NULL; ActorUserID FK; Action; EntityType; EntityID; CreatedAt |
| SYSTEM_SETTINGS | Cấu hình không bí mật | SettingKey PK; Value; UpdatedBy FK; UpdatedAt |
| MODERATION_ACTIONS | Lịch sử kiểm duyệt | ModerationID PK; ModeratorUserID FK; PostID NULL FK; HeritageID NULL FK; Reason; Action; CreatedAt |

## Quy tắc dữ liệu
- USERS khác FAMILY_MEMBERS: người trong phả hệ có thể chưa có tài khoản hoặc đã mất.
- FAMILY_MEMBERSHIPS.Status gồm pending/active/rejected/suspended. RoleInFamily gồm admin/member; vai trò hệ thống lưu riêng. Mỗi tài khoản được phép quản lý nhiều gia đình theo membership.
- FAMILY_MEMBERS.UserID là tùy chọn, nếu gắn tài khoản cần UNIQUE có lọc theo (FamilyID,UserID) khi UserID IS NOT NULL. Duyệt tài khoản không tự tạo thêm người trùng trong cây.
- BranchID của người phải cùng FamilyID; dùng khóa duy nhất (FamilyID,BranchID) và FK ghép tương ứng. Quan hệ cha-con/hôn nhân dùng FK ghép về (FamilyID,MemberID).
- CHECK cha khác con; chống chu trình tổ tiên bằng truy vấn đệ quy trong thủ tục. Khóa điều phối theo FamilyID trong cùng transaction cho mọi thay đổi quan hệ, hoặc giải pháp tương đương được kiểm thử, để hai phiên không đồng thời tạo chu trình.
- Hôn nhân chuẩn hóa Member1ID < Member2ID; không tự kết hôn. Phạm vi demo một bản ghi cho một cặp; ghi rõ nếu sau này cần lịch sử tái hôn.
- Thế hệ tính tương đối theo tổ tiên mốc được chọn; không coi mọi nhánh đều có chung một số thế hệ tuyệt đối. Người chưa nối được phải hiển thị chưa xác định.
- Phản ứng: một phản ứng hiện hành/người/bài. RSVP UNIQUE theo người/sự kiện; nhiều người khác nhau cùng RSVP là hợp lệ.
- Capacity NULL = không giới hạn. Khi có giới hạn, thủ tục RSVP khóa bản ghi sự kiện và kiểm tra số chỗ trong cùng transaction; mọi thao tác đổi trạng thái RSVP đi qua quy tắc này.
- POST_MEDIA/EVENT_MEDIA/HERITAGE_MEDIA thay OwnerType/OwnerID; có FK thật và kiểm tra cùng FamilyID. Đường dẫn StorageKey do máy chủ sinh; CSDL lưu metadata, tệp nằm trong volume bền vững.
- NOTIFICATIONS chống trùng nhắc lịch bằng filtered UNIQUE (RecipientUserID,EventID,ReminderKey) khi EventID/ReminderKey có giá trị.
- MODERATION_ACTIONS CHECK đúng một trong PostID/HeritageID khác NULL; lưu người thực hiện, lý do và hành động.
- EmbeddingJson dùng NVARCHAR(MAX) với ISJSON; kiểm tra dimension/model ở service. Tập demo nhỏ tính tương đồng bằng Python; không đòi hỏi kiểu VECTOR riêng của một phiên bản SQL Server.
- Tìm kiếm phải lọc FamilyID và trạng thái nguồn đang được phép trước khi xếp hạng; đổi/xóa tư liệu cần cập nhật chỉ mục. AI_CHAT_HISTORY phải kiểm tra lại quyền khi truy cập.
- Thời điểm lưu UTC trong DATETIME2; ngày sinh dùng DATE; nội dung tiếng Việt dùng NVARCHAR và N'...'; trạng thái có CHECK.
- Thêm trường cập nhật/rowversion khi cần chống mất cập nhật; không tự thêm cascade delete trên mọi quan hệ. Bài/tư liệu ưu tiên trạng thái ẩn/xóa mềm, tài khoản khóa thay vì xóa lịch sử.

## Giao tác và trách nhiệm
Stored Procedure sở hữu giao tác của các nghiệp vụ nhiều bảng: SET XACT_ABORT ON, TRY/CATCH, BEGIN TRAN, COMMIT, ROLLBACK và THROW. Kết nối repository gọi các thủ tục đó với autocommit=True; không mở transaction ngoài. Nếu đổi quy tắc này phải đổi đồng bộ connection, repository và test.

Script 01–08 tạo cấu trúc/đối tượng. 09 minh họa giao tác, 10 báo cáo, 11 quyền SQL, 12 backup và 13 restore là các bước chạy có mục đích riêng, KHÔNG chạy cả thư mục một lượt.

## Trọng tâm học phần
DDL/DML, JOIN/GROUP BY/CASE, biến và IF/WHILE khi thích hợp, ACID, COMMIT/ROLLBACK, truy cập đồng thời. View/function/procedure/trigger được đưa vào kế hoạch dự án; số lượng bắt buộc cần căn cứ đề chấm, không suy ra từ 3 bộ slide. Cursor chỉ thêm khi có yêu cầu hoặc nghiệp vụ phù hợp; ưu tiên xử lý theo tập hợp.

## Kiểm thử bắt buộc của thiết kế
1. Thêm người kèm quan hệ lỗi: rollback toàn bộ.
2. Hai phiên duyệt cùng yêu cầu: chỉ một lần chuyển pending thành active.
3. Hai phiên tranh một chỗ cuối: không vượt Capacity.
4. Hai phiên thêm quan hệ ngược chiều: không tạo chu trình.
5. Người gia đình A không đọc/sửa tệp, AI, bài hoặc người của B.
6. Backup và restore vào CSDL thử riêng, kiểm tra dữ liệu và nghiệp vụ.
