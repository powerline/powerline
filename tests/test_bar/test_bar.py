import shutil
import subprocess
import os
import time


import pytest

from tests.utils import logs_empty

def get_arg_val(arg_name, args):
    for i, arg in enumerate(args):
        if arg == arg_name:
            return args[i + 1]
        if arg.startswith(arg_name + "="):
            return arg.split("=", 1)[1]


@pytest.mark.parametrize("args", [
    [], ["-i0.5"], ["--interval=0.5"], ["--", "test", "args"],
    ["--bar-command", "bar-aint-recursive"], ["--height=10"]
])
def test_lemonbar(lemonbar_cmd, daemon_env, args, xprocess):
    control_dir = xprocess.getinfo("daemon").controldir
    proc = subprocess.Popen(
        [lemonbar_cmd, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=daemon_env,
        cwd=control_dir
    )
    time.sleep(5)
    proc.kill()
    stdout, stderr = proc.communicate(timeout=0.5)
    assert stdout.decode() == ""
    assert stderr.decode() == ""
    results_dir = control_dir / "results"
    logfiles = list(filter(lambda f: f.endswith(".log"), os.listdir(results_dir)))
    argslog = []
    for file in logfiles:
        argsfile = "{}.args".format(file.rsplit(".log", 1)[0])
        with open(results_dir / argsfile) as fl:
            args_content = fl.read()
        argslog.append(args_content.strip())
        with open(results_dir / file) as fl:
            file_content = fl.read()
        expected_text = "default" if "+1" in args_content else "dvi"
        splitted = file_content.splitlines()
        assert 5 <= len(splitted) <= 15
        expected_line = "%{l}%{F#ffd0d0d0}%{B#ff303030} " + expected_text + \
                        "-left %{F-B--u}%{F#ff303030} %{F-B--u}%{r}%{F#ff303030}" \
                        " %{F-B--u}%{F#ffd0d0d0}%{B#ff303030} " + \
                        expected_text + "-right %{F-B--u}"
        for line in splitted:
            assert expected_line == line
    shutil.rmtree(results_dir)
    assert len(logfiles) == 2
    height = get_arg_val("--height", args)
    if height is None:
        height = ""
    bar_command = get_arg_val("--bar-command", args)
    if bar_command is None:
        bar_command = "lemonbar"
    script_args = " ".join(args)
    if script_args.startswith("-- "):
        script_args = script_args.split("-- ", 1)[1]
    script_args.lstrip(" ")
    if script_args == " ".join(args):
        script_args = ""
    script_args_empty = " " if script_args else ""
    expected_args = \
        "{command} -g 1920x{height}+0+0{script_args_empty}{script_args}\n" \
        "{command} -g 1920x{height}+1+0{script_args_empty}{script_args}".format(command=bar_command, script_args=script_args, script_args_empty=script_args_empty, height=height)
    assert "\n".join(sorted(argslog)) == expected_args


def test_lemonbar_lint(daemon_env, rootdir):
    result = subprocess.run(
        ["powerline-lint",
         "-p", os.path.join(rootdir, "powerline", "config_files"), "-p",
         os.path.join(daemon_env["XDG_CONFIG_HOME"], "powerline")], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=daemon_env,
    )
    assert result.returncode == 0
