import 'package:doorbell_app/screens/in_app_notification.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:overlay_support/overlay_support.dart';
import '../main.dart';


class NotificationService {
  static final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  static final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();

  static Future<void> initialize() async {
    await Firebase.initializeApp();
    NotificationSettings settings = await _firebaseMessaging.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print('User granted permission');
    }

    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
    );

    await _localNotifications.initialize(
      initializationSettings,
      onDidReceiveNotificationResponse: (NotificationResponse response) {
        _handleNotificationTap(response.payload);
      },
    );
    const AndroidNotificationChannel channel = AndroidNotificationChannel(
      'doorbell_notifications',
      'Doorbell Notifications',
      description: 'Notifications for doorbell events',
      importance: Importance.high,
      enableVibration: true,
      playSound: true,
    );

    await _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);

    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
    RemoteMessage? initialMessage = await FirebaseMessaging.instance.getInitialMessage();
    if (initialMessage != null) {
      _handleNotificationTap(initialMessage);
    }
  }

  static Future<String?> getToken() async {
    return await _firebaseMessaging.getToken();
  }

  static void _handleForegroundMessage(RemoteMessage message) {
    showNotification(
      title: message.notification?.title ?? 'Doorbell Alert',
      body: message.notification?.body ?? 'New notification received',
      data: message.data,
    );
  }

  static void _handleNotificationTap(dynamic payload) {
    Navigator.of(navigatorKey.currentContext!).pushNamed('/notifications');
    print('Notification tapped: $payload');
  }

  static void showNotification({
    required String title,
    required String body,
    Map<String, dynamic>? data,
  }) {
    showOverlayNotification(
      (context) => InAppNotification(
        title: title,
        body: body,
        data: data,
        onTap: () {
          OverlaySupportEntry.of(context)?.dismiss();
          _handleNotificationTap(data);
        },
      ),
      duration: Duration(seconds: 4),
    );
  }
}
