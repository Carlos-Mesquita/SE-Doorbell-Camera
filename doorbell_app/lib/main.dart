import 'package:doorbell_app/screens/about_page.dart';
import 'package:doorbell_app/screens/dashboard_screen.dart';
import 'package:doorbell_app/screens/error_page.dart';
import 'package:doorbell_app/screens/live_stream_screen.dart';
import 'package:doorbell_app/screens/login_page.dart';
import 'package:doorbell_app/screens/settings_screen.dart';
import 'package:flutter/material.dart';
import 'screens/stop_motion_viewer_screen.dart';

void main() {
  runApp(const DoorbellApp());
}

class DoorbellApp extends StatelessWidget {
  const DoorbellApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: const StopMotionViewerScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
