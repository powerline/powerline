#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys

from time import sleep
from subprocess import check_call
from glob import glob1
from traceback import print_exc

from powerline.lib.dict import updated

from tests.modules.lib.terminal import (ExpectProcess, MutableDimensions,
                                        do_terminal_tests, get_env)
from tests.modules import PowerlineTestSuite


TEST_ROOT = os.path.abspath(os.environ['TEST_ROOT'])


def main(attempts=3):
	vterm_path = os.path.join(TEST_ROOT, 'path')

	vim_exe = os.path.join(vterm_path, 'vim')

	env = get_env(vterm_path, TEST_ROOT)
	env['ROOT'] = os.path.abspath('.')

	dim = MutableDimensions(rows=50, cols=200)

	vimrc = os.path.join(TEST_ROOT, 'init.vim')
	vimrc_contents = '''
		set laststatus=2
		set runtimepath=$ROOT/powerline/bindings/vim
	'''
	with open(vimrc, 'w') as vd:
		vd.write(vimrc_contents)

	base_attrs = {
		(( 64,  64, 255), (0, 0, 0), 0, 0, 0): 'NT',  # NonText
		((240, 240, 240), (0, 0, 0), 0, 0, 0): 'N',   # Normal
	}

	args = [
		'-u', vimrc,
		'-i', 'NONE',
	]

	def feed(p):
		p.send(':echo strtrans(eval(&statusline[2:]))\n')

	tests = (
	)

	with PowerlineTestSuite('vim') as suite:
		return do_terminal_tests(
			tests=tests,
			cmd=vim_exe,
			dim=dim,
			args=args,
			env=env,
			cwd=TEST_ROOT,
			suite=suite,
		)


if __name__ == '__main__':
	if main():
		raise SystemExit(0)
	else:
		raise SystemExit(1)
