from Xlib import X, XK
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq

import logging

from .snap import snap_window
from .zoning import ZoneProfile
from .conf.settings import SETTINGS
from . import x


class Service:
    def __init__(self) -> None:
        self.active_keys = {
            XK.string_to_keysym(key): False for key in SETTINGS.keybindings
        }

#        self.zp = ZoneProfile.from_file()
        self.coordinates = Coordinates()

        self.display = Display()
        self.root = self.display.screen().root

        #　TODO: change for screen / resolution changes & recalculate zones
        #logging.debug(self.display.xinerama_query_screens())
        #self.zp = ZoneProfile.from_pct_mutliscreen(self.display.xinerama_query_screens())
        
        monitors = x.get_monitors(self.display, self.root)
        logging.debug(f"{monitors=}")

        number_of_virtual_desktops = x.get_number_of_virtual_desktops(self.display)
        work_areas = x.get_work_areas_for_all_desktops(self.display, number_of_virtual_desktops)
        logging.debug(f"for all desktops:\n{work_areas=}")

        if not work_areas:
            # todo: raise exception
            pass

        if len(monitors) != len(work_areas[0]):
            logging.info("Operating on single virtual display work area")


        self.zp = ZoneProfile.get_zones_per_virtual_desktop(monitors, work_areas)


        # todo: there should be some refresh point or cadence for monitor,
        # virtual desktops, scaling, and calculated zone information

        from .zone_display import setup
        setup(self.display, self.zp)


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

        self.display.record_enable_context(self.context, self.handler)
        self.display.record_free_context(self.context)

    def handler(self, reply):
        data = reply.data
        while len(data):

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
                self.coordinates.add(event.root_x, event.root_y)
                if (event.type, event.detail) == (X.ButtonRelease, X.Button1):
                    #logging.debug(f"snap_window(self, {event.root_x}, {event.root_y})")
                    snap_window(self, event.root_x, event.root_y)
            else:
                self.coordinates.clear()

    def listen(self):
        while True:
            self.root.display.next_event()


class Coordinates:
    def __init__(self) -> None:
        self.x = []
        self.y = []

    def __getitem__(self, item):
        """returns an (x,y) coordinate"""
        return self.x[item], self.y[item]

    def __iter__(self):
        """iterate over (x,y) coordinates"""
        return zip(self.x, self.y)

    def add(self, x, y):
        self.x.append(x)
        self.y.append(y)

    def clear(self):
        self.x = []
        self.y = []
