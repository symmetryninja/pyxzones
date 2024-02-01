from ewmh import EWMH
from . import xq

"""

eXtended, Extended Window Manager Hints

These functions are not written in the same style or using
internal methods from EWMH.

This extension is just for fun, for now.

"""

class XEWMH(EWMH):

    def getMonitors(self):
        return xq.get_monitors(self.display, self.root)

    def getWorkAreasForVirtualDesktop(self, desktop_index: int):
        return xq.get_work_areas(self.display, desktop_index)

    def getWorkAreasForAllVirtualDesktops(self):
        return xq.get_work_areas_for_all_desktops(self.display, self.getNumberOfDesktops())

    def getWindowFrameExtents(self, window):
        return xq.get_window_frame_extents(self.display, window)

    def getWindowCoordinates(self, window):
        return xq.get_window_coordinates(window)
