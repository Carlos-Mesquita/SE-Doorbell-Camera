import 'dart:convert';
import 'package:doorbell_app/config/env_config.dart';
import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:crypto/crypto.dart';

class LiveStreamScreen extends StatefulWidget {
  final String authToken;
  const LiveStreamScreen({super.key, required this.authToken});

  @override
  LiveStreamScreenState createState() => LiveStreamScreenState();
}

class LiveStreamScreenState extends State<LiveStreamScreen> {
  final RTCVideoRenderer _remoteRenderer = RTCVideoRenderer();
  WebSocketChannel? _channel;
  RTCPeerConnection? _peerConnection;
  String? _clientId;
  bool _isConnected = false;
  bool _isConnecting = false;
  String _statusText = "Disconnected";
  String get _turnHost => EnvConfig.turnHost;
  String? get _turnSecret => EnvConfig.turnSecret;
  String get _signalingWebsocket => EnvConfig.signalingWebsocket;
  String _roomId = "camera-room-1";

  // Added for UI improvements
  bool _isFullScreen = false;
  bool _controlsVisible = true;

  @override
  void initState() {
    super.initState();
    initRenderers();
    _connect();
  }

  @override
  void dispose() {
    _disconnect();
    _remoteRenderer.dispose();
    super.dispose();
  }

  Future<void> initRenderers() async {
    await _remoteRenderer.initialize();
  }

  void _setStatus(String status) {
    setState(() {
      _statusText = status;
    });
  }

  void _connectToSignalingServer() {
    try {
      final wsUrl = "$_signalingWebsocket?token=${widget.authToken}";
      print("CONNECTING TO SIGNALING SERVER: $wsUrl");
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

      _setStatus("Connecting to signaling server...");

      _channel!.stream.listen(
        (message) {
          final data = jsonDecode(message);
          print("SIGNALING MESSAGE RECEIVED: ${data['type']}");
          _handleSignalingMessage(data);
        },
        onError: (error) {
          print("WEBSOCKET ERROR: $error");
          _setStatus("Signaling server error");
          _disconnect();
        },
        onDone: () {
          print("WEBSOCKET CONNECTION CLOSED");
          _setStatus("Signaling server disconnected");
          _disconnect();
        },
      );
    } catch (e) {
      print("ERROR CONNECTING TO SIGNALING SERVER: $e");
      _setStatus("Failed to connect to signaling server");
      _disconnect();
    }
  }

  void _handleSignalingMessage(Map<String, dynamic> data) async {
    final messageType = data['type'];
    print("HANDLING SIGNALING MESSAGE: $messageType");

    if (messageType == 'registered') {
      _clientId = data['clientId'];
      print("REGISTERED WITH CLIENT ID: $_clientId");

      print("JOINING ROOM: $_roomId AS VIEWER");
      _channel!.sink.add(
        jsonEncode({
          'type': 'join',
          'clientId': _clientId,
          'roomId': _roomId,
          'role': 'viewer',
        }),
      );
    } else if (messageType == 'joined') {
      _setStatus("Joined room ${data['roomId']}");
      print("JOINED ROOM: ${data['roomId']}");

      final clients = data['clients'] as List;
      final hasBroadcaster = clients.any(
        (client) => client['role'] == 'broadcaster',
      );

      if (hasBroadcaster) {
        print("BROADCASTER FOUND, CREATING PEER CONNECTION");
        await _createPeerConnection();
      } else {
        print("NO BROADCASTER IN ROOM, WAITING");
        _setStatus("Waiting for broadcaster to join");
      }
    } else if (messageType == 'client-joined') {
      print("CLIENT JOINED: ${data['role']} - ${data['clientId']}");
      if (data['role'] == 'broadcaster' && _peerConnection == null) {
        print("BROADCASTER JOINED, CREATING PEER CONNECTION");
        await _createPeerConnection();
      }
    } else if (messageType == 'answer' && data['target'] == _clientId) {
      print("RECEIVED SDP ANSWER FROM BROADCASTER");
      final sdp = data['sdp'];
      final answer = RTCSessionDescription(sdp, 'answer');
      print("SETTING REMOTE DESCRIPTION");
      await _peerConnection?.setRemoteDescription(answer);
    } else if (messageType == 'ice-candidate' && data['target'] == _clientId) {
      print("RECEIVED ICE CANDIDATE FROM BROADCASTER");
      final candidate = data['candidate'];
      await _peerConnection?.addCandidate(
        RTCIceCandidate(
          candidate['candidate'],
          candidate['sdpMid'],
          candidate['sdpMLineIndex'],
        ),
      );
    } else {
      print("UNHANDLED MESSAGE TYPE: $messageType");
    }
  }

