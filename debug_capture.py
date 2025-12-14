"""
GPO Fishing Macro - Debug Capture
=================================
Captures frames with detection overlay for debugging.
Saves images to debug_frames/ folder.
"""

import cv2
import numpy as np
import os
import time
from datetime import datetime


class DebugCapture:
    """Saves debug frames with detection visualization."""

    def __init__(self, output_dir="debug_frames"):
        """Initialize debug capture."""
        self.output_dir = output_dir
        self.frame_count = 0
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Log file for data
        self.log_file = open(f"{output_dir}/log_{self.session_id}.csv", "w")
        self.log_file.write("frame,timestamp,fish_y,sweet_y,distance,velocity,action,is_holding\n")

    def save_frame(self, frame, fish_y, sweet_y, velocity, action, is_holding):
        """
        Save a debug frame with visualization.

        Args:
            frame: The captured frame (BGR)
            fish_y: Detected fish Y position
            sweet_y: Detected sweet spot Y position
            velocity: Current velocity
            action: Current action (hold/release)
            is_holding: Whether mouse is being held
        """
        self.frame_count += 1

        # Only save every 5th frame to avoid too many files
        if self.frame_count % 5 != 0:
            return

        # Create a copy for drawing
        debug_frame = frame.copy()
        height, width = frame.shape[:2]

        # Draw fish position (red line)
        if fish_y is not None:
            cv2.line(debug_frame, (0, fish_y), (width, fish_y), (0, 0, 255), 2)
            cv2.putText(debug_frame, f"FISH: {fish_y}", (5, fish_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # Draw sweet spot position (green line)
        if sweet_y is not None:
            cv2.line(debug_frame, (0, sweet_y), (width, sweet_y), (0, 255, 0), 2)
            cv2.putText(debug_frame, f"SWEET: {sweet_y}", (5, sweet_y + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Draw distance
        if fish_y is not None and sweet_y is not None:
            distance = fish_y - sweet_y
            mid_y = (fish_y + sweet_y) // 2
            color = (0, 255, 255) if abs(distance) < 20 else (0, 165, 255)
            cv2.putText(debug_frame, f"DIST: {distance}", (width - 80, mid_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # Draw status
        status_color = (0, 255, 0) if is_holding else (0, 0, 255)
        status_text = "HOLDING" if is_holding else "RELEASED"
        cv2.putText(debug_frame, status_text, (5, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

        # Draw velocity
        cv2.putText(debug_frame, f"VEL: {velocity:.1f}", (5, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Save frame
        filename = f"{self.output_dir}/frame_{self.session_id}_{self.frame_count:05d}.png"
        cv2.imwrite(filename, debug_frame)

        # Log data
        distance = (fish_y - sweet_y) if (fish_y and sweet_y) else 0
        self.log_file.write(f"{self.frame_count},{time.time()},{fish_y},{sweet_y},{distance},{velocity:.2f},{action},{is_holding}\n")
        self.log_file.flush()

    def close(self):
        """Close log file."""
        self.log_file.close()
        print(f"\n[Debug] Saved {self.frame_count} frames to {self.output_dir}/")
        print(f"[Debug] Log saved to {self.output_dir}/log_{self.session_id}.csv")
