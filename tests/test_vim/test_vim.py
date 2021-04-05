import os
import pathlib
import platform
import subprocess

import pytest

from tests.test_shells.run_script import run_main, postprocess_output


scripts = [x for x in os.listdir(os.path.join(os.path.dirname(__file__), "tests")) if not x.endswith(".old.vim")]


@pytest.mark.parametrize("script_name", scripts)
def test_vimtests(script_name):
    abspath = os.path.join(os.path.dirname(__file__), "tests", script_name)
    result = subprocess.run(["/usr/bin/vim", "-S", abspath])
    if os.path.isfile("message.fail"):
        with open("message.fail") as fail_message:
            print(fail_message.read())
        os.remove("message.fail")
    assert result == 0
