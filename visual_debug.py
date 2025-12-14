"""
GPO Fishing Macro - Visual Debugger
====================================
Shows the full screen with the capture region highlighted.
Press Q to quit.
"""

import cv2
import numpy as np
import mss
from config import (
    FISH_MARKER_WHITE,
    FISH_MARKER_GREEN,
    BLUE_BAR_COLOR,
    CAPTURE_REGION,
)


def main():
    print("=" * 50)
    print("     VISUAL DEBUGGER (Full Screen)")
    print("=" * 50)
    print("")
    print("Shows full screen with capture region highlighted:")
    print("  - YELLOW rectangle = capture region")
    print("  - RED line = detected FISH position")
    print("  - GREEN line = detected SWEET SPOT position")
    print("  - CYAN overlay = detected blue bar areas")
    print("")
    print("Press Q to quit")
    print("=" * 50)

    sct = mss.mss()
    monitor = sct.monitors[1]  # Primary monitor

    cv2.namedWindow("Debug View - Full Screen", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Debug View - Full Screen", 960, 540)  # Half size for display

    # Get capture region bounds
    region_left = CAPTURE_REGION["left"]
    region_top = CAPTURE_REGION["top"]
    region_width = CAPTURE_REGION["width"]
    region_height = CAPTURE_REGION["height"]

    while True:
        # Capture full screen
        screenshot = sct.grab(monitor)
        full_frame = np.array(screenshot)[:, :, :3]  # Remove alpha

        # Extract the capture region
        region_frame = full_frame[
            region_top:region_top + region_height,
            region_left:region_left + region_width
        ]

        # === DETECT BLUE BARS in region ===
        lower_blue = np.array(BLUE_BAR_COLOR["lower"], dtype=np.uint8)
        upper_blue = np.array(BLUE_BAR_COLOR["upper"], dtype=np.uint8)
        blue_mask = cv2.inRange(region_frame, lower_blue, upper_blue)

        # Count blue per row
        blue_per_row = np.sum(blue_mask > 0, axis=1)
        max_blue = np.max(blue_per_row) if np.max(blue_per_row) > 0 else 1
        threshold = max_blue * 0.2

        # Find sweet spot (gap in blue)
        sweet_spot_rows = np.where(blue_per_row < threshold)[0]

        if len(sweet_spot_rows) > 0:
            gaps = np.diff(sweet_spot_rows)
            segment_breaks = np.where(gaps > 5)[0]

            if len(segment_breaks) == 0:
                sweet_y = int(np.mean(sweet_spot_rows))
            else:
                segments = np.split(sweet_spot_rows, segment_breaks + 1)
                largest_segment = max(segments, key=len)
                sweet_y = int(np.mean(largest_segment))
        else:
            sweet_y = None

        # === DETECT FISH in region (both white and green) ===
        # White fish (not tracking)
        lower_white = np.array(FISH_MARKER_WHITE["lower"], dtype=np.uint8)
        upper_white = np.array(FISH_MARKER_WHITE["upper"], dtype=np.uint8)
        white_mask = cv2.inRange(region_frame, lower_white, upper_white)

        # Green fish (tracking correctly)
        lower_green = np.array(FISH_MARKER_GREEN["lower"], dtype=np.uint8)
        upper_green = np.array(FISH_MARKER_GREEN["upper"], dtype=np.uint8)
        green_mask = cv2.inRange(region_frame, lower_green, upper_green)

        # Combine both
        fish_mask = cv2.bitwise_or(white_mask, green_mask)

        coords = cv2.findNonZero(fish_mask)
        if coords is not None and len(coords) > 5:
            fish_y = int(np.mean(coords[:, 0, 1]))
        else:
            fish_y = None

        # === DRAW ON FULL FRAME ===
        display = full_frame.copy()

        # Draw capture region rectangle (yellow)
        cv2.rectangle(display,
                     (region_left, region_top),
                     (region_left + region_width, region_top + region_height),
                     (0, 255, 255), 3)

        # Draw blue mask overlay inside region (cyan tint)
        blue_overlay = np.zeros_like(region_frame)
        blue_overlay[:, :, 0] = blue_mask  # Blue
        blue_overlay[:, :, 1] = blue_mask  # Green
        region_with_overlay = cv2.addWeighted(region_frame, 1.0, blue_overlay, 0.4, 0)
        display[region_top:region_top + region_height,
                region_left:region_left + region_width] = region_with_overlay

        # Draw fish position (red line) - full width across region
        if fish_y is not None:
            y_abs = region_top + fish_y
            cv2.line(display, (region_left - 50, y_abs), (region_left + region_width + 50, y_abs), (0, 0, 255), 2)
            cv2.putText(display, f"FISH: {fish_y}", (region_left + region_width + 10, y_abs),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Draw sweet spot position (green line)
        if sweet_y is not None:
            y_abs = region_top + sweet_y
            cv2.line(display, (region_left - 50, y_abs), (region_left + region_width + 50, y_abs), (0, 255, 0), 2)
            cv2.putText(display, f"SWEET: {sweet_y}", (region_left + region_width + 10, y_abs + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Draw distance info
        if fish_y is not None and sweet_y is not None:
            dist = fish_y - sweet_y
            color = (0, 255, 255) if abs(dist) < 30 else (0, 0, 255)
            cv2.putText(display, f"DIST: {dist}", (region_left + region_width + 10, region_top + 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Draw action recommendation
            if dist < -15:
                action = "HOLD (fish above)"
                action_color = (0, 255, 0)
            elif dist > 15:
                action = "RELEASE (fish below)"
                action_color = (0, 0, 255)
            else:
                action = "IN ZONE"
                action_color = (0, 255, 255)
            cv2.putText(display, action, (region_left + region_width + 10, region_top + 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, action_color, 2)

        # Info box at top
        cv2.rectangle(display, (10, 10), (350, 100), (0, 0, 0), -1)
        cv2.putText(display, "VISUAL DEBUGGER", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, "YELLOW box = capture region", (20, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(display, "CYAN = detected blue bars", (20, 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(display, "Press Q to quit", (20, 95),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Debug View - Full Screen", display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    sct.close()
    cv2.destroyAllWindows()
    print("Debug view closed.")


if __name__ == "__main__":
    main()
