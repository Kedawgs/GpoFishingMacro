# GPO Fishing Macro

An automated fishing macro for Grand Piece Online (Roblox). Uses computer vision to detect the fishing minigame UI and automatically controls the mouse to catch fish.

## Features

- **Automatic fish tracking** - Detects and follows the fish marker in real-time
- **Smart position control** - Uses velocity prediction and braking to prevent overshooting
- **Edge handling** - Steady control at top/bottom edges to prevent bouncing
- **Auto-recast** - Automatically recasts when idle too long
- **Anti-AFK** - Moves character when out of bait to prevent disconnection
- **Visual overlay** - Shows current status on top of the game window

## Requirements

- Python 3.8+
- Windows 10/11
- Roblox running in windowed mode

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Kedawgs/gpo-fishing-macro.git
   cd gpo-fishing-macro
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the capture region (see [Configuration](#configuration))

## Usage

1. Open Roblox and go to a fishing spot in GPO
2. Start the macro:
   ```bash
   python main.py
   ```
3. Press `P` to toggle the macro ON/OFF
4. Press `Z` to exit the program

## Controls

| Key | Action |
|-----|--------|
| `P` | Toggle macro ON/OFF |
| `Z` | Exit program |

## Configuration

Edit `config.py` to customize the macro:

### Capture Region

The most important setting - you need to configure this for your screen resolution:

```python
CAPTURE_REGION = {
    "left": 1035,     # X coordinate of fishing bar
    "top": 429,       # Y coordinate of fishing bar
    "width": 48,      # Width of capture area
    "height": 303,    # Height of capture area
}
```

**Tip:** Run `python region_selector.py` to help find the correct coordinates for your setup.

### Hotkeys

```python
TOGGLE_KEY = "p"      # Key to toggle macro ON/OFF
EXIT_KEY = "z"        # Key to exit program
```

### Timing

```python
LOOP_DELAY = 0.008    # Detection speed (~120 checks/sec)
RECAST_DELAY = 1.0    # Delay after catching before recast
IDLE_TIMEOUT = 30.0   # Seconds before auto-recast
```

### Debug Options

```python
DEBUG_MODE = False              # Enable console debug output
SHOW_DEBUG_WINDOW = False       # Show live detection window
SAVE_DEBUG_SCREENSHOTS = False  # Save frames to debug_frames/
```

## How It Works

1. **Screen Capture** - Captures a small region of the screen where the fishing bar appears
2. **Color Detection** - Uses OpenCV to detect:
   - Fish marker (white when not tracking, green when tracking)
   - Sweet spot position (gap between blue bars)
3. **Control Logic** - Decides whether to hold or release mouse:
   - Hold = sweet spot moves up
   - Release = sweet spot falls down
4. **Velocity Prediction** - Tracks movement speed to prevent overshooting
5. **Anti-AFK** - After 7 consecutive idle timeouts (no fish), moves character to prevent disconnect

## Project Structure

```
gpo-fishing-macro/
├── main.py              # Entry point and state machine
├── detector.py          # Fish and sweet spot detection
├── mouse_control.py     # Mouse automation
├── screen_capture.py    # Screen capture using mss
├── overlay.py           # Visual status overlay
├── config.py            # Configuration settings
├── region_selector.py   # Helper to find capture region
├── debug_capture.py     # Debug frame saving
├── visual_debug.py      # Visual debugging tools
├── sweet_spot_debug.py  # Sweet spot detection debugging
└── requirements.txt     # Python dependencies
```

## Troubleshooting

### Macro not detecting the fishing bar
- Make sure the `CAPTURE_REGION` in `config.py` matches your screen
- Run `python region_selector.py` to find correct coordinates
- Enable `DEBUG_MODE = True` to see detection output

### Fish not being tracked properly
- Enable `SHOW_DEBUG_WINDOW = True` to see what the macro detects
- Check if colors in `config.py` match your game (UI themes may vary)

### Running as Administrator
Some systems require admin privileges for mouse control:
- Right-click `main.py` → Run as Administrator
- Or run your terminal as Administrator

## Disclaimer

This macro is for educational purposes. Using automation tools may violate Roblox's Terms of Service. Use at your own risk.

## Support

If this macro saved you time, consider supporting:
- Venmo: @Daniel-K-25
- ETH/EVM: `0x3260f49c7df40cfdc550fff88d48d242e67ec5c5`

## License

MIT License - see [LICENSE](LICENSE) for details.
