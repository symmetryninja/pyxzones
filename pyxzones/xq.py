import logging
from Xlib import Xatom
from Xlib.ext import randr

from .types import WorkArea


def get_monitors(display, root_window):
    screen_resources = randr.get_screen_resources(root_window)

    monitors = []
    for output in screen_resources.outputs:
        output_info = randr.get_output_info(display, output, screen_resources.config_timestamp)
        if output_info.crtc == 0:
            continue

        crtc_info = randr.get_crtc_info(display, output_info.crtc, screen_resources.config_timestamp)
        monitors.append({
            "mode": crtc_info.mode,
            "rotation": crtc_info.rotation,
            "virtual_x": crtc_info.x,
            "virtual_y": crtc_info.y,
            "virtual_width": crtc_info.width,
            "virtual_height": crtc_info.height,
        })

    # sort monitors from left to right, top to bottom (as configuration is expected to be done)
    monitors.sort(key = lambda m: (m['virtual_x'], m['virtual_y']))

    screen_mode_map = {}
    for mode in screen_resources.modes:
        screen_mode_map[mode.id] = (mode.width, mode.height)

    for monitor in monitors:
        monitor['width'] = screen_mode_map[monitor['mode']][0 if monitor['rotation'] in (1, 4) else 1]
        monitor['height'] = screen_mode_map[monitor['mode']][1 if monitor['rotation'] in (1, 4) else 0]

        if monitor['virtual_width'] / monitor['width'] != monitor['virtual_height'] / monitor['height']:
            logging.warning("Unexpected uneven scaling of virtual monitor:")
            logging.warning(f"\t{monitor['virtual_width'] / monitor['width']=}")
            logging.warning(f"\t{monitor['virtual_height'] / monitor['height']=}")

        monitor['scale'] = monitor['virtual_width'] / monitor['width']

    return monitors


# Find available space (no panels)
def get_work_areas(display, desktop):
    # Fallback from best data to worst
    #
    #   _GTK_WORKAREAS_D<desktop>
    #   _NET_WORKAREAS_D<desktop>
    #   _NET_WORKAREA
    #   RootWindow.get_geometry()
    #
    gtk_work_area_d = display.screen().root.get_full_property(
        display.intern_atom(f"_GTK_WORKAREAS_D{desktop}"), Xatom.CARDINAL
    )
    if gtk_work_area_d != None:
        logging.debug(f"gtk_work_area_d{desktop}: {gtk_work_area_d.value}")
        work_areas = [gtk_work_area_d.value[l:l+4] for l in range(0, len(gtk_work_area_d.value), 4)]
        return [WorkArea(*work_areas[i]) for i in range(0, len(work_areas))]


    # don't think any WM implements the _NET_WORKAREAS_D# variant at the moment
    net_work_area_d = display.screen().root.get_full_property(
        display.intern_atom(f"_NET_WORKAREAS_D{desktop}"), Xatom.CARDINAL
    )
    if net_work_area_d != None:
        logging.debug(f"{net_work_area_d=}")
        work_areas = [net_work_area_d.value[l:l+4] for l in range(0, len(net_work_area_d.value), 4)]
        return [WorkArea(*work_areas[i]) for i in range(0, len(work_areas))]


    logging.warning("_GTK_WORKAREAS is not supported, fallback to _NET_WORKAREA. "
            "Work areas may be incorrect on multi-monitor systems.\n")


    work_area_property = display.screen().root.get_full_property(
        display.intern_atom('_NET_WORKAREA'), Xatom.CARDINAL
    )
    # work_area_property.value is a list of desktops of repeating x,y,w,h specs
    # this includes virtual desktops, tbd on what this means for multi-monitor
    
    # todo: this returns a large virtual-desktop without slicing monitors or unusable space
    # the caller needs to know that a result of length 1 on multi-monitor setup is a large virtual screen
    if work_area_property != None:
        logging.debug(f"{work_area_property=}")
        work_area = WorkArea(*work_area_property.value[desktop * 4:4])
        return [work_area]

    logging.warning("_NET_WORKAREA is not supported, Work areas may be incorrect.\n")


    # fallback to geometry
    # there's probably a better way to map geometry data into a namedtuple
    # but it didn't seem worth continuing to look for it
    geometry = display.screen().root.get_geometry()
    return [WorkArea(*[geometry.x, geometry.y, geometry.width, geometry.height])]


def get_work_areas_for_all_desktops(display, number_of_virtual_desktops):
    work_areas = []
    for desktop in range(0, number_of_virtual_desktops):
        work_areas.append(get_work_areas(display, desktop))
    return work_areas


def get_window_frame_extents(display, window) -> list[int] | None:
    extents = window.get_full_property(
        display.intern_atom("_NET_FRAME_EXTENTS"), Xatom.CARDINAL
    )
    return extents.value if extents != None else (0, 0, 0, 0)


def get_window_coordinates(window) -> tuple[int, int] | None:
    if window is None:
        return None

    (x, y) = (0, 0)

    while window:
        geometry = window.get_geometry()
        x += geometry.x
        y += geometry.y
        window = window.query_tree().parent

    return (x, y)
