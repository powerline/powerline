import shutil
import time

import pytest
import os

from xprocess import ProcessStarter
from pathlib import Path
seekpos = 0


def start_daemon(xprocess, daemon, daemon_env):
    address = "/tmp/powerline-ipc-test-{}".format(os.getpid())

    class Starter(ProcessStarter):
        env = daemon_env
        pattern = ""
        args = [daemon, "--socket", address, "--foreground"]

        def wait(self, log_file):
            time.sleep(0.5)
            return True

    xprocess.ensure("daemon", Starter)


def stop_daemon(xprocess):
    cleanup_folder = xprocess.getinfo("daemon").controldir
    xprocess.getinfo("daemon").terminate()
    shutil.rmtree(cleanup_folder)


def get_logs():
    global seekpos


@pytest.fixture(scope="session")
def command():
    return Path(os.path.abspath(os.path.dirname(__file__))).parent.parent / "scripts" / "powerline"


@pytest.fixture(scope="session")
def daemon():
    return Path(os.path.abspath(os.path.dirname(__file__))).parent.parent / "scripts" / "powerline-daemon"


@pytest.fixture(autouse=True, scope="module")
def daemon_process(xprocess, daemon, daemon_env):
    global seekpos
    seekpos = 0
    start_daemon(xprocess, daemon, daemon_env)
    yield
    stop_daemon(xprocess)


@pytest.fixture(scope="session")
def daemon_env():
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = os.path.abspath(os.path.dirname(__file__))
    env["LANG"] = "C"
    env["PATH"] = "{}:{}".format(os.path.join(os.path.abspath(os.path.dirname(__file__)), "path"), env["PATH"])
    return env


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

