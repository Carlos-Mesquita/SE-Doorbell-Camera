import 'package:flutter/material.dart';
import 'services/background_service.dart';
import 'screens/splash.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  initBackgroundService();
  
  runApp(const DoorbellApp());
}

class DoorbellApp extends StatelessWidget {
  const DoorbellApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Doorbell App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const SplashScreen(),
    );
  }
}