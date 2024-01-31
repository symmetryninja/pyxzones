import logging
from .types import Zone
from .settings import SETTINGS


class ZoneProfile:
    def __init__(self, zones) -> None:
        self.zones = zones

    def find_zone(self, virtual_desktop, x, y):
        for zone in self.zones[virtual_desktop]:
            if zone.check(x, y):
                return zone
        return None

    @staticmethod
    def get_zones_for_monitor_work_area(monitor, work_area, zone_spec):
        zones = []

        # the crtc_info rotation is set differently in some environments than others
        # whilst it should represent monitor rotations, it may not always (for example,
        # a virtual machine may represent monitors with portrait resolutions but a
        # landscape 'rotation' value)
        #
        # so this will infer orientation by resoluion rather than relying on 'rotation'
        monitor_orientation = 'landscape' if monitor['width'] >= monitor['height'] else 'portrait'
        #monitor_orientation = 'landscape' if monitor['rotation'] in (1, 4) else 'portrait'


        # todo: `monitor_orientation` and provided `orientation` below may mismatch
        # error?

        # todo: consider splitting out offsets from zones calculation
        # gtk windows don't need offset to position within, but do need them to position windows
        x_offset = work_area.x
        y_offset = work_area.y

        # todo: orientation is pigeonholed in here when it probably shouldn't be part of the Zone definition

        if zone_spec['orientation'] == 'landscape':
            total = sum(zone_spec['columns'])
            x_consumed = 0

            for column in zone_spec['columns']:
                width = int(column / total * work_area.width)
                zones.append({
                                "x": int(x_offset + x_consumed),
                                "y": y_offset,
                                "width": width,
                                "height": work_area.height,
                                "orientation": monitor_orientation
                            })
                x_consumed += width

        elif zone_spec['orientation'] == 'portrait':
            total = sum(zone_spec['rows'])
            y_consumed = 0

            for row in zone_spec['rows']:
                height = int(row / total * work_area.height)
                zones.append({
                                "x": x_offset,
                                "y": int(y_offset + y_consumed),
                                "width": work_area.width,
                                "height": height,
                                "orientation": monitor_orientation
                            })
                y_consumed += height
        else:
            # todo: invalid or missing orientation error
            pass

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


        logging.info("************************************************************")
        logging.info("  zones:")
        for desktop in range(0, len(zones)):
            logging.info(f"  desktop {desktop}:")
            for zone in zones[desktop]:
                logging.info(f"\t{zone=}")
        logging.info("************************************************************")

        # todo: refactor, if `Zone` is useful just apply it in called functions above
        # instead of using dicts as intermediaries
        zone_profile = []
        for desktop in range(len(work_areas)):
            zone_profile.append([Zone(**zone) for zone in zones[desktop]])
        return ZoneProfile(zone_profile)
