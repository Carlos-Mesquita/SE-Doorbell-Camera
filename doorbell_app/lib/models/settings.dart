class Settings {
  final Map<String, dynamic> indicatorLight;
  final Map<String, dynamic> camera;
  final Map<String, dynamic> motionSensor;
  final Map<String, dynamic> doorbell;

  Settings({
    required this.indicatorLight,
    required this.camera,
    required this.motionSensor,
    required this.doorbell,
  });

  factory Settings.fromJson(Map<String, dynamic> json) {
    return Settings(
      indicatorLight: json['indicator_light'] ?? {'enabled': true, 'brightness': 75},
      camera: json['camera'] ?? {
        'bitrate': 1000000,
        'stop_motion': {
          'interval': 0.5, 
          'duration': 300.0, // 5 minutes
          'auto_stop': true
        }
      },
      motionSensor: json['motion_sensor'] ?? {
        'enabled': true,
        'sensitivity': 75, 
        'detection_distance': 100, // in cm
        'debounce': 0.5, 
        'polling_rate': 0.1
      },
      doorbell: json['doorbell'] ?? {
        'enabled': true,
        'notification_sound': true,
        'debounce': 0.5, 
        'polling_rate': 0.1
      },
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'indicator_light': indicatorLight,
      'camera': camera,
      'motion_sensor': motionSensor,
      'doorbell': doorbell,
    };
  }

  Settings copyWith({
    Map<String, dynamic>? indicatorLight,
    Map<String, dynamic>? camera,
    Map<String, dynamic>? motionSensor,
    Map<String, dynamic>? doorbell,
  }) {
    return Settings(
      indicatorLight: indicatorLight ?? this.indicatorLight,
      camera: camera ?? this.camera,
      motionSensor: motionSensor ?? this.motionSensor,
      doorbell: doorbell ?? this.doorbell,
    );
  }
}