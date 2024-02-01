import logging
from .types import MergeZone, Zone, WorkArea
from .settings import SETTINGS


class ZoneProfile:
    def __init__(self, zones, merge_zones):
        self.zones = zones
        self.merge_zones = merge_zones

    def find_zone(self, virtual_desktop, x, y) -> MergeZone | Zone | None:
        for zone in self.merge_zones[virtual_desktop]:
            if zone.check(x, y):
                return zone
        for zone in self.zones[virtual_desktop]:
            if zone.check(x, y):
                return zone
        return None

    @staticmethod
    def get_zones_for_monitor_work_area(monitor, work_area, zone_spec) -> list[Zone]:
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
                zones.append(Zone(
                                x=int(x_offset + x_consumed),
                                y=y_offset,
                                width=width,
                                height=work_area.height,
                                orientation=monitor_orientation
                            ))
                x_consumed += width

        elif zone_spec['orientation'] == 'portrait':
            total = sum(zone_spec['rows'])
            y_consumed = 0

            for row in zone_spec['rows']:
                height = int(row / total * work_area.height)
                zones.append(Zone(
                                x=x_offset,
                                y=int(y_offset + y_consumed),
                                width=work_area.width,
                                height=height,
                                orientation=monitor_orientation
                            ))
                y_consumed += height
        else:
            # todo: invalid or missing orientation error
            pass

        return zones


    @staticmethod
    def get_merge_zones_for_zones_work_area(zones: list[Zone], work_area: WorkArea) -> list[MergeZone]:
        merge_zones = []
        num_zones = len(zones)

        if not SETTINGS.merge_zone_size_preference or num_zones == 0:
            return merge_zones

        merge_zone_half_size_multiplier = max(2, min(SETTINGS.merge_zone_size_preference, 25)) / 100

        for index, zone in enumerate(zones):
            if index == num_zones - 1:
                break
            if zone.orientation == 'landscape':
                merge_zone = MergeZone(
                    x=int((zone.x + zone.width) - work_area.width * merge_zone_half_size_multiplier / 2),
                    y=zone.y,
                    width=int(work_area.width * merge_zone_half_size_multiplier),
                    height=zone.height,
                    orientation=zone.orientation
                )
            else:
                merge_zone = MergeZone(
                    x=zone.x,
                    y=int((zone.y + zone.height) - work_area.height * merge_zone_half_size_multiplier / 2),
                    width=zone.width,
                    height=int(work_area.height * merge_zone_half_size_multiplier),
                    orientation=zone.orientation
                )
            next_zone = zones[index + 1]
            merge_zone.zones = (zone, next_zone)
            merge_zone.surface = Zone(zone.x, zone.y, zone.width, zone.height, zone.orientation)
            if zone.orientation == 'landscape':
                merge_zone.surface.width = zone.width + next_zone.width
            else:
                merge_zone.surface.height = zone.height + next_zone.height
            merge_zones.append(merge_zone)

        return merge_zones


    @staticmethod
    def get_zones_per_virtual_desktop(monitors, work_areas):
        zones = []         # [array of virtual desktops [of arrays of monitors [of array of zones]]]
        merge_zones = []
        zone_specification = SETTINGS.zones

        for desktop in range(len(work_areas)):
            desktop_zones = []
            desktop_merge_zones = []
            single_workarea = len(work_areas[desktop]) == 1
            for monitor in range(len(monitors)):
                work_area = work_areas[desktop][0] if single_workarea else work_areas[desktop][monitor]
                monitor_zones = ZoneProfile.get_zones_for_monitor_work_area(
                    monitors[monitor],
                    work_area,
                    zone_specification['displays'][monitor]
                )
                desktop_zones += monitor_zones
                desktop_merge_zones += ZoneProfile.get_merge_zones_for_zones_work_area(monitor_zones, work_area)

            zones.append(desktop_zones)
            merge_zones.append(desktop_merge_zones)


        logging.info("************************************************************")
        logging.info("  zones:")
        for desktop in range(0, len(zones)):
            logging.info(f"  desktop {desktop}:")
            for zone in zones[desktop]:
                logging.info(f"\t{zone=}")
        logging.info("************************************************************")
        """
        logging.info("************************************************************")
        logging.info("  merge_zones:")
        for desktop in range(0, len(merge_zones)):
            logging.info(f"  desktop {desktop}:")
            for merge_zone in merge_zones[desktop]:
                logging.info(f"\t{merge_zone=}")
        logging.info("************************************************************")
        """

        return ZoneProfile(zones, merge_zones)

