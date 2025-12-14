"""
GPO Fishing Macro - Screen Capture Module
==========================================
Handles fast screen capture of the fishing UI region.
Uses the 'mss' library for high-performance screen grabs.
"""

import numpy as np
import mss
import mss.tools
from config import CAPTURE_REGION


class ScreenCapture:
    """
    Captures a specific region of the screen quickly.

    Usage:
        capture = ScreenCapture()
        image = capture.grab()  # Returns numpy array (BGR format)
    """

    def __init__(self, region=None):
        """
        Initialize the screen capture.

        Args:
            region: Dict with 'left', 'top', 'width', 'height' keys.
                   If None, uses CAPTURE_REGION from config.
        """
        # Use provided region or default from config
        self.region = region or CAPTURE_REGION

        # Create the mss instance (reuse for better performance)
        self.sct = mss.mss()

        # Define the monitor region to capture
        self.monitor = {
            "left": self.region["left"],
            "top": self.region["top"],
            "width": self.region["width"],
            "height": self.region["height"],
        }

    def grab(self):
        """
        Capture the screen region and return as numpy array.

        Returns:
            numpy.ndarray: Image in BGR format (OpenCV compatible)
                          Shape: (height, width, 3)
        """
        # Grab the screen region
        screenshot = self.sct.grab(self.monitor)

        # Convert to numpy array
        # mss returns BGRA format, we need BGR for OpenCV
        img = np.array(screenshot)

        # Remove alpha channel (BGRA -> BGR)
        img = img[:, :, :3]

        return img

    def grab_full_screen(self):
        """
        Capture the entire primary monitor.
        Useful for debugging or finding regions.

        Returns:
            numpy.ndarray: Full screen image in BGR format
        """
        # Monitor 1 is the primary display (0 is "all monitors combined")
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        img = img[:, :, :3]
        return img

    def update_region(self, left, top, width, height):
        """
        Update the capture region.

        Args:
            left: X coordinate of left edge
            top: Y coordinate of top edge
            width: Width of region
            height: Height of region
        """
        self.region = {
            "left": left,
            "top": top,
            "width": width,
            "height": height,
        }
        self.monitor = self.region.copy()

    def close(self):
        """Clean up resources."""
        self.sct.close()


# Quick test if run directly
if __name__ == "__main__":
    import cv2

    print("Testing screen capture...")
    print(f"Capture region: {CAPTURE_REGION}")

    capture = ScreenCapture()

    # Grab a frame
    frame = capture.grab()
    print(f"Captured frame shape: {frame.shape}")

    # Save it for inspection
    cv2.imwrite("test_capture.png", frame)
    print("Saved test_capture.png - check if it shows the fishing UI area!")

    # Also grab full screen for reference
    full = capture.grab_full_screen()
    cv2.imwrite("test_fullscreen.png", full)
    print("Saved test_fullscreen.png - full screen reference")

    capture.close()
    print("Done! Check the saved images.")
