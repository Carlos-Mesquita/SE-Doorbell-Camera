import 'package:flutter/material.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SE-Doorbell-Camera'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: GridView.count(
          crossAxisCount: 2,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          children: [
            _DashboardButton(
              icon: Icons.image,
              label: 'Gravações',
              color: Colors.blueAccent,
              onTap: () {
                // Navegar para a página de gravações
              },
            ),
            _DashboardButton(
              icon: Icons.live_tv,
              label: 'Live Stream',
              color: Colors.redAccent,
              onTap: () {
                // Navegar para a página de live stream
              },
            ),
            _DashboardButton(
              icon: Icons.settings,
              label: 'Definições',
              color: Colors.green,
              onTap: () {
                // Navegar para a página de definições
              },
            ),
            _DashboardButton(
              icon: Icons.notifications,
              label: 'Notificações',
              color: Colors.orangeAccent,
              onTap: () {
                // Navegar para a página de notificações (se fizeres)
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _DashboardButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _DashboardButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: color.withOpacity(0.85),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black26,
              blurRadius: 8,
              offset: Offset(2, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 48, color: Colors.white),
            const SizedBox(height: 12),
            Text(
              label,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
