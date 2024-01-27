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

from ewmh import EWMH
workaround_ewmh = EWMH()

def snap_window(self, window, x, y):
    logging.debug(f"  snap_window({x=}, {y=})")
    try:
        display = Display()
        #dx, dy, dw, dh = geometry_deltas(window)
        #logging.debug(f"snap_window:　{dx=}, {dy=}, {dw=}, {dh=}")

        # todo: implement zone-merge around borders
        zone = self.zp.find_zone(xq.get_current_virtual_desktop(display), x, y)
        logging.debug(f"\tlanding zone: {zone=}")

        """
        if window and zone:
            logging.debug(f"window.configure(x={zone.x}, y={zone.y}, width={zone.width}, height={zone.height})")
            window.configure(
                x=zone.x,
                y=zone.y,
                width=zone.width,# - dx,
                height=zone.height,# - dy,
                stack_mode=X.Above
            )
            window.change_attributes(win_gravity=X.NorthWestGravity, bit_gravity=X.StaticGravity)
            display.sync()
            display.flush()
        """
        if window and zone:
            # ewmh method is much more reliable than window.configure
            #window = ewmh.getActiveWindow() # didn't know this method existed...
            #workaround_ewmh.setMoveResizeWindow(window, x=zone.x, y=zone.y, w=zone.width, h=zone.height)
            workaround_ewmh.setMoveResizeWindow(
                window,
                x=zone.x,
                y=zone.y,
                w=zone.width,
                h=zone.height
            )

            # these window hints provide better movement of windows rather than arbitrary dimensions
            # (without this, WM magic may cause windows to clip out of the usable work area)
            if zone.orientation == 'landscape':
                workaround_ewmh.setWmState(window, 1, '_NET_WM_STATE_MAXIMIZED_VERT')
            elif zone.orientation == 'portrait':
                workaround_ewmh.setWmState(window, 1, '_NET_WM_STATE_MAXIMIZED_HORZ')

            workaround_ewmh.display.flush()
    except BadDrawable:
        pass

