import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import '../models/user_credentials.dart';

class AuthService {
  final String serverUrl;
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  UserCredentials? _credentials;

  AuthService({required this.serverUrl});

  Future<bool> isLoggedIn() async {
    final accessToken = await _secureStorage.read(key: 'access_token');
    final expiresAtString = await _secureStorage.read(key: 'expires_at');
    
    if (accessToken != null && expiresAtString != null) {
      final expiresAt = DateTime.parse(expiresAtString);
      _credentials = UserCredentials(
        accessToken: accessToken, 
        expiresAt: expiresAt
      );
      
      return !_credentials!.isExpired;
    }
    
    return false;
  }

  Future<bool> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/auth'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final accessToken = data['access_token'];
        final expiresAt = DateTime.now().add(Duration(minutes: 15));
        
        await _secureStorage.write(key: 'access_token', value: accessToken);
        await _secureStorage.write(key: 'expires_at', value: expiresAt.toIso8601String());
        
        _credentials = UserCredentials(
          accessToken: accessToken, 
          expiresAt: expiresAt
        );
        
        return true;
      }
      
      return false;
    } catch (e) {
      print('Login error: $e');
      return false;
    }
  }

  Future<bool> refreshToken() async {
    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/auth/refresh'),
        headers: {'Cookie': 'refresh_token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final accessToken = data['access_token'];
        final expiresAt = DateTime.now().add(Duration(minutes: 15));
        
        await _secureStorage.write(key: 'access_token', value: accessToken);
        await _secureStorage.write(key: 'expires_at', value: expiresAt.toIso8601String());
        
        _credentials = UserCredentials(
          accessToken: accessToken, 
          expiresAt: expiresAt
        );
        
        return true;
      }
      
      return false;
    } catch (e) {
      print('Token refresh error: $e');
      return false;
    }
  }

  Future<String?> getAccessToken() async {
    if (_credentials == null) {
      final isLogged = await isLoggedIn();
      if (!isLogged) {
        return null;
      }
    }
    
    if (_credentials!.isExpired) {
      final refreshed = await refreshToken();
      if (!refreshed) {
        return null;
      }
    }
    
    return _credentials!.accessToken;
  }

  Future<void> logout() async {
    await _secureStorage.delete(key: 'access_token');
    await _secureStorage.delete(key: 'expires_at');
    _credentials = null;
  }
}
