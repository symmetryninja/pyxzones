import logging
import stat
import xdg_base_dirs as xdg
from pathlib import Path

"""

This tries to respect the XDG Base Directory Specification as much as possible.

Specification (v0.8 at time of writing):
https://specifications.freedesktop.org/basedir-spec/0.8/

"""


def get_config_file_path(filename: str) -> Path | None:
    xdg_config_home = xdg.xdg_config_home()
    file = Path(xdg_config_home, filename)
    if xdg_config_home.is_dir() and file.exists():
        logging.debug(f"Found configuration file at {file}")
        return file

    xdg_config_dirs = xdg.xdg_config_dirs()
    for config_dir in xdg_config_dirs:
        file = Path(config_dir, filename)
        if config_dir.is_dir() and file.exists():
            logging.debug(f"Found configuration file at {file}")
            return file

    file = Path(Path.home(), filename)
    if file.exists():
        logging.debug(f"Found configuration file at {file}")
        return file

    # Looking at the home directory, lastly check for a hidden config
    if filename[0] != '.':
        file = Path(Path.home(), f".{filename}")
        if file.exists():
            logging.debug(f"Found configuration file at {file}")
            return file

    return None


def get_data_directory_path() -> Path | None:
    xdg_data_home = xdg.xdg_data_home()
    if xdg_data_home.exists():
        if not xdg_data_home.is_dir():
            logging.warning(f"Found XDG_DATA_HOME directory path at {xdg_data_home} but doesn't appear to be a directory")
        elif xdg_data_home.stat().st_mode & stat.S_IWUSR:
            return xdg_data_home
        else:
            logging.warning(f"Found XDG_DATA_HOME directory path at {xdg_data_home} but user doesn't appear to have write permissions")
    else:  # doesn't exist, try to create
        try:
            xdg_data_home.mkdir(mode=700, parents=True)
            return xdg_data_home
        except:
            logging.warning(f"Failed to create XDG_DATA_HOME at {xdg_data_home}")

    xdg_data_dirs = xdg.xdg_data_dirs()
    for data_dir in xdg_data_dirs:
        if data_dir.exists():
            if not data_dir.is_dir():
                logging.warning(f"Found an XDG_DATA_DIR directory path at {data_dir} but doesn't appear to be a directory")
            elif data_dir.stat().st_mode & stat.S_IWUSR:
                return data_dir
            else:
                logging.warning(f"Found an XDG_DATA_DIR directory path at {data_dir} but user doesn't appear to have write permissions")
        else: # doesn't exist, try to create
            try:
                data_dir.mkdir(mode=700, parents=True)
                return data_dir
            except:
                logging.warning(f"Failed to create an XDG_DATA_DIR at {data_dir}")

    return None
