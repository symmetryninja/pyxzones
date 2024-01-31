from Xlib import X, XK
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq
from Xlib.xobject.drawable import Window
from dataclasses import dataclass

import logging

from ewmh import EWMH

from .snap import snap_window
from .zone_profile import ZoneProfile
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


        self.zone_profile = ZoneProfile.get_zones_per_virtual_desktop(monitors, work_areas)


        # TODO: change for screen / resolution changes & recalculate zones
        # todo: there should be some refresh point or cadence for monitor,
        # virtual desktops, scaling, and calculated zone information

        # TODO: not sure what to do yet for desktop switching etc, kill and remake?
        current_virtual_desktop = self.ewmh.getShowingDesktop()

        logging.debug(f"  setup_zone_display():")
        logging.debug(f"\t{current_virtual_desktop=}")
        logging.debug(f"\t{self.zone_profile.zones[current_virtual_desktop]=}")

        geometry = self.ewmh.root.get_geometry()
        self.zone_window = setup_zone_display(
            geometry.width, geometry.height,
            self.zone_profile.zones[current_virtual_desktop]
        )

        self.active_keys_down = False
        self.mouse_button_down = False
        self.active_window = None
        self.last_active_window_position = None
        self.active_window_has_moved = False
        self.zones_shown = False


    @dataclass
    class WindowState:
        window:      Window | None          = None
        coordinates: tuple[int, int] | None = None
        geometry:    object | None          = None
        extents:     list[int] | None       = None


    def get_window_state(self, window: Window) -> WindowState:
        state = Service.WindowState()
        state.window = window
        if state.window:
            state.coordinates = xq.get_window_coordinates(state.window)
            state.geometry = state.window.get_geometry()
            state.extents = xq.get_window_frame_extents(self.ewmh.display, state.window)
        return state


    def get_window_basis_point(self, window_geometry, window_coordinates: tuple[int, int]):
        # NOTE: There's likely an edge case here since geomotry doesn't include extents (and even though most extents don't
        # seem to touch width) so the width may be more than what is referred to here, likely not by much though
        return (window_coordinates[0] + window_geometry.width / 2, window_coordinates[1])


    def on_mousebutton_down(self, event_window: Window, basis_point: tuple[int, int]):
        self.mouse_button_down = True
        self.active_window = event_window.window
        self.last_active_window_position = basis_point


    def on_mouse_move(self, event_window: Window, basis_point: tuple[int, int]):
        if self.last_active_window_position != basis_point:
            self.last_active_window_position = basis_point
            self.active_window_has_moved = True

            if SETTINGS.highlight_hover_zone:
                hover_zone = self.zone_profile.find_zone(self.ewmh.getShowingDesktop(), *basis_point)
                self.zone_window.set_hover_zone(hover_zone)
                GLib.idle_add(self.zone_window.queue_draw)


    def on_mousebutton_up(self, event_window: Window, basis_point: tuple[int, int]):
        self.mouse_button_down = False
        if self.active_keys_down and not (SETTINGS.wait_for_window_movement and not self.active_window_has_moved):
            snap_window(self, self.active_window, *basis_point)
        self.active_window = None
        self.active_window_has_moved = False
        self.last_active_window_position = None

        if SETTINGS.highlight_hover_zone:
            self.zone_window.set_hover_zone(None)


    def on_key_updown(self, event):
        keysym = self.ewmh.display.keycode_to_keysym(event.detail, 0)
        if keysym in self.active_keys:
            self.active_keys[keysym] = (event.type == X.KeyPress)
        self.active_keys_down = all(self.active_keys.values())


    def process_event(self, event):
        # TODO: if Escape is pressed, cancel snapping

        event_window = self.get_window_state(
            self.active_window if self.active_window else self.ewmh.getActiveWindow()
        )
        if SETTINGS.snap_basis_point == 'window' and self.active_window:
            basis_point = self.get_window_basis_point(event_window.geometry, event_window.coordinates)
        else:
            basis_point = (event.root_x, event.root_y)


        if (event.type, event.detail) == (X.ButtonPress, X.Button1):
            self.on_mousebutton_down(event_window, basis_point)

        if event.type == X.MotionNotify and self.active_window != None:
            self.on_mouse_move(event_window, basis_point)

        if (event.type, event.detail) == (X.ButtonRelease, X.Button1):
            self.on_mousebutton_up(event_window, basis_point)

        if event.type in (X.KeyPress, X.KeyRelease):
            self.on_key_updown(event)


        active_mode = self.mouse_button_down and self.active_keys_down
        if SETTINGS.wait_for_window_movement and not self.active_window_has_moved:
            active_mode = False

        if not self.zones_shown and active_mode:
            GLib.idle_add(self.zone_window.show)
            self.zones_shown = True
        elif self.zones_shown and not active_mode:
            GLib.idle_add(self.zone_window.hide)
            self.zones_shown = False


    def event_handler(self, reply):
        data = reply.data

        while len(data):
            event, data = rq.EventField(None).parse_binary_value(
                data, self.ewmh.display.display, None, None
            )
            self.process_event(event)


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

