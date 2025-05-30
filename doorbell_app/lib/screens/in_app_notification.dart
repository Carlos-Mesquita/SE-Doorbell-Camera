import 'package:flutter/material.dart';

class InAppNotification extends StatelessWidget {
  final String title;
  final String body;
  final Map<String, dynamic>? data;
  final VoidCallback? onTap;

  const InAppNotification({
    super.key,
    required this.title,
    required this.body,
    this.data,
    this.onTap,
  });

  IconData _getNotificationIcon() {
    String? type = data?['type'];
    switch (type) {
      case 'motion_detection':
        return Icons.directions_run_rounded;
      case 'door_sensor':
        return Icons.door_front_door_rounded;
      case 'window_sensor':
        return Icons.window_rounded;
      default:
        return Icons.notifications_rounded;
    }
  }

  Color _getNotificationColor() {
    String? type = data?['type'];
    switch (type) {
      case 'motion_detection':
        return Colors.orange;
      case 'door_sensor':
        return Colors.blue;
      case 'window_sensor':
        return Colors.green;
      default:
        return const Color(0xff3b82f6);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Material(
          color: Colors.transparent,
          child: GestureDetector(
            onTap: onTap,
            child: Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xff1e293b),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: _getNotificationColor().withOpacity(0.3),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    offset: Offset(0, 8),
                    blurRadius: 24,
                  ),
                  BoxShadow(
                    color: _getNotificationColor().withOpacity(0.1),
                    offset: Offset(0, 0),
                    blurRadius: 12,
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: _getNotificationColor().withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      _getNotificationIcon(),
                      color: _getNotificationColor(),
                      size: 24,
                    ),
                  ),
                  SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          title,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        SizedBox(height: 4),
                        Text(
                          body,
                          style: TextStyle(
                            color: Colors.grey[300],
                            fontSize: 14,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (data?['timestamp'] != null) ...[
                          SizedBox(height: 6),
                          Text(
                            _formatTime(data!['timestamp']),
                            style: TextStyle(
                              color: Colors.grey[400],
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  SizedBox(width: 12),
                  Container(
                    padding: EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      Icons.chevron_right_rounded,
                      color: Colors.white,
                      size: 16,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _formatTime(String timestamp) {
    try {
      DateTime dateTime = DateTime.parse(timestamp);
      return "${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}";
    } catch (e) {
      return 'Just now';
    }
  }
}
