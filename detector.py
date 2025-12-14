"""
GPO Fishing Macro - Detection Module
=====================================
Detects fish position, sweet spot, and progress bar state.
Uses OpenCV for color-based detection.
"""

import cv2
import numpy as np
from config import (
    FISH_MARKER_WHITE,
    FISH_MARKER_GREEN,
    PROGRESS_BAR_COLOR,
    BAR_BACKGROUND_COLOR,
    BLUE_BAR_COLOR,
    MIN_FISH_MARKER_PIXELS,
    MIN_BAR_PIXELS,
    DEBUG_MODE,
    DEAD_ZONE,
    BRAKE_VELOCITY,
    GRAVITY_COMPENSATION,
)


class FishingDetector:
    """
    Detects elements of the GPO fishing minigame UI.

    The fishing UI has:
    - Left bar: Shows fish position (white line) and your sweet spot (dark)
    - Right bar: Progress bar that fills green as you track successfully
    """

    def __init__(self):
        """Initialize the detector."""
        # Store last known positions for smoothing
        self.last_fish_y = None
        self.last_sweet_spot_y = None
        self.fish_is_green = False  # True when tracking correctly (fish marker is green)

        # Velocity tracking for predictive control
        self.prev_sweet_spot_y = None
        self.sweet_spot_velocity = 0  # Positive = moving down, Negative = moving up

        # Control state
        self.is_holding = False
        self.hold_frames = 0  # How long we've been holding/releasing

        # Pulse counter for maintaining position in dead zone
        self.pulse_counter = 0
        self.PULSE_HOLD_FRAMES = 5   # Hold for 5 frames (counteracts gravity)
        self.PULSE_RELEASE_FRAMES = 1  # Release for 1 frame

        # Sweet spot jump filter - reject detection glitches
        self.MAX_SWEET_SPOT_JUMP = 50  # Reject jumps larger than this
        self.warmup_frames = 0  # Frames to skip filtering at start of each fish

        # Brake phase when entering dead zone
        self.in_dead_zone = False
        self.brake_frames = 0
        self.BRAKE_FRAMES_NEEDED = 5  # Hold for 5 frames to brake before pulsing

    def reset_state(self):
        """Reset all tracking state for a new fish. Call when fishing starts."""
        self.last_fish_y = None
        self.fish_is_green = False
        # Start at middle of bar (150) - will gradually adjust during warmup
        self.last_sweet_spot_y = 150
        self.prev_sweet_spot_y = None
        self.sweet_spot_velocity = 0
        self.is_holding = False
        self.hold_frames = 0
        self.pulse_counter = 0
        self.in_dead_zone = False
        self.brake_frames = 0
        # Allow first few frames to gradually adjust toward real position
        self.warmup_frames = 10  # More frames to smoothly reach real position

    def is_fishing_active(self, frame):
        """
        Check if the fishing minigame is currently active.
        Looks for BOTH dark bar background AND blue bar sections.

        Args:
            frame: BGR image from screen capture

        Returns:
            bool: True if fishing bars are visible
        """
        # Check for dark pixels (bar background)
        lower_dark = np.array(BAR_BACKGROUND_COLOR["lower"], dtype=np.uint8)
        upper_dark = np.array(BAR_BACKGROUND_COLOR["upper"], dtype=np.uint8)
        dark_mask = cv2.inRange(frame, lower_dark, upper_dark)
        dark_pixel_count = cv2.countNonZero(dark_mask)

        # Also check for blue bar pixels (the cyan/blue sections)
        lower_blue = np.array(BLUE_BAR_COLOR["lower"], dtype=np.uint8)
        upper_blue = np.array(BLUE_BAR_COLOR["upper"], dtype=np.uint8)
        blue_mask = cv2.inRange(frame, lower_blue, upper_blue)
        blue_pixel_count = cv2.countNonZero(blue_mask)

        if DEBUG_MODE:
            print(f"[Detector] Dark pixels: {dark_pixel_count}, Blue pixels: {blue_pixel_count}")

        # Fishing is active if we have BOTH dark pixels AND blue bar pixels
        # This prevents false positives from dark ocean water
        # Real fishing has 1400+ blue pixels, use high threshold to avoid false positives
        return dark_pixel_count > MIN_BAR_PIXELS and blue_pixel_count > 300

    def get_fish_position(self, frame):
        """
        Find the Y position of the fish marker.
        Detects BOTH white (not tracking) and green (tracking correctly) fish.

        Args:
            frame: BGR image from screen capture

        Returns:
            int or None: Y coordinate of fish marker, or None if not found
        """
        # Detect WHITE fish marker (not tracking)
        lower_white = np.array(FISH_MARKER_WHITE["lower"], dtype=np.uint8)
        upper_white = np.array(FISH_MARKER_WHITE["upper"], dtype=np.uint8)
        white_mask = cv2.inRange(frame, lower_white, upper_white)
        white_pixels = cv2.countNonZero(white_mask)

        # Detect GREEN fish marker (tracking correctly)
        lower_green = np.array(FISH_MARKER_GREEN["lower"], dtype=np.uint8)
        upper_green = np.array(FISH_MARKER_GREEN["upper"], dtype=np.uint8)
        green_mask = cv2.inRange(frame, lower_green, upper_green)
        green_pixels = cv2.countNonZero(green_mask)

        # Determine if fish is green (tracking) or white (not tracking)
        # Green means we're doing well, white means we need to catch up
        self.fish_is_green = green_pixels > white_pixels

        # Combine both masks - fish can be either color
        combined_mask = cv2.bitwise_or(white_mask, green_mask)

        # Count fish pixels
        fish_pixels = cv2.countNonZero(combined_mask)

        if fish_pixels < MIN_FISH_MARKER_PIXELS:
            if DEBUG_MODE:
                print(f"[Detector] Fish marker not found (only {fish_pixels} pixels)")
            return self.last_fish_y  # Return last known position

        # Find the coordinates of fish pixels
        coords = cv2.findNonZero(combined_mask)

        if coords is None:
            return self.last_fish_y

        # Get the average Y coordinate, adjusted for fish icon center
        # White fish icon is taller than green, so needs larger offset
        # Larger offset = aim higher (more negative)
        y_coords = coords[:, 0, 1]
        offset = -8 if self.fish_is_green else -35  # Green is shorter, white needs bigger offset
        fish_y = int(np.mean(y_coords)) + offset

        # Update last known position
        self.last_fish_y = fish_y

        if DEBUG_MODE:
            color = "GREEN" if self.fish_is_green else "WHITE"
            print(f"[Detector] Fish Y position: {fish_y} ({fish_pixels} pixels, {color})")

        return fish_y

    def get_sweet_spot_position(self, frame):
        """
        Find the Y position of the sweet spot (the section you control).

        The sweet spot is the DARK section between BLUE bars.
        - Blue bars = "not your zone"
        - Gap between blue = your sweet spot

        Args:
            frame: BGR image from screen capture

        Returns:
            int or None: Y coordinate of sweet spot center, or None if not found
        """
        height, width = frame.shape[:2]

        # Use entire frame (capture region should already be just the bar)
        bar_area = frame

        # Detect BLUE pixels (the "not your zone" areas)
        lower_blue = np.array(BLUE_BAR_COLOR["lower"], dtype=np.uint8)
        upper_blue = np.array(BLUE_BAR_COLOR["upper"], dtype=np.uint8)
        blue_mask = cv2.inRange(bar_area, lower_blue, upper_blue)

        # Count blue pixels per row
        blue_per_row = np.sum(blue_mask > 0, axis=1)

        # Find rows with LOW blue count = sweet spot area
        # Threshold: less than 20% of max blue count
        max_blue = np.max(blue_per_row) if np.max(blue_per_row) > 0 else 1
        threshold = max_blue * 0.2

        # Find rows that are NOT blue (sweet spot rows)
        sweet_spot_rows = np.where(blue_per_row < threshold)[0]

        if len(sweet_spot_rows) == 0:
            if DEBUG_MODE:
                print("[Detector] Sweet spot not detected (no gap in blue)")
            return self.last_sweet_spot_y

        # Find the center of the sweet spot
        # Look for the largest continuous gap
        if len(sweet_spot_rows) > 0:
            # Find continuous segments
            gaps = np.diff(sweet_spot_rows)
            segment_breaks = np.where(gaps > 5)[0]

            if len(segment_breaks) == 0:
                # One continuous segment
                sweet_spot_y = int(np.mean(sweet_spot_rows))
            else:
                # Multiple segments - find the largest one
                segments = np.split(sweet_spot_rows, segment_breaks + 1)
                largest_segment = max(segments, key=len)
                sweet_spot_y = int(np.mean(largest_segment))
        else:
            sweet_spot_y = self.last_sweet_spot_y

        # Reject sweet spot detections at extreme edges (false positives from bar edges)
        # Valid range is roughly 20-280 (bar is about 300px tall) - allow near top/bottom
        if sweet_spot_y is not None and (sweet_spot_y < 20 or sweet_spot_y > 280):
            if DEBUG_MODE:
                print(f"[Detector] REJECTING edge sweet_y={sweet_spot_y} (out of valid range 20-280)")
            return self.last_sweet_spot_y

        # During warmup, just count down but accept valid detections immediately
        if self.warmup_frames > 0:
            self.warmup_frames -= 1
            if DEBUG_MODE:
                print(f"[Detector] Warmup frame {self.warmup_frames}, accepting sweet_y={sweet_spot_y}")

        # Validate sweet_spot_y - reject sudden large jumps (likely detection glitches)
        if sweet_spot_y is not None and self.last_sweet_spot_y is not None:
            jump = abs(sweet_spot_y - self.last_sweet_spot_y)
            if jump > self.MAX_SWEET_SPOT_JUMP:
                # Reject this value - likely a detection glitch
                if DEBUG_MODE:
                    print(f"[Detector] REJECTING sweet_y jump: {self.last_sweet_spot_y} -> {sweet_spot_y} (jump={jump})")
                return self.last_sweet_spot_y

        # Update last known position
        if sweet_spot_y is not None:
            self.last_sweet_spot_y = sweet_spot_y

        if DEBUG_MODE:
            print(f"[Detector] Sweet spot Y position: {sweet_spot_y} (gap in blue bars)")

        return sweet_spot_y

    def get_progress(self, frame):
        """
        Get the progress bar fill percentage.

        Args:
            frame: BGR image from screen capture

        Returns:
            float: Progress from 0.0 to 1.0, or 0.0 if not detected
        """
        # Convert color bounds to numpy arrays
        lower = np.array(PROGRESS_BAR_COLOR["lower"], dtype=np.uint8)
        upper = np.array(PROGRESS_BAR_COLOR["upper"], dtype=np.uint8)

        # Look at right portion of frame (where progress bar is)
        height, width = frame.shape[:2]
        right_portion = frame[:, int(width * 0.6):]

        # Create mask for green pixels
        mask = cv2.inRange(right_portion, lower, upper)

        # Count green pixels
        green_pixels = cv2.countNonZero(mask)

        # Estimate total possible pixels in progress bar
        # Rough estimate: progress bar is about 10% of width, full height
        total_bar_pixels = height * (width * 0.1)

        # Calculate fill percentage
        progress = min(1.0, green_pixels / max(1, total_bar_pixels))

        if DEBUG_MODE:
            print(f"[Detector] Progress: {progress:.1%}")

        return progress

    def is_fish_caught(self, frame):
        """
        Check if the fish has been caught (progress bar full or bars gone).

        Args:
            frame: BGR image from screen capture

        Returns:
            bool: True if fish is caught
        """
        # Check if bars are still visible
        if not self.is_fishing_active(frame):
            return True  # Bars gone = fish caught

        # Check if progress bar is nearly full
        progress = self.get_progress(frame)
        if progress > 0.95:
            return True

        return False

    def should_hold_mouse(self, frame):
        """
        Determine if we should hold the mouse button.
        Uses predictive control to account for momentum/acceleration.

        Args:
            frame: BGR image from screen capture

        Returns:
            bool or None: True = hold, False = release, None = can't determine
        """
        fish_y = self.get_fish_position(frame)
        sweet_spot_y = self.get_sweet_spot_position(frame)

        if fish_y is None or sweet_spot_y is None:
            # Can't detect positions - TAP to maintain middle ground
            self.pulse_counter += 1
            should_hold = (self.pulse_counter % 4) < 2  # 2 frames hold, 2 frames release
            if DEBUG_MODE:
                action = "HOLD" if should_hold else "RELEASE"
                print(f"[Detector] Cannot detect - TAP to maintain ({action})")
            self.is_holding = should_hold
            return should_hold

        # If sweet spot is stuck at reset value (150), detection is failing - TAP
        if sweet_spot_y == 150 and abs(self.sweet_spot_velocity) < 0.5:
            self.pulse_counter += 1
            should_hold = (self.pulse_counter % 4) < 2  # 2 frames hold, 2 frames release
            if DEBUG_MODE:
                action = "HOLD" if should_hold else "RELEASE"
                print(f"[Detector] Sweet spot stuck - TAP to maintain ({action})")
            self.is_holding = should_hold
            return should_hold

        # Calculate velocity (how fast sweet spot is moving)
        if self.prev_sweet_spot_y is not None:
            # Smooth the velocity a bit to reduce noise
            new_velocity = sweet_spot_y - self.prev_sweet_spot_y
            self.sweet_spot_velocity = (self.sweet_spot_velocity * 0.5) + (new_velocity * 0.5)
        self.prev_sweet_spot_y = sweet_spot_y

        # For first few frames, be more aggressive (no velocity data yet)
        is_warmup = abs(self.sweet_spot_velocity) < 0.1

        # Calculate distance and direction
        # Apply gravity compensation - aim ABOVE the fish to counteract falling
        # This makes the "target" position slightly above the actual fish
        target_y = fish_y - GRAVITY_COMPENSATION
        distance = target_y - sweet_spot_y  # Positive = target below, Negative = target above

        # Prediction zone - anticipate where sweet spot will be
        # Account for gravity: when released, it falls faster (add gravity factor)
        PREDICTION_FRAMES = 3
        gravity_factor = 2 if not self.is_holding else 0  # Extra fall speed when released
        predicted_sweet_y = sweet_spot_y + (self.sweet_spot_velocity * PREDICTION_FRAMES) + gravity_factor
        predicted_distance = target_y - predicted_sweet_y

        if DEBUG_MODE:
            print(f"[Detector] Fish Y: {fish_y}, Target Y: {target_y}, Sweet Y: {sweet_spot_y}")
            print(f"[Detector] Distance: {distance}, Velocity: {self.sweet_spot_velocity:.1f}")
            print(f"[Detector] Predicted distance: {predicted_distance:.1f}, Gravity comp: {GRAVITY_COMPENSATION}")

        # During warmup, use smaller dead zone for faster initial response
        active_dead_zone = 5 if is_warmup else DEAD_ZONE

        # JUMP THRESHOLDS - use sustained hold/release for jumps instead of tapping
        # This takes priority over velocity braking to catch fast-moving fish
        BIG_JUMP_THRESHOLD = 60    # Big jumps - definitely need sustained action
        MEDIUM_JUMP_THRESHOLD = 30  # Medium jumps - still too big for tapping

        if abs(distance) > MEDIUM_JUMP_THRESHOLD:
            if distance < 0:
                # Fish is above - HOLD to catch up
                if DEBUG_MODE:
                    jump_type = "BIG" if abs(distance) > BIG_JUMP_THRESHOLD else "MEDIUM"
                    print(f"[Detector] {jump_type} JUMP UP: distance={distance} -> sustained HOLD")
                self.is_holding = True
                return True
            else:
                # Fish is below - RELEASE to fall down
                if DEBUG_MODE:
                    jump_type = "BIG" if abs(distance) > BIG_JUMP_THRESHOLD else "MEDIUM"
                    print(f"[Detector] {jump_type} JUMP DOWN: distance={distance} -> sustained RELEASE")
                self.is_holding = False
                return False

        # Calculate proportional brake distance - brake earlier when moving faster
        # This prevents overshoot by starting counter-action before reaching target
        brake_distance = abs(self.sweet_spot_velocity) * 2.5  # Higher multiplier = earlier braking

        # FIRST: Check if we need to brake due to high velocity (regardless of distance)
        # This prevents overshoot by counter-acting momentum early
        if not is_warmup and abs(self.sweet_spot_velocity) > BRAKE_VELOCITY:
            # Moving up fast (negative velocity) - release to brake
            if self.sweet_spot_velocity < -BRAKE_VELOCITY:
                if DEBUG_MODE:
                    print(f"[Detector] VELOCITY BRAKE: moving up fast (v={self.sweet_spot_velocity:.1f}) -> RELEASE")
                self.is_holding = False
                return False
            # Moving down fast (positive velocity) - hold to brake
            elif self.sweet_spot_velocity > BRAKE_VELOCITY:
                if DEBUG_MODE:
                    print(f"[Detector] VELOCITY BRAKE: falling fast (v={self.sweet_spot_velocity:.1f}) -> HOLD")
                self.is_holding = True
                return True

        # Smart control logic using config values
        # If fish is above (distance negative)
        if distance < -active_dead_zone:
            self.in_dead_zone = False  # Left the dead zone
            # Fish is above - we need to go up (hold)
            if DEBUG_MODE:
                print("[Detector] Fish above -> HOLD")
            self.is_holding = True
            return True

        # If fish is below (distance positive)
        elif distance > active_dead_zone:
            self.in_dead_zone = False  # Left the dead zone
            # Fish is below - we need to go down (release)
            if DEBUG_MODE:
                print("[Detector] Fish below -> RELEASE")
            self.is_holding = False
            return False

        # In dead zone - brake first if we were moving, then pulse to maintain
        else:
            # FIRST: Check if fish is green (tracking) at edges - don't pulse, stay steady
            if self.fish_is_green:
                # At top edge - just hold steady instead of pulsing
                if sweet_spot_y < 70:
                    if DEBUG_MODE:
                        print(f"[Detector] TOP EDGE + GREEN - steady HOLD (no bounce)")
                    self.is_holding = True
                    return True
                # At bottom edge - just release instead of pulsing
                if sweet_spot_y > 250:
                    if DEBUG_MODE:
                        print(f"[Detector] BOTTOM EDGE + GREEN - steady RELEASE (no bounce)")
                    self.is_holding = False
                    return False

            # If fish is WHITE (not tracking) and at bottom edge, hold to recover
            if not self.fish_is_green and sweet_spot_y > 250:
                if DEBUG_MODE:
                    print(f"[Detector] BOTTOM EDGE + WHITE - HOLD to recover")
                self.is_holding = True
                return True

            # Check if we just entered the dead zone
            if not self.in_dead_zone:
                self.in_dead_zone = True
                self.brake_frames = 0
                self.pulse_counter = 0
                if DEBUG_MODE:
                    print(f"[Detector] ENTERING dead zone, velocity: {self.sweet_spot_velocity:.1f}")

            # If we have downward velocity (falling), brake until stopped
            if self.sweet_spot_velocity > 3:
                if DEBUG_MODE:
                    print(f"[Detector] BRAKING - holding to stop fall (v={self.sweet_spot_velocity:.1f})")
                self.is_holding = True
                return True

            # If we have upward velocity (rising), brake by releasing
            if self.sweet_spot_velocity < -3:
                if DEBUG_MODE:
                    print(f"[Detector] BRAKING - releasing to stop rise (v={self.sweet_spot_velocity:.1f})")
                self.is_holding = False
                return False

            # After braking (or if already slow), pulse to maintain position
            self.pulse_counter += 1
            total_cycle = self.PULSE_HOLD_FRAMES + self.PULSE_RELEASE_FRAMES

            # Reset counter if it gets too high
            if self.pulse_counter >= total_cycle:
                self.pulse_counter = 0

            # Hold for first part of cycle, release for second part
            if self.pulse_counter < self.PULSE_HOLD_FRAMES:
                if DEBUG_MODE:
                    print(f"[Detector] PULSE HOLD ({self.pulse_counter}/{self.PULSE_HOLD_FRAMES})")
                self.is_holding = True
                return True
            else:
                if DEBUG_MODE:
                    print(f"[Detector] PULSE RELEASE ({self.pulse_counter - self.PULSE_HOLD_FRAMES}/{self.PULSE_RELEASE_FRAMES})")
                self.is_holding = False
                return False


# Quick test if run directly
if __name__ == "__main__":
    import cv2
    from screen_capture import ScreenCapture

    print("Testing detector...")
    print("Make sure Roblox GPO is open with fishing minigame active!")
    print("")

    capture = ScreenCapture()
    detector = FishingDetector()

    # Test for a few seconds
    import time
    for i in range(30):  # 3 seconds of testing
        frame = capture.grab()

        print(f"\n--- Frame {i+1} ---")
        active = detector.is_fishing_active(frame)
        print(f"Fishing active: {active}")

        if active:
            fish_y = detector.get_fish_position(frame)
            sweet_y = detector.get_sweet_spot_position(frame)
            progress = detector.get_progress(frame)
            should_hold = detector.should_hold_mouse(frame)

            print(f"Fish Y: {fish_y}")
            print(f"Sweet Spot Y: {sweet_y}")
            print(f"Progress: {progress:.1%}")
            print(f"Should hold mouse: {should_hold}")

        time.sleep(0.1)

    capture.close()
    print("\nDone testing!")
