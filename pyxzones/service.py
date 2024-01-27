from Xlib import X, XK
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq

import logging

from .snap import snap_window
from .zoning import ZoneProfile
from .settings import SETTINGS
from . import xq
from .types import Coordinates

from .zone_display import setup_zone_display
from gi.repository import GLib

class Service:
    def __init__(self) -> None:
        self.active_keys = {
            XK.string_to_keysym(key): False for key in SETTINGS.keybindings
        }

        self.display = Display()
        self.root = self.display.screen().root
        self.coordinates = Coordinates()

        monitors = xq.get_monitors(self.display, self.root)
        logging.debug(f"{monitors=}")

        number_of_virtual_desktops = xq.get_number_of_virtual_desktops(self.display)
        work_areas = xq.get_work_areas_for_all_desktops(self.display, number_of_virtual_desktops)
        logging.debug(f"for all desktops:\n{work_areas=}")

        if not work_areas:
            # todo: raise exception
            pass

        if len(monitors) != len(work_areas[0]):
            logging.info("Operating on single virtual display work area")


        self.zp = ZoneProfile.get_zones_per_virtual_desktop(monitors, work_areas)


        #　TODO: change for screen / resolution changes & recalculate zones
        # todo: there should be some refresh point or cadence for monitor,
        # virtual desktops, scaling, and calculated zone information

        # todo: not sure what to do yet for desktop switching etc, kill and remake?
        self.zone_window = setup_zone_display(self.display, self.zp)


        self.context = self.display.record_create_context(
            0,
            [record.AllClients],
            [
                {
                    "core_requests": (0, 0),
                    "core_replies": (0, 0),
                    "ext_requests": (0, 0, 0, 0),
                    "ext_replies": (0, 0, 0, 0),
                    "delivered_events": (0, 0),
                    "device_events": (X.KeyReleaseMask, X.ButtonReleaseMask),
                    "errors": (0, 0),
                    "client_started": False,
                    "client_died": False,
                }
            ],
        )

        self.active_keys_down = False
        self.mouse_button_down = False
        self.active_window = None
        self.active_window_id = None
        self.last_active_window_position = None

        self.display.record_enable_context(self.context, self.handler)
        self.display.record_free_context(self.context)

    def handler(self, reply):
        data = reply.data

        while len(data):
            # todo: if Escape is pressed, cancel snapping

            active_window, active_window_id = xq.get_active_window(self.display)
            print(active_window)

            event, data = rq.EventField(None).parse_binary_value(
                data, self.display.display, None, None
            )

            if event.type in (X.KeyPress, X.KeyRelease):
                keysym = self.display.keycode_to_keysym(event.detail, 0)
                if keysym in self.active_keys:
                    self.active_keys[keysym] = (
                        True if event.type == X.KeyPress else False
                    )

            if all(self.active_keys.values()):
                self.active_keys_down = True

                if (event.type, event.detail) == (X.ButtonPress, X.Button1):
                    self.mouse_button_down = True
                    # Show zones when the condition of keys+mouse are active together
                    GLib.idle_add(self.zone_window.show)

                # todo: as mouse moves around, highlight snap zone in window
                self.coordinates.add(event.root_x, event.root_y)

                if (event.type, event.detail) == (X.ButtonRelease, X.Button1):
                    self.mouse_button_down = False
                    #logging.debug(f"snap_window(self, {event.root_x}, {event.root_y})")
                    #GLib.idle_add(self.zone_window.hide)
                    snap_window(self, event.root_x, event.root_y)
            else:
                # Hide zones when mouse button is let off
                if self.mouse_button_down == False:
                    GLib.idle_add(self.zone_window.hide)
                self.coordinates.clear()

    def listen(self):
        while True:
            self.root.display.next_event()

