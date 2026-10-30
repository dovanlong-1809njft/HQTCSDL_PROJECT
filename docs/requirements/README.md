# Đặc tả yêu cầu FamilyConnect

**Trạng thái:** Bản dự thảo để nhóm rà soát trước khi chốt ERD và triển khai database.

## 1. Mục tiêu

FamilyConnect giúp các thành viên trong gia đình lưu trữ thông tin gia phả, trao đổi với nhau, tổ chức sự kiện và gìn giữ tài liệu, câu chuyện, hình ảnh gia đình. Nhóm ưu tiên xây dựng giao diện web trước; ứng dụng di động và AI sẽ được triển khai ở các gói công việc tiếp theo.

Tài liệu này mô tả nhu cầu nghiệp vụ. Đây chưa phải xác nhận rằng các chức năng đã được lập trình. Các file SQL hiện đang để trống; nhóm cần dùng yêu cầu đã thống nhất để rà lại [ERD](../erd/README.md) trước khi viết schema.

## 2. Phạm vi

### Trong phạm vi dự án

- Đăng ký, đăng nhập, quản lý hồ sơ và xác minh thành viên thuộc gia đình.
- Quản lý gia đình, chi nhánh, thành viên và quan hệ gia phả.
- Đăng bài, bình luận, bày tỏ cảm xúc (reaction) và nhận thông báo trong cộng đồng gia đình.
- Tạo sự kiện, RSVP, xem người tham gia và lưu ảnh sự kiện.
- Lưu tài liệu lịch sử, câu chuyện và ảnh gia đình.
- Tìm thành viên theo tên, nghề nghiệp, nơi ở và thế hệ.
- Xem thống kê hoạt động và quản trị nội dung, tài khoản, nhật ký.
- Định hướng tích hợp trợ lý AI, tìm kiếm ngữ nghĩa và giải thích quan hệ.

### Ngoài phạm vi bản đầu

- Ứng dụng mobile hoàn chỉnh.
- Huấn luyện mô hình AI riêng. Ở bản đầu, nhóm chỉ xem xét tích hợp dịch vụ AI nếu thống nhất được cách bảo vệ dữ liệu gia đình.
- Sao lưu tự động lên dịch vụ đám mây; trước mắt nhóm cần có quy trình sao lưu database phù hợp môi trường demo.

## 3. Vai trò người dùng

| Vai trò | Quyền dự kiến |
|---|---|
| `admin` | Quản lý tài khoản, phân quyền, duyệt nội dung toàn hệ thống, xem audit log và hỗ trợ quản lý dữ liệu. |
| `family_head` | Quản lý thông tin gia đình/chi nhánh được giao, xử lý yêu cầu xác minh, cập nhật gia phả và quản lý sự kiện trong phạm vi đó. |
| `member` | Cập nhật hồ sơ của mình, gửi yêu cầu xác minh, tham gia cộng đồng, RSVP và đóng góp di sản. |
| `guest` | Chỉ xem nội dung được công khai; không được chỉnh sửa hoặc xem dữ liệu riêng tư. Phạm vi chính xác cần nhóm thống nhất. |

Người dùng chỉ được xem hoặc sửa dữ liệu thuộc phạm vi gia đình mà họ được cấp quyền. Tài khoản mới mặc định là `member`; quyền quản trị không tự cấp qua form đăng ký công khai.

## 4. Use case chính

### UC-01: Đăng ký và đăng nhập

- **Tác nhân:** Khách truy cập.
- **Luồng chính:** Người dùng nhập họ tên, email và mật khẩu. Hệ thống kiểm tra dữ liệu, tạo tài khoản, băm mật khẩu và cấp JWT khi đăng nhập thành công.
- **Kết quả:** Người dùng vào được các trang phù hợp với quyền của mình.
- **Ngoại lệ:** Email đã tồn tại, dữ liệu không hợp lệ, tài khoản bị vô hiệu hóa hoặc thông tin đăng nhập sai thì hệ thống báo lỗi phù hợp.

### UC-02: Gửi yêu cầu xác minh thành viên

- **Tác nhân:** `member`.
- **Luồng chính:** Tìm thành viên trong gia phả, chọn hồ sơ muốn liên kết và gửi yêu cầu xác minh.
- **Kết quả:** Yêu cầu có trạng thái chờ; trưởng chi hoặc admin xem xét và chấp thuận/từ chối.
- **Quy tắc:** Một tài khoản chỉ liên kết với tối đa một hồ sơ thành viên; cần lưu người duyệt và thời điểm xử lý nếu nhóm muốn truy vết đầy đủ.

