from Xlib import X, XK
from Xlib.error import BadDrawable
from Xlib.display import Display
import logging
from . import xq

from ewmh import EWMH
workaround_ewmh = EWMH()

def snap_window(self, window, x, y):
    logging.debug(f"  snap_window({x=}, {y=})")
    try:
        display = Display()

        # todo: implement zone-merge around borders
        zone = self.zp.find_zone(xq.get_current_virtual_desktop(display), x, y)
        logging.debug(f"\tlanding zone: {zone}")

        if window and zone:
            extents = xq.get_window_frame_extents(window)
            # chrome, system monitor, software manager, etc. don't have extents
            # seemingly because they manage/render their own title bars
            # (tabs, search field, etc.)
            #
            # whilst I'm confident some of these implementations may have
            # their own subwindows for the title bar area, it seems
            # less than worthwile for the time being to dig into
            #
            # it seems like hooking into _NET_WM_MOVERESIZE if possible
            # would be ideal but haven't found a viable option to do so yet
            # and it may be exclusive to one X11 client at a time (intended for WM)
            el, er, et, eb = extents if extents != None else (0, 0, 0, 0)

            # ewmh method is much more reliable than window.configure
            workaround_ewmh.setMoveResizeWindow(
                window,
                x=zone.x,
                y=zone.y,
                w=zone.width - el - er,
                h=zone.height - et - eb
            )

            # these window hints provide better movement of windows rather than arbitrary dimensions
            # (without this, WM magic may cause windows to clip out of the usable work area)
            if zone.orientation == 'landscape':
                workaround_ewmh.setWmState(window, 1, '_NET_WM_STATE_MAXIMIZED_VERT')
            elif zone.orientation == 'portrait':
                workaround_ewmh.setWmState(window, 1, '_NET_WM_STATE_MAXIMIZED_HORZ')


            # certain application windows, for example:
            #    https://github.com/linuxmint/sticky
            #    https://wiki.gnome.org/Apps/SystemMonitor
            #
            # don't have extents due to the title bar embedded UI, but also have some
            # type of "margin" applied to the window which is not measured (afaict)
            # separately from the window geometry
            #
            # haven't looked deeply into it, but so far have been unable to find a
            # workaround for proper zone placement
            #
            # the _NET_WM_STATE_MAXIMIZED_* code above helps ignore the extra space on
            # one dimension, but it remains on the other
            #
            # interestingly, once maximized across an access, the geometry (say,
            # width on a portrait monitor) will be larger than screen size available
            # 1120 on a 1080 wide screen
            #
            # no idea how to figure out where this comes from
            # is there a way to detect these windows programatically? is it always 20px
            # around the window?
            #
            # reference, seems related:
            # https://unix.stackexchange.com/questions/168835/how-can-i-remove-the-window-padding-on-gtk3-apps-in-awesome-wm
            #
            # must be managed by user css? not externally?
            workaround_ewmh.display.flush()

    except BadDrawable:
        logging.debug(f"  snap_window failed with X.BadDrawable")

