import shutil
import time

import pytest
import os

from xprocess import ProcessStarter
from pathlib import Path

seekpos = 0


def __init__(self):
    self.seekpos = 0


def start_daemon(xprocess, daemon, daemon_env):

    class Starter(ProcessStarter):
        env = daemon_env
        pattern = ""
        args = [daemon, "--foreground"]

        def wait(self, log_file):
            time.sleep(0.5)
            return True

    xprocess.ensure("daemon", Starter)


def stop_daemon(xprocess):
    cleanup_folder = xprocess.getinfo("daemon").controldir
    xprocess.getinfo("daemon").terminate()
    shutil.rmtree(cleanup_folder)


@pytest.fixture(scope="session")
def command():
    return Path(os.path.abspath(os.path.dirname(__file__))).parent / "scripts" / "powerline"


@pytest.fixture(scope="session")
def daemon():
    return Path(os.path.abspath(os.path.dirname(__file__))).parent / "scripts" / "powerline-daemon"


@pytest.fixture(scope="session")
def rootdir():
    return Path(os.path.abspath(os.path.dirname(__file__))).parent


@pytest.fixture(scope="session")
def lemonbar_cmd():
    return Path(os.path.abspath(os.path.dirname(__file__))).parent / \
           "powerline" / "bindings" / "lemonbar" / "powerline-lemonbar.py"


@pytest.fixture(autouse=True, scope="module")
def daemon_process(xprocess, daemon, daemon_env):
    global seekpos
    seekpos = 0
    start_daemon(xprocess, daemon, daemon_env)
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


# The following fixture is done that way, as importing from conftest is not really
# feasable, but the global seekpos needs to be known. Therefore, this function
# is imported via Dependency Injection
@pytest.fixture(scope="session")
def daemon_logs(xprocess):
    def fun():
        global seekpos
        with open(xprocess.getinfo("daemon").logpath) as fl:
            fl.seek(seekpos)
            logs = fl.read()
            return logs

    return fun
