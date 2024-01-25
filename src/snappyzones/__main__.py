#! /usr/bin/python3

from .service import Service
import sys

import logging

# todo: read from cmd line --log
logging.basicConfig(level=logging.DEBUG)

# TODO:　Proper(?) command line parsing
def main():
    if len(sys.argv) == 1:
        try:
            service = Service()
            service.listen()
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == "__main__":
    main()
