import 'package:flutter/material.dart';
import 'package:flutter_vlc_player/flutter_vlc_player.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/database_helper.dart';
import '../models/notification.dart' as app_notification;
import '../models/settings.dart';
import 'login.dart';

class MainScreen extends StatefulWidget {
  final String serverUrl;
  final AuthService authService;
  
  const MainScreen({
    super.key,
    required this.serverUrl,
    required this.authService,
  });

  @override
  _MainScreenState createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late ApiService _apiService;
  List<app_notification.Notification> _notifications = [];
  bool _isLoading = true;
  Settings? _settings;
  
  VlcPlayerController? _videoPlayerController;
  String _streamUrl = '';
  bool _isStreamLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    
    _apiService = ApiService(
      serverUrl: widget.serverUrl,
      authService: widget.authService,
      onNewNotification: (notification) {
        setState(() {
          _notifications.add(notification);
        });
      },
    );
    
    _loadData();
    
    _tabController.addListener(() {
      if (_tabController.index == 1 && _streamUrl.isEmpty) {
        _initializeStream();
      } else if (_tabController.index == 2 && _settings == null) {
        _loadSettings();
      }
    });
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
    });
    
    try {
      await _apiService.syncNotifications();
      _apiService.connectWebSocket();
      
      final notifications = await DatabaseHelper.instance.getNotifications();
      setState(() {
        _notifications = notifications;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _initializeStream() async {
    setState(() {
      _isStreamLoading = true;
    });
    
    try {
      final streamUrl = await _apiService.startStream();
      setState(() {
        _streamUrl = streamUrl;
        
        if (_streamUrl.isNotEmpty) {
          _videoPlayerController = VlcPlayerController.network(
            _streamUrl,
            hwAcc: HwAcc.full,
            autoPlay: true,
            options: VlcPlayerOptions(),
          );
        }
        
        _isStreamLoading = false;
      });
    } catch (e) {
      setState(() {
        _isStreamLoading = false;
      });
    }
  }

  Future<void> _loadSettings() async {
    setState(() {
      _isLoading = true;
    });
    
    try {
      final settings = await _apiService.getSettings();
      setState(() {
        _settings = settings;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _logout() async {
    await widget.authService.logout();
    
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => LoginScreen(serverUrl: widget.serverUrl),
      ),
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    _apiService.dispose();
    _videoPlayerController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart Camera'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _logout,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.notifications), text: "Notifications"),
            Tab(icon: Icon(Icons.videocam), text: "Stream"),
            Tab(icon: Icon(Icons.settings), text: "Settings"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildNotificationsTab(),
          _buildStreamTab(),
          _buildSettingsTab(),
        ],
      ),
    );
  }

  Widget _buildNotificationsTab() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (_notifications.isEmpty) {
      return const Center(child: Text('No notifications'));
    }
    
    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        itemCount: _notifications.length,
        itemBuilder: (context, index) {
          final notification = _notifications[index];
          return Card(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: InkWell(
              onTap: () {
                _showNotificationDetails(notification);
              },
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      notification.title,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Timestamp: ${notification.timestamp}',
                      style: TextStyle(
                        color: Colors.grey[600],
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${notification.captures.length} captures',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  void _showNotificationDetails(app_notification.Notification notification) {
    showModalBottomSheet(
      context: context,
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                notification.title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text('Timestamp: ${notification.timestamp}'),
              const SizedBox(height: 16),
              const Text(
                'Captures:',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Expanded(
                child: ListView.builder(
                  itemCount: notification.captures.length,
                  itemBuilder: (context, index) {
                    return ListTile(
                      leading: const Icon(Icons.image),
                      title: Text(notification.captures[index]),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStreamTab() {
    if (_isStreamLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (_streamUrl.isEmpty || _videoPlayerController == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Failed to load stream'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _initializeStream,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }
    
    return Center(
      child: VlcPlayer(
        controller: _videoPlayerController!,
        aspectRatio: 16 / 9,
        placeholder: const Center(child: CircularProgressIndicator()),
      ),
    );
  }

  Widget _buildSettingsTab() {
    if (_isLoading || _settings == null) {
      return const Center(child: CircularProgressIndicator());
    }
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Settings',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 24),
          
          _buildSettingsSection(
            title: 'Color',
            children: [
              _buildColorSetting('R', _settings!.color['r'], (value) {
                setState(() {
                  _settings = _settings!.copyWith(
                    color: {..._settings!.color, 'r': value},
                  );
                });
              }, 0, 100),
              _buildColorSetting('G', _settings!.color['g'], (value) {
                setState(() {
                  _settings = _settings!.copyWith(
                    color: {..._settings!.color, 'g': value},
                  );
                });
              }, 0, 100),
              _buildColorSetting('B', _settings!.color['b'], (value) {
                setState(() {
                  _settings = _settings!.copyWith(
                    color: {..._settings!.color, 'b': value},
                  );
                });
              }, 0, 100),
            ],
          ),
          
          _buildSettingsSection(
            title: 'Camera',
            children: [
              _buildSliderSetting(
                'Bitrate',
                _settings!.camera['bitrate'].toDouble(),
                (value) {
                  setState(() {
                    _settings = _settings!.copyWith(
                      camera: {..._settings!.camera, 'bitrate': value.toInt()},
                    );
                  });
                },
                500000,
                5000000,
                divisions: 45,
                valueDisplay: '${(_settings!.camera['bitrate'] / 1000000).toStringAsFixed(2)} Mbps',
              ),
              const SizedBox(height: 16),
              

              const Text(
                'Stop Motion',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              _buildSliderSetting(
                'Interval',
                _settings!.camera['stop_motion']['interval'],
                (value) {
                  setState(() {
                    final stopMotion = {..._settings!.camera['stop_motion'], 'interval': value};
                    _settings = _settings!.copyWith(
                      camera: {..._settings!.camera, 'stop_motion': stopMotion},
                    );
                  });
                },
                0.1,
                5.0,
                divisions: 49,
                valueDisplay: '${_settings!.camera['stop_motion']['interval'].toStringAsFixed(1)} sec',
              ),
              _buildSliderSetting(
                'Duration',
                _settings!.camera['stop_motion']['duration'],
                (value) {
                  setState(() {
                    final stopMotion = {..._settings!.camera['stop_motion'], 'duration': value};
                    _settings = _settings!.copyWith(
                      camera: {..._settings!.camera, 'stop_motion': stopMotion},
                    );
                  });
                },
                1.0,
                60.0,
                divisions: 59,
                valueDisplay: '${_settings!.camera['stop_motion']['duration'].toStringAsFixed(1)} sec',
              ),
            ],
          ),
          
          _buildSettingsSection(
            title: 'Motion Sensor',
            children: [
              _buildSliderSetting(
                'Debounce',
                _settings!.motionSensor['debounce'],
                (value) {
                  setState(() {
                    _settings = _settings!.copyWith(
                      motionSensor: {..._settings!.motionSensor, 'debounce': value},
                    );
                  });
                },
                0.1,
                2.0,
                divisions: 19,
                valueDisplay: '${_settings!.motionSensor['debounce'].toStringAsFixed(1)} sec',
              ),
              _buildSliderSetting(
                'Polling Rate',
                _settings!.motionSensor['polling_rate'],
                (value) {
                  setState(() {
                    _settings = _settings!.copyWith(
                      motionSensor: {..._settings!.motionSensor, 'polling_rate': value},
                    );
                  });
                },
                0.01,
                1.0,
                divisions: 99,
                valueDisplay: '${_settings!.motionSensor['polling_rate'].toStringAsFixed(2)} sec',
              ),
            ],
          ),
          
          _buildSettingsSection(
            title: 'Button',
            children: [
              _buildSliderSetting(
                'Debounce',
                _settings!.button['debounce'],
                (value) {
                  setState(() {
                    _settings = _settings!.copyWith(
                      button: {..._settings!.button, 'debounce': value},
                    );
                  });
                },
                0.1,
                2.0,
                divisions: 19,
                valueDisplay: '${_settings!.button['debounce'].toStringAsFixed(1)} sec',
              ),
              _buildSliderSetting(
                'Polling Rate',
                _settings!.button['polling_rate'],
                (value) {
                  setState(() {
                    _settings = _settings!.copyWith(
                      button: {..._settings!.button, 'polling_rate': value},
                    );
                  });
                },
                0.01,
                1.0,
                divisions: 99,
                valueDisplay: '${_settings!.button['polling_rate'].toStringAsFixed(2)} sec',
              ),
            ],
          ),
          
          const SizedBox(height: 24),
          
          Center(
            child: ElevatedButton(
              onPressed: () async {
                final success = await _apiService.updateSettings(_settings!);
                
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      success ? 'Settings saved successfully' : 'Failed to save settings',
                    ),
                    backgroundColor: success ? Colors.green : Colors.red,
                  ),
                );
              },
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 32, vertical: 12),
                child: Text('Save Settings'),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsSection({
    required String title,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        ...children,
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildColorSetting(String label, int value, Function(int) onChanged, int min, int max) {
    return Row(
      children: [
        Text('$label: '),
        Expanded(
          child: Slider(
            value: value.toDouble(),
            min: min.toDouble(),
            max: max.toDouble(),
            divisions: max - min,
            onChanged: (newValue) {
              onChanged(newValue.toInt());
            },
          ),
        ),
        Text(value.toString()),
      ],
    );
  }

  Widget _buildSliderSetting(
    String label,
    double value,
    Function(double) onChanged,
    double min,
    double max, {
    int? divisions,
    String? valueDisplay,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label),
            Text(valueDisplay ?? value.toString()),
          ],
        ),
        Slider(
          value: value,
          min: min,
          max: max,
          divisions: divisions,
          onChanged: onChanged,
        ),
      ],
    );
  }
}
