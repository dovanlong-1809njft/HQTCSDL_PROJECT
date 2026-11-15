import 'package:material_ui/material_ui.dart';

import 'api.dart';
import 'reminders.dart';
import 'ui.dart';

const rsvp = {
  'Pending': 'Chờ phản hồi',
  'Going': 'Tham dự',
  'Maybe': 'Có thể',
  'Declined': 'Không tham dự',
};

Future<void> editEvent(
  BuildContext context,
  Api api,
  String family,
  VoidCallback reload, [
  Json? row,
]) => formDialog(
  context,
  title: row == null ? 'Tạo sự kiện' : 'Sửa sự kiện',
  fields: const {
    'title': 'Tên sự kiện',
    'event_date': 'Thời gian (YYYY-MM-DD HH:mm, giờ máy)',
    'location': 'Địa điểm',
  },
  requiredFields: {'title', 'event_date'},
  initial: {
    ...?row,
    if (row != null)
      'event_date': utcDate(row['event_date'])
          .toIso8601String()
          .substring(0, 16),
  },
  save: (values) async {
    final date = DateTime.tryParse(values['event_date']);
    if (date == null) throw ApiError('Nhập thời gian theo YYYY-MM-DD HH:mm.');
    await api.call(
      '/events${row == null ? '' : '/${row['event_id']}'}',
      method: row == null ? 'POST' : 'PUT',
      body: {
        if (row == null) 'family_id': family,
        'title': values['title'],
        'event_date': date.toUtc().toIso8601String(),
        'location': values['location'],
      },
    );
    reload();
  },
);

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({
    super.key,
    required this.api,
    required this.family,
    required this.memberId,
    required this.reminders,
    required this.user,
  });
  final Api api;
  final String family;
  final String? memberId;
  final Reminders reminders;
  final Json user;
  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  DateTime month = DateTime(DateTime.now().year, DateTime.now().month);
  @override
  Widget build(BuildContext context) => DataPane(
    key: ValueKey(month),
    load: () => widget.api.call(
      '/events',
      query: {
        'family_id': widget.family,
        'year': month.year,
        'month': month.month,
        'tz_offset': month.timeZoneOffset.inMinutes,
      },
    ),
    builder: (data, reload) => pageList([
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            tooltip: 'Tháng trước',
            onPressed: month.year > 1900
                ? () => setState(
                    () => month = DateTime(month.year, month.month - 1),
                  )
                : null,
            icon: const Icon(Icons.chevron_left),
          ),
          heading('${month.month}/${month.year}'),
          IconButton(
            tooltip: 'Tháng tiếp',
            onPressed: month.year < 2200
                ? () => setState(
                    () => month = DateTime(month.year, month.month + 1),
                  )
                : null,
            icon: const Icon(Icons.chevron_right),
          ),
        ],
      ),
      if (['admin', 'family_head'].contains(widget.user['role']))
        ActionButton(
          'Tạo sự kiện',
          () => editEvent(context, widget.api, widget.family, reload),
          icon: Icons.add,
        ),
      if ((data as List).isEmpty)
        const Text('Chưa có sự kiện trong tháng này.'),
      for (final row in data)
        Card(
          child: ListTile(
            title: Text(row['title']),
            subtitle: Text(
              '${displayDate(row['event_date'])}\n${row['location'] ?? ''} · ${row['going_count']} tham dự',
            ),
            isThreeLine: true,
            trailing: const Icon(Icons.chevron_right),
            onTap: () async {
              await openPage(
                context,
                'Sự kiện',
                EventScreen(
                  api: widget.api,
                  id: row['event_id'],
                  memberId: widget.memberId,
                  reminders: widget.reminders,
                ),
              );
              reload();
            },
          ),
        ),
    ]),
  );
}

class EventScreen extends StatefulWidget {
  const EventScreen({
    super.key,
    required this.api,
    required this.id,
    required this.memberId,
    required this.reminders,
  });
  final Api api;
  final String id;
  final String? memberId;
  final Reminders reminders;
  @override
  State<EventScreen> createState() => _EventScreenState();
}

