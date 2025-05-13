import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import '../config/env_config.dart';
import '../models/user_credentials.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'dart:io';

class AuthService {
  static const String _refreshTokenKey = 'refresh_token';
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  UserCredentials? _credentials;

  String get apiUrl => EnvConfig.apiUrl;

  UserCredentials? get credentials => _credentials;

  bool get isAuthenticated => _credentials?.accessToken != null;

  Future<UserCredentials> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$apiUrl/auth'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      await _secureStorage.write(
        key: _refreshTokenKey,
        value: data['refresh_token'],
      );

      _credentials = UserCredentials(accessToken: data['access_token']);

      //await registerDeviceForNotifications(data['access_token']);

      return _credentials!;
    } else {
      throw Exception(
        'Failed to login: ${response.statusCode} - ${response.body}',
      );
    }
  }

  Future<UserCredentials> refreshToken() async {
    final refreshToken = await _secureStorage.read(key: _refreshTokenKey);

    if (refreshToken == null) {
      throw Exception('No refresh token available');
    }

    final response = await http.get(
      Uri.parse('$apiUrl/auth/refresh'),
      headers: {
        'Cookie': 'refresh_token=$refreshToken',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      _credentials = UserCredentials(accessToken: data['access_token']);

      return _credentials!;
    } else {
      await logout();
      throw Exception(
        'Failed to refresh token: ${response.statusCode} - ${response.body}',
      );
    }
  }

  Future<void> logout() async {
    try {
      final refreshToken = await _secureStorage.read(key: _refreshTokenKey);

      if (refreshToken != null) {
        await http.delete(
          Uri.parse('$apiUrl/auth/logout'),
          headers: {
            'Cookie': 'refresh_token=$refreshToken',
            'Content-Type': 'application/json',
          },
        );

        final fcmToken = await FirebaseMessaging.instance.getToken();
        final deviceId = await getDeviceId();

        final userId = getUserIdFromToken(refreshToken);

        if (fcmToken != null) {
          await http.delete(
            Uri.parse('$apiUrl/device'),
            body: jsonEncode({'user_id': userId, 'device_id': deviceId, 'token': refreshToken}),
          );
        }
      }
    } catch (e) {
      print('Error during logout: $e');
    } finally {
      _credentials = null;
      await _secureStorage.delete(key: _refreshTokenKey);
    }
  }

  Map<String, String> _getAuthHeaders() {
    if (!isAuthenticated) {
      return {'Content-Type': 'application/json'};
    }

    return {
      'Authorization': 'Bearer ${_credentials!.accessToken}',
      'Content-Type': 'application/json',
    };
  }

  Future<http.Response> authorizedRequest(
    Future<http.Response> Function(Map<String, String> headers) requestFn,
  ) async {
    try {
      var headers = _getAuthHeaders();
      var response = await requestFn(headers);

      if (response.statusCode == 401) {
        await refreshToken();
        headers = _getAuthHeaders();
        response = await requestFn(headers);
      }

      return response;
    } catch (e) {
      throw Exception('Request failed: $e');
    }
  }

  bool isAccessTokenExpired([int bufferSeconds = 30]) {
    if (_credentials?.accessToken == null) {
      return true;
    }

    try {
      final jwt = _credentials!.accessToken;
      final parts = jwt.split('.');
      if (parts.length != 3) return true;

      final payload = parts[1];
      String normalized = base64Url.normalize(payload);
      final decoded = utf8.decode(base64Url.decode(normalized));
      final payloadMap = jsonDecode(decoded);

      if (!payloadMap.containsKey('exp')) return true;

      final expSeconds = payloadMap['exp'] as int;
      final expiry = DateTime.fromMillisecondsSinceEpoch(expSeconds * 1000);
      final now = DateTime.now();

      return now.isAfter(expiry.subtract(Duration(seconds: bufferSeconds)));
    } catch (e) {
      print('Error checking token expiry: $e');
      return true;
    }
  }

  Future<void> registerDeviceForNotifications(String authToken) async {
    try {
      final fcmToken = await FirebaseMessaging.instance.getToken();

      if (fcmToken != null) {
        final userId = getUserIdFromToken(authToken);

        final response = await http.post(
          Uri.parse('$apiUrl/device/register'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $authToken',
          },
          body: jsonEncode({
            'user_id': userId,
            'device_id': getDeviceId(),
            'fcm_token': fcmToken,
          }),
        );

        if (response.statusCode == 200) {
          print('Device registered for notifications successfully');
        } else {
          print('Failed to register device: ${response.body}');
        }
      }
    } catch (e) {
      print('Error registering device: $e');
    }
  }

  String getUserIdFromToken(String token) {
    final parts = token.split('.');
    if (parts.length != 3) {
      throw Exception('Invalid JWT token format');
    }

    final payload = parts[1];

    String normalized = payload;
    while (normalized.length % 4 != 0) {
      normalized += '=';
    }

    final payloadBytes = base64Url.decode(normalized);
    final payloadString = utf8.decode(payloadBytes);

    final payloadMap = jsonDecode(payloadString);

    return payloadMap['id'].toString();
  }

  Future<String> getDeviceId() async {
    DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
    String deviceId = '';

    try {
      if (Platform.isAndroid) {
        AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;
        deviceId = androidInfo.id;
      } else if (Platform.isIOS) {
        IosDeviceInfo iosInfo = await deviceInfo.iosInfo;
        deviceId = iosInfo.identifierForVendor ?? '';
      }
    } catch (e) {
      deviceId = 'flutter-device';
    }

    return deviceId;
  }
}
