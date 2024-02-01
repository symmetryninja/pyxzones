import logging
from dataclasses import dataclass
from gi.repository import GLib
from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import record
from Xlib.protocol import rq
from Xlib.xobject.drawable import Window

from .settings import SETTINGS
from .snap import snap_window
from .xewmh import XEWMH
from .zone_display import setup_zone_display
from .zone_profile import ZoneProfile


class FatalXQueryFailure(Exception):
    pass


class Service:
    def __init__(self) -> None:
        self.ewmh = XEWMH()

        # In modern X11, a "monitor" (crtc) is not generally a separate unit in the
        # X11 Screen that is being used, so multiple monitors simply take up rectangular
        # spaces within the larger Screen canvas
        #
        # That said, while X11 doesn't care, the zoning of work areas does, so this
        # information will be passed along later to appropriately slice out zones of the
        # big Screen rectangle
        monitors = self.ewmh.getMonitors()
        logging.debug(f"{monitors=}")

        work_areas = self.ewmh.getWorkAreasForAllVirtualDesktops()
        logging.debug(f"for all desktops:\n{work_areas=}")

        if not work_areas:
            raise FatalXQueryFailure("Could not find work areas for rendering, potentially unsupported by window manager.")

        # TODO: Double check this logic and document the meaning, confused myself
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

        self.active_window = None
        self.mouse_button_down = False
        self.last_active_window_position = None
        self.active_window_has_moved = False
        self.zones_shown = False
        self.active_keys = { XK.string_to_keysym(key): False for key in SETTINGS.keybindings }
        self.active_keys_down = False # effectively a cache of all(self.active_keys.values())


    @dataclass(frozen=True)
    class WindowState:
        window:      Window | None          = None
        coordinates: tuple[int, int] | None = None
        geometry:    object | None          = None
        extents:     list[int] | None       = None


    def get_window_state(self, window: Window) -> WindowState:
        if not window:
            return Service.WindowState()

        return Service.WindowState(
            window=window,
            coordinates=self.ewmh.getWindowCoordinates(window),
            geometry=window.get_geometry(),
            extents=self.ewmh.getWindowFrameExtents(window)
        )


    def get_window_basis_point(self, geometry, coordinates: tuple[int, int], extents: list[int]):
        el, er, _, _ = extents
        return (coordinates[0] + int((el + er + geometry.width) / 2), coordinates[1])


    def on_mousebutton_down(self, event_window: Window, basis_point: tuple[int, int]):
        # TODO: Don't need mouse_button_down since active_window acts as such a signal (and more)?
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

        # Getting the window state is not particularly expensive, but is also
        # not an insigificant operation. A later optimization, if necessary,
        # may be to change properties to be lazily instantiated and cached
        # as this state is meant to only last for this single process_event()
        # and not all fields may be needed
        event_window = self.get_window_state(
            self.active_window if self.active_window else self.ewmh.getActiveWindow()
        )

        if SETTINGS.snap_basis_point == 'window' and self.active_window:
            basis_point = self.get_window_basis_point(event_window.geometry, event_window.coordinates, event_window.extents)
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
