import 'package:material_ui/material_ui.dart';

import 'api.dart';
import 'ui.dart';

class CommunityScreen extends StatefulWidget {
  const CommunityScreen({
    super.key,
    required this.api,
    required this.family,
    required this.user,
  });
  final Api api;
  final String family;
  final Json user;
  @override
  State<CommunityScreen> createState() => _CommunityScreenState();
}

class _CommunityScreenState extends State<CommunityScreen> {
  int page = 1;
  Future<void> edit(BuildContext context, VoidCallback reload, [Json? row]) =>
      formDialog(
        context,
        title: row == null ? 'Chia sẻ với gia đình' : 'Sửa bài viết',
        fields: {
          'content': 'Nội dung',
          'media': 'URL ảnh, ngăn cách bằng dấu xuống dòng',
          if (['admin', 'family_head'].contains(widget.user['role']))
            'announcement': 'Thông báo gia đình',
        },
        initial: {
          'content': row?['content'],
          'media': (row?['media_urls'] as List? ?? []).join('\n'),
          'announcement': '${row?['is_announcement'] ?? false}',
        },
        requiredFields: {'content'},
        choices: const {
          'announcement': {'false': 'Bài viết thường', 'true': 'Thông báo'},
        },
        save: (values) async {
          await widget.api.call(
            '/community/posts${row == null ? '' : '/${row['post_id']}'}',
            method: row == null ? 'POST' : 'PUT',
            body: {
              if (row == null) 'family_id': widget.family,
              'content': values['content'],
              'media': [
                for (final url
                    in (values['media'] as String)
                        .split('\n')
                        .map((s) => s.trim())
                        .where((s) => s.isNotEmpty))
                  {'url': url, 'type': 'image'},
              ],
              'is_announcement': values['announcement'] == 'true',
            },
          );
          reload();
        },
      );
  @override
  Widget build(BuildContext context) => DataPane(
    key: ValueKey(page),
    load: () => widget.api.call(
      '/community/posts',
      query: {'family_id': widget.family, 'page': page, 'page_size': 12},
    ),
    builder: (data, reload) => pageList([
      ActionButton(
        'Viết bài',
        () => edit(context, reload),
        icon: Icons.edit_outlined,
      ),
      if ((data['items'] as List).isEmpty)
        const Text('Chưa có bài viết. Hãy chia sẻ câu chuyện đầu tiên.'),
      for (final raw in data['items'])
        Builder(
          builder: (context) {
            final row = raw as Json;
            final owner =
                row['author_id'] == widget.user['id'] ||
                widget.user['role'] == 'admin';
            return card([
              Text(
                row['author_name'] ?? 'Thành viên',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              Text(displayDate(row['created_at'])),
              if (row['is_announcement'] == true)
                const Text(
                  'THÔNG BÁO',
                  style: TextStyle(color: Color(0xff244b3e)),
                ),
              SelectableText(row['content']),
              for (final url in row['media_urls']) remoteImage(url),
              Text(
                '${row['reaction_count']} cảm xúc · ${row['comment_count']} bình luận',
              ),
              DropdownButtonFormField<String>(
                key: ValueKey('${row['post_id']}-${row['my_reaction']}'),
                initialValue: row['my_reaction'] ?? '',
                decoration: const InputDecoration(labelText: 'Cảm xúc'),
                items:
                    const {
                          '': 'Chưa thả cảm xúc',
                          'Like': 'Thích',
                          'Love': 'Yêu thích',
                          'Haha': 'Vui',
                          'Wow': 'Bất ngờ',
                          'Sad': 'Buồn',
                          'Angry': 'Giận',
                        }.entries
                        .map(
                          (e) => DropdownMenuItem(
                            value: e.key,
                            child: Text(e.value),
                          ),
                        )
                        .toList(),
                onChanged: (value) async {
                  try {
                    await widget.api.call(
                      '/community/posts/${row['post_id']}/reactions',
                      method: 'PUT',
                      body: {'type': value == '' ? null : value},
                    );
                    reload();
                  } catch (error) {
                    if (context.mounted) message(context, error);
                  }
                },
              ),
              Wrap(
                children: [
                  ActionButton('Bình luận', () async {
                    await openPage(
                      context,
                      'Bình luận',
                      CommentsScreen(
                        api: widget.api,
                        post: row['post_id'],
                        user: widget.user,
                      ),
                    );
                    reload();
                  }, icon: Icons.chat_bubble_outline),
                  ActionButton(
                    'Báo cáo',
                    () => report(context, widget.api, row['post_id'], 'post'),
                    icon: Icons.flag_outlined,
                  ),
                  if (owner) ...[
                    ActionButton(
                      'Sửa',
                      () => edit(context, reload, row),
                      icon: Icons.edit,
                    ),
                    ActionButton('Xóa', () async {
                      if (await confirm(
                        context,
                        'Xóa bài viết và các bình luận liên quan?',
                      )) {
                        await widget.api.call(
                          '/community/posts/${row['post_id']}',
                          method: 'DELETE',
                        );
                        reload();
                      }
                    }, icon: Icons.delete_outline),
                  ],
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

Future<void> report(BuildContext context, Api api, String id, String type) =>
    formDialog(
      context,
      title: 'Báo cáo nội dung',
      fields: const {'reason': 'Lý do'},
      requiredFields: {'reason'},
      save: (values) async {
        await api.call(
          '/community/reports',
          method: 'POST',
          body: {
            'target_id': id,
            'target_type': type,
            'reason': values['reason'],
          },
        );
      },
    );

class CommentsScreen extends StatefulWidget {
  const CommentsScreen({
    super.key,
    required this.api,
    required this.post,
    required this.user,
  });
  final Api api;
  final String post;
  final Json user;
  @override
  State<CommentsScreen> createState() => _CommentsScreenState();
}

class _CommentsScreenState extends State<CommentsScreen> {
  int page = 1;
  Future<void> edit(BuildContext context, VoidCallback reload, [Json? row]) =>
      formDialog(
        context,
        title: row == null ? 'Viết bình luận' : 'Sửa bình luận',
        fields: const {'content': 'Nội dung'},
        initial: row ?? {},
        requiredFields: {'content'},
        save: (values) async {
          await widget.api.call(
            row == null
                ? '/community/posts/${widget.post}/comments'
                : '/community/comments/${row['id']}',
            method: row == null ? 'POST' : 'PUT',
            body: values,
          );
          reload();
        },
      );
  @override
  Widget build(BuildContext context) => DataPane(
    key: ValueKey(page),
    load: () => widget.api.call(
      '/community/posts/${widget.post}/comments',
      query: {'page': page, 'page_size': 20},
    ),
    builder: (data, reload) => pageList([
      ActionButton(
        'Viết bình luận',
        () => edit(context, reload),
        icon: Icons.add_comment_outlined,
      ),
      if ((data as List).isEmpty) const Text('Chưa có bình luận.'),
      for (final raw in data)
        Builder(
          builder: (context) {
            final row = raw as Json;
            return card([
              Text(
                row['author_name'] ?? 'Thành viên',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              Text(displayDate(row['created_at'])),
              Text(row['content']),
              Wrap(
                children: [
                  ActionButton(
                    'Báo cáo',
                    () => report(context, widget.api, row['id'], 'comment'),
                    icon: Icons.flag_outlined,
                  ),
                  if (row['user_id'] == widget.user['id'] ||
                      widget.user['role'] == 'admin') ...[
                    ActionButton(
                      'Sửa',
                      () => edit(context, reload, row),
                      icon: Icons.edit_outlined,
                    ),
                    ActionButton('Xóa', () async {
                      if (await confirm(context, 'Xóa bình luận này?')) {
                        await widget.api.call(
                          '/community/comments/${row['id']}',
                          method: 'DELETE',
                        );
                        reload();
                      }
                    }, icon: Icons.delete_outline),
                  ],
                ],
              ),
            ]);
          },
        ),
      pager(page, data.length == 20, (value) => setState(() => page = value)),
    ]),
  );
}
