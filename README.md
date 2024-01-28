# PyXZones

## FancyZones for Linux

This project is an attempt to emulate the functionality Windows users get from FancyZones. Users can drag and drop windows into predefined zones, and have PyXZones fit the window to the zone specs.

## How to use

PyXZones is in development mode currently and can be started by calling the module `python -m pyxzones` from within the root folder of the project.

Zones are currently configured manually in the `settings.py` file. They can set as vertical or horizontal slices of a monitor. The existing example should be suitable as guidance for usage.

With zones configured, and pyxzones running, the activation key(s) also set in `settings.py` (default `Alt_L`) can be held while moving a window with the cursor to activate snapping. Holding this keybinding, windows can be dragged to a zone, and upon releasing the mouse click the window will snap to the dimensions of the predefined zone.


This project is currently under active development, please check back for more updates and features soon.

`Note:` This package requires access with the Xorg server bindings, so it should only be used on Xorg-based Unix Systems or systems with sufficient Xorg backwards compatibility.
