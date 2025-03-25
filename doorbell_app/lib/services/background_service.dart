import 'dart:async';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'database_helper.dart';
import 'auth_service.dart';
import 'api_service.dart';

void initBackgroundService() async {
  final service = FlutterBackgroundService();
  
  await service.configure(
    androidConfiguration: AndroidConfiguration(
      onStart: onStart,
      autoStart: true,
      isForegroundMode: true,
      notificationChannelId: 'doorbell_app_channel',
      initialNotificationTitle: 'Doorbell App',
      initialNotificationContent: 'Running in the background',
      foregroundServiceNotificationId: 888,
    ),
    iosConfiguration: IosConfiguration(
      autoStart: true,
      onForeground: onStart,
      onBackground: onIosBackground,
    ),
  );
  
  service.startService();
}

@pragma('vm:entry-point')
bool onIosBackground(ServiceInstance service) {
  return true;
}

@pragma('vm:entry-point')
void onStart(ServiceInstance service) {
  service.on('stopService').listen((event) {
    service.stopSelf();
  });
  
  Timer.periodic(Duration(seconds: 30), (timer) async {
    final serverUrl = DatabaseHelper.serverUrl;
    
    final authService = AuthService(serverUrl: serverUrl);
    final isLoggedIn = await authService.isLoggedIn();
    if (!isLoggedIn) return;
    
    final apiService = ApiService(
      serverUrl: serverUrl,
      authService: authService,
      onNewNotification: (notification) {
        service.invoke('newNotification', {
          'id': notification.id,
          'title': notification.title,
        });
      },
    );
    
    try {
      await apiService.syncNotifications();
      apiService.connectWebSocket();
    } catch (e) {
      print('Background sync error: $e');
    }
  });
}
