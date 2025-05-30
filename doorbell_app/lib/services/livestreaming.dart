import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:get_it/get_it.dart';
import 'signaling.dart';
import 'webrtc_streaming.dart';
import '../services/auth_service.dart';
import '../config/env_config.dart';

enum StreamingState {
  disconnected,
  connectingToSignaling,
  joiningRoom,
  creatingConnection,
  connected,
  error,
  refreshingToken,
}

class LiveStreamingService {
  final WebSocketSignalingService _signalingService;
  final WebRTCStreamingService _webrtcService;
  final String roomId;

  StreamingState _state = StreamingState.disconnected;
  String _statusMessage = "Disconnected";
  bool _hasBroadcaster = false;
  String? _lastWsUrl;

  AuthService get _authService => GetIt.instance<AuthService>();

  void Function(StreamingState state, String message)? onStateChanged;
  void Function(MediaStream stream)? onStreamReceived;
  void Function(String error)? onError;

  LiveStreamingService({
    required WebSocketSignalingService signalingService,
    required WebRTCStreamingService webrtcService,
    required this.roomId,
  }) : _signalingService = signalingService,
       _webrtcService = webrtcService {
    _setupCallbacks();
  }

  StreamingState get state => _state;
  String get statusMessage => _statusMessage;
  bool get isConnected => _state == StreamingState.connected;
  bool get isConnecting => _state != StreamingState.disconnected &&
                          _state != StreamingState.connected &&
                          _state != StreamingState.error &&
                          _state != StreamingState.refreshingToken;

  void _setState(StreamingState newState, String message) {
    if (_state != newState || _statusMessage != message) {
      _state = newState;
      _statusMessage = message;
      onStateChanged?.call(_state, _statusMessage);
    }
  }

  void _setupCallbacks() {
    _signalingService.onStateChanged = (signalingState) {
      switch (signalingState) {
        case SignalingState.connecting:
          if (_state != StreamingState.refreshingToken) {
            _setState(StreamingState.connectingToSignaling, "Connecting to signaling server...");
          }
          break;
        case SignalingState.connected:
          _joinRoom();
          break;
        case SignalingState.error:
          if (_state != StreamingState.refreshingToken) {
            _setState(StreamingState.error, "Signaling server error");
          }
          break;
        case SignalingState.tokenExpired:
          _handleTokenExpired();
          break;
        case SignalingState.disconnected:
          if (_state != StreamingState.disconnected && _state != StreamingState.refreshingToken) {
            _setState(StreamingState.disconnected, "Signaling server disconnected");
          }
          break;
      }
    };

    _signalingService.onMessage = (message) {
      _handleSignalingMessage(message);
    };

    _signalingService.onError = (error) {
      if (_state != StreamingState.refreshingToken) {
        onError?.call(error);
        _setState(StreamingState.error, "Signaling error");
      }
    };

    _signalingService.onTokenExpired = () {
      _handleTokenExpired();
    };

    _webrtcService.onStateChanged = (webrtcState) {
      switch (webrtcState) {
        case WebRTCState.connecting:
          _setState(StreamingState.creatingConnection, "Creating connection...");
          break;
        case WebRTCState.connected:
          _setState(StreamingState.connected, "Connected");
          break;
        case WebRTCState.failed:
          _setState(StreamingState.error, "Connection failed");
          break;
        case WebRTCState.disconnected:
          if (_state == StreamingState.connected) {
            _setState(StreamingState.error, "Connection lost");
          }
          break;
      }
    };

    _webrtcService.onStreamReceived = (stream) {
      onStreamReceived?.call(stream);
    };

    _webrtcService.onIceCandidate = (candidate) {
      _signalingService.sendIceCandidate(roomId, {
        'candidate': candidate.candidate,
        'sdpMid': candidate.sdpMid,
        'sdpMLineIndex': candidate.sdpMLineIndex,
      });
    };

    _webrtcService.onError = (error) {
      onError?.call(error);
      _setState(StreamingState.error, "WebRTC error");
    };
  }

