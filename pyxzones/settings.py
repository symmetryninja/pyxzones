import json
from pathlib import Path

class Settings:

    def __init__(self):
        self.user_configuration = None

    # This lookup mechanism is not particularly slow, but frequently accessed
    # fields could be cached by the accessor if concerned
    def __getattribute__(self, name):
        if name != 'user_configuration' and self.user_configuration and name in self.user_configuration:
            return self.user_configuration[name]
        return super().__getattribute__(name)

    def load_from_file(self, file: Path):
        self.user_configuration = json.load(file)

    @property
    def zones(self):
        return {
            "displays": [  # list of displays
                {  # display 1, horizontal (from left to right in virtual display)
                    "orientation": "landscape",
                    "columns": [ 10, 80, 10 ]
                },
                {  # display 2, vertical
                    "orientation": "portrait",
                    "rows": [ 35, 40, 25 ]
                },
            ]
        }

    @property
    def keybindings(self):
        # Shift_L has some annoying window grid snapping functionality in Mutter/Cinnamon
        # (so does Alt for window moving, but that can be disabled if desired)
        return ['Alt_L'] #["Shift_L"]
    
    @property
    def keybinding_quick_shift(self):
        # Shift_L has some annoying window grid snapping functionality in Mutter/Cinnamon
        # (so does Alt for window moving, but that can be disabled if desired)
        return ['Alt_L', 'Shift_L']

    @property
    def maximize_perpendicular_axis_on_snap(self):
        # This is most useful for GTK3.0 windows with their self-determined window margins,
        # but does not correct snapping to full zone on the display axis
        #
        # This can also be useful for stubborn windows, like terminals, which may round down
        # a given window size to align with the closest column/row, yet won't struggle with
        # being maximized
        return False

    @property
    def wait_for_window_movement(self):
        return True

    @property
    def snap_basis_point(self):
        # Valid values: 'cursor' or 'window'
        #
        # 'cursor': will use the mouse cursor as the determining point for zone selection
        # 'window': will use the center of the top of the window as the determining point
        return 'cursor'

    # Inset (margin) in pixels
    @property
    def zone_border_inset(self) -> int:
        return 5

    # float (r, g, b, a)
    @property
    def zone_border_color(self) -> tuple[float, float, float, float]:
        return (0.4, 0.4, 0.8, 0.8)

    # Border thickness in pixels
    @property
    def zone_border_thickness(self) -> int:
        return 5

    # float (r, g, b, a)
    @property
    def zone_background_color(self) -> tuple[float, float, float, float]:
        return (0.6, 0.6, 1.0, 0.2)

    # Inset (margin) in pixels
    @property
    def zone_background_inset(self) -> int:
        return 0

    @property
    def highlight_hover_zone(self) -> bool:
        return True

    # Inset (margin) in pixels
    @property
    def hover_zone_border_inset(self) -> int:
        return 5

    # float (r, g, b, a)
    @property
    def hover_zone_border_color(self) -> tuple[float, float, float, float]:
        return (0.8, 0.0, 0.6, 0.9)

    # Border thickness in pixels
    @property
    def hover_zone_border_thickness(self) -> int:
        return 5

    # float (r, g, b, a)
    @property
    def hover_zone_background_color(self) -> tuple[float, float, float, float]:
        return (0.8, 0.0, 0.6, 0.6)

    # Inset (margin) in pixels
    @property
    def hover_zone_background_inset(self) -> int:
        return 0

    # Percentage of usable work area (generally, screen) to use for identifying
    # merge boundaries across zone borders (for example, 7% is 3.5% on each side
    # of a zone border)
    @property
    def merge_zone_size_preference(self) -> float:
        return 7


"""

From a quick glance, the default FanzyZones colors seem to be something along the lines of:

zone_border_inset: 0
zone_border_color: (0.0, 0.47, 0.84, 1.0)
zone_border_thickness: 4
zone_background_color: (0.96, 0.96, 1.0, 0.5)
zone_background_inset: {zone_border_thickness / 2}
highlight_hover_zone: True
hover_zone_border_inset: {zone_border_inset}
hover_zone_border_color: {zone_border_color}
hover_zone_border_thickness: {zone_border_thickness}
hover_zone_background_color: (0.0, 0.47, 0.84, 0.5)
hover_zone_background_inset: {zone_border_thickness / 2}

"""


SETTINGS = Settings()
