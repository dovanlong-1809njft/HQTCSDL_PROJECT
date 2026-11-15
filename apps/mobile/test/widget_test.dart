import 'package:material_ui/material_ui.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:familyconnect/main.dart';
import 'package:familyconnect/ui.dart';
import 'package:familyconnect/api.dart';
import 'package:familyconnect/reminders.dart';
import 'package:familyconnect/directory.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'dart:convert';

void main() {
  testWidgets('invalid directory generation stays editable', (tester) async {
    final api = Api(
      client: MockClient(
        (_) async => http.Response('{"items":[],"total":0}', 200),
      ),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: DirectoryScreen(api: api, family: 'f'),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tìm kiếm và lọc'));
    // The launcher stays busy until its dialog closes.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Thế hệ'),
      '1001',
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Lưu'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('1001'), findsOneWidget);
    expect(find.textContaining('1 đến 1000'), findsOneWidget);
    await tester.tap(find.text('Hủy'));
    await tester.pumpAndSettle();
  });
  testWidgets('all six mobile destinations load at phone width', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final api = Api(
      client: MockClient((request) async {
        final value = switch (request.url.path) {
          '/api/genealogy/me' => {
            'user': {
              'id': 'u',
              'role': 'member',
              'full_name': 'Nguyễn Chiến',
              'email': 'member@example.com',
            },
            'member': {
              'id': 'm',
              'family_id': 'f',
              'family_name': 'Gia đình Nguyễn',
            },
            'verifications': [],
          },
          '/api/heritage/families' => [
            {'id': 'f', 'name': 'Gia đình Nguyễn'},
          ],
          '/api/events' => [],
          _ => {'items': [], 'total': 0, 'unread': 0},
        };
        return http.Response(
          jsonEncode(value),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Home(
          api: api,
          user: {'id': 'u', 'role': 'member'},
          reminders: Reminders(),
          logout: () async {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    for (var i = 0; i < 6; i++) {
      await tester.tap(find.byType(NavigationDestination).at(i));
      await tester.pumpAndSettle();
      final error = tester.takeException();

      expect(error, isNull, reason: 'Destination $i must fit and load');
    }
    expect(find.text('Nguyễn Chiến'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('a rejected save keeps form values for correction', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) {
              return TextButton(
                onPressed: () => formDialog(
                  context,
                  title: 'Sửa thông tin',
                  fields: const {'title': 'Tiêu đề'},
                  save: (_) async {
                    throw ApiError('Không được ghi đè.');
                  },
                ),
                child: const Text('Mở form'),
              );
            },
          ),
        ),
      ),
    );
    await tester.tap(find.text('Mở form'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField), 'Nội dung cần giữ');
    await tester.tap(find.widgetWithText(FilledButton, 'Lưu'));
    await tester.pumpAndSettle();
    expect(find.text('Nội dung cần giữ'), findsOneWidget);
    expect(find.text('Không được ghi đè.'), findsOneWidget);
    await tester.tap(find.text('Hủy'));
    await tester.pumpAndSettle();
  });
  testWidgets('login preserves password whitespace and shows server failures', (
    tester,
  ) async {
    String? password;
    await tester.pumpWidget(
      MaterialApp(
        home: LoginScreen(
          login: (email, secret, name) async {
            password = secret;
            throw Exception('Sai mật khẩu');
          },
        ),
      ),
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'member@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Mật khẩu'),
      ' password ',
    );
    await tester.tap(find.widgetWithText(ActionButton, 'Đăng nhập'));
    await tester.pumpAndSettle();
    expect(password, ' password ');
    expect(find.textContaining('Sai mật khẩu'), findsOneWidget);
    expect(find.text('FamilyConnect'), findsOneWidget);
  });
  testWidgets('registration rejects a short password without calling the API', (
    tester,
  ) async {
    var calls = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: LoginScreen(
          login: (_, _, _) async {
            calls++;
          },
        ),
      ),
    );
    await tester.tap(find.text('Chưa có tài khoản? Đăng ký'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Họ và tên'),
      'Nguyễn Chiến',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'member@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Mật khẩu'),
      'short',
    );
    await tester.ensureVisible(find.widgetWithText(ActionButton, 'Đăng ký'));
    await tester.tap(find.widgetWithText(ActionButton, 'Đăng ký'));
    await tester.pumpAndSettle();
    expect(calls, 0);
    expect(find.textContaining('ít nhất 8 ký tự'), findsOneWidget);
  });
  testWidgets('failed loading offers a retry and never displays stale data', (
    tester,
  ) async {
    var tries = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: DataPane(
            load: () async {
              if (tries++ == 0) throw Exception('Mất mạng');
              return 'Đã kết nối';
            },
            builder: (data, reload) => ListView(children: [Text(data)]),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('Mất mạng'), findsOneWidget);
    await tester.tap(find.text('Thử lại'));
    await tester.pumpAndSettle();
    expect(find.text('Đã kết nối'), findsOneWidget);
  });
}
