import 'dart:async';
import 'dart:convert';
import 'package:doorbell_app/config/env_config.dart';
import 'package:doorbell_app/services/database_helper.dart';
import 'package:http/http.dart' as http;
import 'package:doorbell_app/models/notification.dart' as app_notification_model;
import 'package:doorbell_app/models/settings.dart' as app_settings_model;
import 'package:doorbell_app/services/auth_service.dart';

class ApiService {
  final AuthService authService;

  String get apiUrl => EnvConfig.apiUrl;

  ApiService({required this.authService});

  Future<List<app_notification_model.Notification>> getAllNotifications({
    int page = 1,
    int pageSize = 20,
    String? sortBy,
    String? sortOrder,
  }) async {
    final queryParams = {
      'page': page.toString(),
      'page_size': pageSize.toString(),
    };
    if (sortBy != null) {
      queryParams['sort_by'] = sortBy;
    }
    if (sortOrder != null) {
      queryParams['sort_order'] = sortOrder;
    }

    final uri = Uri.parse('$apiUrl/notifications').replace(queryParameters: queryParams);
    print('Fetching notifications from: $uri');

    try {
      final response = await authService.authorizedRequest(
        (headers) => http.get(uri, headers: headers),
      );

      if (response.statusCode == 200) {
        final List<dynamic> notificationsJson = jsonDecode(response.body);
        return notificationsJson
            .map((jsonItem) => app_notification_model.Notification.fromMap(jsonItem as Map<String, dynamic>))
            .toList();
      } else {
        print('Failed to fetch notifications: ${response.statusCode} - ${response.body}');
        throw Exception('Failed to fetch notifications: ${response.statusCode}');
      }
    } catch (e) {
      print('Error in getAllNotifications: $e');
      throw Exception('Error fetching notifications: $e');
    }
  }

  Future<void> syncNotifications() async {
    try {
      final allNotifications = await getAllNotifications(pageSize: 100);
      for (var notification in allNotifications) {
         await DatabaseHelper.instance.insertNotification(notification);
      }
      print('Successfully synced ${allNotifications.length} notifications via getAllNotifications.');
    } catch (e) {
      print('Failed to sync notifications: $e');
    }
  }


  Future<bool> deleteCapture(int captureId) async {
    try {
      final response = await authService.authorizedRequest(
        (headers) => http.delete(
          Uri.parse('$apiUrl/captures/$captureId'),
          headers: headers,
        ),
      );
      if (response.statusCode == 204 || response.statusCode == 200) {
        print('Capture $captureId deleted successfully from server.');
        return true;
      } else {
        print('Failed to delete capture $captureId from server: ${response.statusCode} - ${response.body}');
        return false;
      }
    } catch (e) {
      print('Error during deleteCapture: $e');
      return false;
    }
  }

  Future<bool> deleteNotification(int notificationId) async {
    try {
      final response = await authService.authorizedRequest(
        (headers) => http.delete(
          Uri.parse('$apiUrl/notifications/$notificationId'),
          headers: headers,
        ),
      );
      if (response.statusCode == 204 || response.statusCode == 200) {
        print('Notification $notificationId deleted successfully.');
        return true;
      } else {
        print('Failed to delete notification $notificationId: ${response.statusCode} - ${response.body}');
        return false;
      }
    } catch (e) {
      print('Error during deleteNotification: $e');
      return false;
    }
  }

  Future<app_settings_model.Settings> getSettings() async {
    try {
      final response = await authService.authorizedRequest(
        (headers) => http.get(
          Uri.parse('$apiUrl/settings'),
          headers: headers,
        ),
      );
      if (response.statusCode == 200) {
        return app_settings_model.Settings.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
      } else {
        print('Failed to get settings: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      print('Error during getSettings: $e');
    }
    print('Returning default settings due to API failure.');
    return app_settings_model.Settings( // Default settings
      button: app_settings_model.ButtonSettingsConfig(debounceMs: 200, pollingRateHz: 10),
      motionSensor: app_settings_model.MotionSensorSettingsConfig(debounceMs: 1000, pollingRateHz: 2),
      camera: app_settings_model.CameraSettingsConfig(
        stopMotion: app_settings_model.StopMotionSettingsConfig(intervalSeconds: 1.0, durationSeconds: 60.0),
      ),
      color: app_settings_model.ColorSettingsConfig(r: 0, g: 0, b: 100),
    );
  }

  Future<bool> updateSettings(app_settings_model.Settings settings) async {
    try {
      final settingsJson = jsonEncode(settings.toJson());
      final response = await authService.authorizedRequest(
        (headers) => http.put(
          Uri.parse('$apiUrl/settings'),
          body: settingsJson,
          headers: headers,
        ),
      );
      if (response.statusCode == 200) {
        print('Settings updated successfully.');
        return true;
      } else {
        print('Failed to update settings: ${response.statusCode} - ${response.body}');
        return false;
      }
    } catch (e) {
      print('Error during updateSettings: $e');
      return false;
    }
  }
}
