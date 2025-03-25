class UserCredentials {
  final String accessToken;
  final DateTime expiresAt;

  UserCredentials({
    required this.accessToken,
    required this.expiresAt,
  });

  bool get isExpired => DateTime.now().isAfter(expiresAt);
}
