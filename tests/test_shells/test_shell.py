import os
import pathlib

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


def check_screen_log(daemonless, shell, daemon_env, test_root, output):
    base_dir = os.path.join(daemon_env["XDG_CONFIG_HOME"], "outputs")
    file_name = "{sh}.{daemon}daemon.ok".format(daemon="no" if daemonless else "", sh=shell)
    if not os.path.exists(os.path.join(base_dir, file_name)):
        file_name = "{sh}.ok".format(sh=shell)
    with open(os.path.join(base_dir, file_name)) as fl:
        postprocessed = postprocess_output(shell, output, test_root)
        actual = fl.read()
        assert postprocess_output(shell, output, test_root) == actual


def execute_specific_test(daemonless, daemon_env, shell, test_root, client):
    wait_for_echo = shell == "dash" or shell == "ipython" or shell == "pdb"  # Todo improve, try without wait_for_echo
    wait_for_echo = False
    commands = get_test_commands(shell)
    output = run_main(shell, "nodaemon" if daemonless else "daemon", test_root, commands, wait_for_echo, client)
    check_screen_log(daemonless, shell, daemon_env, test_root, output)


@pytest.mark.parametrize("client", ["powerline", "powerline.py", "powerline.sh"])
@pytest.mark.parametrize("shell", ["bash", "zsh", "busybox", "tcsh", "mksh", "fish"])
def test_shell_with_daemon(shell, daemon_env, test_root, client):
    execute_specific_test(False, daemon_env, shell, test_root, client)


@pytest.mark.parametrize("client", ["powerline", "powerline-render", "powerline.py", "powerline.sh"])
@pytest.mark.parametrize("shell", ["bash", "zsh", "busybox", "tcsh", "mksh", "fish"])
def test_shell_without_daemon(shell, daemon_env, test_root, client):
    execute_specific_test(True, daemon_env, shell, test_root, client)
