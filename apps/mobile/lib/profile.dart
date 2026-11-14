import 'package:material_ui/material_ui.dart';

import 'api.dart';
import 'ui.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key, required this.api, required this.updated});
  final Api api;
  final Future<void> Function() updated;
  @override
  Widget build(BuildContext context) => DataPane(
    load: () => api.call('/genealogy/me'),
    builder: (data, reload) {
      final user = data['user'] as Json, member = data['member'] as Json?;
      return pageList([
        heading(user['full_name']),
        Text(user['email']),
        Text('Vai trò: ${user['role']}'),
        ActionButton(
          'Sửa hồ sơ',
          () => formDialog(
            context,
            title: 'Hồ sơ cá nhân',
            fields: const {
              'name': 'Họ và tên',
              'birth_date': 'Ngày sinh (YYYY-MM-DD)',
              'location': 'Nơi ở',
            },
            initial: {
              'name': user['full_name'],
              'birth_date': member?['birth_date'],
              'location': member?['location'],
            },
            requiredFields: {'name'},
            save: (body) async {
              if (body['birth_date'] == '') body['birth_date'] = null;
              await api.call('/genealogy/me', method: 'PUT', body: body);
              reload();
              await updated();
            },
          ),
          icon: Icons.edit_outlined,
        ),
        if (member != null)
          card([
            heading(member['family_name']),
            Text(member['branch_name'] ?? 'Chưa phân chi'),
            Text(member['birth_date'] ?? 'Chưa cập nhật ngày sinh'),
            Text(member['location'] ?? 'Chưa cập nhật nơi ở'),
          ]),
        if (member == null && user['role'] != 'guest') ...[
          const Text(
            'Liên kết hồ sơ gia phả bằng tên gia đình và họ tên chính xác. Quản lý sẽ duyệt yêu cầu.',
          ),
          ActionButton(
            'Tìm hồ sơ để xác minh',
            () => openPage(
              context,
              'Xác minh hồ sơ',
              VerificationScreen(api: api, updated: updated),
            ),
            icon: Icons.verified_user_outlined,
          ),
        ],
        heading('Lịch sử xác minh'),
        if ((data['verifications'] as List).isEmpty)
          const Text('Chưa gửi yêu cầu.'),
        for (final row in data['verifications'])
          card([
            Text('${row['name']} · ${row['family_name']}'),
            Text(
              const {
                    'pending': 'Đang chờ duyệt',
                    'approved': 'Đã duyệt',
                    'rejected': 'Đã từ chối',
                  }[row['status']] ??
                  row['status'],
            ),
            Text(displayDate(row['created_at'])),
          ]),
      ]);
    },
  );
}

class VerificationScreen extends StatefulWidget {
  const VerificationScreen({
    super.key,
    required this.api,
    required this.updated,
  });
  final Api api;
  final Future<void> Function() updated;
  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  Json? search;
  @override
  Widget build(BuildContext context) => Column(
    children: [
      ActionButton(
        'Nhập thông tin tìm kiếm',
        () => formDialog(
          context,
          title: 'Tìm hồ sơ',
          fields: const {
            'family_name': 'Tên gia đình chính xác',
            'full_name': 'Họ và tên chính xác',
            'birth_date': 'Ngày sinh (YYYY-MM-DD, tùy chọn)',
          },
          requiredFields: {'family_name', 'full_name'},
          initial: search ?? {},
          save: (values) async {
            if (mounted) setState(() => search = values);
          },
        ),
        icon: Icons.search,
      ),
      Expanded(
        child: search == null
            ? const Center(child: Text('Nhập thông tin gia đình để tìm hồ sơ.'))
            : DataPane(
                key: ValueKey('$search'),
                load: () => widget.api.call(
                  '/genealogy/verification-candidates',
                  query: search!,
                ),
                builder: (data, reload) => pageList([
                  if ((data as List).isEmpty)
                    const Text(
                      'Không tìm thấy hồ sơ chưa liên kết khớp thông tin.',
                    ),
                  for (final row in data)
                    card([
                      heading(row['name']),
                      Text(row['family_name']),
                      Text(row['branch_name'] ?? 'Chưa phân chi'),
                      ActionButton('Đây là hồ sơ của tôi', () async {
                        await widget.api.call(
                          '/genealogy/verifications',
                          method: 'POST',
                          body: {'member_id': row['id']},
                        );
                        await widget.updated();
                        if (context.mounted) Navigator.pop(context);
                      }, icon: Icons.check_circle_outline),
                    ]),
                ]),
              ),
      ),
    ],
  );
}
