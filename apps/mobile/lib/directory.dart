import 'package:material_ui/material_ui.dart';

import 'api.dart';
import 'ui.dart';

class DirectoryScreen extends StatefulWidget {
  const DirectoryScreen({super.key, required this.api, required this.family});
  final Api api;
  final String family;
  @override
  State<DirectoryScreen> createState() => _DirectoryScreenState();
}

class _DirectoryScreenState extends State<DirectoryScreen> {
  Json filters = {};
  int page = 1;
  @override
  Widget build(BuildContext context) => DataPane(
    key: ValueKey('$page-$filters'),
    load: () => widget.api.call(
      '/directory',
      query: {
        ...filters,
        'family_id': widget.family,
        'page': page,
        'page_size': 12,
      },
    ),
    builder: (data, reload) => pageList([
      ActionButton('Tìm kiếm và lọc', () async {
        final branches = await allPages(widget.api, '/genealogy/branches', {
          'family_id': widget.family,
        });
        if (!context.mounted) return;
        await formDialog(
          context,
          title: 'Tìm người thân',
          fields: const {
            'q': 'Họ tên',
            'occupation': 'Nghề nghiệp',
            'education': 'Học vấn',
            'location': 'Nơi ở',
            'generation': 'Thế hệ',
            'branch_id': 'Chi gia đình',
            'current_job': 'Công việc hiện tại',
          },
          initial: {
            ...filters,
            'current_job': '${filters['current_job'] ?? false}',
            'branch_id': filters['branch_id'] ?? '',
          },
          choices: {
            'branch_id': {
              '': 'Tất cả chi',
              for (final b in branches) b['id']: b['name'],
            },
            'current_job': {
              'false': 'Tất cả công việc',
              'true': 'Chỉ công việc hiện tại',
            },
          },
          save: (values) async {
            final generation = values['generation'] as String;
            if (generation.isNotEmpty &&
                (int.tryParse(generation) == null ||
                    int.parse(generation) < 1 ||
                    int.parse(generation) > 1000)) {
              throw ApiError('Thế hệ phải nằm trong khoảng 1 đến 1000.');
            }
            for (final field in {
              'q': 200,
              'occupation': 200,
              'education': 200,
              'location': 300,
            }.entries) {
              if ((values[field.key] as String).length > field.value) {
                throw ApiError('Thông tin tìm kiếm quá dài. Vui lòng rút gọn.');
              }
            }
            if (mounted) {
              setState(() {
                filters = {
                  ...values,
                  'current_job': values['current_job'] == 'true',
                };
                page = 1;
              });
            }
          },
        );
      }, icon: Icons.manage_search),
      Text('${data['total']} thành viên'),
      if ((data['items'] as List).isEmpty)
        const Text('Không có thành viên khớp bộ lọc.'),
      for (final row in data['items'])
        Card(
          child: ListTile(
            title: Text(row['name']),
            subtitle: Text(
              [
                row['location'],
                row['position'],
                row['institution'],
              ].whereType<String>().join(' · '),
            ),
            leading: const CircleAvatar(child: Icon(Icons.person_outline)),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => openPage(
              context,
              row['name'],
              MemberScreen(
                api: widget.api,
                family: widget.family,
                id: row['id'],
              ),
            ),
          ),
        ),
      pager(
        page,
        page * 12 < data['total'],
        (value) => setState(() => page = value),
      ),
    ]),
  );
}

class MemberScreen extends StatelessWidget {
  const MemberScreen({
    super.key,
    required this.api,
    required this.family,
    required this.id,
  });
  final Api api;
  final String family, id;
  Future<void> edit(
    BuildContext context,
    String resource,
    VoidCallback reload, [
    Json? row,
  ]) => formDialog(
    context,
    title: resource == 'educations' ? 'Học vấn' : 'Công việc',
    fields: {
      if (resource == 'educations') ...{
        'institution': 'Trường / cơ sở đào tạo',
        'degree': 'Bằng cấp',
      } else ...{
        'company': 'Công ty',
        'position': 'Vị trí',
      },
      'start_date': 'Ngày bắt đầu (YYYY-MM-DD)',
      'end_date': 'Ngày kết thúc (YYYY-MM-DD, để trống nếu còn tiếp tục)',
    },
    initial: row ?? {},
    requiredFields: resource == 'educations'
        ? {'institution', 'degree'}
        : {'company', 'position'},
    save: (values) async {
      for (final key in ['start_date', 'end_date']) {
        if ((values[key] as String).isEmpty) values[key] = null;
      }
      await api.call(
        '/directory/$id/$resource${row == null ? '' : '/${row['id']}'}',
        method: row == null ? 'POST' : 'PUT',
        body: values,
      );
      reload();
    },
  );
  @override
  Widget build(BuildContext context) => DataPane(
    load: () => api.call('/directory/$id', query: {'family_id': family}),
    builder: (data, reload) => pageList([
      heading(data['name']),
      Text(data['branch_name'] ?? 'Chưa phân chi'),
      Text(data['birth_date'] ?? 'Chưa cập nhật ngày sinh'),
      Text(data['location'] ?? 'Chưa cập nhật nơi ở'),
      for (final resource in ['educations', 'work']) ...[
        heading(resource == 'educations' ? 'Học vấn' : 'Công việc'),
        if (data['can_edit'] == true)
          ActionButton(
            'Thêm',
            () => edit(context, resource, reload),
            icon: Icons.add,
          ),
        if ((data[resource] as List).isEmpty) const Text('Chưa có thông tin.'),
        for (final raw in data[resource])
          Builder(
            builder: (context) {
              final row = raw as Json;
              return card([
                Text(
                  resource == 'educations'
                      ? '${row['institution']} · ${row['degree']}'
                      : '${row['company']} · ${row['position']}',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                Text(
                  '${row['start_date'] ?? 'Chưa rõ'} → ${row['end_date'] ?? 'Hiện tại'}',
                ),
                if (data['can_edit'] == true)
                  Wrap(
                    children: [
                      ActionButton(
                        'Sửa',
                        () => edit(context, resource, reload, row),
                        icon: Icons.edit_outlined,
                      ),
                      ActionButton('Xóa', () async {
                        if (await confirm(context, 'Xóa thông tin này?')) {
                          await api.call(
                            '/directory/$id/$resource/${row['id']}',
                            method: 'DELETE',
                          );
                          reload();
                        }
                      }, icon: Icons.delete_outline),
                    ],
                  ),
              ]);
            },
          ),
      ],
    ]),
  );
}
