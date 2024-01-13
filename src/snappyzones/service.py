from Xlib import X, XK
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq

from Xlib.ext import randr
from Xlib.ext import xinerama

from .snap import snap_window, shift_window
from .zoning import ZoneProfile
from .conf.settings import SETTINGS


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
        #print(self.display.xinerama_query_screens())
        #self.zp = ZoneProfile.from_pct_mutliscreen(self.display.xinerama_query_screens())
        
        screen_resources = randr.get_screen_resources(self.root)

        monitors = []
        for output in screen_resources.outputs:
            output_info = randr.get_output_info(self.display, output, screen_resources.config_timestamp)
            if output_info.crtc == 0:
                continue

            crtc_info = randr.get_crtc_info(self.display, output_info.crtc, screen_resources.config_timestamp)
            monitors.append({
                "mode": crtc_info.mode,
                "rotation": crtc_info.rotation,
                "virtual_x": crtc_info.x,
                "virtual_y": crtc_info.y,
                "virtual_width": crtc_info.width,
                "virtual_height": crtc_info.height,
            })
       
        # sort monitors from left to right, top to bottom (as configuration is expected to be done)
        monitors = sorted(monitors, key = lambda m: (m['virtual_x'], m['virtual_y']))
  
        screen_mode_map = {}
        for mode in screen_resources.modes:
            screen_mode_map[mode.id] = (mode.width, mode.height)

        for monitor in monitors:
            monitor['width'] = screen_mode_map[monitor['mode']][0 if monitor['rotation'] in (1, 4) else 1]
            monitor['height'] = screen_mode_map[monitor['mode']][1 if monitor['rotation'] in (1, 4) else 0]

            if monitor['virtual_width'] / monitor['width'] != monitor['virtual_height'] / monitor['height']:
                print("UNEXPECTED UNEVEN SCALING!")
                print(f"{monitor['virtual_width'] / monitor['width']=}")
                print(f"{monitor['virtual_height'] / monitor['height']=}")
            monitor['scale'] = monitor['virtual_width'] / monitor['width']

        print(monitors)

        self.zp = ZoneProfile.from_pct_mutliscreen(monitors)
        
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
                    #print(f"snap_window(self, {event.root_x}, {event.root_y})")
                    snap_window(self, event.root_x, event.root_y)
                elif event.type == X.KeyPress:
                    keysym = self.display.keycode_to_keysym(event.detail, 0)
                    #print(f"{event.root_x}, {event.root_y}")
                    #print(f"shift_window(self, {keysym})")
                    shift_window(self, keysym)

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
