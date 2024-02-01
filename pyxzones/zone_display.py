import threading
import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .settings import SETTINGS
from .types import MergeZone, Zone

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

        self.set_app_paintable(True)
        self.connect("draw", self.area_draw)

        self.zones = zones
        self.hover_zone: Zone | MergeZone = None

        # NOTE: Order matters here, expanded as function parameters below
        self.normal_zone_config = (
            SETTINGS.zone_background_color,
            SETTINGS.zone_background_inset,
            SETTINGS.zone_border_color,
            SETTINGS.zone_border_thickness,
            SETTINGS.zone_border_inset
        )
        self.hover_zone_config = (
            SETTINGS.hover_zone_background_color,
            SETTINGS.hover_zone_background_inset,
            SETTINGS.hover_zone_border_color,
            SETTINGS.hover_zone_border_thickness,
            SETTINGS.hover_zone_border_inset
        )


    def set_hover_zone(self, zone):
        self.hover_zone = zone


    def draw_zone(self, cr, zone: Zone, background_color, background_inset, border_color, border_thickness, border_inset):
        cr.set_source_rgba(*background_color)
        cr.rectangle(
            zone.x + background_inset,
            zone.y + background_inset,
            zone.width - background_inset * 2,
            zone.height - background_inset * 2
        )
        cr.fill()

        cr.set_source_rgba(*border_color)
        cr.set_line_width(border_thickness)
        cr.rectangle(
            zone.x + border_inset,
            zone.y + border_inset,
            zone.width - border_inset * 2,
            zone.height - border_inset * 2
        )
        cr.stroke()


    def area_draw(self, widget, cr):
        hover_zones = ()
        if self.hover_zone:
            hover_zones = self.hover_zone.zones if type(self.hover_zone) is MergeZone else (self.hover_zone,)

        for zone in self.zones:
            hover_zone = SETTINGS.highlight_hover_zone and zone in (hover_zones)
            self.draw_zone(cr, zone, *(self.normal_zone_config if not hover_zone else self.hover_zone_config))


def setup_zone_display(x_screen_width, x_screen_height, zones):
    zone_window = ZoneDisplayWindow(x_screen_width, x_screen_height, zones)

    thread = threading.Thread(target=Gtk.main)
    thread.daemon=True
    thread.start()

    return zone_window

