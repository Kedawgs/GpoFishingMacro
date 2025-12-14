"""
GPO Fishing Macro - Main Entry Point
=====================================
Run this file to start the fishing macro.

Controls:
    F6 - Toggle macro ON/OFF
    F7 - Exit program

Usage:
    1. Open Roblox GPO and go to a fishing spot
    2. Run this script: python main.py
    3. Press F6 to start the macro
    4. Press F6 again to pause, F7 to exit
"""

import time
import keyboard
import cv2
import sys
from enum import Enum
from colorama import init, Fore, Style

# Enable ANSI colors on Windows
init()

from config import (
    TOGGLE_KEY,
    EXIT_KEY,
    LOOP_DELAY,
    RECAST_DELAY,
    WAIT_FOR_FISH_DELAY,
    IDLE_TIMEOUT,
    DEBUG_MODE,
    SAVE_DEBUG_SCREENSHOTS,
    SHOW_DEBUG_WINDOW,
    CAPTURE_REGION,
)
from screen_capture import ScreenCapture
from detector import FishingDetector
from mouse_control import MouseController
from debug_capture import DebugCapture
from overlay import FishingOverlay

# Set up logging to file when DEBUG_MODE is on
if DEBUG_MODE:
    # Clear old log and set up new one
    log_file = open('debug.log', 'w')

    class TeeOutput:
        """Write to both console and file."""
        def __init__(self, file, stream):
            self.file = file
            self.stream = stream
        def write(self, data):
            self.stream.write(data)
            self.file.write(data)
            self.file.flush()
        def flush(self):
            self.stream.flush()
            self.file.flush()

    sys.stdout = TeeOutput(log_file, sys.stdout)
    print("[Debug] Logging to debug.log")


class FishingState(Enum):
    """States for the fishing state machine."""
    IDLE = "idle"           # Waiting for fish to bite / ready to cast
    FISHING = "fishing"     # Actively tracking the fish
    CAUGHT = "caught"       # Fish caught, need to recast


