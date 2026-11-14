import 'dart:async';
import 'dart:convert';

import 'package:flutter/services.dart';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:familyconnect/api.dart';
import 'package:familyconnect/reminders.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('media opens safe links and resolves existing server files', () async {
    const channel = MethodChannel('familyconnect/links');
    String? opened;
    final messenger =
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
    messenger.setMockMethodCallHandler(channel, (call) async {
      opened = call.arguments['url'];
      return null;
    });
    addTearDown(() => messenger.setMockMethodCallHandler(channel, null));
    final api = Api(baseUrl: 'https://family.example/api');
    await openMedia(api, '/media/story.pdf');
    expect(opened, 'https://family.example/media/story.pdf');
    await expectLater(
      openMedia(api, 'javascript:alert(1)'),
      throwsA(isA<ApiError>()),
    );
    await expectLater(
      openMedia(api, 'https://user:password@example.com/file'),
      throwsA(isA<ApiError>()),
    );
  });
  test(
    'requests use the current bearer, encoded filters and a JSON body',
    () async {
      final api = Api(
        baseUrl: 'http://localhost/api',
        client: MockClient((request) async {
          expect(request.headers['Authorization'], 'Bearer current');
          expect(request.url.queryParameters['q'], 'Nguyễn & Chiến');
          expect(jsonDecode(request.body), {'content': 'Gia đình'});
          expect(request.method, 'PUT');
          return http.Response('', 204);
        }),
      )..token = 'current';
      expect(
        await api.call(
          '/community/comments/one',
          method: 'PUT',
          query: {'q': 'Nguyễn & Chiến', 'skip': null},
          body: {'content': 'Gia đình'},
        ),
        isNull,
      );
    },
  );
  test('a late 401 cannot clear a newer session', () async {
    final response = Completer<http.Response>();
    final api = Api(client: MockClient((_) => response.future))..token = 'old';
    var cleared = false;
    api.onUnauthorized = () => cleared = true;
    final request = api.call('/auth/me');
    api.token = 'new';
    response.complete(http.Response('{"detail":"Expired"}', 401));
    await expectLater(request, throwsA(isA<ApiError>()));
    expect(api.token, 'new');
    expect(cleared, false);
  });
  test(
    'current 401 clears session and returns the server validation error',
    () async {
      final api = Api(
        client: MockClient(
          (_) async =>
              http.Response('{"detail":[{"msg":"Invalid value"}]}', 401),
        ),
      )..token = 'expired';
      var cleared = false;
      api.onUnauthorized = () => cleared = true;
      await expectLater(
        api.call('/auth/me'),
        throwsA(predicate((e) => '$e' == 'Invalid value')),
      );
      expect(api.token, isNull);
      expect(cleared, true);
    },
  );
  test(
    'selectors load every page including members beyond the first 100',
    () async {
      final api = Api(
        client: MockClient((request) async {
          final page = int.parse(request.url.queryParameters['page']!);
          return http.Response(
            jsonEncode({
              'items': [
                {'id': 'member-$page'},
              ],
              'total': 2,
            }),
            200,
          );
        }),
      );
      expect(
        (await allPages(api, '/heritage/members', {
          'family_id': 'family',
        })).map((r) => r['id']),
        ['member-1', 'member-2'],
      );
    },
  );
  test(
    'SQL dates without a suffix are UTC and expired reminders are excluded',
    () {
      expect(utcDate('2027-01-01T00:00:00').toUtc(), DateTime.utc(2027));
      final plan = futureReminders([
        {'id': 'past', 'reminder_time': '2026-12-31T23:59:59'},
        {'id': 'later', 'reminder_time': '2027-01-01T01:00:00Z'},
        {'id': 'at-now', 'reminder_time': '2027-01-01T00:00:00Z'},
      ], DateTime.utc(2027));
      expect(plan.map((r) => r['id']), ['later']);
    },
  );
}
