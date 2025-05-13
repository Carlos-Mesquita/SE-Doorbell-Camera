import 'package:flutter/material.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Definições'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          const Text(
            'Geral',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          SwitchListTile(
            title: const Text('Notificações'),
            subtitle: const Text('Receber alertas no smartphone'),
            value: true,
            onChanged: (bool value) {
              // Atualizar estado (depois implementas)
            },
          ),
          SwitchListTile(
            title: const Text('Gravação automática'),
            subtitle: const Text('Ativar stop-motion ao detetar movimento'),
            value: true,
            onChanged: (bool value) {
              // Atualizar estado (depois implementas)
            },
          ),
          const SizedBox(height: 20),
          const Text(
            'Avançado',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('Sobre o projeto'),
            onTap: () {
              Navigator.of(context).pushNamed('/about');
            },
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Terminar sessão'),
            onTap: () {
              // Implementar logout
            },
          ),
        ],
      ),
    );
  }
}
