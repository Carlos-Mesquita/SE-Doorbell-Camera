import 'dart:async';
import 'dart:convert';
import 'package:doorbell_app/config/env_config.dart';
import 'package:doorbell_app/services/database_helper.dart';
import 'package:http/http.dart' as http;
import 'package:doorbell_app/models/settings.dart' as app_settings_model;
import 'package:doorbell_app/services/auth_service.dart';
import 'package:doorbell_app/models/notification.dart';
import 'package:get_it/get_it.dart';
import 'dart:io';
import 'package:path_provider/path_provider.dart';

class ApiService {
  final GetIt _serviceLocator = GetIt.instance;

  AuthService get authService => _serviceLocator<AuthService>();
  String get apiUrl => EnvConfig.apiUrl!;

  Future<List<NotificationDTO>> getAllNotifications({
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

    final uri = Uri.parse(
      '$apiUrl/notifications',
    ).replace(queryParameters: queryParams);
    print('Fetching notifications from: $uri');

    try {
      final response = await authService.authorizedRequest(
        (headers) => http.get(uri, headers: headers),
      );

      if (response.statusCode == 200) {
        final List<dynamic> notificationsJson = jsonDecode(response.body);
        return notificationsJson
            .map(
              (jsonItem) =>
                  NotificationDTO.fromMap(jsonItem as Map<String, dynamic>),
            )
            .toList();
      } else {
        print(
          'Failed to fetch notifications: ${response.statusCode} - ${response.body}',
        );
        throw Exception(
          'Failed to fetch notifications: ${response.statusCode}',
        );
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
      print(
        'Successfully synced ${allNotifications.length} notifications via getAllNotifications.',
      );
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
        print(
          'Failed to delete capture $captureId from server: ${response.statusCode} - ${response.body}',
        );
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
        print(
          'Failed to delete notification $notificationId: ${response.statusCode} - ${response.body}',
        );
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
        (headers) => http.get(Uri.parse('$apiUrl/settings'), headers: headers),
      );
      if (response.statusCode == 200) {
        return app_settings_model.Settings.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>,
        );
      } else {
        print(
          'Failed to get settings: ${response.statusCode} - ${response.body}',
        );
      }
    } catch (e) {
      print('Error during getSettings: $e');
    }
    print('Returning default settings due to API failure.');
    return app_settings_model.Settings(
      // Default settings
      button: app_settings_model.ButtonSettingsConfig(
        debounceMs: 200,
        pollingRateHz: 10,
      ),
      motionSensor: app_settings_model.MotionSensorSettingsConfig(
        debounceMs: 1000,
        pollingRateHz: 2,
      ),
      camera: app_settings_model.CameraSettingsConfig(
        stopMotion: app_settings_model.StopMotionSettingsConfig(
          intervalSeconds: 1.0,
          durationSeconds: 60.0,
        ),
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
        print(
          'Failed to update settings: ${response.statusCode} - ${response.body}',
        );
        return false;
      }
    } catch (e) {
      print('Error during updateSettings: $e');
      return false;
    }
  }

  Future<String?> generateStopMotionVideo(
    List<String> capturePaths, {
    Function(double)? onProgress,
    Function(String)? onStatusUpdate,
  }) async {
    if (capturePaths.isEmpty) {
      throw ArgumentError('Capture paths list cannot be empty');
    }

    try {
      if (onStatusUpdate != null) {
        onStatusUpdate('Requesting video generation...');
      }
      if (onProgress != null) onProgress(0.0);

      final request = http.Request('POST', Uri.parse('$apiUrl/capture'));
      late Map<String, String> authHeaders;
      await authService.authorizedRequest((headers) async {
        authHeaders = headers;
        return http.Response('', 200);
      });

      request.headers.addAll(authHeaders);
      request.headers['Content-Type'] = 'application/json';

      request.body = jsonEncode({'request': { 'capture_paths': capturePaths } });

      if (onStatusUpdate != null) onStatusUpdate('Processing...');
      if (onProgress != null) onProgress(0.1);

      final streamedResponse = await request.send();

      if (streamedResponse.statusCode == 200) {
        if (onStatusUpdate != null) onStatusUpdate('Streaming video...');
        if (onProgress != null) onProgress(0.2);

        final tempDir = await getTemporaryDirectory();
        final videoFile = File(
          '${tempDir.path}/stop_motion_${DateTime.now().millisecondsSinceEpoch}.mp4',
        );
        final sink = videoFile.openWrite();

        final contentLength = streamedResponse.contentLength;
        int receivedBytes = 0;

        try {
          await for (final chunk in streamedResponse.stream) {
            sink.add(chunk);
            receivedBytes += chunk.length;

            if (contentLength != null && contentLength > 0) {
              final progress = 0.2 + (receivedBytes / contentLength) * 0.8;
              if (onProgress != null) onProgress(progress);
            }
          }
        } finally {
          await sink.close();
        }

        if (onStatusUpdate != null) onStatusUpdate('Video ready!');
        if (onProgress != null) onProgress(1.0);

        return videoFile.path;
      } else {
        final errorBody = await streamedResponse.stream.bytesToString();
        throw Exception(
          'Failed to generate video: ${streamedResponse.statusCode} - $errorBody',
        );
      }
    } catch (e) {
      throw Exception('Error generating video: $e');
    }
  }
}
