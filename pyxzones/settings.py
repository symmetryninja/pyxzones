import os

HERE = os.path.abspath(os.path.dirname(__file__))

class Settings:

    @property
    def zones(self):
            return {
                "displays": [ # list of displays
                    { # display 1, horizontal (from left to right in virtual display)
                        "orientation": "landscape",
                        "columns": [ 10, 80, 10 ]
                    },
                    { # display 2, vertical
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
    def _pid_file(self):
        return os.path.join(HERE, '.pid')

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
        # 'window': will use the middle of the top of the window as the determining point
        return 'window'

    # Inset in pixels
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

    # Inset in pixels (x, y)
    @property
    def zone_background_inset(self) -> int:
        return 0


SETTINGS = Settings()

