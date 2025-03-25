import 'package:flutter/material.dart';
import '../services/database_helper.dart';
import '../services/auth_service.dart';
import 'login.dart';
import 'main.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  _SplashScreenState createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkLoginStatus();
  }

  Future<void> _checkLoginStatus() async {
    final serverUrl = DatabaseHelper.serverUrl;

    final authService = AuthService(serverUrl: serverUrl);
    final isLoggedIn = await authService.isLoggedIn();
    
    if (isLoggedIn) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => MainScreen(
            serverUrl: serverUrl,
            authService: authService,
          ),
        ),
      );
    } else {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => LoginScreen(serverUrl: serverUrl),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            FlutterLogo(size: 100),
            SizedBox(height: 24),
            CircularProgressIndicator(),
            SizedBox(height: 24),
            Text('Loading...'),
          ],
        ),
      ),
    );
  }
}