### UC-03: Quản lý gia phả

- **Tác nhân:** `family_head`, admin.
- **Luồng chính:** Tạo hoặc cập nhật hồ sơ thành viên; khai báo gia đình, chi nhánh, ngày sinh, nghề nghiệp và nơi ở; thêm quan hệ cha mẹ-con hoặc hôn nhân.
- **Kết quả:** Thành viên có thể tìm kiếm và xem theo thế hệ.
- **Quy tắc:** Không tạo quan hệ cha mẹ-con tự thân; không lưu trùng cùng một quan hệ; cặp hôn nhân chỉ được lưu một lần.

### UC-04: Tìm và xem danh bạ

- **Tác nhân:** Thành viên đã đăng nhập.
- **Luồng chính:** Tìm theo tên hoặc lọc theo nghề nghiệp, nơi ở, chi nhánh và thế hệ.
- **Kết quả:** Danh sách chỉ hiển thị hồ sơ mà người dùng có quyền xem.

### UC-05: Chia sẻ bài viết trong cộng đồng

- **Tác nhân:** `member`, `family_head`.
- **Luồng chính:** Thành viên đăng nội dung; những người khác có thể bình luận hoặc bày tỏ cảm xúc. Chủ bài viết có thể chỉnh sửa hoặc xóa bài theo chính sách nhóm thống nhất.
- **Kết quả:** Bài viết hiển thị trong phạm vi gia đình được chọn; thao tác kiểm duyệt được ghi nhận khi cần.

### UC-06: Tạo sự kiện và RSVP

- **Tác nhân:** `family_head`, admin; thành viên tham gia.
- **Luồng chính:** Người có quyền tạo sự kiện với tiêu đề, thời gian, địa điểm; thành viên phản hồi tham dự, từ chối hoặc chưa chắc chắn.
- **Kết quả:** Ban tổ chức xem được danh sách và trạng thái RSVP; ảnh sự kiện được lưu trong thư viện liên quan.

### UC-07: Lưu giữ di sản gia đình

- **Tác nhân:** `member`, `family_head`.
- **Luồng chính:** Tạo mục di sản thuộc loại tài liệu, câu chuyện hoặc ảnh; nhập tiêu đề, nội dung/mô tả và tải tệp lên hoặc cung cấp đường dẫn lưu trữ.
- **Kết quả:** Thành viên được cấp quyền có thể tìm và xem lại di sản.
- **Quy tắc:** Hệ thống cần ghi người đóng góp và thời điểm tạo; quyền xem/tải cần theo chính sách riêng tư của gia đình.

### UC-08: Nhận thông báo

- **Tác nhân:** Thành viên.
- **Sự kiện tạo thông báo:** Có bài đăng/hoạt động mới trong phạm vi quan tâm, lời mời sự kiện, thay đổi RSVP hoặc kết quả xác minh.
- **Kết quả:** Người dùng xem được thông báo chưa đọc và đã đọc.

### UC-09: Xem dashboard và báo cáo

- **Tác nhân:** `family_head`, admin.
- **Luồng chính:** Xem tổng số thành viên, bài viết, sự kiện và hoạt động trong phạm vi được cấp.
- **Kết quả:** Số liệu tổng hợp khớp với dữ liệu nguồn và không làm lộ dữ liệu gia đình khác.

### UC-10: Kiểm duyệt và xem nhật ký

- **Tác nhân:** Admin; trưởng chi trong phạm vi được giao.
- **Luồng chính:** Xem báo cáo nội dung, xử lý nội dung vi phạm, khóa/mở tài khoản theo quyền; admin tra cứu lịch sử thao tác.
- **Kết quả:** Thao tác quản trị quan trọng có người thực hiện, hành động và thời điểm.

### UC-11: Hỏi trợ lý AI và giải thích quan hệ

- **Tác nhân:** Thành viên đã đăng nhập.
- **Luồng chính:** Người dùng hỏi về dữ liệu mình được phép xem, tìm kiếm bằng câu hỏi tự nhiên hoặc chọn hai thành viên để yêu cầu giải thích quan hệ.
- **Kết quả:** Trợ lý trả lời dựa trên dữ liệu được phép truy cập, nêu rõ khi không đủ thông tin và không tự bịa quan hệ.
- **Điều kiện:** Chỉ triển khai sau khi nhóm thống nhất dịch vụ AI, phạm vi dữ liệu gửi đi và cách bảo vệ thông tin cá nhân.

## 5. Yêu cầu chức năng

