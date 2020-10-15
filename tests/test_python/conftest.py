import os

import pytest


# Needs to be defined as an autouse fixture is using this fixture.
# Leads to a daemon being run on python tests, but that should not be too much of a problem
@pytest.fixture(scope="module")
def daemon_env():
    return os.environ