  Future<void> _handleTokenExpired() async {
    print("TOKEN EXPIRED - REFRESHING AND RECONNECTING");
    _setState(StreamingState.refreshingToken, "Refreshing authentication...");

    try {
      _signalingService.disconnect();
      _webrtcService.disconnect();

      await _authService.refreshToken();
      print("TOKEN REFRESHED SUCCESSFULLY");

      print("RECONNECTING WITH NEW TOKEN");
      await connect();
    } catch (e) {
      print("FAILED TO REFRESH TOKEN: $e");
      _setState(StreamingState.error, "Authentication failed");
      onError?.call("Failed to refresh authentication: $e");
    }
  }

  void _joinRoom() {
    _setState(StreamingState.joiningRoom, "Joining room...");
    _signalingService.joinRoom(roomId, role: 'viewer');
  }

  Future<void> _handleSignalingMessage(SignalingMessage message) async {
    final messageType = message.type;
    final data = message.data;

    switch (messageType) {
      case 'joined':
        print("JOINED ROOM: ${data['roomId']}");
        _setState(StreamingState.joiningRoom, "Joined room ${data['roomId']}");

        final clients = data['clients'] as List;
        _hasBroadcaster = clients.any((client) => client['role'] == 'broadcaster');

        if (_hasBroadcaster) {
          print("BROADCASTER FOUND, CREATING PEER CONNECTION");
          await _createPeerConnection();
        } else {
          print("NO BROADCASTER IN ROOM, WAITING");
          _setState(StreamingState.joiningRoom, "Waiting for broadcaster to join");
        }
        break;

      case 'client-joined':
        print("CLIENT JOINED: ${data['role']} - ${data['clientId']}");
        if (data['role'] == 'broadcaster' && !_hasBroadcaster) {
          _hasBroadcaster = true;
          print("BROADCASTER JOINED, CREATING PEER CONNECTION");
          await _createPeerConnection();
        }
        break;

      case 'answer':
        if (data['target'] == _signalingService.clientId) {
          print("RECEIVED SDP ANSWER FROM BROADCASTER");
          await _webrtcService.setRemoteDescription(data['sdp'], 'answer');
        }
        break;

      case 'ice-candidate':
        if (data['target'] == _signalingService.clientId) {
          print("RECEIVED ICE CANDIDATE FROM BROADCASTER");
          await _webrtcService.addIceCandidate(data['candidate']);
        }
        break;

      default:
        print("UNHANDLED MESSAGE TYPE: $messageType");
    }
  }

  Future<void> _createPeerConnection() async {
    final clientId = _signalingService.clientId;
    if (clientId == null) {
      onError?.call("No client ID available");
      return;
    }

    try {
      await _webrtcService.initializePeerConnection(clientId);
      final offerSdp = await _webrtcService.createOffer();

      print("SENDING MODIFIED OFFER TO BROADCASTER");
      _signalingService.sendOffer(roomId, offerSdp);
    } catch (e) {
      print("ERROR CREATING PEER CONNECTION: $e");
      _setState(StreamingState.error, "Failed to create connection");
    }
  }

  Future<void> connect() async {
    if (isConnecting || isConnected) return;

    final accessToken = _authService.credentials?.accessToken;
    if (accessToken == null) {
      onError?.call("No authentication token available");
      _setState(StreamingState.error, "No authentication token");
      return;
    }

    final wsUrl = "${EnvConfig.signalingWebsocket}?token=$accessToken";
    _lastWsUrl = wsUrl;
    await _signalingService.connect(wsUrl);
  }

  void disconnect() {
    _webrtcService.disconnect();
    _signalingService.disconnect();
    _hasBroadcaster = false;
    _lastWsUrl = null;
    _setState(StreamingState.disconnected, "Disconnected");
  }

  void dispose() {
    disconnect();
    _signalingService.dispose();
    _webrtcService.dispose();
    onStateChanged = null;
    onStreamReceived = null;
    onError = null;
  }
}
