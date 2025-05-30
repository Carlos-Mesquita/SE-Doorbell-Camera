import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

enum SignalingState {
  disconnected,
  connecting,
  connected,
  error,
  tokenExpired,
}

class SignalingMessage {
  final String type;
  final Map<String, dynamic> data;

  SignalingMessage({required this.type, required this.data});
}

class WebSocketSignalingService {
  WebSocketChannel? _channel;
  String? _clientId;
  SignalingState _state = SignalingState.disconnected;

  // Callbacks
  void Function(SignalingState state)? onStateChanged;
  void Function(SignalingMessage message)? onMessage;
  void Function(String error)? onError;
  void Function()? onTokenExpired;

  SignalingState get state => _state;
  String? get clientId => _clientId;
  bool get isConnected => _state == SignalingState.connected;

  void _setState(SignalingState newState) {
    if (_state != newState) {
      _state = newState;
      onStateChanged?.call(_state);
    }
  }

  Future<void> connect(String wsUrl) async {
    if (_state == SignalingState.connecting || _state == SignalingState.connected) {
      return;
    }

    try {
      _setState(SignalingState.connecting);
      print("CONNECTING TO SIGNALING SERVER: $wsUrl");

      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

      _channel!.stream.listen(
        (message) {
          final data = jsonDecode(message) as Map<String, dynamic>;
          print("SIGNALING MESSAGE RECEIVED: ${data['type']}");

          if (data['type'] == 'registered') {
            _clientId = data['clientId'];
            _setState(SignalingState.connected);
            print("REGISTERED WITH CLIENT ID: $_clientId");
          }

          onMessage?.call(SignalingMessage(
            type: data['type'],
            data: data,
          ));
        },
        onError: (error) {
          print("WEBSOCKET ERROR: $error");

          if (error.toString().contains('3000')) {
            print("TOKEN EXPIRED - CODE 3000 DETECTED");
            _setState(SignalingState.tokenExpired);
            onTokenExpired?.call();
          } else {
            onError?.call("Signaling server error: $error");
            _setState(SignalingState.error);
          }
        },
        onDone: () {
          print("WEBSOCKET CONNECTION CLOSED");
          _setState(SignalingState.disconnected);
        },
      );

    } catch (e) {
      print("ERROR CONNECTING TO SIGNALING SERVER: $e");
      onError?.call("Failed to connect: $e");
      _setState(SignalingState.error);
    }
  }

  void sendMessage(Map<String, dynamic> message) {
    if (_channel != null && _state == SignalingState.connected) {
      _channel!.sink.add(jsonEncode(message));
    } else {
      print("WARNING: Trying to send message when not connected");
    }
  }

  void joinRoom(String roomId, {String role = 'viewer'}) {
    if (_clientId == null) {
      print("ERROR: Cannot join room - not registered");
      return;
    }

    print("JOINING ROOM: $roomId AS $role");
    sendMessage({
      'type': 'join',
      'clientId': _clientId,
      'roomId': roomId,
      'role': role,
    });
  }

  void sendOffer(String roomId, String sdp) {
    sendMessage({
      'type': 'offer',
      'clientId': _clientId,
      'target': 'broadcaster',
      'roomId': roomId,
      'sdp': sdp,
    });
  }

  void sendIceCandidate(String roomId, Map<String, dynamic> candidate) {
    sendMessage({
      'type': 'ice-candidate',
      'clientId': _clientId,
      'target': 'broadcaster',
      'roomId': roomId,
      'candidate': candidate,
    });
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
    _clientId = null;
    _setState(SignalingState.disconnected);
  }

  void dispose() {
    disconnect();
    onStateChanged = null;
    onMessage = null;
    onError = null;
    onTokenExpired = null;
  }
}
