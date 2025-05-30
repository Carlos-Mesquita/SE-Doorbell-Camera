import 'package:flutter/material.dart';
import 'filter_panel.dart';

class SearchHeader extends StatelessWidget {
  final TextEditingController searchController;
  final bool showFilters;
  final int activeFilterCount;
  final List<String> notificationTypes;
  final List<String> selectedTypes;
  final String selectedDateRange;
  final VoidCallback onToggleFilters;
  final Function(String) onTypeToggle;
  final Function(String) onDateRangeChange;
  final VoidCallback onClearFilters;
  final VoidCallback onSearchChanged;

  const SearchHeader({
    super.key,
    required this.searchController,
    required this.showFilters,
    required this.activeFilterCount,
    required this.notificationTypes,
    required this.selectedTypes,
    required this.selectedDateRange,
    required this.onToggleFilters,
    required this.onTypeToggle,
    required this.onDateRangeChange,
    required this.onClearFilters,
    required this.onSearchChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).appBarTheme.backgroundColor,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            offset: Offset(0, 2),
            blurRadius: 8,
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            children: [
              // Title and refresh button
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Notifications',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.5,
                    ),
                  ),
                  Container(
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surface.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
                      ),
                    ),
                    child: IconButton(
                      icon: Icon(
                        Icons.refresh_rounded,
                        color: Theme.of(context).iconTheme.color,
                      ),
                      onPressed: () {},
                      tooltip: 'Refresh notifications',
                    ),
                  ),
                ],
              ),
              SizedBox(height: 20),

              // Search and filter bar
              Row(
                children: [
                  Expanded(
                    child: Container(
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
                      child: TextField(
                        controller: searchController,
                        onChanged: (value) => onSearchChanged(),
                        style: Theme.of(context).textTheme.bodyLarge,
                        decoration: InputDecoration(
                          hintText: 'Search notifications...',
                          hintStyle: Theme.of(context).inputDecorationTheme.hintStyle,
                          prefixIcon: Icon(
                            Icons.search_rounded,
                            color: Theme.of(context).iconTheme.color?.withOpacity(0.6),
                          ),
                          suffixIcon: searchController.text.isNotEmpty
                              ? IconButton(
                                  icon: Icon(
                                    Icons.clear_rounded,
                                    color: Theme.of(context).iconTheme.color?.withOpacity(0.6),
                                  ),
                                  onPressed: () {
                                    searchController.clear();
                                    onSearchChanged();
                                  },
                                )
                              : null,
                          border: Theme.of(context).inputDecorationTheme.border,
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
                              width: 1,
                            ),
                          ),
                          filled: true,
                          fillColor: Theme.of(context).inputDecorationTheme.fillColor,
                          contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 12),
                  Stack(
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          color: showFilters || activeFilterCount > 0
                              ? Theme.of(context).colorScheme.primary.withOpacity(0.1)
                              : Theme.of(context).inputDecorationTheme.fillColor,
                          border: Border.all(
                            color: showFilters || activeFilterCount > 0
                                ? Theme.of(context).colorScheme.primary.withOpacity(0.5)
                                : Theme.of(context).colorScheme.outline.withOpacity(0.3),
                          ),
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.05),
                              offset: Offset(0, 2),
                              blurRadius: 4,
                            ),
                          ],
                        ),
                        child: IconButton(
                          icon: Icon(
                            Icons.tune_rounded,
                            color: showFilters || activeFilterCount > 0
                                ? Theme.of(context).colorScheme.primary
                                : Theme.of(context).iconTheme.color?.withOpacity(0.6),
                          ),
                          onPressed: onToggleFilters,
                          tooltip: 'Filter notifications',
                        ),
                      ),
                      if (activeFilterCount > 0)
                        Positioned(
                          right: 6,
                          top: 6,
                          child: Container(
                            width: 18,
                            height: 18,
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.primary,
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: Theme.of(context).appBarTheme.backgroundColor!,
                                width: 2,
                              ),
                            ),
                            child: Center(
                              child: Text(
                                '$activeFilterCount',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ],
              ),

              // Filter panel
              if (showFilters) ...[
                SizedBox(height: 16),
                FilterPanel(
                  notificationTypes: notificationTypes,
                  selectedTypes: selectedTypes,
                  selectedDateRange: selectedDateRange,
                  activeFilterCount: activeFilterCount,
                  onTypeToggle: onTypeToggle,
                  onDateRangeChange: onDateRangeChange,
                  onClearFilters: onClearFilters,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
