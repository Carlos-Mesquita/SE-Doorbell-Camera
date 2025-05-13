import 'dart:async';
import 'dart:convert';
import 'package:doorbell_app/config/env_config.dart';
import 'package:http/http.dart' as http;
import '../models/notification.dart' as app_notification;
import '../models/settings.dart';
import 'auth_service.dart';
import 'database_helper.dart';

class ApiService {
  final AuthService authService;

  String get apiUrl => EnvConfig.apiUrl;

  ApiService({required this.authService});

  Future<void> syncNotifications() async {
    try {
      final response = await authService.authorizedRequest(
        (headers) =>
            http.get(Uri.parse('$apiUrl/notifications'), headers: headers),
      );

      if (response.statusCode == 200) {
        final List<dynamic> notificationsJson = jsonDecode(response.body);

        for (var notification in notificationsJson) {
          final newNotification = app_notification.Notification(
            id: notification['id'],
            title: notification['title'],
            timestamp: notification['timestamp'],
            captures: List<String>.from(notification['captures']),
            eventType: notification['event_type'] ?? 'unknown',
            duration: notification['duration'] ?? 0,
          );

          await DatabaseHelper.instance.insertNotification(newNotification);
        }
      }
    } catch (e) {
      print('Failed to sync notifications: $e');
    }
  }


  Future<bool> deleteRecording(int id) async {
    try {
      final response = await authService.authorizedRequest(
        (headers) => http.delete(
          Uri.parse('$apiUrl/recordings/$id'),
          headers: headers,
        ),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Failed to delete recording: $e');
      return false;
    }
  }

  Future<Settings> getSettings() async {
    try {
      final response = await authService.authorizedRequest(
        (headers) => http.get(
          Uri.parse('$apiUrl/settings'),
          headers: headers,
        ),
      );

      if (response.statusCode == 200) {
        return Settings.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      print('Failed to get settings: $e');
    }

    // Default settings if API call fails
    return Settings(
      camera: {
        'bitrate': 1000000,
        'stop_motion': {'interval': 0.5, 'duration': 300.0, 'auto_stop': true},
      },
      motionSensor: {'debounce': 0.5, 'polling_rate': 0.1},
      doorbell: {'debounce': 0.5, 'polling_rate': 0.1},
    );
  }

  Future<bool> updateSettings(Settings settings) async {
    try {
      final response = await authService.authorizedRequest(
        (headers) => http.put(
          Uri.parse('$apiUrl/settings'),
          body: jsonEncode(settings.toJson()),
          headers: headers,
        ),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Failed to update settings: $e');
      return false;
    }
  }
}
