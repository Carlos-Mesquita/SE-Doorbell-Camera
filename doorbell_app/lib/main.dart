

//@pragma('vm:entry-point')
//Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
 // await FirebaseMessagingService.handleBackgroundMessage(message);
//}

//final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

import 'package:doorbell_app/config/env_config.dart';
import 'package:doorbell_app/firebase_options.dart';
import 'package:doorbell_app/screens/login_page.dart';
import 'package:doorbell_app/services/service_locator.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  //FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  await EnvConfig.init(env: Environment.local);
  setupServiceLocator();
  final messagingService = serviceLocator<FirebaseMessagingService>();
  //await messagingService.initialize(navigatorKey);

  //serviceLocator<NotificationNavigator>().setNavigatorKey(navigatorKey);

  runApp(DoorbellApp());
}

class _firebaseMessagingBackgroundHandler {
}

class FirebaseMessagingService {
}

class DoorbellApp extends StatelessWidget {
  const DoorbellApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
     // navigatorKey: navigatorKey,
      initialRoute: '/login',
      onGenerateRoute: (settings) {
       // final authService = serviceLocator<AuthService>();
        //final apiService = serviceLocator<ApiService>();

        switch (settings.name) {
          case '/login':
            return MaterialPageRoute(builder: (_) => const LoginPage());
          /*case '/home':
            return MaterialPageRoute(builder: (_) => const DashboardScreen());
          case '/settings':
            return MaterialPageRoute(builder: (_) => SettingsScreen());
          case '/stopmotion':
            final Map<String, dynamic>? args = settings.arguments as Map<String, dynamic>?;
            return MaterialPageRoute(
              builder: (_) => StopMotionViewerScreen(
                apiService: apiService,
                initialNotificationId: args?['notification_id'] as String?,
                initialRpiEventId: args?['rpi_event_id'] as String?,
              ),
            );
          case '/live':
            final accessToken = authService.credentials?.accessToken;
            if (!authService.isAuthenticated || accessToken == null) {
                 return MaterialPageRoute(builder: (_) => const LoginPage());
            }
            return MaterialPageRoute(
              builder: (_) => LiveStreamScreen(authToken: accessToken),
            );
          case '/about':
            return MaterialPageRoute(builder: (_) => const AboutPage());
          case '/error':
            final String errorMessage = settings.arguments as String? ?? "An unknown error occurred.";
            return MaterialPageRoute(builder: (_) => ErrorPage(errorMessage: errorMessage));
          default:
            return MaterialPageRoute(builder: (_) => const ErrorPage(errorMessage: "Page not found."));*/
        }
      },
      debugShowCheckedModeBanner: false,
    );
  }
}
