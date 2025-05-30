import 'package:doorbell_app/config/env_config.dart';
import 'package:flutter/material.dart';
import '../../models/notification.dart';
import '../../utils/date_formatter.dart';

class NotificationCard extends StatefulWidget {
  final NotificationDTO notification;
  final bool isExpanded;
  final VoidCallback onToggleExpanded;
  final Function(int) onCapturePressed;
  final VoidCallback? onDelete;


  const NotificationCard({
    Key? key,
    required this.notification,
    required this.isExpanded,
    required this.onToggleExpanded,
    required this.onCapturePressed,
    this.onDelete,  // Added optional delete parameter
  }) : super(key: key);

  @override
  _NotificationCardState createState() => _NotificationCardState();
}

class _NotificationCardState extends State<NotificationCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _expandAnimation;
  final captureBaseUrl = EnvConfig.captureBase ?? '';

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    _expandAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void didUpdateWidget(NotificationCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isExpanded != oldWidget.isExpanded) {
      if (widget.isExpanded) {
        _animationController.forward();
      } else {
        _animationController.reverse();
      }
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  IconData _getNotificationIcon(String? type) {
    switch (type) {
      case 'motion_detection':
        return Icons.directions_run_rounded;
      case 'door_sensor':
        return Icons.door_front_door_rounded;
      case 'window_sensor':
        return Icons.window_rounded;
      case 'system_health':
        return Icons.health_and_safety_rounded;
      default:
        return Icons.notifications_rounded;
    }
  }

  Color _getNotificationColor(String? type) {
    switch (type) {
      case 'motion_detection':
        return Colors.orange;
      case 'door_sensor':
        return Colors.blue;
      case 'window_sensor':
        return Colors.green;
      case 'system_health':
        return Colors.purple;
      default:
        return Theme.of(context).colorScheme.primary;
    }
  }

  void _showDeleteDialog(BuildContext context) {
    showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(
              Icons.delete_outline_rounded,
              color: Colors.red,
              size: 24,
            ),
            SizedBox(width: 12),
            Text('Delete Notification'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Are you sure you want to delete this notification?'),
            SizedBox(height: 12),
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    _getNotificationIcon(widget.notification.typeStr),
                    size: 16,
                    color: _getNotificationColor(widget.notification.typeStr),
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      widget.notification.title,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(height: 8),
            Text(
              'This action cannot be undone.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.red.withOpacity(0.8),
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(
              'Cancel',
              style: TextStyle(
                color: Theme.of(context).textTheme.bodyMedium?.color,
              ),
            ),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop(true);
              widget.onDelete?.call();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
              elevation: 0,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.delete_outline_rounded, size: 16),
                SizedBox(width: 4),
                Text('Delete'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final captures = widget.notification.captures ?? [];

    return Container(
      margin: EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withOpacity(0.1),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            offset: Offset(0, 2),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        children: [
          // Card header
          Container(
            padding: EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Type indicator and timestamp with delete button
                Row(
                  children: [
                    Container(
                      padding: EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: _getNotificationColor(widget.notification.typeStr).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        _getNotificationIcon(widget.notification.typeStr),
                        size: 20,
                        color: _getNotificationColor(widget.notification.typeStr),
                      ),
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.notification.typeStr
                                ?.replaceAll('_', ' ')
                                .toLowerCase()
                                .split(' ')
                                .map((word) => word[0].toUpperCase() + word.substring(1))
                                .join(' ') ?? 'Unknown',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: _getNotificationColor(widget.notification.typeStr),
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            widget.notification.createdAt != null
                                ? DateFormatter.formatRelativeTime(widget.notification.createdAt!)
                                : 'Unknown time',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context).textTheme.bodySmall?.color?.withOpacity(0.6),
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Delete button
                    if (widget.onDelete != null)
                      Container(
                        margin: EdgeInsets.only(left: 8),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () => _showDeleteDialog(context),
                            borderRadius: BorderRadius.circular(8),
                            child: Container(
                              padding: EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: Colors.red.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: Colors.red.withOpacity(0.2),
                                ),
                              ),
                              child: Icon(
                                Icons.delete_outline_rounded,
                                size: 18,
                                color: Colors.red,
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),

                SizedBox(height: 16),

                // Title
                Text(
                  widget.notification.title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    height: 1.3,
                  ),
                ),

                SizedBox(height: 16),

                // Capture preview and info
                Row(
                  children: [
                    if (captures.isNotEmpty) ...[
                      // Stacked preview thumbnails with improved styling
                      Container(
                        width: 100,
                        height: 56,
                        child: Stack(
                          children: captures.take(3).toList().asMap().entries.map((entry) {
                            int index = entry.key;
                            return Positioned(
                              left: index * 20.0,
                              child: Container(
                                width: 56,
                                height: 56,
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color: Theme.of(context).cardTheme.color!,
                                    width: 3,
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.1),
                                      offset: Offset(0, 2),
                                      blurRadius: 4,
                                    ),
                                  ],
                                ),
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(9),
                                  child: Image.network(
                                    captureBaseUrl + entry.value.path,
                                    width: 56,
                                    height: 56,
                                    fit: BoxFit.cover,
                                    errorBuilder: (context, error, stackTrace) {
                                      return Container(
                                        color: Theme.of(context).colorScheme.surface,
                                        child: Icon(
                                          Icons.image_rounded,
                                          size: 24,
                                          color: Theme.of(context).colorScheme.outline,
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                      SizedBox(width: 16),
                    ],

                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (captures.isNotEmpty) ...[
                            Container(
                              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                  color: Theme.of(context).colorScheme.primary.withOpacity(0.2),
                                ),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.photo_camera_rounded,
                                    size: 16,
                                    color: Theme.of(context).colorScheme.primary,
                                  ),
                                  SizedBox(width: 6),
                                  Text(
                                    '${captures.length} capture${captures.length != 1 ? 's' : ''}',
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.w500,
                                      color: Theme.of(context).colorScheme.primary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ] else ...[
                            Container(
                              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: Theme.of(context).colorScheme.surface.withOpacity(0.5),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                  color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
                                ),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.image_not_supported_rounded,
                                    size: 16,
                                    color: Theme.of(context).colorScheme.outline,
                                  ),
                                  SizedBox(width: 6),
                                  Text(
                                    'No captures',
                                    style: TextStyle(
                                      fontSize: 14,
                                      color: Theme.of(context).colorScheme.outline,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),

                // Expand button (only if there are captures)
                if (captures.isNotEmpty) ...[
                  SizedBox(height: 16),
                  InkWell(
                    onTap: widget.onToggleExpanded,
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: widget.isExpanded
                            ? Theme.of(context).colorScheme.primary.withOpacity(0.1)
                            : Theme.of(context).colorScheme.surface.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: widget.isExpanded
                              ? Theme.of(context).colorScheme.primary.withOpacity(0.3)
                              : Theme.of(context).colorScheme.outline.withOpacity(0.2),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            widget.isExpanded ? 'Hide captures' : 'View captures',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                              color: widget.isExpanded
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).textTheme.bodyMedium?.color,
                            ),
                          ),
                          SizedBox(width: 8),
                          AnimatedRotation(
                            turns: widget.isExpanded ? 0.5 : 0,
                            duration: Duration(milliseconds: 300),
                            child: Icon(
                              Icons.expand_more_rounded,
                              size: 18,
                              color: widget.isExpanded
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).textTheme.bodyMedium?.color,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),

          // Expanded content (carousel)
          SizeTransition(
            sizeFactor: _expandAnimation,
            child: widget.isExpanded && captures.isNotEmpty
                ? Container(
                    padding: EdgeInsets.fromLTRB(20, 0, 20, 20),
                    decoration: BoxDecoration(
                      border: Border(
                        top: BorderSide(
                          color: Theme.of(context).colorScheme.outline.withOpacity(0.1),
                        ),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(height: 16),
                        Row(
                          children: [
                            Icon(
                              Icons.photo_library_rounded,
                              size: 18,
                              color: Theme.of(context).textTheme.titleSmall?.color,
                            ),
                            SizedBox(width: 8),
                            Text(
                              'Captures (${captures.length})',
                              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: 16),
                        Container(
                          height: 120,
                          child: ListView.builder(
                            scrollDirection: Axis.horizontal,
                            physics: BouncingScrollPhysics(),
                            itemCount: captures.length,
                            itemBuilder: (context, index) {
                              return GestureDetector(
                                onTap: () => widget.onCapturePressed(index),
                                child: Container(
                                  width: 96,
                                  margin: EdgeInsets.only(right: 12),
                                  child: Column(
                                    children: [
                                      Hero(
                                        tag: 'capture_${captures[index].id}',
                                        child: Container(
                                          width: 96,
                                          height: 96,
                                          decoration: BoxDecoration(
                                            color: Theme.of(context).colorScheme.surface,
                                            borderRadius: BorderRadius.circular(12),
                                            border: Border.all(
                                              color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
                                            ),
                                            boxShadow: [
                                              BoxShadow(
                                                color: Colors.black.withOpacity(0.1),
                                                offset: Offset(0, 2),
                                                blurRadius: 6,
                                              ),
                                            ],
                                          ),
                                          child: ClipRRect(
                                            borderRadius: BorderRadius.circular(11),
                                            child: Stack(
                                              children: [
                                                Image.network(
                                                  captureBaseUrl + captures[index].path,
                                                  width: 96,
                                                  height: 96,
                                                  fit: BoxFit.cover,
                                                  errorBuilder: (context, error, stackTrace) {
                                                    return Container(
                                                      color: Theme.of(context).colorScheme.surface,
                                                      child: Column(
                                                        mainAxisAlignment: MainAxisAlignment.center,
                                                        children: [
                                                          Icon(
                                                            Icons.broken_image_rounded,
                                                            size: 24,
                                                            color: Theme.of(context).colorScheme.outline,
                                                          ),
                                                          SizedBox(height: 2),
                                                          Text(
                                                            'Failed',
                                                            style: TextStyle(
                                                              fontSize: 8,
                                                              color: Theme.of(context).colorScheme.outline,
                                                            ),
                                                          ),
                                                        ],
                                                      ),
                                                    );
                                                  },
                                                  loadingBuilder: (context, child, loadingProgress) {
                                                    if (loadingProgress == null) return child;
                                                    return Container(
                                                      color: Theme.of(context).colorScheme.surface.withOpacity(0.5),
                                                      child: Center(
                                                        child: CircularProgressIndicator(
                                                          strokeWidth: 2,
                                                          value: loadingProgress.expectedTotalBytes != null
                                                              ? loadingProgress.cumulativeBytesLoaded /
                                                                loadingProgress.expectedTotalBytes!
                                                              : null,
                                                          color: Theme.of(context).colorScheme.primary,
                                                        ),
                                                      ),
                                                    );
                                                  },
                                                ),
                                                // Play overlay for video-like appearance
                                                Positioned.fill(
                                                  child: Container(
                                                    decoration: BoxDecoration(
                                                      gradient: LinearGradient(
                                                        begin: Alignment.topCenter,
                                                        end: Alignment.bottomCenter,
                                                        colors: [
                                                          Colors.transparent,
                                                          Colors.black.withOpacity(0.1),
                                                        ],
                                                      ),
                                                    ),
                                                    child: Center(
                                                      child: Container(
                                                        padding: EdgeInsets.all(6),
                                                        decoration: BoxDecoration(
                                                          color: Colors.black.withOpacity(0.6),
                                                          shape: BoxShape.circle,
                                                        ),
                                                        child: Icon(
                                                          Icons.play_arrow_rounded,
                                                          color: Colors.white,
                                                          size: 16,
                                                        ),
                                                      ),
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ),
                                      ),
                                      SizedBox(height: 6),
                                      Flexible(
                                        child: Container(
                                          padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: Theme.of(context).colorScheme.surface.withOpacity(0.5),
                                            borderRadius: BorderRadius.circular(8),
                                          ),
                                          child: Text(
                                            DateFormatter.formatRelativeTime(captures[index].createdAt),
                                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                              fontSize: 10,
                                              fontWeight: FontWeight.w500,
                                            ),
                                            textAlign: TextAlign.center,
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  )
                : SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}
