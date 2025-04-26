import 'dart:convert';

class Notification {
  final int id;
  final String title;
  final String timestamp;
  final List<String> captures;
  final String eventType; // "motion" or "doorbell"
  final int duration; // duration in seconds

  Notification({
    required this.id,
    required this.title,
    required this.timestamp,
    required this.captures,
    required this.eventType,
    required this.duration,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'timestamp': timestamp,
      'captures': jsonEncode(captures),
      'event_type': eventType,
      'duration': duration,
    };
  }

  factory Notification.fromMap(Map<String, dynamic> map) {
    return Notification(
      id: map['id'],
      title: map['title'],
      timestamp: map['timestamp'],
      captures: List<String>.from(jsonDecode(map['captures'])),
      eventType: map['event_type'] ?? 'unknown',
      duration: map['duration'] ?? 0,
    );
  }
}