"""
GPO Fishing Macro - Sweet Spot Debugger
========================================
Focuses specifically on sweet spot detection to help tune parameters.
Shows the blue bar detection and gap finding in detail.
Press Q to quit.
"""

import cv2
import numpy as np
import mss
from config import (
    BLUE_BAR_COLOR,
    CAPTURE_REGION,
)


def main():
    print("=" * 50)
    print("     SWEET SPOT DEBUGGER")
    print("=" * 50)
    print("")
    print("This tool shows how sweet spot detection works:")
    print("  - LEFT: Original capture region")
    print("  - MIDDLE: Blue bar mask (white = blue detected)")
    print("  - RIGHT: Row-by-row blue pixel count graph")
    print("")
    print("  GREEN LINE = detected sweet spot center")
    print("  The sweet spot is the GAP in the blue bars")
    print("")
    print("Press Q to quit")
    print("=" * 50)

    sct = mss.mss()

    # Create window
    cv2.namedWindow("Sweet Spot Debug", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Sweet Spot Debug", 900, 600)

    # Get capture region bounds
    region = {
        "left": CAPTURE_REGION["left"],
        "top": CAPTURE_REGION["top"],
        "width": CAPTURE_REGION["width"],
        "height": CAPTURE_REGION["height"],
    }

    while True:
        # Capture the region
        screenshot = sct.grab(region)
        frame = np.array(screenshot)[:, :, :3]  # Remove alpha

        height, width = frame.shape[:2]

        # === DETECT BLUE BARS ===
        lower_blue = np.array(BLUE_BAR_COLOR["lower"], dtype=np.uint8)
        upper_blue = np.array(BLUE_BAR_COLOR["upper"], dtype=np.uint8)
        blue_mask = cv2.inRange(frame, lower_blue, upper_blue)

        # Count blue pixels per row
        blue_per_row = np.sum(blue_mask > 0, axis=1)
        max_blue = np.max(blue_per_row) if np.max(blue_per_row) > 0 else 1
        threshold = max_blue * 0.2

        # Find rows with LOW blue count = sweet spot area
        sweet_spot_rows = np.where(blue_per_row < threshold)[0]

        sweet_y = None
        largest_segment = None

        if len(sweet_spot_rows) > 0:
            # Find continuous segments
            gaps = np.diff(sweet_spot_rows)
            segment_breaks = np.where(gaps > 5)[0]

            if len(segment_breaks) == 0:
                # One continuous segment
                sweet_y = int(np.mean(sweet_spot_rows))
                largest_segment = sweet_spot_rows
            else:
                # Multiple segments - find the largest one
                segments = np.split(sweet_spot_rows, segment_breaks + 1)
                largest_segment = max(segments, key=len)
                sweet_y = int(np.mean(largest_segment))

        # === CREATE VISUALIZATION ===

        # Scale up the frame for better visibility
        scale = 4
        frame_large = cv2.resize(frame, (width * scale, height), interpolation=cv2.INTER_NEAREST)
        mask_large = cv2.resize(blue_mask, (width * scale, height), interpolation=cv2.INTER_NEAREST)

        # Convert mask to BGR for display
        mask_bgr = cv2.cvtColor(mask_large, cv2.COLOR_GRAY2BGR)

        # Create graph showing blue pixels per row
        graph_width = 200
        graph = np.zeros((height, graph_width, 3), dtype=np.uint8)

        # Draw background grid
        for i in range(0, graph_width, 20):
            cv2.line(graph, (i, 0), (i, height), (30, 30, 30), 1)
        for i in range(0, height, 20):
            cv2.line(graph, (0, i), (graph_width, i), (30, 30, 30), 1)

        # Draw threshold line
        threshold_x = int((threshold / max(max_blue, 1)) * (graph_width - 10))
        cv2.line(graph, (threshold_x, 0), (threshold_x, height), (0, 100, 100), 1)

        # Draw blue count per row as horizontal bars
        for y in range(height):
            bar_width = int((blue_per_row[y] / max(max_blue, 1)) * (graph_width - 10))

            # Color based on whether this row is part of sweet spot
            if blue_per_row[y] < threshold:
                color = (0, 255, 0)  # Green = sweet spot row
            else:
                color = (255, 100, 0)  # Blue = not sweet spot

            if bar_width > 0:
                cv2.line(graph, (0, y), (bar_width, y), color, 1)

        # Draw sweet spot position on all panels
        if sweet_y is not None:
            # On original frame
            cv2.line(frame_large, (0, sweet_y), (width * scale, sweet_y), (0, 255, 0), 2)

            # On mask
            cv2.line(mask_bgr, (0, sweet_y), (width * scale, sweet_y), (0, 255, 0), 2)

            # On graph
            cv2.line(graph, (0, sweet_y), (graph_width, sweet_y), (0, 255, 0), 2)

            # Draw segment bounds if we have them
            if largest_segment is not None and len(largest_segment) > 0:
                seg_top = largest_segment[0]
                seg_bot = largest_segment[-1]

                # Draw segment bounds (dashed effect with dots)
                for x in range(0, width * scale, 10):
                    cv2.circle(frame_large, (x, seg_top), 1, (0, 200, 200), -1)
                    cv2.circle(frame_large, (x, seg_bot), 1, (0, 200, 200), -1)

        # Combine all panels
        display = np.hstack([frame_large, mask_bgr, graph])

        # Add info panel at top
        info_height = 80
        info_panel = np.zeros((info_height, display.shape[1], 3), dtype=np.uint8)

        # Info text
        cv2.putText(info_panel, "SWEET SPOT DEBUGGER", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(info_panel, f"Blue range: {BLUE_BAR_COLOR['lower']} - {BLUE_BAR_COLOR['upper']}",
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 170, 85), 1)

        if sweet_y is not None:
            cv2.putText(info_panel, f"Sweet Spot Y: {sweet_y}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            if largest_segment is not None:
                seg_size = len(largest_segment)
                cv2.putText(info_panel, f"Segment size: {seg_size}px", (200, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.putText(info_panel, "Sweet Spot: NOT DETECTED", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        cv2.putText(info_panel, f"Max blue/row: {max_blue}", (400, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(info_panel, f"Threshold: {threshold:.1f}", (400, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 200), 1)

        # Column labels
        col1_x = width * scale // 2 - 30
        col2_x = width * scale + width * scale // 2 - 30
        col3_x = width * scale * 2 + graph_width // 2 - 40
        cv2.putText(info_panel, "ORIGINAL", (col1_x, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(info_panel, "BLUE MASK", (col2_x, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(info_panel, "BLUE/ROW", (col3_x, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Combine with info panel
        final_display = np.vstack([info_panel, display])

        cv2.imshow("Sweet Spot Debug", final_display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    sct.close()
    cv2.destroyAllWindows()
    print("Sweet spot debugger closed.")


if __name__ == "__main__":
    main()
