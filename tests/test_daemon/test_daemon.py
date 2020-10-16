import shutil
import subprocess
import os
import time


import pytest

from tests.utils import logs_empty


def test_devnull(rootdir):

    result = subprocess.run([
        os.path.join(rootdir, "client", "powerline.py"), "--socket",
        "/tmp/powerline-ipc-test-{}".format(os.getpid()), "-p/dev/null", "shell", "left"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert "file not found" in result.stdout.decode()


def test_proper_config(rootdir):
    result = subprocess.run([
        os.path.join(rootdir, "client", "powerline.py"), "--socket",
        "/tmp/powerline-ipc-test-{}".format(os.getpid()), "-p{}".format(
            os.path.join(rootdir, "powerline", "config_files")
        ), "shell", "left"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert "file not found" not in result.stdout.decode()


def test_cwd(rootdir):
    env = os.environ.copy()
    workdir = os.path.join(rootdir, "tests", "test_daemon")
    env["PWD"] = workdir
    result = subprocess.run([
        os.path.join(rootdir, "client", "powerline.py"), "--socket",
        "/tmp/powerline-ipc-test-{}".format(os.getpid()), "-p{}".format(
            os.path.join(rootdir, "powerline", "config_files")
        ), "shell", "left"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workdir, env=env)
    assert "test_daemon" in result.stdout.decode()

