import 'package:flutter/material.dart';

class FilterPanel extends StatelessWidget {
  final List<String> notificationTypes;
  final List<String> selectedTypes;
  final String selectedDateRange;
  final int activeFilterCount;
  final Function(String) onTypeToggle;
  final Function(String) onDateRangeChange;
  final VoidCallback onClearFilters;

  const FilterPanel({
    super.key,
    required this.notificationTypes,
    required this.selectedTypes,
    required this.selectedDateRange,
    required this.activeFilterCount,
    required this.onTypeToggle,
    required this.onDateRangeChange,
    required this.onClearFilters,
  });

  String _formatNotificationType(String type) {
    return type
        .replaceAll('_', ' ')
        .toLowerCase()
        .split(' ')
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            offset: Offset(0, 4),
            blurRadius: 12,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.filter_alt_rounded,
                    size: 20,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Filters',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
              if (activeFilterCount > 0)
                TextButton.icon(
                  onPressed: onClearFilters,
                  icon: Icon(Icons.clear_all_rounded, size: 18),
                  label: Text('Clear all'),
                  style: TextButton.styleFrom(
                    foregroundColor: Theme.of(context).colorScheme.primary,
                    padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                ),
            ],
          ),
          SizedBox(height: 20),

          // Responsive layout for filters
          LayoutBuilder(
            builder: (context, constraints) {
              if (constraints.maxWidth > 600) {
                // Wide layout - side by side
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: _buildNotificationTypeFilter(context)),
                    SizedBox(width: 24),
                    Expanded(child: _buildDateRangeFilter(context)),
                  ],
                );
              } else {
                // Narrow layout - stacked
                return Column(
                  children: [
                    _buildNotificationTypeFilter(context),
                    SizedBox(height: 20),
                    _buildDateRangeFilter(context),
                  ],
                );
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildNotificationTypeFilter(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Notification Type',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.w600,
            color: Theme.of(context).textTheme.bodyLarge?.color,
          ),
        ),
        SizedBox(height: 12),
        if (notificationTypes.isEmpty)
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface.withOpacity(0.5),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline_rounded,
                  size: 16,
                  color: Theme.of(context).colorScheme.outline,
                ),
                SizedBox(width: 8),
                Text(
                  'No notification types available',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
                ),
              ],
            ),
          )
        else
          ...notificationTypes.map((type) => Container(
            margin: EdgeInsets.only(bottom: 8),
            decoration: BoxDecoration(
              color: selectedTypes.contains(type)
                  ? Theme.of(context).colorScheme.primary.withOpacity(0.1)
                  : Theme.of(context).colorScheme.surface.withOpacity(0.3),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: selectedTypes.contains(type)
                    ? Theme.of(context).colorScheme.primary.withOpacity(0.3)
                    : Theme.of(context).colorScheme.outline.withOpacity(0.2),
              ),
            ),
            child: CheckboxListTile(
              dense: true,
              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              title: Text(
                _formatNotificationType(type),
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: selectedTypes.contains(type)
                      ? FontWeight.w500
                      : FontWeight.normal,
                ),
              ),
              value: selectedTypes.contains(type),
              onChanged: (bool? value) => onTypeToggle(type),
              activeColor: Theme.of(context).colorScheme.primary,
              checkColor: Colors.white,
              side: BorderSide(
                color: Theme.of(context).colorScheme.outline.withOpacity(0.5),
                width: 2,
              ),
            ),
          )),
      ],
    );
  }

  Widget _buildDateRangeFilter(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Date Range',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.w600,
            color: Theme.of(context).textTheme.bodyLarge?.color,
          ),
        ),
        SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                offset: Offset(0, 2),
                blurRadius: 4,
              ),
            ],
          ),
          child: DropdownButtonFormField<String>(
            value: selectedDateRange,
            style: Theme.of(context).textTheme.bodyMedium,
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: Theme.of(context).colorScheme.outline.withOpacity(0.3),
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: Theme.of(context).colorScheme.primary,
                  width: 2,
                ),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: Theme.of(context).colorScheme.outline.withOpacity(0.3),
                ),
              ),
              filled: true,
              fillColor: Theme.of(context).inputDecorationTheme.fillColor,
              contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            ),
            dropdownColor: Theme.of(context).cardTheme.color,
            icon: Icon(
              Icons.keyboard_arrow_down_rounded,
              color: Theme.of(context).iconTheme.color,
            ),
            items: [
              DropdownMenuItem(
                value: 'all',
                child: Row(
                  children: [
                    Icon(Icons.all_inclusive_rounded, size: 18, color: Theme.of(context).iconTheme.color?.withOpacity(0.7)),
                    SizedBox(width: 8),
                    Text('All time'),
                  ],
                ),
              ),
              DropdownMenuItem(
                value: 'today',
                child: Row(
                  children: [
                    Icon(Icons.today_rounded, size: 18, color: Theme.of(context).iconTheme.color?.withOpacity(0.7)),
                    SizedBox(width: 8),
                    Text('Today'),
                  ],
                ),
              ),
              DropdownMenuItem(
                value: 'week',
                child: Row(
                  children: [
                    Icon(Icons.date_range_rounded, size: 18, color: Theme.of(context).iconTheme.color?.withOpacity(0.7)),
                    SizedBox(width: 8),
                    Text('Past week'),
                  ],
                ),
              ),
              DropdownMenuItem(
                value: 'month',
                child: Row(
                  children: [
                    Icon(Icons.calendar_month_rounded, size: 18, color: Theme.of(context).iconTheme.color?.withOpacity(0.7)),
                    SizedBox(width: 8),
                    Text('Past month'),
                  ],
                ),
              ),
            ],
            onChanged: (String? value) {
              if (value != null) onDateRangeChange(value);
            },
          ),
        ),
      ],
    );
  }
}