  Map<String, String> _generateTurnCredentials(String username_base_part) {
    final expiryTimestamp =
        (DateTime.now().millisecondsSinceEpoch / 1000).floor() + 24 * 3600;
    final usernameWithExpiry = "$expiryTimestamp:$username_base_part";
    print("TURN Auth: Generating creds for base='$username_base_part'");
    print("TURN Auth: String to HMAC: '$usernameWithExpiry'");

    final key = utf8.encode(_turnSecret!);
    final bytes = utf8.encode(usernameWithExpiry);
    final hmacSha1 = Hmac(sha1, key);
    final digest = hmacSha1.convert(bytes);
    final credential = base64.encode(digest.bytes);

    print(
      "TURN Auth: Generated username='$usernameWithExpiry', credential='$credential'",
    );
    return {'username': usernameWithExpiry, 'credential': credential};
  }

  Future<void> _createPeerConnection() async {
    _setStatus("Creating connection...");
    print("CREATING PEER CONNECTION");

    if (_turnSecret == null) {
      print("TURN SERVER NOT SET EXITING");
      Navigator.of(context).pop();
      return;
    }

    final credentials = _generateTurnCredentials(_clientId ?? "flutter-client");
    print(
      "GENERATED TURN CREDENTIALS: ${credentials['username']?.substring(0, 10)}...",
    );

    final config = {
      'iceServers': [
        {
          'urls': [
            'turns:$_turnHost:5349?transport=tcp',
            'turns:$_turnHost:5349?transport=udp'
          ],
          'username': credentials['username'],
          'credential': credentials['credential'],
          'credentialType': 'password',
        },
      ],
    };

    print("ICE SERVER CONFIG: Forcing RELAY mode for CGNAT environment");

    final mediaConstraints = <String, dynamic>{'audio': false, 'video': false};

    final offerSdpConstraints = {
      'mandatory': {'OfferToReceiveAudio': false, 'OfferToReceiveVideo': true},
      'optional': [],
    };

    final Map<String, dynamic> options = {
      'enableAudio': false,
      'enableVideo': true,
    };

    print("CREATING RTCPeerConnection WITH CUSTOM OPTIONS - AUDIO DISABLED");
    _peerConnection = await createPeerConnection(config, offerSdpConstraints);

    _peerConnection!.onIceCandidate = (candidate) {
      print(
        "ICE CANDIDATE GENERATED: ${candidate.candidate?.substring(0, 30)}...",
      );
      _channel!.sink.add(
        jsonEncode({
          'type': 'ice-candidate',
          'clientId': _clientId,
          'target': 'broadcaster',
          'roomId': _roomId,
          'candidate': {
            'candidate': candidate.candidate,
            'sdpMid': candidate.sdpMid,
            'sdpMLineIndex': candidate.sdpMLineIndex,
          },
        }),
      );
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
        _remoteRenderer.srcObject = event.streams[0];
        setState(() {
          _isConnected = true;
          _isConnecting = false;
        });
        _setStatus("Connected");
      } else {
        print(
          "IGNORING NON-VIDEO TRACK: ${event.track.kind} - ${event.track.id}",
        );
      }
    };

    _peerConnection!.onConnectionState = (state) {
      print('CONNECTION STATE CHANGE: $state');
      if (state == RTCPeerConnectionState.RTCPeerConnectionStateConnected) {
        print('WEBRTC CONNECTION ESTABLISHED');
        setState(() {
          _isConnected = true;
          _isConnecting = false;
        });
        _setStatus('Connected');
      } else if (state == RTCPeerConnectionState.RTCPeerConnectionStateFailed ||
          state == RTCPeerConnectionState.RTCPeerConnectionStateDisconnected) {
        print('WEBRTC CONNECTION FAILED OR DISCONNECTED');
        setState(() {
          _isConnected = false;
          _isConnecting = false;
        });
        _setStatus('Connection failed');
      }
    };

    print("CREATING OFFER");
    final offer = await _peerConnection!.createOffer(offerSdpConstraints);

    String modifiedSdp = offer.sdp!;

    print(
      "ORIGINAL SDP SECTIONS: ${modifiedSdp.split('m=').length - 1} sections",
    );

    final audioSectionRegExp = RegExp(r'm=audio.*?(m=|$)', dotAll: true);
    modifiedSdp = modifiedSdp.replaceAll(audioSectionRegExp, '');

    modifiedSdp = modifiedSdp.replaceAll(
      RegExp(r'a=rtpmap:.*?opus.*?\r\n'),
      '',
    );

    final modifiedOffer = RTCSessionDescription(modifiedSdp, 'offer');

    print("SETTING LOCAL DESCRIPTION WITH MODIFIED SDP (AUDIO DISABLED)");
    await _peerConnection!.setLocalDescription(modifiedOffer);

