import 'dart:io';
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:get_it/get_it.dart';
import '../../models/notification.dart';
import '../../utils/date_formatter.dart';
import '../../services/api_service.dart';
import '../../config/env_config.dart';

class MediaCarouselScreen extends StatefulWidget {
  final NotificationDTO notification;
  final int startIndex;

  const MediaCarouselScreen({
    super.key,
    required this.notification,
    required this.startIndex,
  });

  @override
  _MediaCarouselScreenState createState() => _MediaCarouselScreenState();
}

class _MediaCarouselScreenState extends State<MediaCarouselScreen>
    with TickerProviderStateMixin {
  late PageController _pageController;
  late int _currentIndex;
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;
  bool _showUI = true;

  VideoPlayerController? _videoController;
  bool _isVideoMode = false;
  bool _isVideoInitialized = false;
  bool _isVideoPlaying = false;
  double _videoPlaybackSpeed = 1.0;

  // Stop motion video creation
  bool _isCreatingVideo = false;
  double _videoCreationProgress = 0.0;
  String _videoCreationStatus = '';

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.startIndex;
    _pageController = PageController(initialPage: widget.startIndex);

    _fadeController = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeInOut),
    );

    _fadeController.forward();

    // Show video option dialog if there are more than 10 captures
    if ((widget.notification.captures?.length ?? 0) > 10) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _showVideoModeDialog();
      });
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    _fadeController.dispose();
    _videoController?.dispose();
    super.dispose();
  }

  void _toggleUI() {
    setState(() {
      _showUI = !_showUI;
    });
  }

  void _showVideoModeDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Create Video'),
          content: Text('You have ${widget.notification.captures?.length ?? 0} images. Would you like to create a video slideshow for easier viewing?'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: Text('View as Images'),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
                _createStopMotionVideo();
              },
              child: Text('Create Video'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _createStopMotionVideo() async {
    final captures = widget.notification.captures ?? [];
    if (captures.isEmpty) return;

    setState(() {
      _isCreatingVideo = true;
      _videoCreationProgress = 0.0;
      _videoCreationStatus = 'Preparing...';
    });

    try {
      final capturePaths = captures.map((capture) => capture.path).toList();
      final ApiService apiService = GetIt.instance<ApiService>();

      final videoPath = await apiService.generateStopMotionVideo(
        capturePaths,
        onProgress: (progress) {
          setState(() {
            _videoCreationProgress = progress;
          });
        },
        onStatusUpdate: (status) {
          setState(() {
            _videoCreationStatus = status;
          });
        },
      );

      if (videoPath != null) {
        _videoController = VideoPlayerController.file(File(videoPath));
        await _videoController!.initialize();

        setState(() {
          _isVideoMode = true;
          _isVideoInitialized = true;
          _isCreatingVideo = false;
        });

        _videoController!.play();
        setState(() {
          _isVideoPlaying = true;
        });
      } else {
        throw Exception('No video path returned from server');
      }

    } catch (e) {
      setState(() {
        _isCreatingVideo = false;
        _videoCreationProgress = 0.0;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to create video: ${e.toString()}'),
          backgroundColor: Colors.red,
          duration: Duration(seconds: 4),
        ),
      );
    }
  }

  void _toggleVideoPlayback() {
    if (_videoController != null && _isVideoInitialized) {
      setState(() {
        if (_isVideoPlaying) {
          _videoController!.pause();
          _isVideoPlaying = false;
        } else {
          _videoController!.play();
          _isVideoPlaying = true;
        }
      });
    }
  }

  void _changeVideoSpeed() {
    if (_videoController != null) {
      double newSpeed;
      if (_videoPlaybackSpeed == 1.0) {
        newSpeed = 0.5;
      } else if (_videoPlaybackSpeed == 0.5) {
        newSpeed = 2.0;
      } else if (_videoPlaybackSpeed == 2.0) {
        newSpeed = 4.0;
      } else {
        newSpeed = 1.0;
      }

      _videoController!.setPlaybackSpeed(newSpeed);
      setState(() {
        _videoPlaybackSpeed = newSpeed;
      });
    }
  }

  void _switchToImageMode() {
    _videoController?.pause();
    setState(() {
      _isVideoMode = false;
      _isVideoPlaying = false;
    });
  }

  Widget _buildVideoCreationProgress() {
    return Container(
      width: double.infinity,
      height: MediaQuery.of(context).size.height,
      color: Colors.black,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 120,
              height: 120,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 120,
                    height: 120,
                    child: CircularProgressIndicator(
                      value: _videoCreationProgress,
                      strokeWidth: 8,
                      backgroundColor: Colors.grey[800],
                      valueColor: AlwaysStoppedAnimation<Color>(
                        Theme.of(context).colorScheme.primary,
                      ),
                    ),
                  ),
                  Text(
                    '${(_videoCreationProgress * 100).round()}%',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(height: 32),
            Text(
              'Creating Video Slideshow',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            SizedBox(height: 12),
            Text(
              _videoCreationStatus,
              style: TextStyle(
                color: Colors.grey[400],
                fontSize: 16,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Processing ${widget.notification.captures?.length ?? 0} frames',
              style: TextStyle(
                color: Colors.grey[500],
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVideoPlayer() {
    if (!_isVideoInitialized || _videoController == null) {
      return Container(
        width: double.infinity,
        height: 300,
        decoration: BoxDecoration(
          color: Colors.grey[900],
          borderRadius: BorderRadius.circular(16),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(
                color: Theme.of(context).colorScheme.primary,
                strokeWidth: 3,
              ),
              SizedBox(height: 16),
              Text(
                'Preparing video...',
                style: TextStyle(
                  color: Colors.grey[400],
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width,
        maxHeight: MediaQuery.of(context).size.height * 0.8,
      ),
      decoration: BoxDecoration(
        color: Colors.grey[900],
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.5),
            offset: Offset(0, 8),
            blurRadius: 24,
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Stack(
          alignment: Alignment.center,
          children: [
            AspectRatio(
              aspectRatio: _videoController!.value.aspectRatio,
              child: VideoPlayer(_videoController!),
            ),
            // Video controls overlay
            if (_showUI)
              Positioned(
                bottom: 20,
                left: 20,
                right: 20,
                child: Container(
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(25),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      // Speed control
                      GestureDetector(
                        onTap: _changeVideoSpeed,
                        child: Container(
                          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(15),
                          ),
                          child: Text(
                            '${_videoPlaybackSpeed}x',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ),
                      // Play/Pause button
                      GestureDetector(
                        onTap: _toggleVideoPlayback,
                        child: Container(
                          padding: EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.primary,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            _isVideoPlaying ? Icons.pause : Icons.play_arrow,
                            color: Colors.white,
                            size: 24,
                          ),
                        ),
                      ),
                      // Switch to image mode
                      GestureDetector(
                        onTap: _switchToImageMode,
                        child: Container(
                          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(15),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.photo_library, size: 16, color: Colors.white),
                              SizedBox(width: 4),
                              Text(
                                'Images',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildImageCarousel() {
    final captures = widget.notification.captures ?? [];
    final captureBaseUrl = EnvConfig.captureBase ?? '';

    return PageView.builder(
      controller: _pageController,
      onPageChanged: (index) {
        setState(() {
          _currentIndex = index;
        });
      },
      itemCount: captures.length,
      itemBuilder: (context, index) {
        // Construct full image URL using captureBase + capture path
        final imageUrl = '$captureBaseUrl/${captures[index].path}';

        return Container(
          margin: EdgeInsets.symmetric(horizontal: 16),
          child: Center(
            child: Hero(
              tag: 'capture_${captures[index].id}',
              child: Container(
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width,
                  maxHeight: MediaQuery.of(context).size.height * 0.8,
                ),
                decoration: BoxDecoration(
                  color: Colors.grey[900],
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.5),
                      offset: Offset(0, 8),
                      blurRadius: 24,
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: Image.network(
                    imageUrl,
                    fit: BoxFit.contain,
                    errorBuilder: (context, error, stackTrace) {
                      return Container(
                        width: double.infinity,
                        height: 300,
                        decoration: BoxDecoration(
                          color: Colors.grey[800],
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.broken_image_rounded,
                              size: 64,
                              color: Colors.grey[600],
                            ),
                            SizedBox(height: 16),
                            Text(
                              'Failed to load image',
                              style: TextStyle(
                                color: Colors.grey[400],
                                fontSize: 16,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              imageUrl,
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 10,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      );
                    },
                    loadingBuilder: (context, child, loadingProgress) {
                      if (loadingProgress == null) return child;
                      return Container(
                        width: double.infinity,
                        height: 300,
                        decoration: BoxDecoration(
                          color: Colors.grey[900],
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              CircularProgressIndicator(
                                value: loadingProgress.expectedTotalBytes != null
                                    ? loadingProgress.cumulativeBytesLoaded /
                                      loadingProgress.expectedTotalBytes!
                                    : null,
                                color: Theme.of(context).colorScheme.primary,
                                strokeWidth: 3,
                              ),
                              SizedBox(height: 16),
                              Text(
                                'Loading image...',
                                style: TextStyle(
                                  color: Colors.grey[400],
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final captures = widget.notification.captures ?? [];
    final captureBaseUrl = EnvConfig.captureBase ?? '';

    if (_isCreatingVideo) {
      return Scaffold(
        backgroundColor: Colors.black,
        body: _buildVideoCreationProgress(),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      body: GestureDetector(
        onTap: _toggleUI,
        child: Stack(
          children: [
            // Main content viewer
            Center(
              child: _isVideoMode ? _buildVideoPlayer() : _buildImageCarousel(),
            ),

            // UI Overlay
            AnimatedOpacity(
              opacity: _showUI ? 1.0 : 0.0,
              duration: Duration(milliseconds: 300),
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.center,
                    colors: [
                      Colors.black.withOpacity(0.7),
                      Colors.transparent,
                    ],
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        // Mode indicator and counter
                        Row(
                          children: [
                            if (_isVideoMode)
                              Container(
                                padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Colors.red.withOpacity(0.8),
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.videocam, size: 16, color: Colors.white),
                                    SizedBox(width: 4),
                                    Text(
                                      'Video Mode',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            if (!_isVideoMode && captures.length > 1)
                              Container(
                                margin: EdgeInsets.only(left: _isVideoMode ? 8 : 0),
                                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                decoration: BoxDecoration(
                                  color: Colors.black.withOpacity(0.6),
                                  borderRadius: BorderRadius.circular(20),
                                  border: Border.all(
                                    color: Colors.white.withOpacity(0.2),
                                  ),
                                ),
                                child: Text(
                                  '${_currentIndex + 1} of ${captures.length}',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                          ],
                        ),

                        // Action buttons
                        Row(
                          children: [
                            // Video mode toggle (show for 10+ captures)
                            if (!_isVideoMode && captures.length > 10)
                              Container(
                                margin: EdgeInsets.only(right: 8),
                                decoration: BoxDecoration(
                                  color: Colors.black.withOpacity(0.6),
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: Colors.white.withOpacity(0.2),
                                  ),
                                ),
                                child: IconButton(
                                  icon: Icon(Icons.play_circle_filled, color: Colors.white),
                                  onPressed: _createStopMotionVideo,
                                  tooltip: 'Create Video',
                                ),
                              ),

                            // Close button
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.6),
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: Colors.white.withOpacity(0.2),
                                ),
                              ),
                              child: IconButton(
                                icon: Icon(Icons.close_rounded, color: Colors.white),
                                onPressed: () => Navigator.of(context).pop(),
                                tooltip: 'Close',
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),

            // Navigation arrows (only in image mode)
            if (!_isVideoMode && captures.length > 1 && _showUI) ...[
              Positioned(
                left: 16,
                top: MediaQuery.of(context).size.height / 2 - 30,
                child: AnimatedOpacity(
                  opacity: _currentIndex > 0 ? 1.0 : 0.3,
                  duration: Duration(milliseconds: 200),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.6),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.white.withOpacity(0.2),
                      ),
                    ),
                    child: IconButton(
                      icon: Icon(Icons.chevron_left_rounded, color: Colors.white, size: 32),
                      onPressed: _currentIndex > 0
                          ? () {
                              _pageController.previousPage(
                                duration: Duration(milliseconds: 300),
                                curve: Curves.easeInOut,
                              );
                            }
                          : null,
                    ),
                  ),
                ),
              ),
              Positioned(
                right: 16,
                top: MediaQuery.of(context).size.height / 2 - 30,
                child: AnimatedOpacity(
                  opacity: _currentIndex < captures.length - 1 ? 1.0 : 0.3,
                  duration: Duration(milliseconds: 200),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.6),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.white.withOpacity(0.2),
                      ),
                    ),
                    child: IconButton(
                      icon: Icon(Icons.chevron_right_rounded, color: Colors.white, size: 32),
                      onPressed: _currentIndex < captures.length - 1
                          ? () {
                              _pageController.nextPage(
                                duration: Duration(milliseconds: 300),
                                curve: Curves.easeInOut,
                              );
                            }
                          : null,
                    ),
                  ),
                ),
              ),
            ],

            // Bottom info panel
            AnimatedPositioned(
              duration: Duration(milliseconds: 300),
              bottom: _showUI ? 16 : -200,
              left: 16,
              right: 16,
              child: Container(
                padding: EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.8),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.white.withOpacity(0.1),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.notification.title,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        height: 1.3,
                      ),
                    ),
                    SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(
                          _isVideoMode ? Icons.videocam : Icons.access_time_rounded,
                          size: 16,
                          color: Colors.grey[400],
                        ),
                        SizedBox(width: 6),
                        Text(
                          _isVideoMode
                            ? 'Video slideshow (${captures.length} frames at ${_videoPlaybackSpeed}x speed)'
                            : 'Captured ${DateFormatter.formatRelativeTime(captures[_currentIndex].createdAt)}',
                          style: TextStyle(
                            color: Colors.grey[300],
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                    if (!_isVideoMode && captures.length > 1) ...[
                      SizedBox(height: 16),
                      // Thumbnail strip
                      SizedBox(
                        height: 60,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          itemCount: captures.length,
                          itemBuilder: (context, index) {
                            final thumbnailUrl = '$captureBaseUrl/${captures[index].path}';

                            return GestureDetector(
                              onTap: () {
                                _pageController.animateToPage(
                                  index,
                                  duration: Duration(milliseconds: 300),
                                  curve: Curves.easeInOut,
                                );
                              },
                              child: Container(
                                width: 60,
                                height: 60,
                                margin: EdgeInsets.only(right: 12),
                                decoration: BoxDecoration(
                                  border: Border.all(
                                    color: index == _currentIndex
                                        ? Theme.of(context).colorScheme.primary
                                        : Colors.grey[600]!,
                                    width: index == _currentIndex ? 3 : 2,
                                  ),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(6),
                                  child: Image.network(
                                    thumbnailUrl,
                                    fit: BoxFit.cover,
                                    errorBuilder: (context, error, stackTrace) {
                                      return Container(
                                        color: Colors.grey[700],
                                        child: Icon(
                                          Icons.broken_image_rounded,
                                          size: 20,
                                          color: Colors.grey[500],
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
