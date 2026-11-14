# FamilyConnect — Flutter Android

App Flutter dùng API FastAPI và SQL Server chung với website. Demo bằng **Android Emulator trong Android Studio**; không cần điện thoại, quét QR hay máy chủ JavaScript cho mobile.

Máy hiện tại đã cài Flutter 3.50/Dart 3.14, Android Studio và plugin Flutter/Dart, SDK 35/36, NDK, CMake và Android Emulator. APK debug đã cài, mở được trên Pixel và gọi được API đăng nhập; 12 kiểm thử Flutter và phân tích Dart đã đạt. Các bước cài đặt dưới đây dùng khi thiết lập lại hoặc chạy trên máy khác.

## Chạy trong Android Studio

1. Cài [Android Studio](https://developer.android.com/studio), plugin **Flutter** (kèm Dart), Android SDK Platform, Platform Tools, Command-line Tools và Android Emulator trong SDK Manager.
2. Chọn Flutter SDK tại `%LOCALAPPDATA%/FamilyConnect/flutter` (máy hiện tại: `C:/Users/LOQ/AppData/Local/FamilyConnect/flutter`). Dự án dùng Flutter 3.50/Dart 3.14 trở lên. SDK đặt ngoài thư mục có dấu để công cụ biên dịch shader hoạt động trên Windows.
3. Trên máy hiện tại, chạy lệnh dưới từ `apps/mobile` để mở Android Studio tại **F:/apps/mobile**. F: trỏ vào thư mục gốc dự án, vẫn là cùng mã nguồn; cách mở này tránh lỗi Gradle với đường dẫn tiếng Việt và lỗi analyzer khi project nằm ngay gốc ổ đĩa. Nếu dự án nằm ở đường dẫn không dấu, có thể mở trực tiếp. Chạy `flutter pub get` nếu IDE chưa tự tải dependencies.
4. Device Manager → Create Virtual Device → chọn Pixel và system image Android → khởi động giả lập.
5. Chạy backend/worker theo hướng dẫn [mục 7–11](../../docs/community-mobile.md). Trên thanh Run, chọn cấu hình **FamilyConnect** (loại Flutter), chọn giả lập **FamilyConnect_Demo** rồi bấm Run.

Cấu hình Flutter được lưu tại `.run/FamilyConnect.run.xml`. Chạy `lib/main.dart` bằng **Dart Command Line App** sẽ thiếu thư viện đồ họa `dart:ui` và sinh hàng loạt lỗi `Size`, `Offset`, `Paint`. Khi gặp lỗi này, vào **Run → Edit Configurations**, bỏ cấu hình Dart chạy `main.dart`, rồi chọn lại **FamilyConnect**. Thiết bị chạy là Android Emulator.

```powershell
powershell -ExecutionPolicy Bypass -File .\open-android-studio.ps1
```

Ổ F: cần chưa được dùng cho mục đích khác. Script kiểm tra trước khi tạo ánh xạ và không chuyển/xóa thư mục nguồn. Chạy lại sau khi khởi động lại Windows. Máy này đã có giả lập **FamilyConnect_Demo** trong Device Manager.

Giả lập này đã bật **GPU host** và hai CPU để dùng GPU có sẵn trên laptop. Khi chỉnh cấu hình Device Manager, giữ tăng tốc đồ họa bằng phần cứng; chế độ software từng làm System UI chậm lúc boot đầu.

API mặc định: `http://10.0.2.2:8000/api`. Trong Android Emulator, `10.0.2.2` trỏ về máy tính đang chạy backend. `localhost` trong giả lập là chính giả lập.

PowerShell, từ thư mục này:

```powershell
$flutter = Join-Path $env:LOCALAPPDATA 'FamilyConnect/flutter/bin/flutter.bat'
Set-Location F:/apps/mobile
& $flutter doctor
& $flutter pub get
& $flutter devices
& $flutter run -d emulator-5554
```

Thay mã thiết bị theo kết quả `flutter devices`. Backend khác máy thì truyền `--dart-define=API_BASE_URL=https://dia-chi-may-chu/api`.

## Những luồng có trong app

- Đăng nhập/đăng ký, lưu JWT bằng Android Keystore qua secure storage, khôi phục phiên, đăng xuất và xử lý 401.
- Chọn gia đình được phép; bảng tin, bài viết/ảnh, cảm xúc, bình luận, sửa/xóa theo quyền, báo cáo nội dung.
- Lịch theo tháng và múi giờ thiết bị; quản lý sự kiện, RSVP hồ sơ cá nhân, người tham gia, ảnh và nhắc lịch.
- Danh bạ lọc tên/nghề/học vấn/nơi ở/chi/thế hệ; sửa học vấn và công việc khi có quyền.
- Di sản, vinh danh, xếp hạng; sửa/xóa có kiểm tra phiên bản để tránh ghi đè thay đổi của người khác.
- Hồ sơ cá nhân, tìm hồ sơ gia phả để yêu cầu xác minh và lịch sử duyệt.
- Hộp thư thông báo, đọc thông báo và mở sự kiện; nhắc cục bộ do Android lập lịch.

Các chức năng quản trị hệ thống và quản lý người tham gia chi tiết tiếp tục có trên web. Không nhập tùy ý mã thành viên để RSVP.

## Nhắc lịch khi demo

Mở tab **Thông báo → Bật nhắc lịch Android**, cấp quyền thông báo và báo thức chính xác nếu hệ thống yêu cầu. Tạo sự kiện tương lai, đặt nhắc sau 2–3 phút. App đồng bộ nhắc khi mở, mỗi phút và sau khi thêm/hủy. Đăng xuất xóa nhắc của phiên cũ. Nội dung trên màn hình khóa chỉ hiển thị lời nhắc chung.

Worker đưa thông báo vào hộp thư SQL kể cả khi app đóng. Nhắc đã đồng bộ được Android phát cục bộ; thay đổi từ web trong lúc app đóng chỉ cập nhật khi mở lại. Chưa cấu hình FCM remote push. Khi chưa cấp quyền báo thức chính xác, Android có thể trì hoãn thông báo.

Kết nối HTTP chỉ được bật cho bản **debug** dùng giả lập. Bản phát hành cần API HTTPS; không dùng khóa ký debug để phát hành chính thức.

## Kiểm tra

```powershell
& $flutter analyze
& $flutter test
& $flutter build apk --debug
```

APK debug nằm tại `build/app/outputs/flutter-apk/app-debug.apk`. Kiểm tra SDK và giấy phép bằng `flutter doctor` trước khi build. Máy Windows có thể yêu cầu bật Developer Mode để Flutter tạo liên kết plugin.

Trong phiên này APK được build bằng `flutter build apk --debug --target-platform android-x64` để demo trên giả lập đã tạo; chưa kiểm thử điện thoại Android thật hoặc bản phát hành.

Tài liệu nền tảng: [thiết lập Flutter Android](https://docs.flutter.dev/platform-integration/android/setup), [Android Studio với Flutter](https://docs.flutter.dev/tools/android-studio).
