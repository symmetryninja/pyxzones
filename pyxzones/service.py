from Xlib import X, XK
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq

import logging

from .snap import snap_window
from .zoning import ZoneProfile
from .settings import SETTINGS
from . import xq

from .zone_display import setup_zone_display
from gi.repository import GLib

class Service:
    def __init__(self) -> None:
        self.active_keys = {
            XK.string_to_keysym(key): False for key in SETTINGS.keybindings
        }

        self.display = Display()
        self.root = self.display.screen().root

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

        self.active_keys_down = False
        self.mouse_button_down = False
        self.active_window = None
        self.last_active_window_position = None
        self.active_window_has_moved = False
        self.zones_shown = False

    def event_handler(self, reply):
        data = reply.data

        while len(data):
            # todo: if Escape is pressed, cancel snapping
            event, data = rq.EventField(None).parse_binary_value(
                data, self.display.display, None, None
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
                self.active_window, _ = xq.get_active_window()
                #window_coordinates = xq.get_window_coordinates(self.active_window)
                #self.last_active_window_position = window_coordinates
                #print(f"Picked up window at ({window_coordinates=})")
                self.last_active_window_position = (event.root_x, event.root_y)

            if event.type == X.MotionNotify and self.active_window != None:
                #window_coordinates = xq.get_window_coordinates(self.active_window)
                #print(f"Active window position is now ({window_coordinates=})")
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
                keysym = self.display.keycode_to_keysym(event.detail, 0)
                if keysym in self.active_keys:
                    self.active_keys[keysym] = (event.type == X.KeyPress)
                self.active_keys_down = all(self.active_keys.values())

            active_mode = self.mouse_button_down and self.active_keys_down
            if SETTINGS.wait_for_window_movement and not self.active_window_has_moved:
                active_mode = False


            if not self.zones_shown and active_mode:
                GLib.idle_add(self.zone_window.show)
                self.zones_shown = True

                # attempt to bring the active window above the zone window
                #
                # note: there are some edge cases where this timing may keep the
                # zone window on top
                #
                # haven't found a good way to get this to execute after displaying
                # the zone window as that occurs on the Gtk thread
                #
                # also this temporary display and remade window below seems required
                # to have this actually execute properly, unclear as to why at the
                # moment (threading?)
                temporary_display = Display()
                window = temporary_display.create_resource_object('window', self.active_window.id)
                window.configure(stack_mode=X.Above)
                window.set_input_focus(X.RevertToParent, X.CurrentTime)
                temporary_display.sync()

            elif self.zones_shown and not active_mode:
                GLib.idle_add(self.zone_window.hide)
                self.zones_shown = False


    def listen(self):
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
        self.display.record_enable_context(self.context, self.event_handler)
        self.display.record_free_context(self.context)

