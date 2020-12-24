from subprocess import CompletedProcess


def logs_empty(output: CompletedProcess):
    stdout = output.stdout.decode()
    stderr = output.stderr.decode()
    print(stdout)
    print(stderr)
    assert stdout == ""
    assert stderr == ""
