import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class FirebaseMessagingService {
  static final FirebaseMessagingService _instance = FirebaseMessagingService._internal();

  factory FirebaseMessagingService() => _instance;

  FirebaseMessagingService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _notificationsPlugin = FlutterLocalNotificationsPlugin();

  Future<void> initialize() async {
    NotificationSettings settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    // TODO: if user rejects permissions say that the app wont work properly

    FirebaseMessaging.onMessage.listen(handleForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(handleNotificationOpened);

    RemoteMessage? initialMessage = await FirebaseMessaging.instance.getInitialMessage();
    if (initialMessage != null) {
      handleInitialMessage(initialMessage);
    }
  }

  void handleForegroundMessage(RemoteMessage message) {
    print('Foreground message received: ${message.messageId}');

    if (message.notification != null) {
      showLocalNotification(message);
    }
  }

  void handleNotificationOpened(RemoteMessage message) {
    print('Notification opened app: ${message.messageId}');

    _handleNotificationAction(message.data.toString());
  }

  void handleInitialMessage(RemoteMessage message) {
    print('App opened from notification: ${message.messageId}');

    _handleNotificationAction(message.data.toString());
  }

  Future<void> showLocalNotification(RemoteMessage message) async {
    RemoteNotification? notification = message.notification;
    AndroidNotification? android = message.notification?.android;

    if (notification != null) {
      await _notificationsPlugin.show(
        notification.hashCode,
        notification.title ?? 'New Notification',
        notification.body ?? 'You have a new notification',
        NotificationDetails(
          android: AndroidNotificationDetails(
            'doorbell_events_channel',
            'Doorbell Events',
            channelDescription: 'Channel used to get doorbell events',
            icon: android?.smallIcon ?? '@mipmap/ic_launcher',
            importance: Importance.high,
            priority: Priority.high,
          ),
          iOS: const DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        ),
        payload: message.data.toString(),
      );
    }
  }

  void _handleNotificationAction(String? payload) {
    if (payload != null) {
      // TODO: navigate to app
    }
  }

  Future<String?> getToken() async {
    return await _messaging.getToken();
  }

  Future<void> deleteToken() async {
    return await _messaging.deleteToken();
  }

  static Future<void> handleBackgroundMessage(RemoteMessage message) async {
    await Firebase.initializeApp();

    final service = FirebaseMessagingService();
    await service.showLocalNotification(message);
  }
}
