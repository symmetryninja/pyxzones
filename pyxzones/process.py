import logging
import os
import signal
import sys
from pathlib import Path

from .service import Service, FatalXQueryFailure
from . import config

PID_FILE = 'pyxzones.pid'


def check_pid_running(pid: int):
    if not pid:
        return False
    try:
        """
        Supposedly for POSIX, the following is true:

        "If sig is 0 (the null signal), error checking is performed but no signal is actually
        sent. This can be used to check the validity of pid."

        However, this doesn't matter in practice as checking for the process is only
        used to kill it afterwards here, so even if it's killed by 0 signal, there
        should be no real issue.
        """
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def get_stored_pid() -> int | None:
    pid_file = Path(config.get_data_directory_path(), PID_FILE)
    if pid_file.exists():
        with open(pid_file, 'r') as file:
            return int(file.read())
    return None


def save_stored_pid(pid: int) -> bool:
    pid_file = Path(config.get_data_directory_path(), PID_FILE)
    try:
        with open(pid_file, 'w') as file:
            file.write(str(pid))
        return True
    except:
        return False


def start() -> None:
    try:
        service = Service()
        service.listen()
    except FatalXQueryFailure as exception:
        logging.critical(exception)
        sys.exit(1)
    except KeyboardInterrupt:
        # Mute the Exception output
        sys.exit(0)


def launch_daemon() -> None:
    pid = get_stored_pid()
    if check_pid_running(pid):
        print("Found existing process, terminating...")
        kill_daemon()

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as exception:
        logging.fatal(f"Process fork failed: {exception.errno} ({exception.strerror})")
        sys.exit(1)

    pid = os.getpid()
    save_stored_pid(pid)
    logging.debug(f"Started process: {pid}")

    start()


def kill_daemon() -> None:
    pid = get_stored_pid()

    if not check_pid_running(pid):
        print("No running process found.")
        return

    print("Found existing process, terminating...")
    os.kill(pid, signal.SIGTERM)
    print(f"Terminated process: {pid}")
    Path(config.get_data_directory_path(), PID_FILE).unlink()
