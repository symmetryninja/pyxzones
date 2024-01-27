from Xlib import X, XK
from Xlib.error import BadDrawable
from Xlib.display import Display
import logging
from . import xq

def geometry_deltas(window):
    """The window of an app usually sits within an Xorg parent frame, and we
    want to fit that parent frame to the zone and not the inner window (so
    decorations like borders are properly handled). I can't seem to get that
    window to update directly, so we'll update the child window using the
    difference b/t the parent and child so to fit the final result
    correctly."""
    wg = window.get_geometry()
    dx, dy, dw, dh = 0, 0, 0, 0
    parent = window.query_tree().parent
    pg = parent.get_geometry()
    dx = pg.x - wg.x
    dy = pg.y - wg.y
    dw = pg.width - wg.width
    dh = pg.height - wg.height
    return dx, dy, dw, dh

def snap_window(self, window, x, y):
    try:
        display = Display()
        zone_profile = self.zp
        #dx, dy, dw, dh = geometry_deltas(window)
        #logging.debug(f"snap_window:　{dx=}, {dy=}, {dw=}, {dh=}")
        zone = zone_profile.find_zones(xq.get_current_virtual_desktop(display), self, x, y)
        if window and zone:
            logging.debug(f"window.configure(x={zone.x}, y={zone.y}, width={zone.width}, height={zone.height})")
            window.configure(
                x=zone.x,
                y=zone.y,
                width=zone.width,# - dx,
                height=zone.height,# - dy,
                stack_mode=X.Above,
            )
            display.sync()
    except BadDrawable:
        pass
