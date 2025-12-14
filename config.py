"""
GPO Fishing Macro - Configuration
==================================
Adjust these settings to match your screen and game setup.
"""

# =============================================================================
# SCREEN REGION - Where to look for the fishing bars
# =============================================================================
# You'll need to adjust these values for your screen resolution.
# The region is defined as (left, top, width, height)
#
# TIP: Run the region_selector.py helper to find the correct values,
# or use a screenshot tool to find the pixel coordinates of the fishing UI.

CAPTURE_REGION = {
    "left": 1035,     # X coordinate of the left edge of capture area
    "top": 429,       # Y coordinate of the top edge of capture area
    "width": 48,      # Width - just the left fishing bar
    "height": 303,    # Height of capture area
}

# =============================================================================
# COLOR DETECTION - Colors to look for in the fishing UI
# =============================================================================
# Colors are in BGR format (Blue, Green, Red) - NOT RGB!
# OpenCV uses BGR by default.
#
# Each color has a "lower" and "upper" bound for detection tolerance.
# The detector looks for pixels within this range.

# Fish indicator marker - WHITE when not tracking
# Looking for bright white pixels that mark the fish position
FISH_MARKER_WHITE = {
    "lower": (200, 200, 200),  # Minimum BGR values
    "upper": (255, 255, 255),  # Maximum BGR values
}

# Fish indicator marker - GREEN when tracking correctly
# RGB (172, 255, 127) = BGR (127, 255, 172)
FISH_MARKER_GREEN = {
    "lower": (100, 220, 140),  # Minimum BGR values
    "upper": (160, 255, 200),  # Maximum BGR values
}

# Green progress bar (right bar that fills up)
# Bright green color when successfully tracking
PROGRESS_BAR_COLOR = {
    "lower": (0, 200, 0),      # Minimum BGR (greenish)
    "upper": (100, 255, 100),  # Maximum BGR
}

# Dark bar detection (to check if fishing UI is visible)
# Looking for the dark/black bar background
BAR_BACKGROUND_COLOR = {
    "lower": (0, 0, 0),        # Minimum BGR (black)
    "upper": (50, 50, 50),     # Maximum BGR (dark gray)
}

# Cyan/blue bar color (the "not your zone" sections)
# The sweet spot is the GAP between these colored bars
# User provided: RGB (85, 170, 255) = BGR (255, 170, 85)
BLUE_BAR_COLOR = {
    "lower": (220, 140, 50),   # Minimum BGR - tight range to avoid ocean
    "upper": (255, 200, 120),  # Maximum BGR
}

# =============================================================================
# TIMING SETTINGS
# =============================================================================

# How often to check the screen (in seconds)
# Lower = more responsive but uses more CPU
# Recommended: 0.008 (120 checks/sec) for fast response
LOOP_DELAY = 0.008  # ~120 checks per second for fast reaction

# Delay after catching a fish before clicking to recast (in seconds)
RECAST_DELAY = 1.0

# Delay between recasting and checking for new fish (in seconds)
# Fish can take a while to bite - set this high enough
WAIT_FOR_FISH_DELAY = 10.0

# Auto-recast timeout (in seconds)
# If waiting for fish longer than this, click to recast
# Helps recover from stuck states and prevents AFK timeout
IDLE_TIMEOUT = 30.0

# =============================================================================
# HOTKEY SETTINGS
# =============================================================================

# Key to toggle the macro ON/OFF
TOGGLE_KEY = "p"

# Key to exit the program completely
EXIT_KEY = "z"

# =============================================================================
# DETECTION THRESHOLDS
# =============================================================================

# Minimum number of white pixels to consider fish marker detected
MIN_FISH_MARKER_PIXELS = 10

# Minimum number of dark pixels to consider fishing bar present
# Real fishing has 2700+ dark pixels, set threshold high to avoid false positives
MIN_BAR_PIXELS = 500

# How close the sweet spot needs to be to the fish (in pixels)
# Smaller = more precise tracking, larger = more forgiving
TRACKING_TOLERANCE = 20

# Dead zone - don't change action if within this many pixels
# Helps prevent oscillation/overshooting
DEAD_ZONE = 20

# Velocity threshold for braking - if moving faster than this, apply brakes
# Lower value = more aggressive braking to prevent overshoot
BRAKE_VELOCITY = 8

# =============================================================================
# DEBUG SETTINGS
# =============================================================================

# Show debug output in console (set to False to reduce spam)
DEBUG_MODE = False

# Show live debug window with visual overlay
# Displays what the macro sees in real-time
SHOW_DEBUG_WINDOW = False

# Save screenshots when detection fails (for troubleshooting)
# Set to True to capture frames for debugging
SAVE_DEBUG_SCREENSHOTS = False

# Gravity compensation - sweet spot falls when mouse released
# Higher value = more aggressive holding to counteract gravity
GRAVITY_COMPENSATION = 0  # disabled for simpler control
