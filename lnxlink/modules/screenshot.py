"""Stream your desktop directly to Home Assistant via a camera entity"""
import base64
import subprocess
import os
import threading
import time
import logging
from lnxlink.modules.scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


class FastVideoCapture:
    """Fast video capture using gpu-screen-recorder"""

    def __init__(self, cmd, cv2):
        self.process = None
        self.cap = None
        self.frame = None
        self.ret = False
        self.running = True
        self.lock = threading.Lock()
        self.thread = None

        try:
            # Start the subprocess
            # pylint: disable=consider-using-with
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # Replaces preexec_fn for creating new process group
            )

            # Give process a moment to start
            time.sleep(0.5)

            # Open the pipe in OpenCV
            pipe_path = f"/proc/{os.getpid()}/fd/{self.process.stdout.fileno()}"
            self.cap = cv2.VideoCapture(pipe_path)

            if not self.cap.isOpened():
                raise SystemError("Could not open video stream")

            # Start the thread
            self.thread = threading.Thread(target=self.update, args=())
            self.thread.daemon = True
            self.thread.start()

            logger.debug("FastVideoCapture initialized successfully")

        except Exception as err:
            logger.error("Failed to initialize FastVideoCapture: %s", err)
            self.cleanup()
            raise

    def update(self):
        """Constantly reads frames to keep the buffer empty."""
        consecutive_failures = 0
        max_failures = 30  # Allow ~0.5s of failures before stopping

        while self.running:
            try:
                ret, frame = self.cap.read()
                with self.lock:
                    self.ret = ret
                    if ret and frame is not None:
                        self.frame = frame
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1

                if consecutive_failures > max_failures:
                    logger.warning(
                        "Too many consecutive frame read failures, stopping capture"
                    )
                    self.running = False
                    break

            except Exception as err:
                logger.error("Error reading frame: %s", err)
                consecutive_failures += 1
                if consecutive_failures > max_failures:
                    self.running = False
                    break

            # Small sleep to prevent CPU spinning
            time.sleep(0.001)

    def read(self):
        """Returns the latest available frame."""
        with self.lock:
            if self.frame is not None:
                return self.ret, self.frame.copy()
            return False, None

    def is_running(self):
        """Check if capture is still running"""
        return self.running and self.thread and self.thread.is_alive()

    def cleanup(self):
        """Clean up resources"""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass

        if self.process is not None:
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(self.process.pid), 9)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

    def release(self):
        """Release resources"""
        self.running = False

        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        # Clean up OpenCV and process
        self.cleanup()

        # Kill all gpu-screen-recorder processes as fallback
        try:
            subprocess.run(
                ["pkill", "-9", "-f", "gpu-screen-recorder"],
                timeout=2.0,
                capture_output=True,
                check=False,
            )
        except Exception:
            pass


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.lnxlink = lnxlink
        self.name = "Screenshot"
        _, _, returncode = syscommand(
            "flatpak info com.dec05eba.gpu_screen_recorder",
            ignore_errors=True,
        )
        if returncode != 0:
            raise SystemError("gpu-screen-recorder Flatpak is not installed")
        self._requirements()
        self.run = False
        self.read_thr = None
        self.video_capture = None

    def _requirements(self):
        self.lib = {
            "cv2": import_install_package("opencv-python", ">=4.7.0.68", "cv2"),
        }

    def get_camera_frame(self):
        """Convert screen image to Base64 text"""
        if not self.run:
            return

        # Setup gpu-screen-recorder command
        cmd = [
            "flatpak",
            "run",
            "--command=gpu-screen-recorder",
            "com.dec05eba.gpu_screen_recorder",
            "-w",
            "screen",
            "-f",
            "30",  # 30 FPS is usually sufficient for monitoring
            "-c",
            "flv",
            "-v",
            "no",  # Disable audio
        ]

        logger.debug("Starting screenshot capture...")

        frame_count = 0
        last_frame_time = time.time()

        try:
            self.video_capture = FastVideoCapture(cmd, self.lib["cv2"])

            # Wait for first frame
            max_wait = 50  # 5 seconds
            wait_count = 0
            while self.run and wait_count < max_wait:
                ret, frame = self.video_capture.read()
                if ret and frame is not None:
                    break
                time.sleep(0.1)
                wait_count += 1

            if wait_count >= max_wait:
                logger.debug("Timeout waiting for first frame")
                return

            logger.debug("Screenshot capture started successfully")

            # Main capture loop
            while self.run:
                # Check if capture is still running
                if not self.video_capture.is_running():
                    logger.debug("Video capture stopped unexpectedly")
                    break

                ret, frame = self.video_capture.read()

                # If frame is not ready yet, wait a bit
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                try:
                    # Encode frame to jpg with quality setting
                    encode_param = [int(self.lib["cv2"].IMWRITE_JPEG_QUALITY), 85]
                    _, buffer = self.lib["cv2"].imencode(".jpg", frame, encode_param)
                    frame_b64 = base64.b64encode(buffer)
                    self.lnxlink.run_module(f"{self.name}/Screenshot feed", frame_b64)

                    frame_count += 1

                    # Optional: Log stats every 100 frames
                    if frame_count % 100 == 0:
                        current_time = time.time()
                        elapsed = current_time - last_frame_time
                        fps = 100 / elapsed if elapsed > 0 else 0
                        logger.debug(
                            "Processed %s frames, current FPS: %s",
                            frame_count,
                            round(fps, 0),
                        )
                        last_frame_time = current_time

                except Exception as err:
                    logger.info("Error encoding/sending frame: %s", err)
                    time.sleep(0.1)
                    continue

        except Exception as err:
            logger.error("Error in screenshot capture: %s", err)
        finally:
            logger.debug("Stopping screenshot capture...")
            if self.video_capture is not None:
                self.video_capture.release()
                self.video_capture = None
            logger.info("Screenshot capture stopped. Total frames: %s", frame_count)

    def get_info(self):
        """Gather information from the system"""
        return self.run

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Screenshot": {
                "type": "switch",
                "icon": "mdi:monitor-screenshot",
                "entity_category": "config",
            },
            "Screenshot feed": {
                "type": "camera",
                "encoding": "b64",
                "subtopic": True,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            logger.info("Received OFF command")
            self.run = False
            if self.read_thr is not None:
                self.read_thr.join(timeout=5.0)
                self.read_thr = None
        elif data.lower() == "on":
            logger.info("Received ON command")
            self.run = True
            if self.read_thr is None:
                self.read_thr = threading.Thread(
                    target=self.get_camera_frame, daemon=True
                )
                self.read_thr.start()
