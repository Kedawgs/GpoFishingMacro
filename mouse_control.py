"""
GPO Fishing Macro - Mouse Control Module
=========================================
Handles mouse automation (click, hold, release).
Uses pynput for reliable mouse control.
"""

from pynput.mouse import Button, Controller
import time


class MouseController:
    """
    Controls mouse actions for the fishing macro.

    Handles:
    - Holding the left mouse button (sweet spot goes up)
    - Releasing the left mouse button (sweet spot falls down)
    - Single clicks (for recasting the line)
    """

    def __init__(self):
        """Initialize the mouse controller."""
        self.mouse = Controller()
        self.is_holding = False

    def hold(self):
        """
        Press and hold the left mouse button.
        Call this when the fish is above the sweet spot.
        """
        if not self.is_holding:
            self.mouse.press(Button.left)
            self.is_holding = True

    def release(self):
        """
        Release the left mouse button.
        Call this when the fish is below the sweet spot.
        """
        if self.is_holding:
            self.mouse.release(Button.left)
            self.is_holding = False

    def click(self, delay=0.05):
        """
        Perform a single left click.
        Used for casting/recasting the fishing line.

        Args:
            delay: Time between press and release (seconds)
        """
        # Make sure we're not holding before clicking
        self.release()

        self.mouse.press(Button.left)
        time.sleep(delay)
        self.mouse.release(Button.left)

    def get_position(self):
        """
        Get current mouse cursor position.

        Returns:
            tuple: (x, y) coordinates
        """
        return self.mouse.position

    def move_to(self, x, y):
        """
        Move mouse cursor to specific position.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.mouse.position = (x, y)

    def cleanup(self):
        """
        Ensure mouse button is released.
        Call this when stopping the macro.
        """
        self.release()


# Quick test if run directly
if __name__ == "__main__":
    print("Testing mouse control...")
    print("Watch your mouse - it will click in 3 seconds!")
    print("")

    controller = MouseController()

    # Countdown
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    # Test click
    print("Clicking!")
    controller.click()

    print("")
    print("Test hold for 1 second:")
    time.sleep(1)
    print("Holding...")
    controller.hold()
    time.sleep(1)
    print("Releasing...")
    controller.release()

    print("")
    print("Mouse control test complete!")
