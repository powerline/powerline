import os
import pathlib
import platform

import pytest

from tests.test_shells.run_script import run_main, postprocess_output


def get_test_commands(shell):
    args = [
        ["bash", "--norc", "--noprofile", "-i"],
        ["zsh", "-f", "-i"],
        ["fish", "-i"],
        ["tcsh", "-f", "-i"],
        ["busybox", "ash", "-i"],
        ["mksh", "-i"],
        ["dash", "-i"],
        ["rc", "-i", "-p"]
    ]
    for arg in args:
        if shell == arg[0]:
            return arg


def check_screen_log(test_type, shell, daemon_env, test_root, output):
    base_dir = os.path.join(daemon_env["XDG_CONFIG_HOME"], "outputs")
    file_name = "{sh}.{type}.ok".format(type=test_type, sh=shell)
    if not os.path.exists(os.path.join(base_dir, file_name)):
        file_name = "{sh}.ok".format(sh=shell)
    with open(os.path.join(base_dir, file_name)) as fl:
        postprocessed = postprocess_output(shell, output, test_root)
        actual = fl.read()
        assert postprocess_output(shell, output, test_root) == actual


def execute_specific_test(test_type, daemon_env, shell, test_root, client):
    commands = get_test_commands(shell)
    output = run_main(shell, test_type, test_root, commands, False, client)
    check_screen_log(test_type, shell, daemon_env, test_root, output)


def execute_pdb_test(test_type, daemon_env, test_root, commands):
    output = run_main("pdb", test_type, test_root, commands, False, "python")
    check_screen_log(test_type, "pdb", daemon_env, test_root, output)


@pytest.mark.parametrize("client", ["powerline", "powerline.py", "powerline.sh"])
@pytest.mark.parametrize("shell", ["bash", "zsh", "busybox", "tcsh", "mksh", "fish"])
def test_shell_with_daemon(shell, daemon_env, test_root, client, daemon_logs):
    if shell == "fish":
        pytest.skip("fish will be skipped, it currently fails and was also disabled with Travis CI")
    if shell == "busybox":
        pytest.skip("busybox will be skipped, it has issues with showing job number")
    execute_specific_test("daemon", daemon_env, shell, test_root, client)
    assert daemon_logs() == ""


@pytest.mark.parametrize("client", ["powerline", "powerline-render", "powerline.py", "powerline.sh"])
@pytest.mark.parametrize("shell", ["bash", "zsh", "busybox", "tcsh", "mksh", "fish"])
def test_shell_without_daemon(shell, daemon_env, test_root, client):
    if shell == "fish":
        pytest.skip("fish will be skipped, it currently fails and was also disabled with Travis CI")
    if shell == "busybox":
        pytest.skip("busybox will be skipped, it has issues with showing job number")
    execute_specific_test("nodaemon", daemon_env, shell, test_root, client)


def test_pdb_subclass(daemon_env, test_root):
    if platform.python_implementation() == 'PyPy':
        pytest.skip("PDB tests not enabled for PyPy")
    commands = ["python", os.path.join("tests", "test_shells", "pdb-main.py")]
    execute_pdb_test("subclass", daemon_env, test_root, commands)


def test_pdb_module(daemon_env, test_root):
    if platform.python_implementation() == 'PyPy':
        pytest.skip("PDB tests not enabled for PyPy")
    commands = ["python", "-m", "powerline.bindings.pdb", os.path.join("tests", "test_shells", "pdb-script.py")]
    execute_pdb_test("module", daemon_env, test_root, commands)


@pytest.skip("IPython test currently fails and was also disabled with Travis CI")
def test_ipython(daemon_env, test_root):
    os.environ["POWERLINE_CONFIG_OVERRIDES"] = "common.term_escape_style=fbterm"
    os.environ["POWERLINE_THEME_OVERRIDES"] = "in.segments.left=[]"
    commands = ["python", "-m", "IPython"]
    output = run_main("ipython", "ipython", test_root, commands, False, "python")
    check_screen_log("ipython", "ipython", daemon_env, test_root, output)
    os.unsetenv("POWERLINE_CONFIG_OVERRIDES")
    os.unsetenv("POWERLINE_THEME_OVERRIDES")
