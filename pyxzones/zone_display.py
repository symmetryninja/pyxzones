import logging
import threading
from . import xq
from .zoning import ZoneProfile
from .settings import SETTINGS

import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class ZoneDisplayWindow(Gtk.Window):
    def __init__(self, screen_width, screen_height, zones):
        super(ZoneDisplayWindow, self).__init__()
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(30)
        self.screen = self.get_screen()
        self.visual = self.screen.get_rgba_visual()
        # todo: still renders on top but doesn't take keyboard input
        # would be nice for currently focused window to keep focus with
        # this rendering immediately underneath
        self.set_accept_focus(False)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        #self.set_keep_below(True)
        #self.set_keep_above(True)
        #self.maximize() # used if one window per monitor, but annoying to set up that way
        self.set_position(Gtk.WindowPosition.NONE)
        self.set_default_size(screen_width, screen_height)
        self.set_size_request(screen_width, screen_height) # only way to force the larger size, classic hack
        self.move(0, 0)
        self.resize(screen_width, screen_height)
        #self.fullscreen()
        if self.visual != None and self.screen.is_composited():
            self.set_visual(self.visual)

        self.zones = zones

        rw = self.get_parent_window()
        self.set_transient_for(rw)

        self.set_app_paintable(True)
        self.connect("draw", self.area_draw)
        #self.show_all()

        # need to set this after show_all
        region = cairo.Region(cairo.RectangleInt(0, 0, 1, 1))
        self.input_shape_combine_region(region)


    def area_draw(self, widget, cr):
        # TODO: Why these four lines are here again, remove?
        cr.set_source_rgba(.2, .2, .2, 0.2)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        for zone in self.zones:
            cr.set_source_rgba(*SETTINGS.zone_background_color)
            cr.rectangle(
                zone.x + SETTINGS.zone_background_inset,
                zone.y + SETTINGS.zone_background_inset,
                zone.width - SETTINGS.zone_background_inset * 2,
                zone.height - SETTINGS.zone_background_inset * 2
            )
            cr.fill()

            cr.set_source_rgba(*SETTINGS.zone_border_color)
            # todo?: avoid double thickness border between zones
            cr.set_line_width(SETTINGS.zone_border_thickness)
            cr.rectangle(
                zone.x + SETTINGS.zone_border_inset,
                zone.y + SETTINGS.zone_border_inset,
                zone.width - SETTINGS.zone_border_inset * 2,
                zone.height - SETTINGS.zone_border_inset * 2
            )
            cr.stroke()


def setup_zone_display(display, zone_profile: ZoneProfile):
    current_virtual_desktop = xq.get_current_virtual_desktop(display)

    logging.debug(f"  setup_zone_display():")
    logging.debug(f"\t{current_virtual_desktop=}")
    logging.debug(f"\t{zone_profile.zones[current_virtual_desktop]=}")

    geometry = display.screen().root.get_geometry()
    zone_window = ZoneDisplayWindow(
        geometry.width, geometry.height,
        zone_profile.zones[current_virtual_desktop]
    )

    thread = threading.Thread(target=Gtk.main)
    thread.daemon=True
    thread.start()

    return zone_window

