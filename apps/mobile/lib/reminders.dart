import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest.dart' as tz_data;
import 'package:timezone/timezone.dart' as tz;

import 'api.dart';

List<Json> futureReminders(List<dynamic> rows, DateTime now) =>
    rows
        .cast<Json>()
        .where((row) => utcDate(row['reminder_time']).isAfter(now))
        .toList()
      ..sort((a, b) => '${a['id']}'.compareTo('${b['id']}'));

class Reminders {
  final plugin = FlutterLocalNotificationsPlugin();
  bool enabled = false;
  bool exact = false;
  int generation = 0;
  Future<void> pending = Future.value();

  Future<void> initialize() async {
    tz_data.initializeTimeZones();
    await plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('ic_notification'),
      ),
    );
    final android = plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    enabled = await android?.areNotificationsEnabled() ?? false;
    exact = await android?.canScheduleExactNotifications() ?? false;
  }

  Future<bool> enable() async {
    final android = plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    enabled = await android?.requestNotificationsPermission() ?? false;
    if (enabled) exact = await android?.requestExactAlarmsPermission() ?? false;
    return enabled;
  }

  Future<void> clear() {
    generation++;
    return pending = pending
        .catchError((Object _) {})
        .then((_) => plugin.cancelAll());
  }

  Future<void> sync(Api api) async {
    final version = ++generation, session = api.token;
    if (session == null || !enabled) return;
    final rows = await api.call('/notifications/reminders') as List;
    if (version != generation || api.token != session) return;
    // shortcut: changes made while the app is closed sync on resume; use FCM for live remote cancellation.
    pending = pending.catchError((Object _) {}).then((_) async {
      if (version != generation || api.token != session) return;
      final plan = futureReminders(rows, DateTime.now());
      final wanted = plan.map((row) => row['id']).toSet();
      final existing = await plugin.pendingNotificationRequests();
      final ids = {for (final row in existing) row.payload: row.id};
      for (final row in existing) {
        if (!wanted.contains(row.payload)) await plugin.cancel(id: row.id);
      }
      var nextId = 1;
      for (final row in plan) {
        if (version != generation || api.token != session) return;
        while (ids.values.contains(nextId)) {
          nextId++;
        }
        final id = ids[row['id']] ?? nextId++;
        ids[row['id']] = id;
        final when = utcDate(row['reminder_time']);
        if (!when.isAfter(DateTime.now())) continue;
        await plugin.zonedSchedule(
          id: id,
          title: 'FamilyConnect',
          body: 'Bạn có nhắc lịch sự kiện. Mở app để xem chi tiết.',
          scheduledDate: tz.TZDateTime.from(when, tz.UTC),
          notificationDetails: const NotificationDetails(
            android: AndroidNotificationDetails(
              'family_events',
              'Nhắc lịch gia đình',
              importance: Importance.high,
              priority: Priority.high,
              visibility: NotificationVisibility.private,
            ),
          ),
          androidScheduleMode: exact
              ? AndroidScheduleMode.exactAllowWhileIdle
              : AndroidScheduleMode.inexactAllowWhileIdle,
          payload: row['id'],
        );
      }
    });
    await pending;
  }
}
