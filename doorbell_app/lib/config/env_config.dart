import 'package:flutter_dotenv/flutter_dotenv.dart';

enum Environment {
  local,
  staging,
}

class EnvConfig {
  static Future init({Environment env = Environment.staging}) async {
    String fileName;

    switch (env) {
      case Environment.local:
        fileName = '.env.local';
        break;
      case Environment.staging:
        fileName = '.env.staging';
        break;
    }

    await dotenv.load(fileName: fileName);
  }

  static String? get apiUrl => dotenv.env['API_URL'];
  static String get turnHost => dotenv.env['TURN_HOST'] ?? 'stun.l.google.com';
  static String? get turnSecret => dotenv.env['TURN_SECRET'];
  static String? get signalingWebsocket =>  dotenv.env['SIGNALING_WS'];
  static String? get captureBase  =>  dotenv.env['CAPTURES'];
}
