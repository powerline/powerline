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
    wait_for_echo = shell == "dash" or shell == "ipython" or shell == "pdb"  # Todo improve, try without wait_for_echo
    commands = get_test_commands(shell)
    output = run_main(shell, test_type, test_root, commands, wait_for_echo, client)
    check_screen_log(test_type, shell, daemon_env, test_root, output)


def execute_pdb_test(test_type, daemon_env, test_root):
    wait_for_echo = False
    commands = ["python", os.path.join("tests", "test_shells", "pdb-main.py")]
    output = run_main("pdb", test_type, test_root, commands, wait_for_echo, "python")

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


def test_pdb(daemon_env, test_root):
    if platform.python_implementation() == 'PyPy':
        pytest.skip("PDB tests not enabled for PyPy")
    execute_pdb_test("subclass", daemon_env, test_root)
