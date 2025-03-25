import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/notification.dart';
import '../models/settings.dart';
import 'auth_service.dart';
import 'database_helper.dart';

class ApiService {
  final String serverUrl;
  final AuthService authService;
  WebSocketChannel? _channel;
  bool _isConnected = false;
  final Function(Notification) onNewNotification;

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
          final newNotification = Notification(
            id: notification['id'],
            title: notification['title'],
            timestamp: notification['timestamp'],
            captures: List<String>.from(notification['captures']),
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
            final notification = Notification(
              id: data['id'],
              title: data['title'],
              timestamp: data['timestamp'],
              captures: List<String>.from(data['captures']),
            );
            
            DatabaseHelper.instance.insertNotification(notification);
            onNewNotification(notification);
          }
        },
        onDone: () {
          _isConnected = false;
          Timer(Duration(seconds: 5), connectWebSocket);
        },
        onError: (error) {
          _isConnected = false;
          Timer(Duration(seconds: 5), connectWebSocket);
        },
      );
      
      _isConnected = true;
    } catch (e) {
      _isConnected = false;
      Timer(Duration(seconds: 5), connectWebSocket);
    }
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
    
    
    return Settings(
      color: {'r': 50, 'g': 50, 'b': 50},
      camera: {
        'bitrate': 1000000,
        'stop_motion': {'interval': 1.0, 'duration': 10.0}
      },
      motionSensor: {'debounce': 0.5, 'polling_rate': 0.1},
      button: {'debounce': 0.5, 'polling_rate': 0.1},
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
