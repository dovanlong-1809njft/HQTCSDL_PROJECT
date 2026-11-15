import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api.dart';
import 'reminders.dart';
import 'ui.dart';
import 'community.dart';
import 'calendar.dart';
import 'directory.dart';
import 'heritage.dart';
import 'profile.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const FamilyConnectApp());
}

class FamilyConnectApp extends StatefulWidget {
  const FamilyConnectApp({super.key, this.api});
  final Api? api;
  @override
  State<FamilyConnectApp> createState() => _FamilyConnectAppState();
}

class _FamilyConnectAppState extends State<FamilyConnectApp>
    with WidgetsBindingObserver {
  late final Api api = widget.api ?? Api();
  final storage = const FlutterSecureStorage();
  final reminders = Reminders();
  final navigator = GlobalKey<NavigatorState>();
  Json? user;
  bool loading = true;
  String? bootError;
  Timer? timer;
  Future<void> cleanup = Future.value();
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    api.onUnauthorized = () {
      unawaited(logout());
    };
    unawaited(restore());
  }

  Future<void> restore() async {
    try {
      await reminders.initialize();
      api.token = await storage.read(key: 'familyconnect.token');
      if (api.token != null) user = await api.call('/auth/me') as Json;
      bootError = null;
    } catch (error) {
      bootError = '$error';
    }
    if (mounted) setState(() => loading = false);
    if (user != null) startSync();
  }

  void startSync() {
    timer?.cancel();
    timer = Timer.periodic(const Duration(minutes: 1), (_) => sync());
    sync();
  }

  void sync() {
    if (api.token != null) {
      unawaited(reminders.sync(api).catchError((Object _) {}));
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) sync();
  }

  Future<void> login(String email, String password, String? name) async {
    final session = await api.call(
      name == null ? '/auth/login' : '/auth/register',
      method: 'POST',
      body: {
        'email': email.trim(),
        'password': password,
        if (name != null) 'full_name': name.trim(),
      },
    ) as Json;
    await cleanup;
    await storage.write(
      key: 'familyconnect.token',
      value: session['access_token'],
    );
    api.token = session['access_token'];
    if (mounted) {
      setState(() {
        user = session['user'];
        bootError = null;
      });
    }
    startSync();
  }

  Future<void> logout() async {
    timer?.cancel();
    api.token = null;
    navigator.currentState?.popUntil((route) => route.isFirst);
    cleanup = Future.wait([
      storage.delete(key: 'familyconnect.token'),
      reminders.clear(),
    ]).then((_) {});
    if (mounted) setState(() => user = null);
    await cleanup;
  }

  @override
  void dispose() {
    timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    api.client.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    navigatorKey: navigator,
    title: 'FamilyConnect',
    locale: const Locale('vi'),
    supportedLocales: const [Locale('vi'), Locale('en')],
    localizationsDelegates: GlobalMaterialLocalizations.delegates,
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff244b3e)),
      scaffoldBackgroundColor: const Color(0xfff7f5ef),
      inputDecorationTheme: const InputDecorationTheme(
        border: OutlineInputBorder(),
      ),
      appBarTheme: const AppBarTheme(backgroundColor: Color(0xfff7f5ef)),
    ),
    home: loading
        ? const Scaffold(body: Center(child: CircularProgressIndicator()))
        : user == null
        ? LoginScreen(login: login, error: bootError)
        : Home(
            key: ValueKey(user!['id']),
            api: api,
            user: user!,
            reminders: reminders,
            logout: logout,
          ),
  );
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.login, this.error});
  final Future<void> Function(String, String, String?) login;
  final String? error;
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController(),
      password = TextEditingController(),
      name = TextEditingController();
  final form = GlobalKey<FormState>();
  bool register = false;
  @override
  void dispose() {
    email.dispose();
    password.dispose();
    name.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Form(
              key: form,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(
                    Icons.diversity_1_outlined,
                    size: 48,
                    color: Color(0xff244b3e),
                  ),
                  const SizedBox(height: 16),
                  heading('FamilyConnect'),
                  Text(
                    register
                        ? 'Tạo tài khoản gia đình'
                        : 'Chào bạn, mời đăng nhập',
                  ),
                  const SizedBox(height: 24),
                  if (register)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: TextFormField(
                        controller: name,
                        decoration: const InputDecoration(
                          labelText: 'Họ và tên',
                        ),
                        validator: (value) => (value?.trim().length ?? 0) < 2
                            ? 'Nhập họ và tên.'
                            : null,
                      ),
                    ),
                  TextFormField(
                    controller: email,
                    keyboardType: TextInputType.emailAddress,
                    autocorrect: false,
                    decoration: const InputDecoration(labelText: 'Email'),
                    validator: (value) => (value?.contains('@') ?? false)
                        ? null
                        : 'Email chưa hợp lệ.',
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: password,
                    obscureText: true,
                    autocorrect: false,
                    decoration: const InputDecoration(labelText: 'Mật khẩu'),
                    validator: (value) =>
                        (value?.length ?? 0) < (register ? 8 : 1)
                        ? 'Mật khẩu ${register ? 'ít nhất 8 ký tự' : 'không được trống'}.'
                        : null,
                  ),
                  if (widget.error != null)
                    Text(
                      widget.error!,
                      style: const TextStyle(color: Colors.red),
                    ),
                  const SizedBox(height: 16),
                  ActionButton(register ? 'Đăng ký' : 'Đăng nhập', () async {
                    if (form.currentState!.validate()) {
                      await widget.login(
                        email.text,
                        password.text,
                        register ? name.text : null,
                      );
                    }
                  }, icon: Icons.login),
                  TextButton(
                    onPressed: () => setState(() => register = !register),
                    child: Text(
                      register
                          ? 'Đã có tài khoản? Đăng nhập'
                          : 'Chưa có tài khoản? Đăng ký',
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );
}

class Home extends StatefulWidget {
  const Home({
    super.key,
    required this.api,
    required this.user,
    required this.reminders,
    required this.logout,
  });
  final Api api;
  final Json user;
  final Reminders reminders;
  final Future<void> Function() logout;
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> with WidgetsBindingObserver {
  List<dynamic> families = [];
  String? family;
  Json? profile;
  int tab = 0, revision = 0;
  String? error;
  bool loading = true;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    unawaited(load());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) unawaited(load());
  }

  Future<void> load() async {
    try {
      final fresh = await widget.api.call('/genealogy/me') as Json;
      final list = fresh['user']['role'] == 'guest'
          ? <dynamic>[]
          : await widget.api.call('/heritage/families') as List;
      if (!mounted) return;
      setState(() {
        profile = fresh;
        families = list;
        if (!families.any((row) => row['id'] == family)) {
          family = families.firstOrNull?['id'];
        }
        if (family == null) tab = 5;
        error = null;
        loading = false;
        revision++;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          error = '$e';
          loading = false;
        });
      }
    }
  }

  static const labels = [
    'Bảng tin',
    'Lịch',
    'Danh bạ',
    'Di sản',
    'Thông báo',
    'Hồ sơ',
  ];
  static const icons = [
    Icons.forum_outlined,
    Icons.calendar_month,
    Icons.people_outline,
    Icons.auto_stories_outlined,
    Icons.notifications_outlined,
    Icons.person_outline,
  ];
  @override
  Widget build(BuildContext context) {
    final api = widget.api, user = profile?['user'] as Json? ?? widget.user;
    final member = profile?['member'];
    final memberId = member != null && member['family_id'] == family
        ? member['id'] as String?
        : null;
    final body = loading
        ? const Center(child: CircularProgressIndicator())
        : error != null
        ? pageList([Text(error!), ActionButton('Thử lại', load)])
        : tab == 5
        ? ProfileScreen(api: api, updated: load)
        : tab == 4
        ? InboxScreen(api: api, reminders: widget.reminders)
        : family == null
        ? pageList([
            const Text(
              'Chưa liên kết gia đình. Gửi yêu cầu xác minh trong Hồ sơ.',
            ),
          ])
        : switch (tab) {
            0 => CommunityScreen(api: api, family: family!, user: user),
            1 => CalendarScreen(
              api: api,
              family: family!,
              memberId: memberId,
              reminders: widget.reminders,
              user: user,
            ),
            2 => DirectoryScreen(api: api, family: family!),
            _ => HeritageScreen(api: api, family: family!, user: user),
          };
    return Scaffold(
      appBar: AppBar(
        title: Text(labels[tab]),
        actions: [
          IconButton(
            tooltip: 'Làm mới hồ sơ',
            onPressed: load,
            icon: const Icon(Icons.refresh),
          ),
          ActionButton('Đăng xuất', widget.logout, icon: Icons.logout),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (families.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                child: DropdownButtonFormField<String>(
                  key: ValueKey(family),
                  initialValue: family,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Gia đình'),
                  items: families
                      .map(
                        (row) => DropdownMenuItem<String>(
                          value: row['id'],
                          child: Text(
                            row['name'],
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (value) => setState(() => family = value),
                ),
              ),
            Expanded(
              child: KeyedSubtree(
                key: ValueKey('${user['role']}-$family-$tab-$revision'),
                child: body,
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        labelBehavior: NavigationDestinationLabelBehavior.onlyShowSelected,
        onDestinationSelected: (value) => setState(() => tab = value),
        destinations: [
          for (var i = 0; i < labels.length; i++)
            NavigationDestination(icon: Icon(icons[i]), label: labels[i]),
        ],
      ),
    );
  }
}

class InboxScreen extends StatefulWidget {
  const InboxScreen({super.key, required this.api, required this.reminders});
  final Api api;
  final Reminders reminders;
  @override
  State<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends State<InboxScreen> {
  int page = 1, revision = 0;
  Timer? timer;
  @override
  void initState() {
    super.initState();
    timer = Timer.periodic(const Duration(seconds: 15), (_) {
      if (mounted) setState(() => revision++);
    });
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => DataPane(
    key: ValueKey('$page-$revision'),
    load: () => widget.api.call(
      '/notifications',
      query: {'page': page, 'page_size': 20},
    ),
    builder: (data, reload) => pageList([
      ActionButton('Bật nhắc lịch Android', () async {
        final granted = await widget.reminders.enable();
        if (granted) await widget.reminders.sync(widget.api);
        if (context.mounted) {
          message(
            context,
            !granted
                ? 'Chưa cấp quyền thông báo.'
                : widget.reminders.exact
                ? 'Đã bật nhắc lịch.'
                : 'Đã bật. Android có thể trì hoãn khi chưa cấp quyền báo thức chính xác.',
          );
        }
      }, icon: Icons.notifications_active_outlined),
      Text('${data['unread']} thông báo chưa đọc'),
      if ((data['items'] as List).isEmpty) const Text('Chưa có thông báo.'),
      for (final row in data['items'])
        card([
          heading(row['title']),
          Text(row['body']),
          Text(displayDate(row['created_at'])),
          if (row['read_at'] == null)
            ActionButton('Đánh dấu đã đọc', () async {
              await widget.api.call(
                '/notifications/${row['id']}/read',
                method: 'PATCH',
              );
              reload();
            }, icon: Icons.done),
          if (row['event_id'] != null)
            ActionButton('Xem sự kiện', () async {
              final profile = await widget.api.call('/genealogy/me');
              final own = profile['member'];
              if (context.mounted) {
                await openPage(
                  context,
                  'Sự kiện',
                  EventScreen(
                    api: widget.api,
                    id: row['event_id'],
                    reminders: widget.reminders,
                    memberId:
                        own != null && own['family_id'] == row['family_id']
                        ? own['id']
                        : null,
                  ),
                );
              }
            }, icon: Icons.event),
        ]),
      pager(
        page,
        page * 20 < data['total'],
        (value) => setState(() => page = value),
      ),
    ]),
  );
}
