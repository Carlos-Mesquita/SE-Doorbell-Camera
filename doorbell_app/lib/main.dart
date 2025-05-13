import 'package:doorbell_app/config/env_config.dart';
import 'package:doorbell_app/firebase_options.dart';
import 'package:doorbell_app/screens/about_page.dart';
import 'package:doorbell_app/screens/dashboard_screen.dart';
import 'package:doorbell_app/screens/error_page.dart';
import 'package:doorbell_app/screens/live_stream_screen.dart';
import 'package:doorbell_app/screens/login_page.dart';
import 'package:doorbell_app/screens/settings_screen.dart';
import 'package:doorbell_app/screens/stop_motion_viewer_screen.dart';
import 'package:doorbell_app/services/auth_service.dart';
import 'package:doorbell_app/services/fcm_service.dart';
import 'package:doorbell_app/services/service_locator.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';


@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await FirebaseMessagingService.handleBackgroundMessage(message);
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  final messagingService = FirebaseMessagingService();
  await messagingService.initialize();
  serviceLocator.registerSingleton<FirebaseMessagingService>(messagingService);

  await EnvConfig.init(env: Environment.local);
  setupServiceLocator();
  runApp(const DoorbellApp());
}

class DoorbellApp extends StatelessWidget {
  const DoorbellApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      initialRoute: '/login',
      onGenerateRoute: (settings) {
        final authService = serviceLocator<AuthService>();

        switch (settings.name) {
          case '/login':
            return MaterialPageRoute(builder: (_) => const LoginPage());
          case '/home':
            return MaterialPageRoute(builder: (_) => const DashboardScreen());
          case '/settings':
            return MaterialPageRoute(builder: (_) => const SettingsScreen());
          case '/stopmotion':
            return MaterialPageRoute(
              builder: (_) => const StopMotionViewerScreen(),
            );
          case '/live':
            return MaterialPageRoute(
              builder: (_) => LiveStreamScreen(
                authToken: authService.credentials!.accessToken,
              ),
            );
          case '/about':
            return MaterialPageRoute(builder: (_) => const AboutPage());
          case '/error':
            return MaterialPageRoute(builder: (_) => const ErrorPage());
          default:
            return MaterialPageRoute(builder: (_) => const ErrorPage());
        }
      },
      debugShowCheckedModeBanner: false,
    );
  }
}