- **FR-01:** Hệ thống đăng ký, đăng nhập, đăng xuất và cấp JWT; mật khẩu phải được băm trước khi lưu.
- **FR-02:** Hệ thống hỗ trợ hồ sơ người dùng và yêu cầu xác minh tài khoản với thành viên gia phả.
- **FR-03:** Người có quyền quản lý được tạo/sửa gia đình, chi nhánh, hồ sơ thành viên, quan hệ cha mẹ-con và hôn nhân.
- **FR-04:** Thành viên được tìm kiếm và lọc danh bạ theo các trường đã thống nhất.
- **FR-05:** Cộng đồng hỗ trợ bài viết, bình luận, reaction và thông báo.
- **FR-06:** Sự kiện hỗ trợ tạo, sửa, RSVP, xem người tham gia và quản lý ảnh.
- **FR-07:** Di sản hỗ trợ tài liệu, câu chuyện và ảnh, kèm người đóng góp và thời điểm.
- **FR-08:** Dashboard hiển thị số liệu theo phạm vi gia đình hoặc quyền quản trị.
- **FR-09:** Admin có chức năng quản lý tài khoản, kiểm duyệt nội dung và xem audit log.
- **FR-10:** AI hỗ trợ hỏi đáp, tìm kiếm ngữ nghĩa và giải thích quan hệ sau khi được nhóm duyệt về quyền riêng tư.

## 6. Yêu cầu phi chức năng

- **NFR-01 – Bảo mật:** Kiểm tra quyền ở backend cho từng tài nguyên; không dựa riêng vào việc ẩn nút trên giao diện.
- **NFR-02 – Riêng tư:** Hồ sơ gia đình, bài viết và di sản có phạm vi xem rõ ràng; dữ liệu nhạy cảm không đưa vào log hoặc prompt AI nếu chưa được phép.
- **NFR-03 – Tính dễ dùng:** Giao diện tiếng Việt, responsive trên điện thoại và máy tính; form báo lỗi cụ thể.
- **NFR-04 – Tính toàn vẹn:** Dữ liệu có khóa ngoại, UNIQUE/CHECK phù hợp; xóa dữ liệu phải theo chính sách đã thống nhất.
- **NFR-05 – Bảo trì:** Tách module, service và schema theo chức năng; thay đổi database phải có script/migration và hướng dẫn chạy.
- **NFR-06 – Sao lưu:** Có hướng dẫn sao lưu và phục hồi SQL Server trước khi đưa dữ liệu thật vào.

## 7. Điểm cần nhóm thống nhất trước khi chốt database

1. Guest xem được nội dung công khai nào? Có cần duyệt thành viên trước khi xem gia phả không?
2. Thông báo có cần lưu trong database và có loại nào? ERD hiện chưa có bảng thông báo.
3. Ảnh sự kiện và tệp di sản sẽ lưu trong dịch vụ/file storage nào? Database chỉ lưu đường dẫn hay lưu nội dung tệp?
4. Có cần bảng riêng cho thư viện ảnh/sự kiện hay dùng chung bảng di sản?
5. Trưởng chi có quyền quản lý toàn bộ gia đình hay chỉ chi nhánh được phân công?
6. Bài viết, bình luận và di sản được xóa vĩnh viễn hay cần trạng thái ẩn/kiểm duyệt?
7. AI được truy cập những dữ liệu nào, có gửi dữ liệu ra dịch vụ bên ngoài không?
8. Có cần bổ sung bảng theo dõi người duyệt, thời điểm duyệt và lý do từ chối xác minh?

## 8. Tiêu chí nghiệm thu bản đầu

- Người dùng đăng ký, đăng nhập và truy cập trang theo quyền; mật khẩu không lưu dạng rõ.
- Người có quyền tạo và xem được dữ liệu gia đình, thành viên và quan hệ gia phả; dữ liệu không hợp lệ bị từ chối.
- Thành viên có thể sử dụng các chức năng cộng đồng, sự kiện và di sản trong đúng phạm vi gia đình.
- Dashboard và chức năng quản trị chỉ hiển thị dữ liệu mà vai trò được phép xem.
- Có hướng dẫn khởi tạo database, cấu hình môi trường và chạy ứng dụng; các luồng chính được kiểm thử.

## 9. Các bước tiếp theo

Nhóm rà soát và thống nhất các câu hỏi ở mục 7; sau đó cập nhật ERD, hoàn thiện các file SQL đang để trống, rồi xây dựng API và giao diện theo các ca sử dụng. Nếu quy tắc nghiệp vụ thay đổi trong quá trình làm, nhóm cập nhật lại tài liệu này.
