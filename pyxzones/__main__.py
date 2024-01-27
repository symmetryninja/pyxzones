#! /usr/bin/python3

from .service import Service
import sys

import logging

# todo: read from cmd line --log or -v[vv]
logging.basicConfig(level=logging.DEBUG)

# TODO: Command line parsing & flags
def main():
    if len(sys.argv) == 1:
        try:
            service = Service()
            service.listen()
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == "__main__":
    main()