class FishingMacro:
    """
    Main fishing macro controller.

    Handles the state machine and coordinates all modules.
    """

    def __init__(self):
        """Initialize the macro."""
        self.capture = ScreenCapture()
        self.detector = FishingDetector()
        self.mouse = MouseController()

        # Debug capture (if enabled)
        self.debug_capture = DebugCapture() if SAVE_DEBUG_SCREENSHOTS else None

        # Visual overlay on top of game
        self.overlay = FishingOverlay(CAPTURE_REGION)

        self.enabled = False
        self.running = True
        self.state = FishingState.IDLE
        self.is_holding = False  # Track current mouse state
        self.idle_start_time = None  # Track when we started waiting for fish
        self.consecutive_idle_recasts = 0  # Track idle recasts (for out of bait detection)
        self.NO_BAIT_THRESHOLD = 7  # After this many idle recasts, assume out of bait

        # Set up hotkeys
        keyboard.on_press_key(TOGGLE_KEY, self._on_toggle)
        keyboard.on_press_key(EXIT_KEY, self._on_exit)

        print("=" * 50)
        print("     GPO FISHING MACRO")
        print("=" * 50)
        print("")
        print(f"  Press {TOGGLE_KEY.upper()} to toggle ON/OFF")
        print(f"  Press {EXIT_KEY.upper()} to exit")
        print("")
        if SAVE_DEBUG_SCREENSHOTS:
            print("  DEBUG MODE: Saving frames to debug_frames/")
        print("  Status: PAUSED")
        print("=" * 50)
        print("")
        print(f"  {Fore.CYAN}<3 If this macro saved you time, consider supporting:")
        print("      Venmo: @Daniel-K-25")
        print(f"      ETH/EVM: 0x3260f49c7df40cfdc550fff88d48d242e67ec5c5{Style.RESET_ALL}")
        print("")

    def _on_toggle(self, event):
        """Handle toggle hotkey press."""
        self.enabled = not self.enabled
        status = "RUNNING" if self.enabled else "PAUSED"
        print(f"\n[Macro] {status}")

        # Reset state when toggling
        if self.enabled:
            self.state = FishingState.IDLE
            self.idle_start_time = time.time()  # Start idle timer
        else:
            self.mouse.cleanup()
            self.overlay.update(is_active=False, status="OFF")

    def _on_exit(self, event):
        """Handle exit hotkey press."""
        print("\n[Macro] Exiting...")
        self.running = False
        self.enabled = False

    def run(self):
        """Main loop - run the macro."""
        try:
            while self.running:
                if self.enabled:
                    self._tick()
                time.sleep(LOOP_DELAY)

        except KeyboardInterrupt:
            print("\n[Macro] Interrupted by user")
        finally:
            self._cleanup()

    def _tick(self):
        """Single tick of the macro logic."""
        # Capture screen
        frame = self.capture.grab()

        # State machine
        if self.state == FishingState.IDLE:
            self._handle_idle(frame)

        elif self.state == FishingState.FISHING:
            self._handle_fishing(frame)

        elif self.state == FishingState.CAUGHT:
            self._handle_caught(frame)

    def _handle_idle(self, frame):
        """Handle IDLE state - waiting for fish."""
        # Update overlay to show idle state
        self.overlay.update(is_active=False, status="IDLE")

        # Check if fishing minigame started (bars appeared)
        if self.detector.is_fishing_active(frame):
            print("[State] Fish on the line! -> FISHING")
            self.detector.reset_state()  # Reset all tracking state for the new fish
            self.state = FishingState.FISHING
            self.idle_start_time = None  # Reset idle timer
            self.consecutive_idle_recasts = 0  # Reset - we got a fish!
            # Immediately start holding to prevent bar from falling
            self.mouse.hold()
            self.is_holding = True
        else:
            # No fish yet - track how long we've been waiting
            if self.idle_start_time is None:
                self.idle_start_time = time.time()

            # Check if we've been waiting too long
            idle_duration = time.time() - self.idle_start_time
            if idle_duration > IDLE_TIMEOUT:
                self.consecutive_idle_recasts += 1
                print(f"[State] Idle timeout ({IDLE_TIMEOUT}s) - auto recasting... ({self.consecutive_idle_recasts}/{self.NO_BAIT_THRESHOLD})")

                # Check if we've hit the no-bait threshold
                if self.consecutive_idle_recasts >= self.NO_BAIT_THRESHOLD:
                    print(f"[State] {Fore.YELLOW}No bait detected! Doing anti-AFK movement...{Style.RESET_ALL}")
                    self._do_anti_afk()
                    self.consecutive_idle_recasts = 0  # Reset after anti-AFK
                else:
                    self.mouse.click()

                self.idle_start_time = time.time()  # Reset timer
            elif DEBUG_MODE:
                print("[State] Waiting for fish...")

    def _handle_fishing(self, frame):
        """Handle FISHING state - actively tracking."""
        # Check if fish was caught
        if self.detector.is_fish_caught(frame):
            print("[State] Fish caught! -> CAUGHT")
            self.mouse.release()  # Make sure we release
            self.is_holding = False
            self.state = FishingState.CAUGHT
            return

        # Determine if we should hold or release
        should_hold = self.detector.should_hold_mouse(frame)

        if should_hold is True:
            self.mouse.hold()
            self.is_holding = True
        elif should_hold is False:
            self.mouse.release()
            self.is_holding = False
        # If None, keep current state (couldn't determine)

        # Update overlay with current state
        fish_y = self.detector.last_fish_y
        sweet_y = self.detector.last_sweet_spot_y
        action = "HOLD" if should_hold else "RELEASE" if should_hold is False else None
        self.overlay.update(
            fish_y=fish_y,
            sweet_y=sweet_y,
            is_active=True,
            status="FISHING",
            action=action
        )

        # Save debug frame if enabled
        if self.debug_capture:
            fish_y = self.detector.last_fish_y
            sweet_y = self.detector.last_sweet_spot_y
            velocity = self.detector.sweet_spot_velocity
            action = "HOLD" if should_hold else "RELEASE" if should_hold is False else "NONE"
            self.debug_capture.save_frame(frame, fish_y, sweet_y, velocity, action, self.is_holding)

        # Show live debug window if enabled
        if SHOW_DEBUG_WINDOW:
            self._show_debug_window(frame, should_hold)

    def _show_debug_window(self, frame, should_hold):
        """Show live debug window with detection overlay."""
        # Make a copy and scale it up for visibility
        display = cv2.resize(frame, (frame.shape[1] * 4, frame.shape[0] * 2))

        fish_y = self.detector.last_fish_y
        sweet_y = self.detector.last_sweet_spot_y

        # Scale Y coordinates to match display size
        scale_y = 2
        scale_x = 4

        # Draw fish position (green line)
        if fish_y is not None:
            scaled_fish_y = int(fish_y * scale_y)
            cv2.line(display, (0, scaled_fish_y), (display.shape[1], scaled_fish_y), (0, 255, 0), 2)
            cv2.putText(display, f"Fish: {fish_y}", (5, scaled_fish_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Draw sweet spot position (blue line)
        if sweet_y is not None:
            scaled_sweet_y = int(sweet_y * scale_y)
            cv2.line(display, (0, scaled_sweet_y), (display.shape[1], scaled_sweet_y), (255, 100, 0), 2)
            cv2.putText(display, f"Sweet: {sweet_y}", (5, scaled_sweet_y + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 0), 1)

        # Draw action indicator
        action_text = "HOLD" if should_hold else "RELEASE" if should_hold is False else "???"
        action_color = (0, 255, 0) if should_hold else (0, 0, 255)
        cv2.putText(display, action_text, (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, action_color, 2)

        # Draw distance if both positions known
        if fish_y is not None and sweet_y is not None:
            distance = fish_y - sweet_y
            cv2.putText(display, f"Dist: {distance}", (5, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        cv2.imshow("GPO Fishing Debug", display)
        cv2.waitKey(1)  # Required to update window

    def _handle_caught(self, frame):
        """Handle CAUGHT state - recast and return to idle."""
        self.overlay.update(is_active=False, status="CAUGHT")
        print("[State] Recasting...")

        # Wait a moment
        time.sleep(RECAST_DELAY)

        # Click to recast
        self.mouse.click()

        # Wait for fish but keep checking - don't just sleep!
        print("[State] -> IDLE (waiting for fish)")
        self.state = FishingState.IDLE
        self.idle_start_time = time.time()  # Start idle timer
        # Don't sleep here - let the main loop handle detection immediately

    def _do_anti_afk(self):
        """Do anti-AFK actions to prevent disconnect when out of bait."""
        import random

        # Random movement to look more natural
        movements = ['w', 'a', 's', 'd']

        # Do a few movements
        for _ in range(3):
            # Pick a random direction
            key = random.choice(movements)
            keyboard.press(key)
            time.sleep(0.2)
            keyboard.release(key)
            time.sleep(0.1)

        # Jump
        keyboard.press('space')
        time.sleep(0.1)
        keyboard.release('space')
        time.sleep(0.3)

        # One more movement
        key = random.choice(movements)
        keyboard.press(key)
        time.sleep(0.15)
        keyboard.release(key)

        print("[State] Anti-AFK complete, resuming idle...")

    def _cleanup(self):
        """Clean up resources."""
        print("[Macro] Cleaning up...")
        self.mouse.cleanup()
        self.capture.close()
        self.overlay.close()
        if self.debug_capture:
            self.debug_capture.close()
        if SHOW_DEBUG_WINDOW:
            cv2.destroyAllWindows()
        keyboard.unhook_all()
        if DEBUG_MODE:
            print("[Macro] Debug log saved to: debug.log")
        print("[Macro] Goodbye!")


def main():
    """Entry point."""
    print("")
    print("Starting GPO Fishing Macro...")
    print("")

    # Check that we're not running in a weird environment
    try:
        macro = FishingMacro()
        macro.run()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("")
        print("Troubleshooting tips:")
        print("1. Try running as Administrator")
        print("2. Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        print("3. Make sure Roblox is open and visible")
        raise


if __name__ == "__main__":
    main()
