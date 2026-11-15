import 'package:material_ui/material_ui.dart';

import 'api.dart';
import 'ui.dart';

const itemTypes = {
  'story': 'Câu chuyện',
  'document': 'Tài liệu',
  'photo': 'Ảnh',
};

class HeritageScreen extends StatefulWidget {
  const HeritageScreen({
    super.key,
    required this.api,
    required this.family,
    required this.user,
  });
  final Api api;
  final String family;
  final Json user;
  @override
  State<HeritageScreen> createState() => _HeritageScreenState();
}

class _HeritageScreenState extends State<HeritageScreen> {
  String resource = 'items', q = '', type = '';
  int page = 1;
  bool get manager => ['admin', 'family_head'].contains(widget.user['role']);
  Future<void> edit(
    BuildContext context,
    VoidCallback reload, [
    Json? row,
  ]) async {
    final members = resource == 'honors' && row == null
        ? await allPages(widget.api, '/heritage/members', {
            'family_id': widget.family,
          })
        : <Json>[];
    if (resource == 'honors' && row == null && members.isEmpty) {
      throw ApiError('Gia đình chưa có thành viên để vinh danh.');
    }
    if (!context.mounted) return;
    await formDialog(
      context,
      title: row == null ? 'Thêm mới' : 'Chỉnh sửa',
      fields: {
        'title': 'Tiêu đề',
        'description': 'Mô tả',
        if (resource == 'items') ...{
          'type': 'Loại tư liệu',
          'content': 'Nội dung',
          'media_url': 'URL HTTPS hoặc /media/',
        } else ...{
          if (row == null) 'member_id': 'Thành viên',
          'date_awarded': 'Ngày trao (YYYY-MM-DD)',
        },
      },
      initial: {'type': 'story', ...?row},
      requiredFields: {
        'title',
        if (resource == 'items') 'type' else if (row == null) 'member_id',
      },
      choices: {
        'type': itemTypes,
        if (members.isNotEmpty)
          'member_id': {for (final m in members) m['id']: m['full_name']},
      },
      save: (values) async {
        for (final key in [
          'description',
          'content',
          'media_url',
          'date_awarded',
        ]) {
          if (values[key] == '') values[key] = null;
        }
        if (row != null) values['expected_version'] = row['version_token'];
        await widget.api.call(
          '/heritage/$resource${row == null ? '' : '/${row['id']}'}',
          query: {'family_id': widget.family},
          method: row == null ? 'POST' : 'PATCH',
          body: values,
        );
        reload();
      },
    );
  }

  @override
  Widget build(BuildContext context) => DataPane(
    key: ValueKey('$resource-$page-$q-$type'),
    load: () => widget.api.call(
      '/heritage/$resource',
      query: {
        'family_id': widget.family,
        'page': page,
        'page_size': 12,
        'q': q,
        if (resource == 'items' && type.isNotEmpty) 'item_type': type,
      },
    ),
    builder: (data, reload) => pageList([
      SegmentedButton<String>(
        segments: const [
          ButtonSegment(value: 'items', label: Text('Di sản')),
          ButtonSegment(value: 'honors', label: Text('Vinh danh')),
          ButtonSegment(value: 'ranking', label: Text('Xếp hạng')),
        ],
        selected: {resource},
        onSelectionChanged: (value) => setState(() {
          resource = value.first;
          page = 1;
        }),
      ),
      Wrap(
        children: [
          ActionButton(
            'Tìm và lọc',
            () => formDialog(
              context,
              title: 'Tìm tư liệu',
              fields: {
                'q': 'Từ khóa',
                if (resource == 'items') 'type': 'Loại tư liệu',
              },
              initial: {'q': q, 'type': type},
              choices: const {
                'type': {'': 'Tất cả', ...itemTypes},
              },
              save: (values) async {
                if ((values['q'] as String).length > 200) {
                  throw ApiError('Từ khóa tìm kiếm tối đa 200 ký tự.');
                }
                if (mounted) {
                  setState(() {
                    q = values['q'];
                    type = values['type'] ?? '';
                    page = 1;
                  });
                }
              },
            ),
            icon: Icons.search,
          ),
          if (resource == 'items' || resource == 'honors' && manager)
            ActionButton(
              'Thêm mới',
              () => edit(context, reload),
              icon: Icons.add,
            ),
        ],
      ),
      if ((data['items'] as List).isEmpty)
        const Text('Chưa có dữ liệu khớp bộ lọc.'),
      for (final raw in data['items'])
        Builder(
          builder: (context) {
            final row = raw as Json;
            if (resource == 'ranking') {
              return ListTile(
                leading: CircleAvatar(child: Text('${row['rank']}')),
                title: Text(row['full_name']),
                subtitle: Text('${row['honor_count']} danh hiệu'),
              );
            }
            final canEdit = resource == 'honors'
                ? manager
                : manager || row['created_by_user_id'] == widget.user['id'];
            return card([
              heading(row['title']),
              if (resource == 'honors') Text(row['full_name']),
              if (row['description'] != null) Text(row['description']),
              if (resource == 'items') ...[
                Text(itemTypes[row['type']] ?? row['type']),
                if (row['type'] == 'photo')
                  remoteImage(
                    Uri.parse(widget.api.baseUrl)
                        .resolve(row['media_url'])
                        .toString(),
                  ),
                ActionButton(
                  'Xem nội dung',
                  () => openPage(
                    context,
                    row['title'],
                    pageList([
                      heading(row['title']),
                      if (row['content'] != null)
                        SelectableText(row['content']),
                      if (row['media_url'] != null) ...[
                        remoteImage(
                          Uri.parse(widget.api.baseUrl)
                              .resolve(row['media_url'])
                              .toString(),
                        ),
                        SelectableText(row['media_url']),
                        ActionButton(
                          'Mở tư liệu',
                          () => openMedia(widget.api, row['media_url']),
                          icon: Icons.open_in_browser,
                        ),
                      ],
                    ]),
                  ),
                  icon: Icons.open_in_new,
                ),
              ] else if (row['date_awarded'] != null)
                Text('Ngày trao: ${row['date_awarded']}'),
              if (canEdit)
                Wrap(
                  children: [
                    ActionButton(
                      'Sửa',
                      () => edit(context, reload, row),
                      icon: Icons.edit_outlined,
                    ),
                    ActionButton('Xóa', () async {
                      if (await confirm(context, 'Xóa ${row['title']}?')) {
                        await widget.api.call(
                          '/heritage/$resource/${row['id']}',
                          method: 'DELETE',
                          query: {
                            'family_id': widget.family,
                            'expected_version': row['version_token'],
                          },
                        );
                        reload();
                      }
                    }, icon: Icons.delete_outline),
                  ],
                ),
            ]);
          },
        ),
      pager(
        page,
        page * 12 < data['total'],
        (value) => setState(() => page = value),
      ),
    ]),
  );
}
