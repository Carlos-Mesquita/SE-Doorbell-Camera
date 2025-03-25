class Settings {
  final Map<String, dynamic> color;
  final Map<String, dynamic> camera;
  final Map<String, dynamic> motionSensor;
  final Map<String, dynamic> button;

  Settings({
    required this.color,
    required this.camera,
    required this.motionSensor,
    required this.button,
  });

  factory Settings.fromJson(Map<String, dynamic> json) {
    return Settings(
      color: json['color'],
      camera: json['camera'],
      motionSensor: json['motion_sensor'],
      button: json['button'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'color': color,
      'camera': camera,
      'motion_sensor': motionSensor,
      'button': button,
    };
  }

  Settings copyWith({
    Map<String, dynamic>? color,
    Map<String, dynamic>? camera,
    Map<String, dynamic>? motionSensor,
    Map<String, dynamic>? button,
  }) {
    return Settings(
      color: color ?? this.color,
      camera: camera ?? this.camera,
      motionSensor: motionSensor ?? this.motionSensor,
      button: button ?? this.button,
    );
  }
}
