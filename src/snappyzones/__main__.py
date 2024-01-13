#! /usr/bin/python3

from .service import Service
from .process import launch_background_process, stop_background_process
import sys

# TODO:　Proper(?) command line parsing
def main():
    if len(sys.argv) == 1:
        service = Service()
        service.listen()

    elif sys.argv[-1] == "start":
        launch_background_process(*args, **kwargs)

    elif sys.argv[-1] == "stop":
        stop_background_process()

if __name__ == "__main__":
    main()
