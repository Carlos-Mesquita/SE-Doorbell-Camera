import 'package:flutter/material.dart';

class AboutPage extends StatelessWidget {
  const AboutPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sobre o Projeto'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Doorbell Camera 🎦',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 20),
            const Text(
              'Este projeto implementa uma câmara inteligente na campainha de uma casa ou apartamento.\n\n'
              '• Grava automaticamente imagens em stop-motion ao detetar presença ou toque na campainha.\n'
              '• Permite ver transmissões ao vivo.\n'
              '• Notifica o utilizador no smartphone.\n\n'
              'O objetivo é garantir segurança e eficiência no uso de espaço de armazenamento.',
              style: TextStyle(fontSize: 16),
            ),
          ],
        ),
      ),
    );
  }
}
