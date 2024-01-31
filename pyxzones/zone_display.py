import threading
from .settings import SETTINGS

import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class ZoneDisplayWindow(Gtk.Window):
    def __init__(self, screen_width, screen_height, zones):
        super(ZoneDisplayWindow, self).__init__()
        self.screen = self.get_screen()
        self.visual = self.screen.get_rgba_visual()
        self.set_accept_focus(False)
        self.set_focus_on_map(False) # Found the magic setting to prevent foreground stealing
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_position(Gtk.WindowPosition.NONE)
        self.set_default_size(screen_width, screen_height)
        self.set_size_request(screen_width, screen_height) # only way to force the larger size, classic hack
        self.move(0, 0)
        self.resize(screen_width, screen_height)

        if self.visual != None and self.screen.is_composited():
            self.set_visual(self.visual)

        self.zones = zones

        self.set_app_paintable(True)
        self.connect("draw", self.area_draw)


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


def setup_zone_display(x_screen_width, x_screen_height, zones):
    zone_window = ZoneDisplayWindow(x_screen_width, x_screen_height, zones)

    thread = threading.Thread(target=Gtk.main)
    thread.daemon=True
    thread.start()

    return zone_window

