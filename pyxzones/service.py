from Xlib import X, XK
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq

import logging

from ewmh import EWMH

from .snap import snap_window
from .zoning import ZoneProfile
from .settings import SETTINGS
from . import xq

import sys
from .zone_display import setup_zone_display
from gi.repository import GLib

class Service:
    def __init__(self) -> None:
        self.active_keys = {
            XK.string_to_keysym(key): False for key in SETTINGS.keybindings
        }

        self.ewmh = EWMH()

        monitors = xq.get_monitors(self.ewmh.display, self.ewmh.root)
        logging.debug(f"{monitors=}")

        number_of_virtual_desktops = self.ewmh.getNumberOfDesktops()
        work_areas = xq.get_work_areas_for_all_desktops(self.ewmh.display, number_of_virtual_desktops)
        logging.debug(f"for all desktops:\n{work_areas=}")

        if not work_areas:
            # TODO: Don't fail out here, raise exception for main() to handle
            logging.critical("Could not find work areas for rendering, potentially unsupported by window manager.")
            sys.exit(1)

        if len(monitors) != len(work_areas[0]):
            logging.info("Operating on single virtual display work area")


        self.zp = ZoneProfile.get_zones_per_virtual_desktop(monitors, work_areas)


        # TODO: change for screen / resolution changes & recalculate zones
        # todo: there should be some refresh point or cadence for monitor,
        # virtual desktops, scaling, and calculated zone information

        # TODO: not sure what to do yet for desktop switching etc, kill and remake?
        current_virtual_desktop = self.ewmh.getShowingDesktop()#self.ewmh.getShowingDesktop()

        logging.debug(f"  setup_zone_display():")
        logging.debug(f"\t{current_virtual_desktop=}")
        logging.debug(f"\t{self.zp.zones[current_virtual_desktop]=}")

        geometry = self.ewmh.root.get_geometry()
        self.zone_window = setup_zone_display(
            geometry.width, geometry.height,
            self.zp.zones[current_virtual_desktop]
        )

        self.active_keys_down = False
        self.mouse_button_down = False
        self.active_window = None
        self.last_active_window_position = None
        self.active_window_has_moved = False
        self.zones_shown = False

    def event_handler(self, reply):
        data = reply.data

        while len(data):
            # TODO: if Escape is pressed, cancel snapping
            event, data = rq.EventField(None).parse_binary_value(
                data, self.ewmh.display.display, None, None
            )

            # Commented out logic below works for tracking window movement,
            # but is much more expensive than tracking cursor movement (X.MotionNotify
            # already includes the event position) as identifying window coordinates
            # is nontrivial.
            #
            # For the time being, the two seem functionally equivalent, so leaving in
            # event based coordinates rather than window, but there may come a time when
            # the latter is required
            if (event.type, event.detail) == (X.ButtonPress, X.Button1):
                self.mouse_button_down = True
                self.active_window = self.ewmh.getActiveWindow()
                #window_coordinates = xq.get_window_coordinates(self.active_window)
                #self.last_active_window_position = window_coordinates
                self.last_active_window_position = (event.root_x, event.root_y)

            if event.type == X.MotionNotify and self.active_window != None:
                #window_coordinates = xq.get_window_coordinates(self.active_window)
                #if self.last_active_window_position != window_coordinates:
                #    self.last_active_window_position = window_coordinates
                #    self.active_window_has_moved = True
                if self.last_active_window_position != (event.root_x, event.root_y):
                    self.last_active_window_position = (event.root_x, event.root_y)
                    self.active_window_has_moved = True
                # todo: may want to highlight a would-be landing zone here given new (x, y)

            if (event.type, event.detail) == (X.ButtonRelease, X.Button1):
                self.mouse_button_down = False
                if self.active_keys_down and not (SETTINGS.wait_for_window_movement and not self.active_window_has_moved):
                    if SETTINGS.snap_basis_point.lower() == 'window':
                        window_coordinates = xq.get_window_coordinates(self.active_window)
                        window_geometry = self.active_window.get_geometry()
                        # NOTE: There's likely an edge case here since geomotry doesn't include extents (and even though most extents don't
                        # seem to touch width) so the width may be more than what is referred to here, likely not by much though
                        snap_window(self, self.active_window, window_coordinates[0] + window_geometry.width / 2, window_coordinates[1])
                    else: # default to cursor
                        snap_window(self, self.active_window, event.root_x, event.root_y)
                self.active_window = None
                self.active_window_has_moved = False
                self.last_active_window_position = None

            if event.type in (X.KeyPress, X.KeyRelease):
                keysym = self.ewmh.display.keycode_to_keysym(event.detail, 0)
                if keysym in self.active_keys:
                    self.active_keys[keysym] = (event.type == X.KeyPress)
                self.active_keys_down = all(self.active_keys.values())

            active_mode = self.mouse_button_down and self.active_keys_down
            if SETTINGS.wait_for_window_movement and not self.active_window_has_moved:
                active_mode = False

            if not self.zones_shown and active_mode:
                GLib.idle_add(self.zone_window.show)
                self.zones_shown = True
            elif self.zones_shown and not active_mode:
                GLib.idle_add(self.zone_window.hide)
                self.zones_shown = False


    def listen(self):
        # Not sure why this needs its own Display but display-referencing behavior
        # becomes somewhat unpredictable without it
        self.record_display = Display()
        self.context = self.record_display.record_create_context(
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
        self.record_display.record_enable_context(self.context, self.event_handler)
        self.record_display.record_free_context(self.context)