    print("SENDING MODIFIED OFFER TO BROADCASTER");
    _channel!.sink.add(
      jsonEncode({
        'type': 'offer',
        'clientId': _clientId,
        'target': 'broadcaster',
        'roomId': _roomId,
        'sdp': modifiedSdp,
      }),
    );
  }

  Future<void> _connect() async {
    if (_isConnecting || _isConnected) return;

    setState(() {
      _isConnecting = true;
    });

    _connectToSignalingServer();
  }

  void _disconnect() {
    _channel?.sink.close();
    _channel = null;

    _peerConnection?.close();
    _peerConnection = null;

    _remoteRenderer.srcObject = null;

    setState(() {
      _clientId = null;
      _isConnected = false;
      _isConnecting = false;
      _statusText = "Disconnected";
    });
  }

  void _toggleFullScreen() {
    setState(() {
      _isFullScreen = !_isFullScreen;
      if (_isFullScreen) {
        Future.delayed(const Duration(seconds: 3), () {
          if (mounted && _isFullScreen) {
            setState(() {
              _controlsVisible = false;
            });
          }
        });
      } else {
        _controlsVisible = true;
      }
    });
  }

  void _toggleControls() {
    setState(() {
      _controlsVisible = !_controlsVisible;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar:
          _isFullScreen
              ? null
              : AppBar(
                backgroundColor: Colors.black,
                title: Text(
                  'Live Stream',
                  style: TextStyle(color: Colors.white),
                ),
                elevation: 0,
                actions: [_buildConnectionButton()],
              ),
      body: GestureDetector(
        onTap: _isFullScreen ? _toggleControls : null,
        child: Stack(
          children: [
            Center(
              child: Container(
                width: double.infinity,
                height: double.infinity,
                decoration: BoxDecoration(color: Colors.black),
                child:
                    _isConnected
                        ? RTCVideoView(
                          _remoteRenderer,
                          objectFit:
                              RTCVideoViewObjectFit.RTCVideoViewObjectFitCover,
                        )
                        : Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                _isConnecting
                                    ? Icons.sensors
                                    : Icons.videocam_off,
                                size: 50,
                                color:
                                    _isConnecting
                                        ? Colors.orange
                                        : Colors.white54,
                              ),
                              const SizedBox(height: 16),
                              Text(
                                _statusText,
                                style: TextStyle(
                                  color:
                                      _isConnecting
                                          ? Colors.orange
                                          : Colors.white54,
                                  fontSize: 16,
                                ),
                              ),
                              if (_isConnecting)
                                Padding(
                                  padding: const EdgeInsets.only(top: 24.0),
                                  child: CircularProgressIndicator(
                                    color: Colors.orange,
                                  ),
                                ),
                            ],
                          ),
                        ),
              ),
            ),

            // Controls overlay
            if (_controlsVisible || !_isFullScreen)
              AnimatedOpacity(
                opacity: _controlsVisible ? 1.0 : 0.0,
                duration: const Duration(milliseconds: 300),
                child: Container(
                  decoration: BoxDecoration(
                    gradient:
                        _isFullScreen
                            ? LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                Colors.black.withOpacity(0.7),
                                Colors.transparent,
                                Colors.transparent,
                                Colors.black.withOpacity(0.7),
                              ],
                              stops: const [0.0, 0.2, 0.8, 1.0],
                            )
                            : null,
                  ),
                  child: SafeArea(
                    child: Column(
                      children: [
                        if (_isFullScreen)
                          Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                IconButton(
                                  icon: const Icon(
                                    Icons.arrow_back,
                                    color: Colors.white,
                                  ),
                                  onPressed: _toggleFullScreen,
                                ),
                                Text(
                                  'Room: $_roomId',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                _buildConnectionButton(),
                              ],
                            ),
                          ),

                        Spacer(),
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 16.0,
                            vertical: _isFullScreen ? 24.0 : 16.0,
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12.0,
                                  vertical: 6.0,
                                ),
                                decoration: BoxDecoration(
                                  color: _getStatusColor().withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(
                                    color: _getStatusColor(),
                                    width: 1,
                                  ),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Container(
                                      width: 8,
                                      height: 8,
                                      decoration: BoxDecoration(
                                        color: _getStatusColor(),
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _statusText,
                                      style: TextStyle(
                                        color: _getStatusColor(),
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ),

                              IconButton(
                                icon: Icon(
                                  _isFullScreen
                                      ? Icons.fullscreen_exit
                                      : Icons.fullscreen,
                                  color: Colors.white,
                                ),
                                onPressed: _toggleFullScreen,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor() {
    if (_isConnected) return Colors.green;
    if (_isConnecting) return Colors.orange;
    return Colors.red;
  }

  Widget _buildConnectionButton() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0),
      child: ElevatedButton(
        onPressed:
            _isConnecting ? null : (_isConnected ? _disconnect : _connect),
        style: ElevatedButton.styleFrom(
          backgroundColor: _isConnected ? Colors.red : Colors.green,
          disabledBackgroundColor: Colors.grey,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        ),
        child:
            _isConnecting
                ? SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
                : Text(
                  _isConnected ? 'Disconnect' : 'Connect',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
      ),
    );
  }
}
