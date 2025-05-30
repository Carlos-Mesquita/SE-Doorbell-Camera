import 'package:doorbell_app/models/notification.dart';
import 'package:doorbell_app/services/api_service.dart';
import 'package:doorbell_app/utils/notification_grouping.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import './notifications/search.dart';
import './notifications/card.dart';
import './notifications/carousel.dart';

class NotificationListScreen extends StatefulWidget {
  const NotificationListScreen({super.key});

  @override
  _NotificationListScreenState createState() => _NotificationListScreenState();
}

class _NotificationListScreenState extends State<NotificationListScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ApiService _apiService = GetIt.instance<ApiService>();

  bool _showFilters = false;
  bool _isLoading = true;
  bool _hasError = false;
  String _errorMessage = '';
  final Set<int> _expandedCards = <int>{};
  final List<String> _selectedTypes = [];
  String _selectedDateRange = 'all';
  List<NotificationDTO> _notifications = [];
  bool _enableGrouping = true;

  int _currentPage = 1;
  final int _pageSize = 20;
  bool _hasMoreData = true;
  bool _isLoadingMore = false;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadNotifications({bool loadMore = false}) async {
    if (loadMore) {
      if (_isLoadingMore || !_hasMoreData) return;
      setState(() {
        _isLoadingMore = true;
      });
    } else {
      setState(() {
        _isLoading = true;
        _hasError = false;
        _currentPage = 1;
        _hasMoreData = true;
      });
    }

    try {
      final notifications = await _apiService.getAllNotifications(
        page: loadMore ? _currentPage + 1 : 1,
        pageSize: _pageSize,
        sortBy: 'created_at',
        sortOrder: 'desc',
      );

      setState(() {
        if (loadMore) {
          _notifications.addAll(notifications);
          _currentPage++;
          _isLoadingMore = false;
          _hasMoreData = notifications.length == _pageSize;
        } else {
          _notifications = notifications;
          _isLoading = false;
          _hasMoreData = notifications.length == _pageSize;
        }
      });
    } catch (e) {
      setState(() {
        _hasError = true;
        _errorMessage = e.toString();
        _isLoading = false;
        _isLoadingMore = false;
      });
    }
  }

  Future<void> _refreshNotifications() async {
    setState(() {
      _expandedCards.clear();
      _currentPage = 1;
      _hasMoreData = true;
      _notifications.clear();
    });
    await _loadNotifications();
  }

  Future<void> _deleteNotification(int notificationId) async {
    try {
      final success = await _apiService.deleteNotification(notificationId);
      if (success) {
        setState(() {
          _notifications.removeWhere((n) => n.id == notificationId);
          _expandedCards.remove(notificationId);
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Notification deleted successfully'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        throw Exception('Failed to delete notification');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to delete notification: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  List<NotificationDTO> get _filteredNotifications {
    List<NotificationDTO> filtered = _notifications;

    if (_searchController.text.isNotEmpty) {
      filtered = filtered.where((n) =>
        n.title.toLowerCase().contains(_searchController.text.toLowerCase()) ||
        (n.typeStr?.toLowerCase().contains(_searchController.text.toLowerCase()) ?? false)
      ).toList();
    }

    if (_selectedTypes.isNotEmpty) {
      filtered = filtered.where((n) => _selectedTypes.contains(n.typeStr)).toList();
    }

    if (_selectedDateRange != 'all') {
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final weekAgo = today.subtract(Duration(days: 7));
      final monthAgo = today.subtract(Duration(days: 30));

      filtered = filtered.where((n) {
        final notificationDate = DateTime.tryParse(n.createdAt)!;
        switch (_selectedDateRange) {
          case 'today':
            return notificationDate.isAfter(today);
          case 'week':
            return notificationDate.isAfter(weekAgo);
          case 'month':
            return notificationDate.isAfter(monthAgo);
          default:
            return true;
        }
      }).toList();
    }

    return filtered;
  }

  List<NotificationGroup> get _groupedNotifications {
    final filtered = _filteredNotifications;
    return NotificationGrouping.groupSequentialNotifications(
      filtered,
      enableGrouping: _enableGrouping,
    );
  }

  List<String> get _notificationTypes {
    return _notifications
        .map((n) => n.typeStr)
        .where((type) => type != null)
        .cast<String>()
        .toSet()
        .toList();
  }

  int get _activeFilterCount {
    return _selectedTypes.length + (_selectedDateRange != 'all' ? 1 : 0);
  }

  String _generateGroupKey(NotificationGroup group) {
    final captureCount = group.allCaptures.length;
    final notificationCount = group.notifications.length;
    final lastCreatedAt = group.lastCreatedAt.millisecondsSinceEpoch;
    final firstNotificationId = group.notifications.isNotEmpty ? group.notifications.first.id : 0;
    return 'notification_group_${firstNotificationId}_${notificationCount}_${captureCount}_$lastCreatedAt';
  }

  void _toggleExpanded(int id) {
    setState(() {
      if (_expandedCards.contains(id)) {
        _expandedCards.remove(id);
      } else {
        _expandedCards.add(id);
      }
    });
  }

  void _clearFilters() {
    setState(() {
      _selectedTypes.clear();
      _selectedDateRange = 'all';
      _searchController.clear();
    });
  }

  void _openCarousel(NotificationDTO notification, int startIndex) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => MediaCarouselScreen(
          notification: notification,
          startIndex: startIndex,
        ),
      ),
    );
  }

  void _onTypeToggle(String type) {
    setState(() {
      if (_selectedTypes.contains(type)) {
        _selectedTypes.remove(type);
      } else {
        _selectedTypes.add(type);
      }
    });
  }

  void _onDateRangeChange(String dateRange) {
    setState(() {
      _selectedDateRange = dateRange;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: Column(
        children: [
          SearchHeader(
            searchController: _searchController,
            showFilters: _showFilters,
            activeFilterCount: _activeFilterCount,
            notificationTypes: _notificationTypes,
            selectedTypes: _selectedTypes,
            selectedDateRange: _selectedDateRange,
            onToggleFilters: () {
              setState(() {
                _showFilters = !_showFilters;
              });
            },
            onTypeToggle: _onTypeToggle,
            onDateRangeChange: _onDateRangeChange,
            onClearFilters: _clearFilters,
            onSearchChanged: () => setState(() {}),
          ),

          if (!_isLoading) ...[
            Container(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      '${_groupedNotifications.length} ${_enableGrouping ? 'groups' : 'notifications'} of ${_notifications.length} total'
                      '${_searchController.text.isNotEmpty ? ' matching "${_searchController.text}"' : ''}',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).textTheme.bodyMedium?.color?.withOpacity(0.7),
                      ),
                    ),
                  ),
                  Row(
                    children: [
                      // Grouping toggle
                      Container(
                        margin: EdgeInsets.only(right: 8),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () {
                              setState(() {
                                _enableGrouping = !_enableGrouping;
                                // Clear expanded state when toggling grouping
                                _expandedCards.clear();
                              });
                            },
                            borderRadius: BorderRadius.circular(8),
                            child: Container(
                              padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: _enableGrouping
                                    ? Theme.of(context).colorScheme.primary.withOpacity(0.1)
                                    : Theme.of(context).colorScheme.surface.withOpacity(0.5),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: _enableGrouping
                                      ? Theme.of(context).colorScheme.primary.withOpacity(0.3)
                                      : Theme.of(context).colorScheme.outline.withOpacity(0.2),
                                ),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    _enableGrouping ? Icons.group_work_rounded : Icons.list_rounded,
                                    size: 14,
                                    color: _enableGrouping
                                        ? Theme.of(context).colorScheme.primary
                                        : Theme.of(context).textTheme.bodyMedium?.color,
                                  ),
                                  SizedBox(width: 4),
                                  Text(
                                    _enableGrouping ? 'Grouped' : 'List',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w500,
                                      color: _enableGrouping
                                          ? Theme.of(context).colorScheme.primary
                                          : Theme.of(context).textTheme.bodyMedium?.color,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                      if (_activeFilterCount > 0)
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                            ),
                          ),
                          child: Text(
                            '$_activeFilterCount filter${_activeFilterCount != 1 ? 's' : ''} active',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],

          Expanded(
            child: _buildContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return _buildLoadingState();
    }

    if (_hasError) {
      return _buildErrorState();
    }

    if (_groupedNotifications.isEmpty) {
      return _buildEmptyState();
    }

    return RefreshIndicator(
      onRefresh: _refreshNotifications,
      child: NotificationListener<ScrollNotification>(
        onNotification: (ScrollNotification scrollInfo) {
          // Load more when user scrolls near bottom
          if (scrollInfo.metrics.pixels >= scrollInfo.metrics.maxScrollExtent - 200) {
            if (_hasMoreData && !_isLoadingMore) {
              _loadNotifications(loadMore: true);
            }
          }
          return false;
        },
        child: ListView.builder(
          padding: EdgeInsets.all(16),
          itemCount: _groupedNotifications.length + (_hasMoreData ? 1 : 0),
          itemBuilder: (context, index) {
            if (index == _groupedNotifications.length) {
              return _buildLoadMoreIndicator();
            }

            final group = _groupedNotifications[index];
            final displayNotification = NotificationGrouping.createGroupedNotificationDTO(group);
            final groupKey = _generateGroupKey(group);

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Group header (only for groups with multiple notifications)
                if (group.notifications.length > 1) ...[
                  Container(
                    margin: EdgeInsets.only(bottom: 8, left: 4),
                    child: Row(
                      children: [
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: Theme.of(context).colorScheme.primary.withOpacity(0.2),
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.group_work_rounded,
                                size: 14,
                                color: Theme.of(context).colorScheme.primary,
                              ),
                              SizedBox(width: 4),
                              Text(
                                '${group.notifications.length} events',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                              ),
                              if (group.groupTitle.isNotEmpty) ...[
                                SizedBox(width: 8),
                                Text(
                                  '• ${group.groupTitle}',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: Theme.of(context).colorScheme.primary.withOpacity(0.7),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],

                // Notification card with content-sensitive key
                Dismissible(
                  key: Key(groupKey),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    alignment: Alignment.centerRight,
                    padding: EdgeInsets.only(right: 20),
                    margin: EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: Colors.red,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      Icons.delete,
                      color: Colors.white,
                      size: 24,
                    ),
                  ),
                  confirmDismiss: (direction) async {
                    if (group.notifications.length > 1) {
                      return await showDialog<bool>(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: Text('Delete Notification Group'),
                          content: Text('Are you sure you want to delete all ${group.notifications.length} notifications in this group?'),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.of(context).pop(false),
                              child: Text('Cancel'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.of(context).pop(true),
                              style: TextButton.styleFrom(foregroundColor: Colors.red),
                              child: Text('Delete All'),
                            ),
                          ],
                        ),
                      );
                    } else {
                      return await showDialog<bool>(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: Text('Delete Notification'),
                          content: Text('Are you sure you want to delete this notification?'),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.of(context).pop(false),
                              child: Text('Cancel'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.of(context).pop(true),
                              style: TextButton.styleFrom(foregroundColor: Colors.red),
                              child: Text('Delete'),
                            ),
                          ],
                        ),
                      );
                    }
                  },
                  onDismissed: (direction) {
                    if (group.notifications.length > 1) {
                      // Delete all notifications in the group
                      for (final notification in group.notifications) {
                        _deleteNotification(notification.id);
                      }
                    } else {
                      _deleteNotification(group.notifications.first.id);
                    }
                  },
                  child: NotificationCard(
                    key: Key('card_$groupKey'),
                    notification: displayNotification,
                    isExpanded: _expandedCards.contains(group.notifications.first.id),
                    onToggleExpanded: () => _toggleExpanded(group.notifications.first.id),
                    onCapturePressed: (captureIndex) => _openCarousel(displayNotification, captureIndex),
                    onDelete: () {
                      if (group.notifications.length > 1) {
                        // Show dialog for group deletion
                        showDialog<bool>(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: Text('Delete Notification Group'),
                            content: Text('Are you sure you want to delete all ${group.notifications.length} notifications in this group?'),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.of(context).pop(false),
                                child: Text('Cancel'),
                              ),
                              TextButton(
                                onPressed: () {
                                  Navigator.of(context).pop(true);
                                  // Delete all notifications in the group
                                  for (final notification in group.notifications) {
                                    _deleteNotification(notification.id);
                                  }
                                },
                                style: TextButton.styleFrom(foregroundColor: Colors.red),
                                child: Text('Delete All'),
                              ),
                            ],
                          ),
                        );
                                              } else {
                        _deleteNotification(group.notifications.first.id);
                      }
                    },
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text(
            'Loading notifications...',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).textTheme.bodyMedium?.color?.withOpacity(0.7),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(48),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                shape: BoxShape.circle,
                border: Border.all(
                  color: Colors.red.withOpacity(0.3),
                  width: 2,
                ),
              ),
              child: Icon(
                Icons.error_outline_rounded,
                size: 40,
                color: Colors.red,
              ),
            ),
            SizedBox(height: 24),
            Text(
              'Failed to load notifications',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            SizedBox(height: 8),
            Text(
              _errorMessage,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).textTheme.bodyMedium?.color?.withOpacity(0.7),
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _loadNotifications,
              icon: Icon(Icons.refresh_rounded, size: 18),
              label: Text('Retry'),
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(48),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                shape: BoxShape.circle,
                border: Border.all(
                  color: Theme.of(context).colorScheme.outline.withOpacity(0.3),
                  width: 2,
                ),
              ),
              child: Icon(
                Icons.search_off_rounded,
                size: 40,
                color: Theme.of(context).colorScheme.outline,
              ),
            ),
            SizedBox(height: 24),
            Text(
              'No notifications found',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            SizedBox(height: 8),
            Text(
              _searchController.text.isNotEmpty || _activeFilterCount > 0
                  ? 'Try adjusting your search terms or filters'
                  : 'No notifications to display at this time',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).textTheme.bodyMedium?.color?.withOpacity(0.7),
              ),
              textAlign: TextAlign.center,
            ),
            if (_searchController.text.isNotEmpty || _activeFilterCount > 0) ...[
              SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _clearFilters,
                icon: Icon(Icons.clear_all_rounded, size: 18),
                label: Text('Clear search and filters'),
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildLoadMoreIndicator() {
    if (!_isLoadingMore) return SizedBox.shrink();

    return Padding(
      padding: EdgeInsets.all(16),
      child: Center(
        child: CircularProgressIndicator(),
      ),
    );
  }
}
