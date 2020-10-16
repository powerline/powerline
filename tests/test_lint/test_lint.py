import os
import subprocess


def test_lint(rootdir):
    result = subprocess.run(
        ["powerline-lint",
         "-p", os.path.join(rootdir, "powerline", "config_files")], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    assert result.returncode == 0
