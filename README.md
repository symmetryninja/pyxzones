# PyXZones

## A slice of [FancyZones](https://learn.microsoft.com/en-us/windows/powertoys/fancyzones) on Linux

This project is an attempt to emulate some of the functionality Windows users are able to leverage from FancyZones. Users can drag and drop windows into predefined zones, and have PyXZones fit the window to the zone space.


## How to use

Installed locally via `pip` (ie. `pip install pyxzones`) or executed as a python module from a clone of the git repository (`python -m pyxzones`) are effectively equivalent.

The default zone configuration and various other settings are provided the `settings.py` file and can be overwritten from a `pyxzones.json` configuration file located at the [XDG_CONFIG*](https://wiki.archlinux.org/title/XDG_Base_Directory) locations, or the user's home folder (a `.pyxzones.json` file is also suitable in the home folder).

Zones can be set as vertical or horizontal slices of a monitor. The existing example is hopefully suitable as guidance for general usage (please see `example_config/pyxzones.json`).

With zones configured, and pyxzones running, the activation key(s) also set in settings (efault `Alt_L`) can be held while moving a window with the cursor to activate snapping. Holding this keybinding, windows can be dragged to a zone, and upon releasing the mouse click, the window will snap to the dimensions of the predefined zone.


`Note:` This package requires access with the Xorg server bindings, so it should only be used on Xorg-based Unix Systems or systems with sufficient Xorg backwards compatibility. Please see more information in the below [System Requirements](#system-requirements) section.


## Seeing stubborn windows?

You may run across some windows that behave strangely. Specifically calling out here GTK3.0 windows, which have a default margin around them and will not cooperate with resizing to fill a zone completely.

To get around this GTK quirk, you may adjust your user CSS rules (located at `~/.config/gtk-3.0/gtk.css`) for GTK as follows:
```css
/* early GTK 3 rules */
.window-frame {
  margin: 0px;
  box-shadow: none;
}

/* newer GTK 3 rules */
window > decoration {
  margin: 0;
  box-shadow: none;
}
```
Note that you may need to create the file mentioned above and this will likely require an X server restart (not just log out/log in) to apply.

## System Requirements

#### Building

To build the app, a system must have the required GTK libraries used in the current zone display window. On the development system used, these included `libcairo2-dev libgirepository1.0-dev gir1.2-gtk-4.0`. A reference for multiple systems is located at the PyGObject documentation [located here](https://pygobject.readthedocs.io/en/latest/getting_started.html).

#### Window Manager

In addition, the X Window Manager being used must support the `Xrandr` and `Record` extentions and the following X features are _required_ for basic expected functionality:
* _NET_WORKAREA
* _NET_MOVERESIZE_WINDOW
* _NET_SHOWING_DESKTOP
* _NET_ACTIVE_WINDOW

The features below may not be strictly required, but will degrate the quality of the experience that can be expected:
* _NET_FRAME_EXTENTS
* _GTK_WORKAREAS
* _NET_WM_STATE
* _NET_CURRENT_DESKTOP
