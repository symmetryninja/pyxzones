
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

        #return json.loads(
            """
            [
                {
                    "height": 1024,
                    "width": 640,
                    "x": 0,
                    "y": 0
                },
                {
                    "height": 1024,
                    "width": 640,
                    "x": 640,
                    "y": 0
                },
                {
                    "height": 1024,
                    "width": 640,
                    "x": 1280,
                    "y": 0
                }
            ]
            """
        #)

    @zones.setter
    def zones(self, _zones):
        pass

    @property
    def keybindings(self):
        return ['Alt_L'] #["Shift_L"]


SETTINGS = Settings()
