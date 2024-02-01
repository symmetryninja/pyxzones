import argparse
import logging
import sys
from json.decoder import JSONDecodeError

from .settings import SETTINGS
from . import config
from . import process

SETTINGS_FILE = 'pyxzones.json'


def main():
    parser = argparse.ArgumentParser(
        prog='pyxzones',
        description='Drag and drop window zoning'
    )
    parser.add_argument(
        '--daemon',
        help='run pyxzones in the background',
        action="store_true"
    )
    parser.add_argument(
        '--kill',
        help='kill any running instance of pyxzones and exit',
        action="store_true"
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL'],
        default='WARNING',
        type=str.upper,
        help=argparse.SUPPRESS
    )
    args = parser.parse_args()

    log_level = logging.getLevelName(args.log_level)
    logging.basicConfig(
        level=log_level,
        format="%(levelname)-8s %(message)s",
    )

    config_file = config.get_config_file_path(SETTINGS_FILE)
    if config_file is not None:
        with config_file.open() as file:
            try:
                SETTINGS.load_from_file(file)
            except JSONDecodeError:
                logging.fatal(f"Failed to parse user configuration json file located at {config_file}")
                sys.exit(1)

    if args.daemon:
        process.launch_daemon()
    elif args.kill:
        process.kill_daemon()
    else:
        process.start()


if __name__ == "__main__":
    main()
