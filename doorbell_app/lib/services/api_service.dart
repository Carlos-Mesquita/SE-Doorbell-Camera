import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../models/notification.dart' as app_notification;
import '../models/settings.dart';
import 'auth_service.dart';
import 'database_helper.dart';

class ApiService {
  final String serverUrl;
  final AuthService authService;
  WebSocketChannel? _channel;
  bool _isConnected = false;
  final Function(app_notification.Notification) onNewNotification;
  final FlutterLocalNotificationsPlugin _notificationsPlugin = FlutterLocalNotificationsPlugin();

  ApiService({
    required this.serverUrl, 
    required this.authService,
    required this.onNewNotification
  });

  Future<Map<String, String>> _getAuthHeaders() async {
    final token = await authService.getAccessToken();
    if (token == null) {
      throw Exception('Not authenticated');
    }
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  Future<void> syncNotifications() async {
    try {
      final headers = await _getAuthHeaders();
      final response = await http.get(
        Uri.parse('$serverUrl/api/notifications'),
        headers: headers,
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

  void connectWebSocket() async {
    if (_isConnected) return;
    
    try {
      final token = await authService.getAccessToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }
      
      _channel = WebSocketChannel.connect(
        Uri.parse('ws://$serverUrl/ws?token=$token'),
      );

      _channel!.stream.listen(
        (message) {
          final data = jsonDecode(message);
          if (data['type'] == 'notification') {
            final notification = app_notification.Notification(
              id: data['id'],
              title: data['title'],
              timestamp: data['timestamp'],
              captures: List<String>.from(data['captures']),
              eventType: data['event_type'] ?? 'unknown',
              duration: data['duration'] ?? 0,
            );
            
            DatabaseHelper.instance.insertNotification(notification);
            onNewNotification(notification);
            
            // Show push notification if the event was triggered by doorbell
            if (notification.eventType == 'doorbell') {
              _showPushNotification(notification);
            }
          }
        },
        onDone: () {
          _isConnected = false;
          Timer(const Duration(seconds: 5), connectWebSocket);
        },
        onError: (error) {
          _isConnected = false;
          Timer(const Duration(seconds: 5), connectWebSocket);
        },
      );
      
      _isConnected = true;
    } catch (e) {
      _isConnected = false;
      Timer(const Duration(seconds: 5), connectWebSocket);
    }
  }

  Future<void> _showPushNotification(app_notification.Notification notification) async {
    const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
      'doorbell_channel',
      'Doorbell Notifications',
      channelDescription: 'Notifications for doorbell events',
      importance: Importance.high,
      priority: Priority.high,
      showWhen: true,
    );
    
    const NotificationDetails platformDetails = NotificationDetails(android: androidDetails);
    
    await _notificationsPlugin.show(
      notification.id,
      'Doorbell',
      'Someone is at your door',
      platformDetails,
      payload: notification.id.toString(),
    );
  }

  void dispose() {
    _channel?.sink.close();
  }

  Future<String> startStream() async {
    try {
      final headers = await _getAuthHeaders();
      final response = await http.get(
        Uri.parse('$serverUrl/api/stream/start'),
        headers: headers,
      );
      
      if (response.statusCode == 200) {
        final token = await authService.getAccessToken();
        return '$serverUrl/api/stream?token=$token';
      }
    } catch (e) {
      print('Failed to start stream: $e');
    }
    
    return '';
  }

  Future<void> controlIndicatorLight(bool enable) async {
    try {
      final headers = await _getAuthHeaders();
      await http.post(
        Uri.parse('$serverUrl/api/indicators/light'),
        headers: headers,
        body: jsonEncode({'enable': enable}),
      );
    } catch (e) {
      print('Failed to control indicator light: $e');
    }
  }

  Future<bool> deleteRecording(int id) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await http.delete(
        Uri.parse('$serverUrl/api/recordings/$id'),
        headers: headers,
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('Failed to delete recording: $e');
      return false;
    }
  }

  Future<Settings> getSettings() async {
    try {
      final headers = await _getAuthHeaders();
      final response = await http.get(
        Uri.parse('$serverUrl/api/settings'),
        headers: headers,
      );
      
      if (response.statusCode == 200) {
        return Settings.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      print('Failed to get settings: $e');
    }
    
    // Default settings if API call fails
    return Settings(
      indicatorLight: {'enabled': true, 'brightness': 75},
      camera: {
        'bitrate': 1000000,
        'stop_motion': {'interval': 0.5, 'duration': 300.0, 'auto_stop': true}
      },
      motionSensor: {
        'enabled': true,
        'sensitivity': 75,
        'detection_distance': 100, // in cm
        'debounce': 0.5, 
        'polling_rate': 0.1
      },
      doorbell: {
        'enabled': true,
        'notification_sound': true,
        'debounce': 0.5, 
        'polling_rate': 0.1
      },
    );
  }

  Future<bool> updateSettings(Settings settings) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await http.post(
        Uri.parse('$serverUrl/api/settings'),
        headers: headers,
        body: jsonEncode(settings.toJson()),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('Failed to update settings: $e');
      return false;
    }
  }
}