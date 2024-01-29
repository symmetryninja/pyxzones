#! /usr/bin/python3

from .service import Service
import sys
import argparse
import logging
from . import process


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
        help=argparse.SUPPRESS
    )

    args = parser.parse_args()

    log_level = logging.getLevelName(args.log_level)
    logging.basicConfig(level=log_level)

    if args.daemon:
        process.launch_daemon()
    elif args.kill:
        process.kill_daemon()
    else:
        try:
            service = Service()
            service.listen()
        except KeyboardInterrupt:
            # Mute the Exception output
            sys.exit(0)


if __name__ == "__main__":
    main()
