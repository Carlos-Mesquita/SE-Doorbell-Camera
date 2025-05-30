import 'package:doorbell_app/config/env_config.dart';
import 'package:doorbell_app/firebase_options.dart';
import 'package:doorbell_app/screens/about_page.dart';
import 'package:doorbell_app/screens/dashboard_screen.dart';
import 'package:doorbell_app/screens/error_page.dart';
import 'package:doorbell_app/screens/live_stream_screen.dart';
import 'package:doorbell_app/screens/login_page.dart';
import 'package:doorbell_app/screens/notification_list.dart';
import 'package:doorbell_app/screens/settings_screen.dart';
import 'package:doorbell_app/services/service_locator.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:doorbell_app/services/fcm_service.dart';
import 'package:flutter/services.dart';
import 'package:overlay_support/overlay_support.dart';

final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  SystemChrome.setEnabledSystemUIMode(
    SystemUiMode.immersiveSticky,
    overlays: [SystemUiOverlay.top],
  );

  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  await NotificationService.initialize();
  await EnvConfig.init(env: Environment.local);

  setupServiceLocator();
  runApp(const DoorbellApp());
}

class DoorbellApp extends StatelessWidget {
  const DoorbellApp({super.key});

  @override
  Widget build(BuildContext context) {
    return OverlaySupport.global(
      child: MaterialApp(
        navigatorKey: navigatorKey,
        initialRoute: '/login',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xff3b82f6),
            brightness: Brightness.dark,
            surface: const Color(0xff1e293b),
          ),

          cardTheme: CardTheme(
            color: const Color(0xff1e293b),
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),

          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xff1e293b),
            foregroundColor: Color(0xfff1f5f9),
            elevation: 0,
          ),

          textTheme: const TextTheme(
            headlineLarge: TextStyle(color: Color(0xfff1f5f9)),
            headlineMedium: TextStyle(color: Color(0xfff1f5f9)),
            bodyLarge: TextStyle(color: Color(0xffe2e8f0)),
            bodyMedium: TextStyle(color: Color(0xffcbd5e1)),
          ),

          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xff3b82f6),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),

          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: const Color(0xff374151),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
            hintStyle: const TextStyle(color: Color(0xff9ca3af)),
          ),
        ),
        onGenerateRoute: (settings) {
          switch (settings.name) {
            case '/login':
              return MaterialPageRoute(builder: (_) => const LoginPage());
            case '/home':
              return MaterialPageRoute(builder: (_) => const DashboardScreen());
            case '/settings':
              return MaterialPageRoute(builder: (_) => SettingsScreen());
            case '/notifications':
              return MaterialPageRoute(
                builder: (_) => NotificationListScreen(),
              );
            case '/live':
              return MaterialPageRoute(builder: (_) => LiveStreamScreen());
            case '/about':
              return MaterialPageRoute(builder: (_) => const AboutPage());
            case '/error':
              final String errorMessage =
                  settings.arguments as String? ?? "An unknown error occurred.";
              return MaterialPageRoute(
                builder: (_) => ErrorPage(errorMessage: errorMessage),
              );
            default:
              return MaterialPageRoute(
                builder:
                    (_) => const ErrorPage(errorMessage: "Page not found."),
              );
          }
        },
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
