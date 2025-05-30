class CaptureDTO {
  final int? id;
  final String path;
  final String createdAt;
  final int? notificationId;
  final String? userId;

  CaptureDTO({
    this.id,
    required this.path,
    required this.createdAt,
    this.notificationId,
    this.userId,
  });

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'path': path,
      'created_at': createdAt,
      if (notificationId != null) 'notification_id': notificationId,
      if (userId != null) 'user_id': userId,
    };
  }

  factory CaptureDTO.fromMap(Map<String, dynamic> map) {
    return CaptureDTO(
      id: map['id'] as int?,
      path: map['path'] as String? ?? '',
      createdAt: map['created_at'] as String? ?? DateTime.now().toIso8601String(),
      notificationId: map['notification_id'] as int?,
      userId: map['user_id'] as String?,
    );
  }
}
