import 'package:get_it/get_it.dart';
import 'package:doorbell_app/services/api_service.dart';
import 'package:doorbell_app/services/auth_service.dart';

final GetIt serviceLocator = GetIt.instance;

void setupServiceLocator() {
  serviceLocator.registerSingleton<AuthService>(AuthService());
  serviceLocator.registerLazySingleton<ApiService>(() => ApiService());
}
