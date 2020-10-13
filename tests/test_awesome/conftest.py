import time

import pytest
import os

from xprocess import ProcessStarter
from pathlib import Path
seekpos = 0


def start_daemon(xprocess):
    address = "powerline-ipc-test-{}".format(os.getpid())
    daemon = Path(os.path.abspath(os.path.dirname(__file__))).parent.parent / "scripts" / "powerline-daemon"

    daemon_env = os.environ.copy()
    daemon_env["XDG_CONFIG_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "powerline")

    class Starter(ProcessStarter):
        env = daemon_env
        pattern = ""
        args = [daemon, "--socket", address, "--foreground"]

        def wait(self, log_file):
            time.sleep(0.5)
            return True

    xprocess.ensure("daemon", Starter)


def stop_daemon(xprocess):
    xprocess.getinfo("daemon").terminate()


def get_logs():
    global seekpos


@pytest.fixture(autouse=True)
def command():
    return Path(os.path.abspath(os.path.dirname(__file__))).parent.parent / "scripts" / "powerline"


@pytest.fixture(autouse=True, scope="module")
def daemon(xprocess):
    global seekpos
    seekpos = 0
    start_daemon(xprocess)
    yield
    stop_daemon(xprocess)


@pytest.fixture(autouse=True, scope="function")
def print_daemon_logs(xprocess):
    global seekpos
    yield
    with open(xprocess.getinfo("daemon").logpath) as fl:
        fl.seek(seekpos)
        print(fl.read())
        seekpos = fl.tell()


@pytest.fixture(scope="function")
def daemon_logs(xprocess):
    global seekpos
    with open(xprocess.getinfo("daemon").logpath) as fl:
        fl.seek(seekpos)
        return fl.read()


