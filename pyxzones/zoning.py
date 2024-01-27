from Xlib import XK
import logging

from .types import Zone
from .settings import SETTINGS

MEAN_PIXEL_TOLERANCE = 10


def mean(lst):
    return sum(lst) / len(lst)





class ZoneProfile:
    def __init__(self, zones) -> None:
        self.zones = zones

    def find_zones(self, virtual_desktop, service, x, y):
        _zones = []
        for coordinate in service.coordinates:
            for item in self.zones[virtual_desktop]:
                if item.check(*coordinate) and item not in _zones:
                    _zones.append(item)
                    break

        if not _zones:
            return None

        if len(_zones) == 1:
            return _zones.pop()

        x_min_zone = min((i for i in _zones), key=lambda i: i.x)
        y_min_zone = min((i for i in _zones), key=lambda i: i.y)

        # if all zones are in the same row
        if abs(mean(set(i.x for i in _zones)) - x_min_zone.x) < MEAN_PIXEL_TOLERANCE:
            width = x_min_zone.width
            height = sum(i.height for i in _zones)

        # if all zones are in the same column
        elif abs(mean(set(i.y for i in _zones)) - y_min_zone.y) < MEAN_PIXEL_TOLERANCE:
            width = sum(i.width for i in _zones)
            height = y_min_zone.height

        # stretch first zone into last zone
        elif len(_zones) == 2:
            initial_zone = self.find_zone(virtual_desktop, *service.coordinates[0])
            final_zone = self.find_zone(virtual_desktop, *service.coordinates[-1])
            slope = abs(
                (initial_zone.y - final_zone.y) / (initial_zone.x - final_zone.x)
            )
            if slope > 1:  # means we're stretching the height
                x = x_min_zone.x
                y = y_min_zone.y
                width = initial_zone.width
                height = initial_zone.height + final_zone.height
            else:  # means we're stretching the width
                x = x_min_zone.x
                y = initial_zone.y
                width = initial_zone.width + final_zone.width
                height = initial_zone.height
            return Zone(x, y, width, height)

        # return a zone which covers all zones
        else:
            width, height = 0, 0
            for z in _zones:
                if z.corners[1][0] - x_min_zone.x > width:
                    width = z.corners[1][0] - x_min_zone.x
                if z.corners[3][1] - y_min_zone.y > height:
                    height = z.corners[3][1] - y_min_zone.y
            return Zone(x_min_zone.x, y_min_zone.y, width, height)
        return Zone(x_min_zone.x, y_min_zone.y, width, height)


    def find_zone(self, virtual_desktop, x, y):
        #for index, item in enumerate(self.zones[virtual_desktop]):
        print(self.zones)
        print(virtual_desktop)
        print(x, y)
        for zone in self.zones[virtual_desktop]:
            if zone.check(x, y):
                return zone#self.zones[virtual_desktop][index]
        return None


    @staticmethod
    def get_zones_for_monitor_work_area(monitor, work_area, zone_spec):
        zones = []

        # todo: consider splitting out offsets from zones calculation
        # gtk windows don't need offset to position within, but do need them to position windows
        x_offset = work_area.x
        y_offset = work_area.y
        y_consumed = 0

        for row in zone_spec['rows']:
            height = row['height_pct'] / 100 * work_area.height

            x_consumed = 0
            for column in row['columns']:
                width = column['width_pct'] / 100 * work_area.width

                zones.append({
                                "x": int(x_offset + x_consumed),
                                "y": int(y_offset + y_consumed),
                                "width": int(width),
                                "height": int(height),
                            })

                x_consumed += width

            y_consumed += height

        return zones


    @staticmethod
    def get_zones_per_virtual_desktop(monitors, work_areas):
        zones = []
        zone_spec = SETTINGS.zones

        for desktop in range(len(work_areas)):
            desktop_zones = []
            single_workarea = len(work_areas[desktop]) == 1
            for monitor in range(len(monitors)):
                desktop_zones += ZoneProfile.get_zones_for_monitor_work_area(
                    monitors[monitor],
                    work_areas[desktop][0] if single_workarea else work_areas[desktop][monitor],
                    zone_spec['displays'][monitor]
                )
            zones.append(desktop_zones)


        print("************************************************************")
        logging.info("  zones:")
        for desktop in range(0, len(zones)):
            logging.info(f"  desktop {desktop}:")
            for zone in zones[desktop]:
                logging.info(f"\t{zone=}")
        print("************************************************************")

        #logging.debug(f"{zones=}")
        #return zones

        # todo: refactor, if `Zone` is useful just apply it in called functions above
        zone_profile = []
        for desktop in range(len(work_areas)):
            zone_profile.append([Zone(**zone) for zone in zones[desktop]])
        return ZoneProfile(zone_profile)
