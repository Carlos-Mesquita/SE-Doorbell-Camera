import 'package:flutter/material.dart';

class StopMotionViewerScreen extends StatefulWidget {
  const StopMotionViewerScreen({super.key});

  @override
  State<StopMotionViewerScreen> createState() => _StopMotionViewerScreenState();
}

class _StopMotionViewerScreenState extends State<StopMotionViewerScreen> {
  Map<String, List<String>> sequences = {
    'Video - 2025/04/10': [
      'assets/images/seq1/img1.webp',
      'assets/images/seq1/istockphoto-814423752-612x612.jpg',
      'assets/images/seq1/MainBefore.jpg',
      'assets/images/seq1/transferir.jpeg',
    ],
    'Video - 2025/04/11': [
      'assets/images/seq2/free-nature-images.jpg',
      'assets/images/seq2/istockphoto-1317323736-612x612.jpg',
      'assets/images/seq2/pexels-hsapir-1054655.jpg',
      'assets/images/seq2/young-conceptual-image-large-stone-shape-human-brain-conceptual-image-large-stone-shape-110748113.webp',
    ],
  };

  void _deleteSequence(String title) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Delete video"),
        content: Text("Are you sure you want to delete '$title'?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          TextButton(
            onPressed: () {
              setState(() {
                sequences.remove(title);
              });
              Navigator.pop(context);
            },
            child: const Text("Delete", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Stop Motion History')),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: sequences.entries.map((entry) {
          final title = entry.key;
          final images = entry.value;

          return Card(
            margin: const EdgeInsets.only(bottom: 20),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            elevation: 4,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(title, style: Theme.of(context).textTheme.titleMedium),
                      IconButton(
                        icon: const Icon(Icons.delete, color: Colors.red),
                        onPressed: () => _deleteSequence(title),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 120,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: images.length,
                      itemBuilder: (context, index) {
                        return GestureDetector(
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => SequenceViewer(images: images),
                              ),
                            );
                          },
                          child: Padding(
                            padding: const EdgeInsets.only(right: 8.0),
                            child: Image.asset(images[index]),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class SequenceViewer extends StatelessWidget {
  final List<String> images;
  const SequenceViewer({super.key, required this.images});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ver sequência')),
      body: PageView.builder(
        itemCount: images.length,
        itemBuilder: (context, index) {
          return Center(child: Image.asset(images[index]));
        },
      ),
    );
  }
}
