import 'package:material_ui/material_ui.dart';

import 'api.dart';

void message(BuildContext context, Object error) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
}

class ActionButton extends StatefulWidget {
  const ActionButton(this.label, this.action, {super.key, this.icon});
  final String label;
  final Future<void> Function()? action;
  final IconData? icon;
  @override
  State<ActionButton> createState() => _ActionButtonState();
}

class _ActionButtonState extends State<ActionButton> {
  bool busy = false;
  @override
  Widget build(BuildContext context) => TextButton.icon(
    onPressed: busy || widget.action == null
        ? null
        : () async {
            setState(() => busy = true);
            try {
              await widget.action!();
            } catch (error) {
              if (context.mounted) message(context, error);
            } finally {
              if (mounted) setState(() => busy = false);
            }
          },
    icon: busy
        ? const SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2),
          )
        : Icon(widget.icon, size: 18),
    label: Text(widget.label),
  );
}

class DataPane extends StatefulWidget {
  const DataPane({super.key, required this.load, required this.builder});
  final Future<dynamic> Function() load;
  final Widget Function(dynamic, VoidCallback) builder;
  @override
  State<DataPane> createState() => _DataPaneState();
}

class _DataPaneState extends State<DataPane> {
  late Future<dynamic> future = widget.load();
  void reload() {
    if (mounted) {
      setState(() {
        future = widget.load();
      });
    }
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<dynamic>(
    future: future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('${snapshot.error}'),
                TextButton(onPressed: reload, child: const Text('Thử lại')),
              ],
            ),
          ),
        );
      }
      return RefreshIndicator(
        onRefresh: () async {
          reload();
          try {
            await future;
          } catch (_) {}
        },
        child: widget.builder(snapshot.data, reload),
      );
    },
  );
}

Widget pageList(List<Widget> children) => ListView(
  padding: const EdgeInsets.all(16),
  physics: const AlwaysScrollableScrollPhysics(),
  children: [
    for (final child in children)
      Padding(padding: const EdgeInsets.only(bottom: 12), child: child),
  ],
);

Widget card(List<Widget> children) => Card(
  child: Padding(
    padding: const EdgeInsets.all(16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final child in children)
          Padding(padding: const EdgeInsets.only(bottom: 8), child: child),
      ],
    ),
  ),
);

Widget heading(String text) => Text(
  text,
  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
);

Widget remoteImage(String? url) {
  if (url == null ||
      !RegExp(r'^https?://', caseSensitive: false).hasMatch(url)) {
    return const SizedBox.shrink();
  }
  return ClipRRect(
    borderRadius: BorderRadius.circular(12),
    child: Image.network(
      url,
      height: 180,
      fit: BoxFit.cover,
      errorBuilder: (_, _, _) => const Text('Không tải được ảnh.'),
    ),
  );
}

Widget pager(int page, bool more, void Function(int) change) => Wrap(
  alignment: WrapAlignment.spaceBetween,
  crossAxisAlignment: WrapCrossAlignment.center,
  spacing: 8,
  runSpacing: 4,
  children: [
    TextButton(
      onPressed: page > 1 ? () => change(page - 1) : null,
      child: const Text('Trang trước'),
    ),
    Text('Trang $page'),
    TextButton(
      onPressed: more ? () => change(page + 1) : null,
      child: const Text('Trang tiếp'),
    ),
  ],
);

Future<bool> confirm(BuildContext context, String text) async =>
    await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Xác nhận'),
        content: Text(text),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Xác nhận'),
          ),
        ],
      ),
    ) ??
    false;

Future<void> formDialog(
  BuildContext context, {
  required String title,
  required Map<String, String> fields,
  Json initial = const {},
  Set<String> requiredFields = const {},
  Map<String, Map<String, String>> choices = const {},
  required Future<void> Function(Json) save,
}) => showDialog<void>(
  context: context,
  barrierDismissible: false,
  builder: (_) => _RecordForm(
    title: title,
    fields: fields,
    initial: initial,
    requiredFields: requiredFields,
    choices: choices,
    save: save,
  ),
);

class _RecordForm extends StatefulWidget {
  const _RecordForm({
    required this.title,
    required this.fields,
    required this.initial,
    required this.requiredFields,
    required this.choices,
    required this.save,
  });
  final String title;
  final Map<String, String> fields;
  final Json initial;
  final Set<String> requiredFields;
  final Map<String, Map<String, String>> choices;
  final Future<void> Function(Json) save;
  @override
  State<_RecordForm> createState() => _RecordFormState();
}

class _RecordFormState extends State<_RecordForm> {
  late final controllers = {
    for (final key in widget.fields.keys)
      key: TextEditingController(text: widget.initial[key]?.toString() ?? ''),
  };
  final form = GlobalKey<FormState>();
  bool saving = false;
  @override
  void dispose() {
    for (final controller in controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !saving,
    child: AlertDialog(
      title: Text(widget.title),
      content: SizedBox(
        width: 440,
        child: SingleChildScrollView(
          child: Form(
            key: form,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (final field in widget.fields.entries)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: widget.choices.containsKey(field.key)
                        ? DropdownButtonFormField<String>(
                            initialValue: controllers[field.key]!.text.isEmpty
                                ? null
                                : controllers[field.key]!.text,
                            isExpanded: true,
                            decoration: InputDecoration(labelText: field.value),
                            items: widget.choices[field.key]!.entries
                                .map(
                                  (e) => DropdownMenuItem(
                                    value: e.key,
                                    child: Text(
                                      e.value,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                )
                                .toList(),
                            onChanged: saving
                                ? null
                                : (value) => controllers[field.key]!.text =
                                      value ?? '',
                            validator: (value) =>
                                widget.requiredFields.contains(field.key) &&
                                    (value == null || value.isEmpty)
                                ? 'Vui lòng chọn giá trị.'
                                : null,
                          )
                        : TextFormField(
                            enabled: !saving,
                            controller: controllers[field.key],
                            decoration: InputDecoration(labelText: field.value),
                            minLines:
                                [
                                  'content',
                                  'description',
                                  'media',
                                ].contains(field.key)
                                ? 3
                                : 1,
                            maxLines:
                                [
                                  'content',
                                  'description',
                                  'media',
                                ].contains(field.key)
                                ? 5
                                : 1,
                            validator: (value) =>
                                widget.requiredFields.contains(field.key) &&
                                    (value?.trim().isEmpty ?? true)
                                ? 'Vui lòng nhập thông tin.'
                                : null,
                          ),
                  ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: saving ? null : () => Navigator.pop(context),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: saving
              ? null
              : () async {
                  if (!form.currentState!.validate()) return;
                  setState(() => saving = true);
                  try {
                    await widget.save({
                      for (final entry in controllers.entries)
                        entry.key: entry.value.text.trim(),
                    });
                    if (context.mounted) Navigator.pop(context);
                  } catch (error) {
                    if (context.mounted) message(context, error);
                  } finally {
                    if (mounted) setState(() => saving = false);
                  }
                },
          child: Text(saving ? 'Đang lưu…' : 'Lưu'),
        ),
      ],
    ),
  );
}

Future<void> openPage(BuildContext context, String title, Widget body) =>
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => Scaffold(
          appBar: AppBar(title: Text(title)),
          body: body,
        ),
      ),
    );
