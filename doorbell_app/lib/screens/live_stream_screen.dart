import 'package:doorbell_app/config/env_config.dart';
import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:doorbell_app/services/signaling.dart';
import 'package:doorbell_app/services/webrtc_streaming.dart';
import 'package:doorbell_app/services/livestreaming.dart';

class LiveStreamScreen extends StatefulWidget {
  const LiveStreamScreen({super.key});

  @override
  LiveStreamScreenState createState() => LiveStreamScreenState();
}

class LiveStreamScreenState extends State<LiveStreamScreen> {
  final RTCVideoRenderer _remoteRenderer = RTCVideoRenderer();
  late LiveStreamingService _streamingService;

  StreamingState _streamingState = StreamingState.disconnected;
  String _statusText = "Disconnected";
  bool _isFullScreen = false;
  bool _controlsVisible = true;

  final String _roomId = "camera-room-1";

  @override
  void initState() {
    super.initState();
    _initializeServices();
    _initRenderers();
    _connect();
  }

  @override
  void dispose() {
    _streamingService.dispose();
    _remoteRenderer.dispose();
    super.dispose();
  }

  void _initializeServices() {
    final signalingService = WebSocketSignalingService();

    final webrtcService = WebRTCStreamingService(
      turnHost: EnvConfig.turnHost,
      turnSecret: EnvConfig.turnSecret,
    );

    _streamingService = LiveStreamingService(
      signalingService: signalingService,
      webrtcService: webrtcService,
      roomId: _roomId,
    );

    _streamingService.onStateChanged = (state, message) {
      setState(() {
        _streamingState = state;
        _statusText = message;
      });
    };

    _streamingService.onStreamReceived = (stream) {
      setState(() {
        _remoteRenderer.srcObject = stream;
      });
    };

    _streamingService.onError = (error) {
      print("STREAMING ERROR: $error");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Streaming error: $error')),
      );
    };
  }

  Future<void> _initRenderers() async {
    await _remoteRenderer.initialize();
  }

  Future<void> _connect() async {
    if (_streamingService.isConnecting || _streamingService.isConnected) return;

    await _streamingService.connect();
  }

  void _disconnect() {
    _streamingService.disconnect();
    setState(() {
      _remoteRenderer.srcObject = null;
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

  bool get _isConnected => _streamingState == StreamingState.connected;
  bool get _isConnecting => _streamingService.isConnecting;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: _isFullScreen
          ? null
          : AppBar(
              backgroundColor: Colors.black,
              title: const Text(
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
                decoration: const BoxDecoration(color: Colors.black),
                child: _isConnected
                    ? RTCVideoView(
                        _remoteRenderer,
                        objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitCover,
                      )
                    : Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              _isConnecting ? Icons.sensors : Icons.videocam_off,
                              size: 50,
                              color: _isConnecting ? Colors.orange : Colors.white54,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              _statusText,
                              style: TextStyle(
                                color: _isConnecting ? Colors.orange : Colors.white54,
                                fontSize: 16,
                              ),
                            ),
                            if (_isConnecting)
                              const Padding(
                                padding: EdgeInsets.only(top: 24.0),
                                child: CircularProgressIndicator(
                                  color: Colors.orange,
                                ),
                              ),
                          ],
                        ),
                      ),
              ),
            ),

            if (_controlsVisible || !_isFullScreen)
              AnimatedOpacity(
                opacity: _controlsVisible ? 1.0 : 0.0,
                duration: const Duration(milliseconds: 300),
                child: Container(
                  decoration: BoxDecoration(
                    gradient: _isFullScreen
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

                        const Spacer(),
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
    switch (_streamingState) {
      case StreamingState.connected:
        return Colors.green;
      case StreamingState.connectingToSignaling:
      case StreamingState.joiningRoom:
      case StreamingState.creatingConnection:
      case StreamingState.refreshingToken:
        return Colors.orange;
      case StreamingState.error:
        return Colors.red;
      case StreamingState.disconnected:
      default:
        return Colors.red;
    }
  }

  Widget _buildConnectionButton() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0),
      child: ElevatedButton(
        onPressed: _isConnecting ? null : (_isConnected ? _disconnect : _connect),
        style: ElevatedButton.styleFrom(
          backgroundColor: _isConnected ? Colors.red : Colors.green,
          disabledBackgroundColor: Colors.grey,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        ),
        child: _isConnecting
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Text(
                _isConnected ? 'Disconnect' : 'Connect',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
      ),
    );
  }
}
