import pytest
import os


@pytest.fixture(scope="module")
def daemon_env():
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = os.path.abspath(os.path.dirname(__file__))
    env["LANG"] = "C"
    env["PATH"] = "{}:{}".format(os.path.join(os.path.abspath(os.path.dirname(__file__)), "path"), env["PATH"])
    return env

