"""
GPO Fishing Macro - Region Selector Helper
==========================================
Run this to help find the correct screen region for your setup.

This tool will:
1. Take a screenshot of your screen
2. Let you see pixel coordinates as you move around
3. Help you determine the capture region values for config.py
"""

import cv2
import numpy as np
import mss
import mss.tools

# Global variables for mouse callback
current_pos = (0, 0)
click_points = []


def mouse_callback(event, x, y, flags, param):
    """Handle mouse events on the preview window."""
    global current_pos, click_points

    current_pos = (x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        click_points.append((x, y))
        print(f"Point {len(click_points)}: ({x}, {y})")

        if len(click_points) == 2:
            # Calculate region
            x1, y1 = click_points[0]
            x2, y2 = click_points[1]

            left = min(x1, x2)
            top = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            print("")
            print("=" * 50)
            print("COPY THIS TO config.py:")
            print("=" * 50)
            print(f"""
CAPTURE_REGION = {{
    "left": {left},
    "top": {top},
    "width": {width},
    "height": {height},
}}
""")
            print("=" * 50)
            print("")
            print("Press 'r' to reset and select again")
            print("Press 'q' to quit")


def main():
    """Main function to run the region selector."""
    global click_points

    print("")
    print("=" * 50)
    print("     REGION SELECTOR")
    print("=" * 50)
    print("")
    print("1. Make sure GPO fishing UI is visible on screen")
    print("2. Click TOP-LEFT corner of the fishing bars")
    print("3. Click BOTTOM-RIGHT corner of the fishing bars")
    print("4. Copy the output to config.py")
    print("")
    print("Press 'r' to reset selection")
    print("Press 'q' to quit")
    print("")
    print("Taking screenshot...")

    # Capture full screen
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = img[:, :, :3]  # Remove alpha channel
        # Convert from BGR to RGB for display
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    print(f"Screenshot size: {img.shape[1]}x{img.shape[0]}")
    print("")

    # Create window
    window_name = "Region Selector - Click corners of fishing UI"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)

    # Resize for easier viewing if screen is very large
    scale = 1.0
    if img.shape[1] > 1920:
        scale = 1920 / img.shape[1]

    while True:
        # Create display image
        display = img.copy()

        # Draw click points
        for i, point in enumerate(click_points):
            cv2.circle(display, point, 5, (0, 255, 0), -1)
            cv2.putText(display, f"P{i+1}", (point[0]+10, point[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Draw rectangle if we have 2 points
        if len(click_points) == 2:
            cv2.rectangle(display, click_points[0], click_points[1], (0, 255, 0), 2)

        # Draw crosshair at current position
        cv2.line(display, (current_pos[0]-20, current_pos[1]),
                (current_pos[0]+20, current_pos[1]), (0, 0, 255), 1)
        cv2.line(display, (current_pos[0], current_pos[1]-20),
                (current_pos[0], current_pos[1]+20), (0, 0, 255), 1)

        # Show coordinates
        coord_text = f"({current_pos[0]}, {current_pos[1]})"
        cv2.putText(display, coord_text, (current_pos[0]+10, current_pos[1]-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Instructions
        cv2.putText(display, "Click corners of fishing bars | R=Reset | Q=Quit",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Resize for display
        if scale != 1.0:
            display = cv2.resize(display, None, fx=scale, fy=scale)

        cv2.imshow(window_name, display)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            click_points = []
            print("\nSelection reset. Click two corners again.")

    cv2.destroyAllWindows()
    print("\nRegion selector closed.")


if __name__ == "__main__":
    main()
