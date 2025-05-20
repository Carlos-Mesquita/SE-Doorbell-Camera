class CaptureInfo {
  final int? id;
  final String path;
  final String timestamp;
  final int? notificationId;
  final String? userId;

  CaptureInfo({
    this.id,
    required this.path,
    required this.timestamp,
    this.notificationId,
    this.userId,
  });


  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'path': path,
      'timestamp': timestamp,
      if (notificationId != null) 'notification_id': notificationId,
      if (userId != null) 'user_id': userId,
    };
  }

  factory CaptureInfo.fromMap(Map<String, dynamic> map) {
    return CaptureInfo(
      id: map['id'] as int?,
      path: map['path'] as String? ?? '',
      timestamp: map['timestamp'] as String? ?? DateTime.now().toIso8601String(),
      notificationId: map['notification_id'] as int?,
      userId: map['user_id'] as String?,
    );
  }
}
