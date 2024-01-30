from Xlib import X, XK
from Xlib.ext import record
from Xlib.error import BadDrawable
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
        self.active_window_id = None
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

            #if event.type == X.MotionNotify:
            #    print(f"{event.detail=}")  # 0 for movement, unsure when it wouldn't be 0
            #
            # consider only showing zones when active window has moved (inconsistent with FancyZones)
            #
            # can potentially enable highlighting of predicted landing zone(s)
            #
            # would also enable not showing zones when key(s)+click is active but no window is moving
            # (can currently snap to cursor area even if mouse has just moved somewhere without
            # dragging a window)
            #
            # but obviously a very spammy event so performing too much processing here may put
            # the cpu load higher than it should be for this type of tool
            #
            # secondary, partially unrelated note:
            # it can be nonobvious if the cursor is on the right side of a relative large window
            # that the snapping is based on the cursor position and not the window position
            #
            # it may be better to snap based on the middle of the window's "title bar"
            # even if we don't accurately have those coordianates (could use window.x+w/2, cursor y)
            # or (window.window.x+w/2, window.y+<small number>)
            if (event.type, event.detail) == (X.ButtonPress, X.Button1):
                self.mouse_button_down = True

            if (event.type, event.detail) == (X.ButtonRelease, X.Button1):
                self.mouse_button_down = False
                if self.active_keys_down:
                    # todo?: track mouse movement events to see if active window is moving?
                    active_window, active_window_id = xq.get_active_window()#self.display)
                    #print(f"{active_window=}, {active_window_id=}")
                    snap_window(self, active_window, event.root_x, event.root_y)

            if event.type in (X.KeyPress, X.KeyRelease):
                keysym = self.display.keycode_to_keysym(event.detail, 0)
                if keysym in self.active_keys:
                    self.active_keys[keysym] = (event.type == X.KeyPress)
                self.active_keys_down = all(self.active_keys.values())

            if not self.zones_shown and (self.mouse_button_down and self.active_keys_down):
                GLib.idle_add(self.zone_window.show)
                self.zones_shown = True
            elif self.zones_shown and (not self.mouse_button_down or not self.active_keys_down):
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

