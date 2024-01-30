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
        # For now, default to True, move to settings file when re-added
        #
        # This is most useful for GTK3.0 windows with their self-determined window margin,
        # but does not correct snapping to full zone on the display axis
        return True

    @property
    def wait_for_window_movement(self):
        return True


SETTINGS = Settings()

