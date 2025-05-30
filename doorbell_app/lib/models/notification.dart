import 'dart:convert';

import 'package:doorbell_app/models/capture.dart';


class NotificationDTO {
  final int id;
  final String title;
  final String createdAt;
  final List<CaptureDTO> captures;
  final String? rpiEventId;
  final String? typeStr;
  final int? userId;

  NotificationDTO({
    required this.id,
    required this.title,
    required this.createdAt,
    required this.captures,
    this.rpiEventId,
    this.typeStr,
    this.userId,
  });

  Map<String, dynamic> toDbMap() {
    return {
      'id': id,
      'title': title,
      'created_at': createdAt,
      'captures_json': jsonEncode(captures.map((c) => c.toMap()).toList()),
      'rpi_event_id': rpiEventId,
      'type_str': typeStr,
      'user_id': userId,
    };
  }

  factory NotificationDTO.fromMap(Map<String, dynamic> map) {
    List<CaptureDTO> capturesList = [];
    dynamic rawCaptures = map['captures_json'] ?? map['captures'];

    if (rawCaptures != null) {
      try {
        List<dynamic> decodedCaptures;
        if (rawCaptures is String) {
          decodedCaptures = jsonDecode(rawCaptures);
        } else if (rawCaptures is List) {
          decodedCaptures = rawCaptures;
        } else {
          decodedCaptures = [];
        }
        capturesList = decodedCaptures
            .map((cMap) => CaptureDTO.fromMap(cMap as Map<String, dynamic>))
            .toList();
      } catch (e) {
        print("Error decoding captures in Notification.fromMap: $e. Raw data: $rawCaptures");
      }
    }

    final dynamic idValue = map['id'];
    int parsedId = 0;
    if (idValue is int) {
      parsedId = idValue;
    } else if (idValue is String) {
      parsedId = int.tryParse(idValue) ?? 0;
    }

    final dynamic userIdValue = map['user_id'];
    int? parsedUserId;
    if (userIdValue is int) {
      parsedUserId = userIdValue;
    } else if (userIdValue is String) {
      parsedUserId = int.tryParse(userIdValue);
    }

    return NotificationDTO(
      id: parsedId,
      title: map['title'] as String? ?? 'Untitled Notification',
      createdAt: map['created_at'] as String? ?? DateTime.now().toIso8601String(),
      captures: capturesList,
      rpiEventId: map['rpi_event_id'] as String?,
      typeStr: map['type_str'] as String? ?? map['event_type'] as String?,
      userId: parsedUserId,
    );
  }
}
