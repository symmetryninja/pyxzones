import logging
import threading
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


def get_zone_profile(ewmh):
    # In modern X11, a "monitor" (crtc) is not generally a separate unit in the
    # X11 Screen that is being used, so multiple monitors simply take up rectangular
    # spaces within the larger Screen canvas
    #
    # That said, while X11 doesn't care, the zoning of work areas does, so this
    # information will be passed along later to appropriately slice out zones of the
    # big Screen rectangle
    monitors = ewmh.getMonitors()
    logging.debug(f"{monitors=}")

    work_areas = ewmh.getWorkAreasForAllVirtualDesktops()
    logging.debug(f"for all desktops:\n{work_areas=}")

    if not work_areas:
        raise FatalXQueryFailure("Could not find work areas for rendering, potentially unsupported by window manager.")

    # TODO: Double check this logic and document the meaning, confused myself
    if len(monitors) != len(work_areas[0]):
        logging.info("Operating on single virtual display work area")

    return ZoneProfile.get_zones_per_virtual_desktop(monitors, work_areas)


class Service:
    def __init__(self) -> None:
        self.ewmh = XEWMH()

        if not self.ewmh.display.has_extension("RANDR"):
            raise FatalXQueryFailure("X server does not have the required RANDR extension")

        if not self.ewmh.display.has_extension("RECORD"):
            raise FatalXQueryFailure("X server does not have the required RECORD extension")

        self.zone_profile = get_zone_profile(self.ewmh)
        self.current_virtual_desktop = self.ewmh.getShowingDesktop()

        logging.debug(f"  setup_zone_display():")
        logging.debug(f"\t{self.current_virtual_desktop=}")
        logging.debug(f"\t{self.zone_profile.zones[self.current_virtual_desktop]=}")

        geometry = self.ewmh.root.get_geometry()
        self.zone_window = setup_zone_display(
            geometry.width, geometry.height,
            self.zone_profile.zones[self.current_virtual_desktop]
        )

        self.active_window = None
        self.mouse_button_down = False
        self.last_active_window_position = None
        self.active_window_has_moved = False
        self.zones_shown = False
        self.active_keys = { XK.string_to_keysym(key): False for key in SETTINGS.keybindings }
        self.active_keys_down = False # effectively a cache of all(self.active_keys.values())

        self.setup_property_change_monitor()


    def setup_property_change_monitor(self):
        thread = threading.Thread(target=self.property_change_event_handler)
        thread.daemon=True
        thread.start()

    def property_change_event_handler(self):
        local = threading.local()
        local.ewmh = XEWMH()

        """
        This below enables monitoring of xrandr events around display status
        (added, disconnected, on/off, etc.). It's quite useful, but the updates
        provided by X.PropertyNotify seem sufficient for now.

        Leaving in as a reference.

        from Xlib.ext import randr
        randr.select_input(local.ewmh.root,
            randr.RRScreenChangeNotifyMask | randr.RRCrtcChangeNotifyMask |
            randr.RROutputChangeNotifyMask | randr.RROutputPropertyNotifyMask
        )
        """
        local.ewmh.root.change_attributes(event_mask=X.PropertyChangeMask)

        update_desktop_timer = None
        zone_refresh_timer = None

        logging.debug("Beginning X.PropertyChanged event monitor")

        # These operations should be thread-safe atomic assigments, and no other
        # threads will likely be writing at this same moment
        #
        # Given that, hopefully it's unlikely there will be any race conditions
        # arising from this that will require the addition of locking
        def virtual_desktop_updater_task():
            self.current_virtual_desktop = XEWMH().getShowingDesktop()
            self.zone_window.set_zones(self.zone_profile.zones[self.current_virtual_desktop])
            GLib.idle_add(self.zone_window.reset_position)

        def zone_refresh_task():
            self.zone_profile = get_zone_profile(XEWMH())
            self.zone_window.set_zones(self.zone_profile.zones[self.current_virtual_desktop])
            GLib.idle_add(self.zone_window.reset_position)


        while True:
            event = local.ewmh.display.next_event()

            if event.type != X.PropertyNotify:
                continue

            """
            Events of interest:

                _NET_CURRENT_DESKTOP triggered for virtual desktop change

                _GTK_WORKAREAS_D# for each virtual desktop are all triggered when changed
                    this includes adding/removing panels, adding or removing displays
                
                _NET_WORKAREA triggered after _GTK_WORKAREAS_D#

            """
            event_name = local.ewmh.display.get_atom_name(event.atom)

            if event_name == '_NET_CURRENT_DESKTOP':
                if update_desktop_timer and update_desktop_timer.is_alive():
                    update_desktop_timer.cancel()
                logging.debug(f"Virtual desktop changed, scheduling task to update state")
                update_desktop_timer = threading.Timer(0.2, virtual_desktop_updater_task)
                update_desktop_timer.start()

            if event_name.startswith('_GTK_WORKAREAS_D') or event_name.startswith('_NET_WORKAREAS_D') or event_name == '_NET_WORKAREA':
                if zone_refresh_timer and zone_refresh_timer.is_alive():
                    zone_refresh_timer.cancel()
                logging.debug(f"Work areas changed, scheduling task to update known work areas and zones")
                zone_refresh_timer = threading.Timer(0.2, zone_refresh_task)
                zone_refresh_timer.start()


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
                hover_zone = self.zone_profile.find_zone(self.current_virtual_desktop, *basis_point)
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
