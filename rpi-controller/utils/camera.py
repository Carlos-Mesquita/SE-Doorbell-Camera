import sys
import time

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from datetime import datetime


def test_photo():
    print("Taking a photo ...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = f"test_{timestamp}.jpg"
    picam2.capture_file(image_path)
    print(f"Result: {image_path}")

def test_recording():
    encoder = H264Encoder(bitrate=10000000)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = f"test_video_{timestamp}.h264"
    picam2.start_recording(encoder, video_path)
    print("Recording video ...")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    picam2.stop_recording()
    print(f"Result: {video_path}")


if __name__ == "__main__":
    record_video = False
    if len(sys.argv) > 1 and "video" == sys.argv[1]:
        record_video = True

    print("Booting up ...")

    picam2 = Picamera2()
    config = picam2.create_preview_configuration()
    picam2.configure(config)
    picam2.start()
    time.sleep(2)

    print("Done")

    try:
        if record_video:
            test_recording()
        else:
            test_photo()

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        picam2.stop()
        picam2.close()
