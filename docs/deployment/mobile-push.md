# Chạy app trên điện thoại và nhận thông báo đẩy

Tài liệu của TV3. Trả lời câu hỏi: làm sao để app trên điện thoại nhận được thông báo nhắc sự kiện, và vẫn dùng được khi máy tính đã tắt.

## 1. Vì sao hiện tại tắt máy là mất app

Hiện tại cả ba thứ đều nằm trên laptop: SQL Server trong Docker, backend FastAPI ở cổng 8000, và tiến trình nền quét nhắc nhở. Điện thoại chỉ là màn hình gọi vào laptop qua Wi-Fi. Tắt laptop thì không còn ai trả lời, nên app trắng dữ liệu.

Muốn tắt laptop mà app vẫn chạy thì cần ba điều kiện, thiếu một cái là không được:

| Điều kiện | Vì sao cần | Làm ở đâu |
| --- | --- | --- |
| 1. Cơ sở dữ liệu và backend chạy trên máy luôn bật | Điện thoại phải có nơi để gọi API | Dịch vụ cloud, mục 5 |
| 2. Tiến trình nền chạy trên máy luôn bật | Nhắc nhở đến hạn phải có ai đó quét và gửi | Cùng chỗ với backend, mục 5 |
| 3. Firebase Cloud Messaging (FCM) | Để hệ điều hành đẩy thông báo tới điện thoại kể cả khi app đóng | Mục 3 và 4 |

Thông báo trong app (`/notifications`) khác với thông báo đẩy. Thông báo trong app chỉ hiện khi người dùng mở app. Muốn điện thoại rung lên khi app đang đóng thì phải qua FCM, không có cách nào khác.

## 2. Phần đã có trong repo

Phía server đã làm xong, chỉ còn cắm cấu hình vào:

| Thành phần | Tệp | Việc nó làm |
| --- | --- | --- |
| Bảng thiết bị | `database/schema/11_push_devices.sql` | `community.DeviceTokens` lưu token FCM của từng máy; thêm cột `Notifications.PushedAt` |
| Thủ tục | `database/procedures/14_push_devices_procs.sql` | Đăng ký, gỡ token; lấy thông báo chưa đẩy; trả lại thông báo gửi lỗi |
| API | `apps/backend/app/domains/notifications/devices.py` | `POST /api/notifications/devices`, `DELETE /api/notifications/devices` |
| Tiến trình nền | `apps/worker/jobs/push_notification.py` | Gửi thông báo tới FCM, xóa token hết hiệu lực, gửi lại khi lỗi |

Sau khi kéo code về, nạp hai tệp SQL mới vào database:

```powershell
# Trong Git Bash hoặc PowerShell, tại gốc repo
docker cp database/schema/11_push_devices.sql sqlserver:/tmp/
docker cp database/procedures/14_push_devices_procs.sql sqlserver:/tmp/
docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'Long@12345678' -C `
  -v DB_NAME=FamilyConnect -i /tmp/11_push_devices.sql
docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'Long@12345678' -C `
  -v DB_NAME=FamilyConnect -i /tmp/14_push_devices_procs.sql
```

Chưa cấu hình FCM thì tiến trình nền in một dòng thông báo bỏ qua rồi chạy tiếp, không làm hỏng phần của ai.

## 3. Lập project Firebase

Miễn phí, không cần thẻ. Làm một lần.

