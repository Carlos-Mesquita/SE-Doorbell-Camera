class ButtonSettingsConfig {
  final int? debounceMs;       // Matches backend: milliseconds
  final int? pollingRateHz;  // Matches backend: Hz

  ButtonSettingsConfig({this.debounceMs, this.pollingRateHz});

  factory ButtonSettingsConfig.fromJson(Map<String, dynamic> json) {
    return ButtonSettingsConfig(
      debounceMs: json['debounce_ms'] as int?,
      pollingRateHz: json['polling_rate_hz'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (debounceMs != null) data['debounce_ms'] = debounceMs;
    if (pollingRateHz != null) data['polling_rate_hz'] = pollingRateHz;
    return data;
  }
}

class MotionSensorSettingsConfig {
  final int? debounceMs;
  final int? pollingRateHz;

  MotionSensorSettingsConfig({
    this.debounceMs,
    this.pollingRateHz,
  });

  factory MotionSensorSettingsConfig.fromJson(Map<String, dynamic> json) {
    return MotionSensorSettingsConfig(
      debounceMs: json['debounce_ms'] as int?,
      pollingRateHz: json['polling_rate_hz'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (debounceMs != null) data['debounce_ms'] = debounceMs;
    if (pollingRateHz != null) data['polling_rate_hz'] = pollingRateHz;
    return data;
  }
}

class StopMotionSettingsConfig {
  final double? intervalSeconds;
  final double? durationSeconds;

  StopMotionSettingsConfig({this.intervalSeconds, this.durationSeconds/*, this.autoStop*/});

  factory StopMotionSettingsConfig.fromJson(Map<String, dynamic> json) {
    return StopMotionSettingsConfig(
      intervalSeconds: (json['interval_seconds'] as num?)?.toDouble(),
      durationSeconds: (json['duration_seconds'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (intervalSeconds != null) data['interval_seconds'] = intervalSeconds;
    if (durationSeconds != null) data['duration_seconds'] = durationSeconds;
    return data;
  }
}

class CameraSettingsConfig {
  final StopMotionSettingsConfig? stopMotion;

  CameraSettingsConfig({/*this.bitrate,*/ this.stopMotion});

  factory CameraSettingsConfig.fromJson(Map<String, dynamic> json) {
    return CameraSettingsConfig(
      stopMotion: json['stop_motion'] != null
          ? StopMotionSettingsConfig.fromJson(json['stop_motion'] as Map<String, dynamic>)
                    : null,
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (stopMotion != null) data['stop_motion'] = stopMotion!.toJson();
    return data;
  }
}

class ColorSettingsConfig {
  final int? r;
  final int? g;
  final int? b;

  ColorSettingsConfig({this.r, this.g, this.b});

  factory ColorSettingsConfig.fromJson(Map<String, dynamic> json) {
    return ColorSettingsConfig(
      r: json['r'] as int?,
      g: json['g'] as int?,
      b: json['b'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (r != null) data['r'] = r;
    if (g != null) data['g'] = g;
    if (b != null) data['b'] = b;
    return data;
  }
}


class Settings {
  final ButtonSettingsConfig? button;
  final MotionSensorSettingsConfig? motionSensor;
  final CameraSettingsConfig? camera;
  final ColorSettingsConfig? color;

  Settings({
    this.button,
    this.motionSensor,
    this.camera,
    this.color,
  });

  factory Settings.fromJson(Map<String, dynamic> json) {
    return Settings(
      button: json['button'] != null
          ? ButtonSettingsConfig.fromJson(json['button'] as Map<String, dynamic>)
          : null,
      motionSensor: json['motion_sensor'] != null
          ? MotionSensorSettingsConfig.fromJson(json['motion_sensor'] as Map<String, dynamic>)
          : null,
      camera: json['camera'] != null
          ? CameraSettingsConfig.fromJson(json['camera'] as Map<String, dynamic>)
          : null,
      color: json['color'] != null
          ? ColorSettingsConfig.fromJson(json['color'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (button != null) data['button'] = button!.toJson();
    if (motionSensor != null) data['motion_sensor'] = motionSensor!.toJson();
    if (camera != null) data['camera'] = camera!.toJson();
    if (color != null) data['color'] = color!.toJson();
    return data;
  }

  Settings copyWith({
    ButtonSettingsConfig? button,
    MotionSensorSettingsConfig? motionSensor,
    CameraSettingsConfig? camera,
    ColorSettingsConfig? color,
  }) {
    return Settings(
      button: button ?? this.button,
      motionSensor: motionSensor ?? this.motionSensor,
      camera: camera ?? this.camera,
      color: color ?? this.color,
    );
  }
}
