// notification_nav.dart (Fixed version)
import 'package:flutter/material.dart';

/*class NotificationNavigator {
  GlobalKey<NavigatorState>? _navigatorKey;
  DateTime? _lastNavigationTime;
  bool _isNavigating = false;

  NotificationNavigator();

  void setNavigatorKey(GlobalKey<NavigatorState> key) {
    _navigatorKey = key;
  }

  void handleNotificationNavigation(Map<String, dynamic> data, {GlobalKey<NavigatorState>? navigatorKey}) {
    final now = DateTime.now();
    if (_lastNavigationTime != null &&
        now.difference(_lastNavigationTime!).inMilliseconds < 500) {
      print('NotificationNavigator: Ignoring rapid navigation request');
      return;
    }

    if (_isNavigating) {
      print('NotificationNavigator: Already navigating. Request queued.');
      return;
    }

    _lastNavigationTime = now;
    _isNavigating = true;

    final GlobalKey<NavigatorState>? currentNavigatorKey = navigatorKey ?? _navigatorKey;

    if (currentNavigatorKey == null ||
        currentNavigatorKey.currentState == null ||
        !currentNavigatorKey.currentState!.mounted) {
      print('NotificationNavigator: NavigatorKey unavailable or not mounted. Cannot navigate.');
      _isNavigating = false;
      return;
    }

    final String? notificationType = data['type_str'] as String?;
    final String? notificationIdStr = data['id'] as String?;
    final String? rpiEventId = data['rpi_event_id'] as String?;

    String targetRoute = '/stopmotion';
    Object? arguments = {
      'notification_id': notificationIdStr,
      'rpi_event_id': rpiEventId,
      'notification_type': notificationType,
    };

    WidgetsBinding.instance.addPostFrameCallback((_) {
      try {
        if (currentNavigatorKey.currentState == null ||
            !currentNavigatorKey.currentState!.mounted) {
          print('NotificationNavigator: NavigatorKey no longer mounted in post frame callback. Cannot navigate.');
          _isNavigating = false;
          return;
        }

        currentNavigatorKey.currentState!.pushNamedAndRemoveUntil(
          targetRoute,
          (route) => false,
          arguments: arguments,
        );

        print('NotificationNavigator: Successfully navigated to $targetRoute');
      } catch (e) {
        print('NotificationNavigator: Error during navigation: $e');
      } finally {
        _isNavigating = false;
      }
    });
  }
}
*/