1. Vào [Firebase Console](https://console.firebase.google.com), tạo project tên `FamilyConnect`.
2. Thêm app Android: nhập package name đúng như trong `apps/mobile/android/app/build.gradle` (mục `applicationId`), tải về `google-services.json`, đặt vào `apps/mobile/android/app/`.
3. Vào Project settings, tab Service accounts, bấm Generate new private key. Tải về tệp JSON, **không commit tệp này lên GitHub**.
4. Đặt tệp JSON ở chỗ an toàn, rồi thêm vào `.env` ở gốc repo:

```
FCM_SERVICE_ACCOUNT_FILE=C:/Users/ADMIN/secrets/familyconnect-fcm.json
```

Thêm dòng sau vào `.gitignore` nếu đặt tệp trong repo:

```
*-fcm.json
```

## 4. Phần việc trong app Flutter

Phần này nằm trong `apps/mobile` do Hân phụ trách, cần nói với bạn ấy. Ba việc:

1. Thêm thư viện vào `pubspec.yaml`: `firebase_core`, `firebase_messaging`.
2. Thêm plugin Google Services vào Gradle theo hướng dẫn Firebase khi thêm app Android.
3. Sau khi đăng nhập xong, xin quyền thông báo, lấy token rồi gửi lên backend:

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

// Gọi một lần trong main() trước runApp
await Firebase.initializeApp();

// Gọi ngay sau khi đăng nhập thành công, và mỗi lần token đổi
Future<void> dangKyThietBi(String jwt) async {
  final messaging = FirebaseMessaging.instance;
  await messaging.requestPermission();            // Android 13+ bắt buộc xin quyền
  final token = await messaging.getToken();
  if (token == null) return;

  await api.post(
    '/api/notifications/devices',
    headers: {'Authorization': 'Bearer $jwt'},
    body: {'token': token, 'platform': 'android'},
  );

  // Token có thể đổi khi cài lại app hoặc xóa dữ liệu
  messaging.onTokenRefresh.listen((moi) => api.post(
    '/api/notifications/devices',
    headers: {'Authorization': 'Bearer $jwt'},
    body: {'token': moi, 'platform': 'android'},
  ));
}
```

Khi đăng xuất thì gọi `DELETE /api/notifications/devices` với cùng token, để người khác dùng chung máy không nhận thông báo của mình.

Thông báo gửi kèm `data.event_id`, app dùng nó để mở đúng sự kiện khi người dùng bấm vào thông báo.

## 5. Đưa backend và database lên cloud

Đây là phần quyết định việc tắt laptop vẫn dùng được. Hai phương án, chọn một.

### Phương án A — Thuê một máy ảo, giữ nguyên SQL Server

Giữ đúng Docker Compose đang chạy, nên không phải sửa SQL. Phù hợp khi muốn chắc ăn trước ngày bảo vệ.

- Đăng ký [Azure for Students](https://azure.microsoft.com/free/students/): sinh viên có mã trường được cấp tín dụng dùng trong 12 tháng, không cần thẻ tín dụng. Hạn mức có thể đổi theo thời điểm, xem lại trên trang đăng ký.
- Tạo một máy ảo Linux khoảng 2 vCPU và 4 GB RAM. SQL Server cần tối thiểu 2 GB RAM nên đừng chọn máy 1 GB.
- Cài Docker, kéo repo về, tạo `.env`, chạy `docker compose up -d`, rồi chạy backend và `apps/worker` bằng systemd để tự bật lại sau khi máy khởi động.
- Mở cổng 8000 trong Network Security Group. Không mở cổng 1433 ra Internet.
- Lấy địa chỉ IP công khai của máy ảo, điền vào app Flutter thay cho `10.0.2.2:8000`.

Lưu ý: SQL Server trong Docker chỉ chạy trên CPU x86-64, không chạy trên máy ảo ARM.

### Phương án B — Database quản trị sẵn, backend ở dịch vụ miễn phí

Rẻ hơn nhưng phải sửa script SQL.

- Database: [Azure SQL Database free offer](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer-faq) cho mỗi subscription một hạn mức vCore mỗi tháng, dùng được lâu dài, giới hạn 4 vCore và 32 GB, không có SLA. Hết hạn mức tháng thì mặc định database tạm dừng tới đầu tháng sau, nên nhớ đổi thiết lập nếu không muốn bị dừng giữa buổi demo. Gói Azure for Students Starter không dùng được offer này.
- Backend: Render, Railway hoặc Fly.io đều có gói rẻ hoặc miễn phí. Gói miễn phí thường ngủ khi không có ai gọi và mất mấy chục giây để tỉnh lại, chấp nhận được với web nhưng không ổn cho tiến trình nền. Kiểm tra lại hạn mức hiện hành trước khi chọn.
- Tiến trình nền: nếu không muốn trả tiền cho một tiến trình chạy liên tục, chuyển sang gọi định kỳ. Thêm một endpoint nội bộ có khóa bí mật để chạy một lượt quét, rồi dùng GitHub Actions với `schedule` gọi vào đó mỗi 5 phút. Cách này miễn phí và không phụ thuộc laptop.

Những chỗ phải sửa khi chuyển sang Azure SQL:

1. Azure SQL không cho lệnh `USE`. Mọi tệp trong `database/` đều mở đầu bằng `USE [$(DB_NAME)]`, phải bỏ dòng đó và kết nối trực tiếp vào database khi nạp script.
2. Chuỗi kết nối đổi sang tên server `*.database.windows.net`, bật mã hóa, và tài khoản không còn là `sa`.
3. Mở firewall của Azure SQL cho địa chỉ IP của backend.
4. Sao lưu và phục hồi trong phần quản trị của TV1 dùng lệnh `BACKUP DATABASE`, lệnh này không chạy trên Azure SQL. Cần báo TV1 để đổi sang export bacpac hoặc để nguyên tính năng đó cho bản chạy nội bộ.

### GitHub làm được tới đâu

GitHub không cho chạy một tiến trình thường trú, và cũng không chứa được SQL Server, nên không thể thay thế toàn bộ máy chủ. Nhưng GitHub Actions chạy được theo lịch, nên nó thay được đúng phần tiến trình nền.

| Thành phần | GitHub làm được không |
| --- | --- |
| Quét nhắc nhở, gửi thông báo đẩy | Được. `.github/workflows/nhac-lich.yml` chạy mỗi 15 phút trên máy của GitHub |
| Cơ sở dữ liệu | Không. Phải đặt ở nơi truy cập được từ Internet |
| API cho app gọi vào | Không. Phải có một dịch vụ nhận HTTP, như Render hoặc máy ảo |

Nên nếu chỉ cần **thông báo vẫn tới điện thoại khi laptop tắt**, cần database ở cloud cộng với GitHub Actions, và không tốn tiền máy chủ. Còn muốn **mở app xem được bảng tin và lịch** thì vẫn phải có API chạy ở đâu đó, vì app phải gọi HTTP vào một địa chỉ.

Cách bật:

1. Đưa database lên cloud theo phương án A hoặc B ở trên. Máy chạy của GitHub không vào được SQL Server trong Docker trên máy cá nhân.
2. Vào Settings > Secrets and variables > Actions của repo, thêm: `MSSQL_HOST`, `MSSQL_PORT`, `MSSQL_DB`, `MSSQL_USER`, `MSSQL_SA_PASSWORD`, `JWT_SECRET_KEY`, và `FCM_SERVICE_ACCOUNT_JSON` dán toàn bộ nội dung tệp JSON service account.
3. Vào tab Actions, chọn workflow rồi bấm Run workflow để thử ngay, không phải đợi tới lịch.

Mấy điểm cần biết trước khi tin vào cách này:

- Lịch nhanh nhất là 5 phút, và GitHub có thể chạy trễ vài phút vào giờ cao điểm. Nhắc nhở vì vậy không đúng phút tuyệt đối. Với nhắc sự kiện gia đình thì không sao, nhưng đừng demo kiểu đặt nhắc trước 30 giây.
- Actions miễn phí không giới hạn với **repo công khai** dùng máy chạy tiêu chuẩn. Repo riêng tư chỉ có hạn mức phút mỗi tháng, mà chạy 15 phút một lần là khoảng 2.880 lượt mỗi tháng nên sẽ vượt. Repo của nhóm đang riêng tư thì hoặc chuyển sang công khai, hoặc giãn lịch ra, hoặc chọn cách khác.
- GitHub tự tắt workflow theo lịch sau khoảng 60 ngày repo không có hoạt động nào. Trong lúc làm đồ án thì gần như ngày nào cũng commit nên không gặp, nhưng sau khi bảo vệ xong và để yên thì nó sẽ tự dừng.
- Mỗi lượt chạy phải cài lại thư viện, mất khoảng một phút. Không phù hợp nếu sau này cần quét mỗi vài giây.
- Secret trong repo công khai vẫn được mã hóa và không hiện trong log, nhưng tuyệt đối không commit tệp JSON service account vào repo.

### Nếu chưa muốn thuê gì

Dùng Cloudflare Tunnel hoặc ngrok để mở backend trên laptop ra Internet, app trên điện thoại gọi qua 4G cũng được. Cách này đủ để thử thông báo đẩy và để demo, nhưng laptop vẫn phải bật. Đây không phải lời giải cho yêu cầu tắt laptop.

## 6. Thử thông báo đẩy

Thử ngay trên laptop trước khi tốn tiền thuê máy:

1. Chạy SQL Server, backend, và `python scheduler.py` trong `apps/worker`. Trong log phải thấy dòng `Đã cấu hình FCM cho project ...`.
2. Mở app trên điện thoại, đăng nhập. Kiểm tra token đã lưu:

```sql
SELECT UserId, Platform, LastSeenAt FROM community.DeviceTokens;
```

3. Tạo một sự kiện, đặt nhắc nhở trước thời điểm hiện tại một phút.
4. Đóng hẳn app, đợi tối đa một phút. Điện thoại phải hiện thông báo.
5. Kiểm tra lại trong database, cột `PushedAt` của thông báo phải có giá trị:

```sql
SELECT TOP 5 Title, CreatedAt, PushedAt FROM community.Notifications ORDER BY CreatedAt DESC;
```

Không nhận được thông báo thì xem theo thứ tự: log của worker có báo lỗi FCM không, bảng `DeviceTokens` có token không, điện thoại có bật quyền thông báo cho app không.

## 7. Cài app vào điện thoại để dùng thật

```bash
cd apps/mobile
flutter build apk --release
```

Tệp nằm ở `build/app/outputs/flutter-apk/app-release.apk`. Chép vào điện thoại và cài, nhớ bật cho phép cài từ nguồn ngoài. Sau khi backend đã lên cloud, app cài kiểu này dùng được bình thường dù laptop tắt.

## 8. Về iPhone

Thông báo đẩy trên iOS đi qua APNs của Apple, muốn dùng phải có tài khoản Apple Developer trả phí theo năm và một máy Mac để build. Nếu không có cả hai thì iPhone không nhận được thông báo đẩy, và cũng không cài được app theo kiểu chép tệp như Android. Với bài tập lớn, nên demo trên máy Android và nói rõ trong báo cáo rằng iOS cần tài khoản trả phí nên để lại cho hướng phát triển.

Nếu chỉ cần xem được trên iPhone chứ không cần thông báo, mở bản web trên Safari là xong, miễn backend đã lên cloud.

## 9. Việc cần chốt với nhóm

- Hân: thêm `firebase_core`, `firebase_messaging` và gọi đăng ký token sau khi đăng nhập.
- Nhóm trưởng: quyết định phương án A hay B, vì nó quyết định có phải sửa script SQL hay không.
- TV1: nếu chọn phương án B, tính năng sao lưu phục hồi cần đổi cách làm.

## Nguồn

- [Azure SQL Database free offer FAQ](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer-faq)
- [Deploy Azure SQL Database for free](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer)
- [Azure for Students](https://azure.microsoft.com/free/students/)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
