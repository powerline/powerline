#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import json

from time import sleep
from subprocess import check_call
from glob import glob1
from traceback import print_exc

from tests.modules.lib.terminal import (ExpectProcess, MutableDimensions,
                                        do_terminal_tests, get_env)


VTERM_TEST_DIR = os.path.abspath('tests/vterm_vim')


def main(attempts=3):
	vterm_path = os.path.join(VTERM_TEST_DIR, 'path')

	vim_exe = os.path.join(vterm_path, 'vim')

	env = get_env(vterm_path, VTERM_TEST_DIR)

	dim = MutableDimensions(rows=50, cols=200)

	tests = (
	)

	args = []

	return do_terminal_tests(
		tests=tests,
		cmd=vim_exe,
		dim=dim,
		args=args,
		env=env,
		cwd=VTERM_TEST_DIR,
	)


if __name__ == '__main__':
	if main():
		raise SystemExit(0)
	else:
		raise SystemExit(1)
