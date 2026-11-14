import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:flutter/services.dart';

typedef Json = Map<String, dynamic>;

Future<void> openMedia(Api api, String value) async {
  final uri = Uri.parse(api.baseUrl).resolve(value);
  if (!['http', 'https'].contains(uri.scheme) ||
      uri.host.isEmpty ||
      uri.userInfo.isNotEmpty) {
    throw ApiError('Liên kết tư liệu không hợp lệ.');
  }
  await const MethodChannel('familyconnect/links')
      .invokeMethod<void>('open', {'url': '$uri'});
}

class Api {
  Api({
    http.Client? client,
    this.baseUrl = const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:8000/api',
    ),
  }) : client = client ?? http.Client();
  final http.Client client;
  final String baseUrl;
  String? token;
  void Function()? onUnauthorized;

  Future<dynamic> call(
    String path, {
    String method = 'GET',
    Json? body,
    Map<String, dynamic> query = const {},
  }) async {
    final session = token;
    final uri = Uri.parse('$baseUrl$path').replace(
      queryParameters: {
        for (final e in query.entries)
          if (e.value != null && e.value.toString().isNotEmpty)
            e.key: '${e.value}',
      },
    );
    final request = http.Request(method, uri)
      ..headers.addAll({
        'Content-Type': 'application/json',
        if (session != null) 'Authorization': 'Bearer $session',
      });
    if (body != null) request.body = jsonEncode(body);
    try {
      final response = await client
          .send(request)
          .then(http.Response.fromStream)
          .timeout(const Duration(seconds: 15));
      if (response.statusCode == 401 && token == session && session != null) {
        token = null;
        onUnauthorized?.call();
      }
      dynamic value;
      try {
        value = response.bodyBytes.isEmpty
            ? null
            : jsonDecode(utf8.decode(response.bodyBytes));
      } on FormatException {
        value = null;
      }
      if (response.statusCode >= 400) {
        final detail = value is Map ? value['detail'] : null;
        throw ApiError(
          detail is String
              ? detail
              : detail is List
              ? detail.map((e) => e is Map ? e['msg'] : e).join('\n')
              : 'Yêu cầu thất bại (${response.statusCode}).',
        );
      }
      return value;
    } on TimeoutException {
      throw ApiError('Máy chủ phản hồi chậm. Vui lòng thử lại.');
    } on http.ClientException {
      throw ApiError('Không kết nối được máy chủ. Kiểm tra backend và mạng.');
    }
  }
}

class ApiError implements Exception {
  ApiError(this.message);
  final String message;
  @override
  String toString() => message;
}

DateTime utcDate(String value) {
  final hasZone = RegExp(r'(Z|[+-]\d{2}:\d{2})$').hasMatch(value);
  return DateTime.parse(hasZone ? value : '${value}Z').toLocal();
}

String displayDate(dynamic value) {
  if (value == null) return 'Chưa cập nhật';
  final d = utcDate(value.toString());
  String two(int n) => n.toString().padLeft(2, '0');
  return '${two(d.day)}/${two(d.month)}/${d.year} ${two(d.hour)}:${two(d.minute)}';
}

Future<List<Json>> allPages(Api api, String path, Json query) async {
  final rows = <Json>[];
  for (var page = 1; ; page++) {
    final data = await api.call(
      path,
      query: {...query, 'page': page, 'page_size': 100},
    );
    final batch = (data['items'] as List).cast<Json>();
    rows.addAll(batch);
    if (batch.isEmpty || rows.length >= data['total']) return rows;
  }
}
