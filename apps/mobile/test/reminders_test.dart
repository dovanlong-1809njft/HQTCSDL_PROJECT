import 'dart:async';
import 'dart:convert';

import 'package:familyconnect/api.dart';
import 'package:familyconnect/reminders.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('dexterous.com/flutter/local_notifications');
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  final scheduled = <Map<String, dynamic>>[];
  late Reminders reminders;
  late List<Json> rows;

  setUp(() async {
    debugDefaultTargetPlatformOverride = TargetPlatform.android;
    AndroidFlutterLocalNotificationsPlugin.registerWith();
    scheduled.clear();
    rows = [
      {
        'id': 'cancelled',
        'reminder_time': DateTime.now()
            .toUtc()
            .add(const Duration(days: 2))
            .toIso8601String(),
      },
    ];
    messenger.setMockMethodCallHandler(channel, (call) async {
      switch (call.method) {
        case 'pendingNotificationRequests':
          return scheduled.map((row) => Map<String, dynamic>.of(row)).toList();
        case 'zonedSchedule':
          final args = Map<String, dynamic>.from(call.arguments);
          scheduled.removeWhere((row) => row['id'] == args['id']);
          scheduled.add(args);
        case 'cancel':
          scheduled.removeWhere((row) => row['id'] == call.arguments['id']);
        case 'cancelAll':
          scheduled.clear();
        case 'initialize':
        case 'areNotificationsEnabled':
          return true;
        case 'canScheduleExactNotifications':
          return false;
      }
      return null;
    });
    reminders = Reminders();
    await reminders.initialize();
  });

  tearDown(() {
    messenger.setMockMethodCallHandler(channel, null);
    debugDefaultTargetPlatformOverride = null;
  });

  test('a late response cannot restore a cancelled reminder', () async {
    scheduled.add({'id': 7, 'payload': 'cancelled'});
    final oldResponse = Completer<http.Response>();
    final newResponse = Completer<http.Response>();
    var requests = 0;
    final api = Api(
      client: MockClient(
        (_) => requests++ == 0 ? oldResponse.future : newResponse.future,
      ),
    )..token = 'current';
    final first = reminders.sync(api);
    final second = reminders.sync(api);
    await Future<void>.delayed(Duration.zero);
    newResponse.complete(http.Response('[]', 200));
    await second;
    expect(scheduled, isEmpty);
    oldResponse.complete(http.Response(jsonEncode(rows), 200));
    await first;
    expect(scheduled, isEmpty);
  });

  test('logout clears alarms and ignores an in-flight sync', () async {
    final response = Completer<http.Response>();
    final api = Api(client: MockClient((_) => response.future))..token = 'old';
    final syncing = reminders.sync(api);
    scheduled.add({'id': 7, 'payload': 'cancelled'});
    await reminders.clear();
    response.complete(http.Response(jsonEncode(rows), 200));
    await syncing;
    expect(scheduled, isEmpty);

    final newSession = Api(
      client: MockClient((_) async => http.Response(jsonEncode(rows), 200)),
    )..token = 'new';
    await reminders.sync(newSession);
    expect(scheduled.map((row) => row['payload']), ['cancelled']);
  });
}
