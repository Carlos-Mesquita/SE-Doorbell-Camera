import 'package:doorbell_app/models/capture.dart';
import 'package:doorbell_app/models/notification.dart';

class NotificationGroup {
  final String typeStr;
  final List<NotificationDTO> notifications;
  final DateTime firstCreatedAt;
  final DateTime lastCreatedAt;
  final String groupTitle;
  final List<CaptureDTO> allCaptures;

  NotificationGroup({
    required this.typeStr,
    required this.notifications,
    required this.firstCreatedAt,
    required this.lastCreatedAt,
    required this.groupTitle,
    required this.allCaptures,
  });

  NotificationDTO get primaryNotification => notifications.first;
  int get count => notifications.length;
  bool get isGroup => notifications.length > 1;

  String get timeRange {
    if (!isGroup) return '';

    final duration = lastCreatedAt.difference(firstCreatedAt);
    if (duration.inMinutes < 60) {
      return '${duration.inMinutes}m span';
    } else if (duration.inHours < 24) {
      return '${duration.inHours}h span';
    } else {
      return '${duration.inDays}d span';
    }
  }
}

class NotificationGrouping {
  static List<NotificationGroup> groupSequentialNotifications(
    List<NotificationDTO> notifications, {
    Duration maxGapBetweenNotifications = const Duration(minutes: 30),
    bool enableGrouping = true,
  }) {
    if (!enableGrouping || notifications.isEmpty) {
      return notifications
          .map((notification) => _createSingleNotificationGroup(notification))
          .toList();
    }

    final List<NotificationGroup> groups = [];
    List<NotificationDTO> currentGroup = [];
    String? currentType;
    DateTime? lastNotificationTime;

    for (final notification in notifications) {
      final notificationTime =
          DateTime.tryParse(notification.createdAt) ?? DateTime.now();
      final notificationType = notification.typeStr;

      bool shouldStartNewGroup = false;

      if (currentGroup.isEmpty) {
        shouldStartNewGroup = false;
      } else if (notificationType != currentType) {
        shouldStartNewGroup = true;
      } else if (lastNotificationTime != null &&
          notificationTime.difference(lastNotificationTime).abs() >
              maxGapBetweenNotifications) {
        shouldStartNewGroup = true;
      }

      if (shouldStartNewGroup && currentGroup.isNotEmpty) {
        groups.add(_createNotificationGroup(currentGroup, currentType!));
        currentGroup = [];
      }

      currentGroup.add(notification);
      currentType = notificationType;
      lastNotificationTime = notificationTime;
    }

    if (currentGroup.isNotEmpty) {
      groups.add(_createNotificationGroup(currentGroup, currentType!));
    }

    return groups;
  }

  static NotificationGroup _createSingleNotificationGroup(
    NotificationDTO notification,
  ) {
    final createdAt =
        DateTime.tryParse(notification.createdAt) ?? DateTime.now();

    return NotificationGroup(
      typeStr: notification.typeStr ?? 'unknown',
      notifications: [notification],
      firstCreatedAt: createdAt,
      lastCreatedAt: createdAt,
      groupTitle: notification.title,
      allCaptures: notification.captures ?? [],
    );
  }

  static NotificationGroup _createNotificationGroup(
    List<NotificationDTO> notifications,
    String type,
  ) {
    if (notifications.length == 1) {
      return _createSingleNotificationGroup(notifications.first);
    }

    final sortedNotifications = List<NotificationDTO>.from(notifications)..sort(
      (a, b) =>
          DateTime.tryParse(
            b.createdAt,
          )?.compareTo(DateTime.tryParse(a.createdAt) ?? DateTime.now()) ??
          0,
    );

    final firstTime =
        DateTime.tryParse(sortedNotifications.last.createdAt) ?? DateTime.now();
    final lastTime =
        DateTime.tryParse(sortedNotifications.first.createdAt) ??
        DateTime.now();

    final allCaptures = <CaptureDTO>[];
    for (final notification in sortedNotifications) {
      allCaptures.addAll(notification.captures);
    }

    allCaptures.sort(
      (a, b) =>
          DateTime.tryParse(
            b.createdAt,
          )?.compareTo(DateTime.tryParse(a.createdAt) ?? DateTime.now()) ??
          0,
    );
    final typeDisplay = _formatNotificationType(type);
    final groupTitle = '${notifications.length} $typeDisplay events';

    return NotificationGroup(
      typeStr: type,
      notifications: sortedNotifications,
      firstCreatedAt: firstTime,
      lastCreatedAt: lastTime,
      groupTitle: groupTitle,
      allCaptures: allCaptures,
    );
  }

  static String _formatNotificationType(String? type) {
    if (type == null) return 'notification';

    return type
        .replaceAll('_', ' ')
        .toLowerCase()
        .split(' ')
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }

  static NotificationDTO createGroupedNotificationDTO(NotificationGroup group) {
    if (!group.isGroup) {
      return group.primaryNotification;
    }

    return NotificationDTO(
      id: group.primaryNotification.id,
      title: group.groupTitle,
      createdAt: group.lastCreatedAt.toIso8601String(),
      captures: group.allCaptures,
      rpiEventId: group.primaryNotification.rpiEventId,
      typeStr: group.typeStr,
      userId: group.primaryNotification.userId,
    );
  }
}
