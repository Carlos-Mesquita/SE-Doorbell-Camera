class DateFormatter {
  static String formatRelativeTime(String dateTime) {
    final now = DateTime.now();
    final difference = now.difference(DateTime.tryParse(dateTime)!);

    if (difference.inDays >= 1) {
      return '${difference.inDays} day${difference.inDays != 1 ? 's' : ''} ago';
    } else if (difference.inHours >= 1) {
      return '${difference.inHours} hour${difference.inHours != 1 ? 's' : ''} ago';
    } else {
      return '${difference.inMinutes} minute${difference.inMinutes != 1 ? 's' : ''} ago';
    }
  }
}
