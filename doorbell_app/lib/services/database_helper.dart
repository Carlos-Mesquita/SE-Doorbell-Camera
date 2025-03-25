import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/notification.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;
  
  static const String serverUrl = "http://127.0.0.1:8000";

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('camera_app.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE notifications(
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        captures TEXT NOT NULL
      )
    ''');
  }

  Future<int> insertNotification(Notification notification) async {
    final db = await database;
    return await db.insert('notifications', notification.toMap());
  }

  Future<List<Notification>> getNotifications() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query('notifications');
    return List.generate(maps.length, (i) {
      return Notification.fromMap(maps[i]);
    });
  }

  Future<void> clearNotifications() async {
    final db = await database;
    await db.delete('notifications');
  }
}
