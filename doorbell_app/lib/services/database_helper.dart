import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/notification.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('doorbell_camera_v2.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 2,
      onCreate: _createDB,
      onUpgrade: _onUpgradeDB,
    );
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE notifications(
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        captures_json TEXT,
        rpi_event_id TEXT,
        type_str TEXT,
        user_id TEXT
      )
    ''');
  }

  Future _onUpgradeDB(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      await db.execute("DROP TABLE IF EXISTS notifications");
      await _createDB(db, newVersion);
      print("Database upgraded to version $newVersion (old table dropped and recreated).");
    }
  }

  Future<int> insertNotification(NotificationDTO notification) async {
    final db = await database;
    Map<String, dynamic> row = notification.toDbMap();

    return await db.insert('notifications', row, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<List<NotificationDTO>> getNotifications() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'notifications',
      orderBy: 'created_at DESC'
    );

    if (maps.isEmpty) {
      return [];
    }
    return List.generate(maps.length, (i) {
      return NotificationDTO.fromMap(maps[i]);
    });
  }

  Future<int> deleteNotification(int serverNotificationId) async {
    final db = await database;
    return await db.delete(
      'notifications',
      where: 'id = ?',
      whereArgs: [serverNotificationId],
    );
  }

  Future<int> clearNotifications() async {
    final db = await database;
    return await db.delete('notifications');
  }

  Future<NotificationDTO?> getNotificationById(int serverNotificationId) async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'notifications',
      where: 'id = ?',
      whereArgs: [serverNotificationId],
      limit: 1,
    );

    if (maps.isNotEmpty) {
      return NotificationDTO.fromMap(maps.first);
    }
    return null;
  }
}
