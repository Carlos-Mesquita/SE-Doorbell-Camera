import 'package:doorbell_app/config/env_config.dart';
import 'package:doorbell_app/models/capture.dart' as app_notification_model;
import 'package:flutter/material.dart';
import 'package:doorbell_app/services/api_service.dart';
import 'package:doorbell_app/models/notification.dart' as app_notification_model;
/*
class StopMotionViewerScreen extends StatefulWidget {
  final ApiService apiService;
  final String? initialNotificationId;
  final String? initialRpiEventId;

  const StopMotionViewerScreen({
    super.key,
    required this.apiService,
    this.initialNotificationId,
    this.initialRpiEventId,
  });

  @override
  State<StopMotionViewerScreen> createState() => _StopMotionViewerScreenState();
}

class _StopMotionViewerScreenState extends State<StopMotionViewerScreen> {
  List<app_notification_model.Notification> _notifications = [];
  bool _isLoading = true;
  String? _error;
  late String captureBaseUrl;

  final ScrollController _scrollController = ScrollController();
  final Map<int, GlobalKey> _notificationKeys = {};

  @override
  void initState() {
    super.initState();
    captureBaseUrl = EnvConfig.captureBase;
    _fetchNotifications();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _fetchNotifications() async {
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final fetchedNotifications = await widget.apiService.getAllNotifications(
        sortBy: 'created_at',
        sortOrder: 'desc',
      );
      if (!mounted) return;

      _notificationKeys.clear();
      for (var notification in fetchedNotifications) {
        _notificationKeys[notification.id] = GlobalKey();
      }

      setState(() {
        _notifications = fetchedNotifications;
        _isLoading = false;
      });

      if (widget.initialNotificationId != null) {
        _scrollToNotificationById(widget.initialNotificationId!);
      } else if (widget.initialRpiEventId != null) {
        _scrollToNotificationByRpiEventId(widget.initialRpiEventId!);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = "Failed to load notification history: $e";
        _isLoading = false;
      });
      print('Error fetching notifications: $e');
    }
  }

  void _scrollToNotificationById(String notificationIdStr) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      try {
        final int notificationId = int.parse(notificationIdStr);
        final GlobalKey? itemKey = _notificationKeys[notificationId];
        if (itemKey != null && itemKey.currentContext != null) {
          Scrollable.ensureVisible(
            itemKey.currentContext!,
            duration: const Duration(milliseconds: 500),
            curve: Curves.easeInOut,
            alignment: 0.5,
          );
        } else {
          print("Could not find or scroll to notification ID $notificationId (key not found or context null).");
        }
      } catch (e) {
        print("Error parsing or scrolling to notification ID $notificationIdStr: $e");
      }
    });
  }

    void _scrollToNotificationByRpiEventId(String rpiEventId) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      app_notification_model.Notification? targetNotification; // Make it nullable
      try {
        targetNotification = _notifications.firstWhere(
          (n) => n.rpiEventId == rpiEventId,
        );
      } catch (e) {
        targetNotification = null;
        print("Notification with RPI event ID $rpiEventId not found in list (firstWhere failed).");
      }

      if (targetNotification != null) {
        final GlobalKey? itemKey = _notificationKeys[targetNotification.id];
        if (itemKey != null && itemKey.currentContext != null) {
          Scrollable.ensureVisible(
            itemKey.currentContext!,
            duration: const Duration(milliseconds: 500),
            curve: Curves.easeInOut,
            alignment: 0.5, // Try to align the item to the center of the viewport
          );
        } else {
          print("Could not find key or context for notification (ID: ${targetNotification.id}) to scroll for RPI event ID $rpiEventId.");
        }
      }
    });
  }

  Future<void> _deleteNotification(app_notification_model.Notification notification) async {
    bool? confirmDelete = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Delete Notification"),
        content: Text("Are you sure you want to delete '${notification.title}' and all associated captures? This action cannot be undone."),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15.0)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text("Cancel"),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            onPressed: () => Navigator.pop(context, true),
            child: const Text("Delete"),
          ),
        ],
      ),
    );

    if (confirmDelete == true) {
      try {
        bool success = await widget.apiService.deleteNotification(notification.id);
        if (!mounted) return;
        if (success) {
          setState(() {
            _notifications.removeWhere((n) => n.id == notification.id);
            _notificationKeys.remove(notification.id);
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("'${notification.title}' deleted successfully."), backgroundColor: Colors.green),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("Failed to delete '${notification.title}'. Please try again."), backgroundColor: Colors.red),
          );
        }
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error deleting notification: $e"), backgroundColor: Colors.red),
        );
        print('Error deleting notification: $e');
      }
    }
  }

  Widget _buildImageThumbnail(app_notification_model.CaptureInfo captureInfo) {
    final imageUrl = '${captureBaseUrl}${captureInfo.path}';
    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: Card(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
        clipBehavior: Clip.antiAlias,
        child: Image.network(
          imageUrl,
          width: 100,
          height: 120,
          fit: BoxFit.cover,
          loadingBuilder: (BuildContext context, Widget child, ImageChunkEvent? loadingProgress) {
            if (loadingProgress == null) return child;
            return Container(
              width: 100,
              height: 120,
              color: Colors.grey[200],
              child: Center(
                child: CircularProgressIndicator(
                  strokeWidth: 2.0,
                  value: loadingProgress.expectedTotalBytes != null
                      ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                      : null,
                ),
              ),
            );
          },
          errorBuilder: (BuildContext context, Object exception, StackTrace? stackTrace) {
            return Container(
              width: 100,
              height: 120,
              color: Colors.grey[200],
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.broken_image_outlined, color: Colors.grey[400], size: 30),
                  const SizedBox(height: 4),
                  Text("No Image", style: TextStyle(fontSize: 10, color: Colors.grey[600])),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Event History'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: "Refresh history",
            onPressed: _isLoading ? null : _fetchNotifications,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, color: Colors.red[300], size: 60),
              const SizedBox(height: 20),
              Text("Error Loading History", style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.red[700])),
              const SizedBox(height: 10),
              Text(_error!, style: TextStyle(color: Colors.red[700]), textAlign: TextAlign.center),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                icon: const Icon(Icons.refresh),
                label: const Text("Try Again"),
                onPressed: _fetchNotifications,
              )
            ],
          ),
        ),
      );
    }
    if (_notifications.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.history_toggle_off_outlined, color: Colors.grey[400], size: 80),
            const SizedBox(height: 20),
            Text('No notifications recorded yet.', style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.grey[600])),
             const SizedBox(height: 10),
            Text('Events from your doorbell will appear here.', style: TextStyle(color: Colors.grey[600]), textAlign: TextAlign.center),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchNotifications,
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(8.0),
        itemCount: _notifications.length,
        itemBuilder: (context, index) {
          final notification = _notifications[index];
          final GlobalKey itemKey = _notificationKeys[notification.id] ?? GlobalKey();
           _notificationKeys[notification.id] = itemKey;

          bool isHighlighted = false;
          if (widget.initialNotificationId != null) {
            try { isHighlighted = (notification.id == int.parse(widget.initialNotificationId!)); } catch(_){}
          } else if (widget.initialRpiEventId != null) {
            isHighlighted = (notification.rpiEventId == widget.initialRpiEventId);
          }

          final title = notification.title;
          final parsedDate = DateTime.tryParse(notification.createdAt)?.toLocal();
          final dateString = parsedDate != null ?
            '${parsedDate.year}-${parsedDate.month.toString().padLeft(2, '0')}-${parsedDate.day.toString().padLeft(2, '0')} ${parsedDate.hour.toString().padLeft(2, '0')}:${parsedDate.minute.toString().padLeft(2, '0')}'
            : notification.createdAt;
          final subtitle = '${notification.typeStr?.replaceAll('_', ' ').toUpperCase() ?? "EVENT"} - $dateString';

          return Card(
            key: itemKey,
            margin: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 4.0),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            elevation: 3,
            color: isHighlighted ? Theme.of(context).highlightColor.withOpacity(0.7) : null,
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: notification.captures.isNotEmpty ? () {
                 final imageUrls = notification.captures.map((c) => '$captureBaseUrl${c.path}').toList();
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => SequenceViewer(imageUrls: imageUrls, initialIndex: 0),
                    ),
                  );
              } : null,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                               Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600, fontSize: 18)),
                               const SizedBox(height: 4),
                               Text(subtitle, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[700], fontSize: 12)),
                            ],
                          ),
                        ),
                        Material(
                          color: Colors.transparent,
                          child: IconButton(
                            icon: const Icon(Icons.delete_sweep_outlined),
                            color: Colors.red[300],
                            tooltip: "Delete Notification",
                            iconSize: 24.0,
                            splashRadius: 20.0,
                            onPressed: () => _deleteNotification(notification),
                          ),
                        ),
                      ],
                    ),
                    if (notification.captures.isNotEmpty) ...[
                      const SizedBox(height: 12),


                      SizedBox(
                        height: 120,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          itemCount: notification.captures.length,
                          itemBuilder: (context, imageIndex) {
                            final captureInfo = notification.captures[imageIndex];
                            final imageUrls = notification.captures.map((c) => '$captureBaseUrl${c.path}').toList();

                            return Hero(
                              tag: 'capture-${captureInfo.id ?? imageIndex}',
                              child: GestureDetector(
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => SequenceViewer(
                                        imageUrls: imageUrls,
                                        initialIndex: imageIndex,
                                        heroTagPrefix: 'capture-',
                                      ),
                                    ),
                                  );
                                },
                                child: _buildImageThumbnail(captureInfo),
                              ),
                            );
                          },
                        ),
                      ),
                    ] else ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 10),
                        decoration: BoxDecoration(
                          color: Colors.grey[100],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          "No captures associated with this event.",
                          style: TextStyle(fontStyle: FontStyle.italic, color: Colors.grey[600]),
                        ),
                      ),
                    ]
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class SequenceViewer extends StatefulWidget {
  final List<String> imageUrls;
  final int initialIndex;
  final String? heroTagPrefix;

  const SequenceViewer({
    super.key,
    required this.imageUrls,
    this.initialIndex = 0,
    this.heroTagPrefix,
  });

  @override
  State<SequenceViewer> createState() => _SequenceViewerState();
}

class _SequenceViewerState extends State<SequenceViewer> {
  late PageController _pageController;
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

   @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.imageUrls.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('View Sequence')),
        body: const Center(child: Text('No images in this sequence.')),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text('Image ${_currentIndex + 1} of ${widget.imageUrls.length}'),
        backgroundColor: Colors.black.withOpacity(0.6),
        elevation: 0,
      ),
      body: Stack(
        alignment: Alignment.center,
        children: [
          PageView.builder(
            controller: _pageController,
            itemCount: widget.imageUrls.length,
            onPageChanged: (index) {
              if(mounted) {
                setState(() {
                  _currentIndex = index;
                });
              }
            },
            itemBuilder: (context, index) {
              final uniqueHeroTag = widget.heroTagPrefix != null ? '${widget.heroTagPrefix}${widget.imageUrls[index].hashCode}' : null;
              return HeroMode(
                enabled: uniqueHeroTag != null,
                child: Hero(
                  tag: uniqueHeroTag ?? ValueKey(widget.imageUrls[index]),
                  child: InteractiveViewer(
                    panEnabled: true,
                    minScale: 1.0,
                    maxScale: 5.0,
                    child: Center(
                      child: Image.network(
                        widget.imageUrls[index],
                        fit: BoxFit.contain,
                        loadingBuilder: (BuildContext context, Widget child, ImageChunkEvent? loadingProgress) {
                          if (loadingProgress == null) return child;
                          return Center(child: CircularProgressIndicator(
                             value: loadingProgress.expectedTotalBytes != null
                                ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                                : null,
                          ));
                        },
                        errorBuilder: (BuildContext context, Object exception, StackTrace? stackTrace) {
                          return const Center(child: Icon(Icons.broken_image_sharp, color: Colors.white54, size: 60));
                        },
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
          if (widget.imageUrls.length > 1)
            Positioned(
              left: 0,
              child: Material(
                color: Colors.transparent,
                child: IconButton(
                  icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white70, size: 30),
                  onPressed: _currentIndex > 0 ? () {
                    _pageController.previousPage(duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
                  } : null,
                  splashRadius: 24,
                ),
              ),
            ),
          if (widget.imageUrls.length > 1)
            Positioned(
              right: 0,
              child: Material(
                 color: Colors.transparent,
                child: IconButton(
                  icon: const Icon(Icons.arrow_forward_ios, color: Colors.white70, size: 30),
                  onPressed: _currentIndex < widget.imageUrls.length - 1 ? () {
                    _pageController.nextPage(duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
                  } : null,
                  splashRadius: 24,
                ),
              ),
            ),
        ],
      ),
    );
  }
}*/
