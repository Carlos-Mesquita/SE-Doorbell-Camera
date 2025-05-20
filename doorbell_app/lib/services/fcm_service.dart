import 'dart:convert';
import 'package:doorbell_app/firebase_options.dart';
import 'package:doorbell_app/services/notification_nav.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';
import 'package:doorbell_app/services/service_locator.dart';
/*
class FirebaseMessagingService {
  static final FirebaseMessagingService _instance = FirebaseMessagingService._internal();
  factory FirebaseMessagingService() => _instance;
  FirebaseMessagingService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _notificationsPlugin = FlutterLocalNotificationsPlugin();

  Future<void> initialize(GlobalKey<NavigatorState> navigatorKey) async {
    await _initializeLocalNotifications(navigatorKey);

    NotificationSettings settings = await _messaging.requestPermission(
      alert: true, badge: true, sound: true, provisional: false,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      FirebaseMessaging.onMessage.listen(handleForegroundMessage);
      FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationOpenedAppFromBackground);

      RemoteMessage? initialMessage = await _messaging.getInitialMessage();
      if (initialMessage != null) {
        _handleInitialMessageFromTerminated(initialMessage);
      }
    }
  }

  Future<void> _initializeLocalNotifications(GlobalKey<NavigatorState> navigatorKey) async {
    const AndroidInitializationSettings androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const DarwinInitializationSettings iosSettings = DarwinInitializationSettings();
    const InitializationSettings initSettings = InitializationSettings(android: androidSettings, iOS: iosSettings);

    await _notificationsPlugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (NotificationResponse response) {
        if (response.payload != null && response.payload!.isNotEmpty) {
          try {
            final Map<String, dynamic> data = jsonDecode(response.payload!);
            //serviceLocator<NotificationNavigator>().handleNotificationNavigation(data, navigatorKey: navigatorKey);
          } catch (e) {
            print('Error parsing local notification payload: $e');
          }
        }
      },
    );
    await _createNotificationChannels();
  }

  Future<void> _createNotificationChannels() async {
    const AndroidNotificationChannel channel = AndroidNotificationChannel(
      'doorbell_events_channel_id',
      'Doorbell Events',
      description: 'Notifications for doorbell events.',
      importance: Importance.max,
      playSound: true,
    );
    await _notificationsPlugin
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  void handleForegroundMessage(RemoteMessage message) {
    print('Foreground FCM: ${message.messageId}');
    if (message.data.isNotEmpty || message.notification != null) {
      showLocalNotification(message);
    }
  }

  void _handleInitialMessageFromTerminated(RemoteMessage message) {
    print('App opened from FCM (Terminated): ${message.messageId}');
    final Map<String, dynamic> data = Map<String, dynamic>.from(message.data);
    //serviceLocator<NotificationNavigator>().handleNotificationNavigation(data);
  }

  void _handleNotificationOpenedAppFromBackground(RemoteMessage message) {
    print('App opened from FCM (Background): ${message.messageId}');
    final Map<String, dynamic> data = Map<String, dynamic>.from(message.data);
    //serviceLocator<NotificationNavigator>().handleNotificationNavigation(data);
  }

  Future<void> showLocalNotification(RemoteMessage message) async {
    final Map<String, dynamic> data = Map<String, dynamic>.from(message.data);
    final String title = data['title'] ?? message.notification?.title ?? 'Doorbell Alert';
    final String body = data['type_str'] != null
                        ? 'Event: ${data['type_str']?.replaceAll('_', ' ')}'
                        : (message.notification?.body ?? 'A new event occurred.');
    final String payloadJson = jsonEncode(data);

    await _notificationsPlugin.show(
      message.hashCode,
      title,
      body,
      NotificationDetails(
        android: const AndroidNotificationDetails(
          'doorbell_events_channel_id',
          'Doorbell Events',
          channelDescription: 'Notifications for doorbell events.',
          icon: '@mipmap/ic_launcher',
          importance: Importance.max,
          priority: Priority.high,
        ),
        iOS: const DarwinNotificationDetails(presentAlert: true, presentBadge: true, presentSound: true),
      ),
      payload: payloadJson,
    );
  }

  Future<String?> getToken() async => await _messaging.getToken();
  Future<void> deleteToken() async => await _messaging.deleteToken();

  static Future<void> handleBackgroundMessage(RemoteMessage message) async {
    await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
    print('Background FCM (static handler): ${message.messageId}');

    final FlutterLocalNotificationsPlugin notificationsPlugin = FlutterLocalNotificationsPlugin();
    const AndroidNotificationChannel channel = AndroidNotificationChannel(
      'doorbell_events_channel_id',
      'Doorbell Events',
      description: 'Notifications for doorbell events.',
      importance: Importance.max,
      playSound: true,
    );
    await notificationsPlugin
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);

    final Map<String, dynamic> data = Map<String, dynamic>.from(message.data);
    final String title = data['title'] ?? message.notification?.title ?? 'Doorbell Alert';
    final String body = data['type_str'] != null
                        ? 'Event: ${data['type_str']?.replaceAll('_', ' ')}'
                        : (message.notification?.body ?? 'A new event occurred.');

    final String payloadJson = jsonEncode(data);

    await notificationsPlugin.show(
      message.hashCode,
      title,
      body,
      NotificationDetails(
        android: const AndroidNotificationDetails(
          'doorbell_events_channel_id',
          'Doorbell Events',
          channelDescription: 'Notifications for doorbell events.',
          icon: '@mipmap/ic_launcher',
          importance: Importance.max,
          priority: Priority.high,
        ),
        iOS: const DarwinNotificationDetails(presentAlert: true, presentBadge: true, presentSound: true),
      ),
      payload: payloadJson,
    );
  }
}
*/