class _EventScreenState extends State<EventScreen> {
  int galleryPage = 1, participantPage = 1;
  Future<void> addReminder(
    BuildContext context,
    VoidCallback reload,
    bool family,
  ) async {
    final now = DateTime.now();
    final day = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: now,
      lastDate: DateTime(2200),
    );
    if (day == null || !context.mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(now.add(const Duration(minutes: 2))),
    );
    if (time == null) return;
    final date = DateTime(day.year, day.month, day.day, time.hour, time.minute);
    await widget.api.call(
      '/events/${widget.id}/reminders',
      method: 'POST',
      body: {
        'reminder_time': date.toUtc().toIso8601String(),
        'for_family': family,
      },
    );
    reload();
    try {
      await widget.reminders.sync(widget.api);
    } catch (error) {
      if (context.mounted) {
        message(
          context,
          'Đã lưu nhắc trên máy chủ. Chưa đồng bộ Android: $error',
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) => DataPane(
    key: ValueKey('$galleryPage-$participantPage'),
    load: () => Future.wait([
      widget.api.call('/events/${widget.id}'),
      widget.api.call('/auth/me'),
      widget.api.call(
        '/events/${widget.id}/gallery',
        query: {'page': galleryPage, 'page_size': 12},
      ),
      widget.api.call(
        '/events/${widget.id}/participants',
        query: {'page': participantPage, 'page_size': 20},
      ),
      widget.api.call('/events/${widget.id}/reminders'),
    ]),
    builder: (values, reload) {
      final event = values[0] as Json, user = values[1] as Json;
      final manager = ['admin', 'family_head'].contains(user['role']);
      final gallery = values[2] as List, participants = values[3] as Json;
      return pageList([
        heading(event['title']),
        Text(displayDate(event['event_date'])),
        Text(event['location'] ?? 'Chưa ghi địa điểm'),
        if (manager)
          Wrap(
            children: [
              ActionButton(
                'Sửa',
                () => editEvent(
                  context,
                  widget.api,
                  event['family_id'],
                  reload,
                  event,
                ),
                icon: Icons.edit,
              ),
              ActionButton('Xóa sự kiện', () async {
                if (await confirm(
                  context,
                  'Xóa sự kiện, RSVP, ảnh và nhắc liên quan?',
                )) {
                  await widget.api.call(
                    '/events/${widget.id}',
                    method: 'DELETE',
                  );
                  await widget.reminders.sync(widget.api);
                  if (context.mounted) Navigator.pop(context);
                }
              }, icon: Icons.delete_outline),
            ],
          ),
        heading('Phản hồi tham dự'),
        if (widget.memberId == null)
          const Text('Cần liên kết hồ sơ cá nhân trong gia đình để phản hồi.'),
        Wrap(
          children: [
            for (final option in rsvp.entries.where((e) => e.key != 'Pending'))
              ActionButton(
                '${event['my_rsvp'] == option.key ? '✓ ' : ''}${option.value}',
                widget.memberId == null
                    ? null
                    : () async {
                        await widget.api.call(
                          '/events/${widget.id}/rsvp',
                          method: 'PUT',
                          body: {
                            'member_id': widget.memberId,
                            'rsvp_status': option.key,
                          },
                        );
                        reload();
                      },
                icon: Icons.event_available_outlined,
              ),
          ],
        ),
        heading('Người tham gia'),
        Text(
          rsvp.entries
              .map((e) => '${e.value}: ${participants['counts'][e.key] ?? 0}')
              .join(' · '),
        ),
        for (final row in participants['items'])
          ListTile(
            title: Text(row['name']),
            subtitle: Text(rsvp[row['rsvp_status']] ?? row['rsvp_status']),
          ),
        pager(
          participantPage,
          participantPage * 20 < participants['total'],
          (value) => setState(() => participantPage = value),
        ),
        heading('Ảnh sự kiện'),
        for (final row in gallery)
          card([
            remoteImage(row['media_url']),
            if (manager || row['uploaded_by'] == user['id'])
              ActionButton('Xóa ảnh', () async {
                if (await confirm(context, 'Xóa ảnh này khỏi sự kiện?')) {
                  await widget.api.call(
                    '/events/${widget.id}/gallery/${row['id']}',
                    method: 'DELETE',
                  );
                  reload();
                }
              }, icon: Icons.delete_outline),
          ]),
        pager(
          galleryPage,
          gallery.length == 12,
          (value) => setState(() => galleryPage = value),
        ),
        ActionButton(
          'Thêm ảnh bằng URL',
          () => formDialog(
            context,
            title: 'Thêm ảnh',
            fields: const {'media_url': 'URL ảnh HTTP/HTTPS'},
            requiredFields: {'media_url'},
            save: (body) async {
              await widget.api.call(
                '/events/${widget.id}/gallery',
                method: 'POST',
                body: body,
              );
              reload();
            },
          ),
          icon: Icons.add_photo_alternate_outlined,
        ),
        heading('Nhắc lịch'),
        Wrap(
          children: [
            ActionButton(
              'Nhắc riêng tôi',
              () => addReminder(context, reload, false),
              icon: Icons.alarm_add,
            ),
            if (manager)
              ActionButton(
                'Nhắc cả gia đình',
                () => addReminder(context, reload, true),
                icon: Icons.group_outlined,
              ),
          ],
        ),
        for (final row in values[4])
          card([
            Text(
              '${displayDate(row['reminder_time'])} · ${row['user_id'] == null ? 'Cả gia đình' : 'Cá nhân'}',
            ),
            Text(
              const {
                    'pending': 'Chờ đến giờ',
                    'sent': 'Đã vào hộp thư',
                    'cancelled': 'Đã hủy',
                    'failed': 'Gửi lỗi',
                  }[row['status']] ??
                  row['status'],
            ),
            if (row['status'] == 'pending' &&
                (manager || row['user_id'] == user['id']))
              ActionButton('Hủy nhắc', () async {
                await widget.api.call(
                  '/events/${widget.id}/reminders/${row['id']}',
                  method: 'DELETE',
                );
                reload();
                await widget.reminders.sync(widget.api);
              }, icon: Icons.alarm_off),
          ]),
      ]);
    },
  );
}
