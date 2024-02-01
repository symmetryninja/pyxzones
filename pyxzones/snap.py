import logging
from Xlib.error import BadDrawable

from .settings import SETTINGS
from .types import MergeZone


def snap_window(self, window, x, y):
    logging.debug(f"  snap_window({x=}, {y=})")
    try:
        zone = self.zone_profile.find_zone(self.ewmh.getShowingDesktop(), x, y)

        if type(zone) is MergeZone:
            zone = zone.surface

        logging.debug(f"\tlanding zone: {zone}")

        if window and zone:
            extents = self.ewmh.getWindowFrameExtents(window)
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
            el, er, et, eb = extents

            # ewmh method is much more reliable than window.configure
            self.ewmh.setMoveResizeWindow(
                window,
                x=zone.x,
                y=zone.y,
                w=zone.width - el - er,
                h=zone.height - et - eb
            )

            # these window hints provide better movement of windows rather than arbitrary dimensions
            # (without this, WM magic may cause windows to clip out of the usable work area)
            if SETTINGS.maximize_perpendicular_axis_on_snap:
                if zone.orientation == 'landscape':
                    self.ewmh.setWmState(window, 1, '_NET_WM_STATE_MAXIMIZED_VERT')
                else:
                    self.ewmh.setWmState(window, 1, '_NET_WM_STATE_MAXIMIZED_HORZ')

            # Certain application windows, for example:
            #    https://github.com/linuxmint/sticky
            #    https://wiki.gnome.org/Apps/SystemMonitor
            #
            # don't have extents due to the title bar embedded UI, but also have some
            # type of "margin" applied to the window which is not measured (afaict)
            # separately from the window geometry
            #
            # The _NET_WM_STATE_MAXIMIZED_* code above helps ignore the extra space on
            # one dimension, but it remains on the other
            #
            # UPDATE: After some digging, these appear to be GTK3.0 windows with default
            # margin CSS rules applied. The only fix _seems_ to be having tiling WM users
            # (and pyxzones users) add custom user styling to ~/.config/gtk-3.0/gtk.css
            # to remove the margin, if the window positioning oddness bothers them.
            #
            # NOTE: There seems to be an early GTK3.0 version of the fix targeting the
            # "window-frame" CSS class and a newer fix targeting "window > decoration"
            #
            # References:
            # https://web.archive.org/web/20220520000107/https://elementaryos.stackexchange.com/questions/23972/gtk-3-22-migration-of-older-gtk-css-black-margin-on-elementaryos-apps
            # https://web.archive.org/web/20220817014757/https://unix.stackexchange.com/questions/168835/how-can-i-remove-the-window-padding-on-gtk3-apps-in-awesome-wm

            self.ewmh.display.flush()

    except BadDrawable:
        logging.debug("  snap_window failed with X.BadDrawable")
