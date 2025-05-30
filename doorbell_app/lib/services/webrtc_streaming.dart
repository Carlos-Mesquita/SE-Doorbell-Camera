import 'dart:convert';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:crypto/crypto.dart';

enum WebRTCState {
  disconnected,
  connecting,
  connected,
  failed,
}

class WebRTCStreamingService {
  RTCPeerConnection? _peerConnection;
  WebRTCState _state = WebRTCState.disconnected;

  // Configuration
  final String turnHost;
  final String? turnSecret;

  // Callbacks
  void Function(WebRTCState state)? onStateChanged;
  void Function(MediaStream stream)? onStreamReceived;
  void Function(RTCIceCandidate candidate)? onIceCandidate;
  void Function(String error)? onError;

  WebRTCStreamingService({
    required this.turnHost,
    this.turnSecret,
  });

  WebRTCState get state => _state;
  bool get isConnected => _state == WebRTCState.connected;
  RTCPeerConnection? get peerConnection => _peerConnection;

  void _setState(WebRTCState newState) {
    if (_state != newState) {
      _state = newState;
      onStateChanged?.call(_state);
    }
  }

  Map<String, String> _generateTurnCredentials(String usernameBasePart) {
    if (turnSecret == null) {
      throw Exception('TURN secret not configured');
    }

    final expiryTimestamp =
        (DateTime.now().millisecondsSinceEpoch / 1000).floor() + 24 * 3600;
    final usernameWithExpiry = "$expiryTimestamp:$usernameBasePart";

    print("TURN Auth: Generating creds for base='$usernameBasePart'");
    print("TURN Auth: String to HMAC: '$usernameWithExpiry'");

    final key = utf8.encode(turnSecret!);
    final bytes = utf8.encode(usernameWithExpiry);
    final hmacSha1 = Hmac(sha1, key);
    final digest = hmacSha1.convert(bytes);
    final credential = base64.encode(digest.bytes);

    print("TURN Auth: Generated username='$usernameWithExpiry', credential='$credential'");
    return {'username': usernameWithExpiry, 'credential': credential};
  }

  Future<void> initializePeerConnection(String clientId) async {
    if (_peerConnection != null) {
      print("WARNING: Peer connection already exists");
      return;
    }

    try {
      _setState(WebRTCState.connecting);
      print("CREATING PEER CONNECTION");

      if (turnSecret == null) {
        throw Exception("TURN server credentials not configured");
      }

      final credentials = _generateTurnCredentials(clientId);
      print("GENERATED TURN CREDENTIALS: ${credentials['username']?.substring(0, 10)}...");

      final config = {
        'iceServers': [
          {
            'urls': [
              'turns:$turnHost:5349?transport=tcp',
              'turns:$turnHost:5349?transport=udp'
            ],
            'username': credentials['username'],
            'credential': credentials['credential'],
            'credentialType': 'password',
          },
        ],
      };

      print("ICE SERVER CONFIG: Forcing RELAY mode for CGNAT environment");

      final offerSdpConstraints = {
        'mandatory': {'OfferToReceiveAudio': false, 'OfferToReceiveVideo': true},
        'optional': [],
      };

      print("CREATING RTCPeerConnection WITH CUSTOM OPTIONS - AUDIO DISABLED");
      _peerConnection = await createPeerConnection(config, offerSdpConstraints);

      _setupPeerConnectionCallbacks();

    } catch (e) {
      print("ERROR CREATING PEER CONNECTION: $e");
      onError?.call("Failed to create peer connection: $e");
      _setState(WebRTCState.failed);
    }
  }

  void _setupPeerConnectionCallbacks() {
    if (_peerConnection == null) return;

    _peerConnection!.onIceCandidate = (candidate) {
      print("ICE CANDIDATE GENERATED: ${candidate.candidate?.substring(0, 30)}...");
      onIceCandidate?.call(candidate);
    };

    _peerConnection!.onIceGatheringState = (state) {
      print("ICE GATHERING STATE: $state");
    };

    _peerConnection!.onIceConnectionState = (state) {
      print("ICE CONNECTION STATE: $state");
    };

    _peerConnection!.onTrack = (event) {
      if (event.track.kind == 'video') {
        print("VIDEO STREAM RECEIVED: Track ID ${event.track.id}");
        _setState(WebRTCState.connected);
        onStreamReceived?.call(event.streams[0]);
      } else {
        print("IGNORING NON-VIDEO TRACK: ${event.track.kind} - ${event.track.id}");
      }
    };

    _peerConnection!.onConnectionState = (state) {
      print('CONNECTION STATE CHANGE: $state');
      switch (state) {
        case RTCPeerConnectionState.RTCPeerConnectionStateConnected:
          print('WEBRTC CONNECTION ESTABLISHED');
          _setState(WebRTCState.connected);
          break;
        case RTCPeerConnectionState.RTCPeerConnectionStateFailed:
        case RTCPeerConnectionState.RTCPeerConnectionStateDisconnected:
          print('WEBRTC CONNECTION FAILED OR DISCONNECTED');
          _setState(WebRTCState.failed);
          break;
        default:
          break;
      }
    };
  }

  Future<String> createOffer() async {
    if (_peerConnection == null) {
      throw Exception("Peer connection not created");
    }

    print("CREATING OFFER");
    final offerSdpConstraints = {
      'mandatory': {'OfferToReceiveAudio': false, 'OfferToReceiveVideo': true},
      'optional': [],
    };

    final offer = await _peerConnection!.createOffer(offerSdpConstraints);

    // Remove audio sections from SDP
    String modifiedSdp = offer.sdp!;
    print("ORIGINAL SDP SECTIONS: ${modifiedSdp.split('m=').length - 1} sections");

    final audioSectionRegExp = RegExp(r'm=audio.*?(m=|$)', dotAll: true);
    modifiedSdp = modifiedSdp.replaceAll(audioSectionRegExp, '');
    modifiedSdp = modifiedSdp.replaceAll(RegExp(r'a=rtpmap:.*?opus.*?\r\n'), '');

    final modifiedOffer = RTCSessionDescription(modifiedSdp, 'offer');

    print("SETTING LOCAL DESCRIPTION WITH MODIFIED SDP (AUDIO DISABLED)");
    await _peerConnection!.setLocalDescription(modifiedOffer);

    return modifiedSdp;
  }

  Future<void> setRemoteDescription(String sdp, String type) async {
    if (_peerConnection == null) {
      throw Exception("Peer connection not created");
    }

    print("SETTING REMOTE DESCRIPTION: $type");
    final description = RTCSessionDescription(sdp, type);
    await _peerConnection!.setRemoteDescription(description);
  }

  Future<void> addIceCandidate(Map<String, dynamic> candidateData) async {
    if (_peerConnection == null) {
      throw Exception("Peer connection not created");
    }

    print("ADDING ICE CANDIDATE");
    final candidate = RTCIceCandidate(
      candidateData['candidate'],
      candidateData['sdpMid'],
      candidateData['sdpMLineIndex'],
    );
    await _peerConnection!.addCandidate(candidate);
  }

  void disconnect() {
    _peerConnection?.close();
    _peerConnection = null;
    _setState(WebRTCState.disconnected);
  }

  void dispose() {
    disconnect();
    onStateChanged = null;
    onStreamReceived = null;
    onIceCandidate = null;
    onError = null;
  }
}
