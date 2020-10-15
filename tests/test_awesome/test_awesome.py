import subprocess
import os
import time

from tests.utils import logs_empty


def test_wm_awesome(command, daemon_env):
    time.sleep(2)
    for _ in range(5):
        output = subprocess.run(
            [command, "--socket", "/tmp/powerline-ipc-test-{}".format(os.getpid()), "wm.awesome"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=daemon_env)
        logs_empty(output)


def test_kill_log(daemon, daemon_logs, daemon_env):
    time.sleep(5)
    output = subprocess.run(
        [daemon, "--socket", "/tmp/powerline-ipc-test-{}".format(os.getpid()), "--quiet", "--kill"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=daemon_env)
    logs_empty(output)
    logs = daemon_logs()
    assert logs == ""


def test_check_awesome_logs(xprocess):
    results_dir = xprocess.getinfo("daemon").controldir / "results"
    with open(results_dir / "requests") as requests_file:
        content = requests_file.read()
    content_split = content.splitlines()
    line_count = len(content_split)
    assert 5 <= line_count <= 15
    for line in content_split:
        assert line == \
           "powerline_widget:set_markup('<span foreground=\"#303030\">" \
           " </span><span foreground=\"#d0d0d0\" background=\"#303030\" " \
           "font_weight=\"bold\"> default-right </span>')"
