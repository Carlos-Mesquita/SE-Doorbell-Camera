import 'dart:convert';

class Notification {
  final int id;
  final String title;
  final String timestamp;
  final List<String> captures;

  Notification({
    required this.id,
    required this.title,
    required this.timestamp,
    required this.captures,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'timestamp': timestamp,
      'captures': jsonEncode(captures),
    };
  }

  factory Notification.fromMap(Map<String, dynamic> map) {
    return Notification(
      id: map['id'],
      title: map['title'],
      timestamp: map['timestamp'],
      captures: List<String>.from(jsonDecode(map['captures'])),
    );
  }
}
