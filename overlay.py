"""
GPO Fishing Macro - Visual Overlay
===================================
Transparent overlay that sits ON TOP of the game showing detection lines.
"""

import tkinter as tk
import threading


class FishingOverlay:
    """
    Transparent overlay directly over the capture region.
    Shows fish and sweet spot lines on top of the game.
    """

    def __init__(self, region):
        self.region = region
        self.fish_y = None
        self.sweet_y = None
        self.is_active = False
        self.status = "OFF"
        self.action = None
        self.running = True

        # Start overlay in background thread
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        import time
        time.sleep(0.2)

    def _run(self):
        """Run the overlay window."""
        self.root = tk.Tk()
        self.root.title("")

        # Position directly over capture region
        x = self.region["left"]
        y = self.region["top"]
        w = self.region["width"]
        h = self.region["height"]

        self.w = w
        self.h = h

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)

        # Make background transparent
        self.trans_color = '#010101'
        self.root.config(bg=self.trans_color)
        self.root.attributes('-transparentcolor', self.trans_color)

        self.canvas = tk.Canvas(self.root, width=w, height=h, bg=self.trans_color, highlightthickness=2, highlightbackground='#ff0000')
        self.canvas.pack()

        self._draw()
        self.root.mainloop()

    def _draw(self):
        """Redraw the overlay."""
        if not self.running:
            self.root.destroy()
            return

        self.canvas.delete("all")

        w, h = self.w, self.h

        # Border color based on state
        if self.is_active:
            self.canvas.config(highlightbackground='#00ff00')
        else:
            self.canvas.config(highlightbackground='#ff0000')

        # Draw sweet spot line (orange) with zone
        if self.sweet_y is not None:
            # Sweet spot zone (semi-transparent box)
            zone_h = 30
            self.canvas.create_rectangle(
                0, self.sweet_y - zone_h//2,
                w, self.sweet_y + zone_h//2,
                fill='', outline='#ff8800', width=1
            )
            # Center line
            self.canvas.create_line(0, self.sweet_y, w, self.sweet_y, fill='#ff8800', width=2)
            # Label
            self.canvas.create_text(w-3, self.sweet_y-8, text="S", font=('Arial', 8, 'bold'), fill='#ff8800', anchor='e')

        # Draw fish marker (green line)
        if self.fish_y is not None and self.is_active:
            self.canvas.create_line(0, self.fish_y, w, self.fish_y, fill='#00ff00', width=3)
            # Small label
            self.canvas.create_text(w-3, self.fish_y+10, text="F", font=('Arial', 8, 'bold'), fill='#00ff00', anchor='e')

        # Action indicator at bottom
        if self.action == "HOLD":
            self.canvas.create_rectangle(2, h-18, w-2, h-2, fill='#00aa00', outline='')
            self.canvas.create_text(w//2, h-10, text="HOLD", font=('Arial', 8, 'bold'), fill='#ffffff')
        elif self.action == "RELEASE":
            self.canvas.create_rectangle(2, h-18, w-2, h-2, fill='#aa0000', outline='')
            self.canvas.create_text(w//2, h-10, text="REL", font=('Arial', 8, 'bold'), fill='#ffffff')

        self.root.after(33, self._draw)

    def update(self, fish_y=None, sweet_y=None, is_active=False, status="OFF", action=None):
        """Update overlay state."""
        self.fish_y = fish_y
        self.sweet_y = sweet_y
        self.is_active = is_active
        self.status = status
        self.action = action

    def close(self):
        """Close overlay."""
        self.running = False
