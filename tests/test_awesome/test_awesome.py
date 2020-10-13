import subprocess
import os


def test_first(command):
    for _ in range(5):
        output = subprocess.run([command, "--socket", "powerline-ipc-test-{}".format(os.getpid()), "wm.awesome"], capture_output=True)
        assert output.stdout.decode() == ""
        assert output.stderr.decode() == ""

