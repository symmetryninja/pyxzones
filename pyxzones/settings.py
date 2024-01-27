
class Settings:

    # TODO:　This lets columns exist in rows but that's all the flexibility
    # Need to rethink this, pixels are fine now that scaling is known but not very practical
    @property
    def zones(self):
            return {
                "displays": [ # list of displays
                    { # display 1, horizontal (from left to right in virtual display)
                        "protected_area": { "left": 0, "right": 0, "top": 0, "bottom": 32, },
                        "rows": [ # list of rows on display
                            {
                                "height_pct": 100,
                                "columns": [ # list of columns in each row
                                    {
                                        "width_pct": 10,
                                    },
                                    {
                                        "width_pct": 80,
                                    },
                                    {
                                        "width_pct": 10,
                                    }
                                ],
                            },
                        ],
                    },
                    { # display 2, vertical
                        "protected_area": { "left": 0, "right": 0, "top": 0, "bottom": 32, },
                        "rows": [ # list of rows on display
                            {
                                "height_pct": 35,
                                "columns": [
                                    {
                                        "width_pct": 100,
                                    },
                                ],
                            },
                            {
                                "height_pct": 40,
                                "columns": [
                                    {
                                        "width_pct": 100,
                                    },
                                ],
                            },
                            {
                                "height_pct": 25,
                                "columns": [
                                    {
                                        "width_pct": 100,
                                    },
                                ],
                            },
                        ],
                    },
                ]
            }
            """
            y_offset = 1156
            x_offset = 0
            return [
                {
                    "height": 1024,
                    "width": 640,
                    "x": 0,
                    "y": y_offset
                },
                {
                    "height": 1024,
                    "width": 640,
                    "x": 640,
                    "y": y_offset
                },
                {
                    "height": 1024,
                    "width": 640,
                    "x": 1280,
                    "y": y_offset
                }
            ]
            """


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
