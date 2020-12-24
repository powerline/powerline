import os
import pytest


# This is placed here as autouse, such that daemon process is actually used for all tests in this module
# This is done so that the daemon does not need to be run for each test, and therefore
# daemon_env only needs to be defined when the daemon is actually used
@pytest.fixture(scope="module", autouse=True)
def autouse_daemon(daemon_process):
    yield daemon_process


@pytest.fixture(scope="module")
def daemon_env():
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = os.path.abspath(os.path.dirname(__file__))
    env["LANG"] = "C"
    env["PATH"] = "{}:{}".format(os.path.join(os.path.abspath(os.path.dirname(__file__)), "path"), env["PATH"])
    return env
