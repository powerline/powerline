#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from time import sleep

from powerline.lib.dict import updated

from tests.modules.lib.terminal import (MutableDimensions, do_terminal_tests,
                                        get_env)


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
		let g:powerline_config_paths = [expand("$ROOT/powerline/config_files")]
		set runtimepath=$ROOT/powerline/bindings/vim
	'''
	with open(vimrc, 'w') as vd:
		vd.write(vimrc_contents)

	base_attrs = {
		# Pref
		# S/   segments
		# s/   separators
		#      Vim own highlight
		(( 64,  64, 255), (  0,   0,   0), 0, 0, 0): 'NT',       # NonText
		((240, 240, 240), (  0,   0,   0), 0, 0, 0): 'N',        # Normal
		((  0,  51,   0), (153, 204,   0), 1, 0, 0): 'S/mn',     # Normal mode
		((153, 204,   0), ( 44,  44,  44), 0, 0, 0): 's/mn-bg',  # Separator mode-filler
		((255, 255, 255), ( 44,  44,  44), 0, 0, 0): 'S/bg',     # Filler segment
		((166, 166, 166), ( 44,  44,  44), 0, 0, 0): 'S/ft',     # Filetype
		(( 88,  88,  88), ( 44,  44,  44), 0, 0, 0): 's/ft-ps',  # Separator filetype-position
		((166, 166, 166), ( 88,  88,  88), 0, 0, 0): 'S/pc',     # Vertical position (percent)
		((221, 221, 221), ( 88,  88,  88), 0, 0, 0): 's/pc-ln',  # Separator position-line number
		(( 33,  33,  33), (221, 221, 221), 0, 0, 0): 'S/ln',     # LN text
		(( 33,  33,  33), (221, 221, 221), 1, 0, 0): 'S/lN',     # Actual line number
		((  0,  51,   0), (221, 221, 221), 0, 0, 0): 'S/cl',     # Column
	}

	args = [
		'-u', vimrc,
		'-i', 'NONE',
	]

	testss = (
		{
			'tests': (
				{
					'expected_result': (
						'{S/mn: NORMAL }'
						'{s/mn-bg: }'
						'{S/bg:' + (' ' * 169) + '}'
						'{S/ft:unix}'
						'{s/ft-ps: }'
						'{S/pc: 100%}'
						'{s/pc-ln: }'
						'{S/ln: LN }'
						'{S/lN:  1}'
						'{S/cl::1  }',
						base_attrs
					),
				},
			),
		},
		{
			'tests': (
				{
					'expected_result': (
						'{S/mn: NORMAL }'
						'{s/mn-bg: }'
						'{S/bg:' + (' ' * 169) + '}'
						'{S/ft:unix}'
						'{s/ft-ps: }'
						'{S/pc: 100%}'
						'{s/pc-ln: }'
						'{S/ln: LN }'
						'{S/lN:  1}'
						'{S/cl::1  }',
						base_attrs
					),
				},
			),
			'env': updated(env, LANG='C'),
		},
		{
			'tests': (
				{
					'expected_result': (
						'{S/mn: NORMAL }'
						'{s/mn-bg: }'
						'{S/bg:' + (' ' * 167) + '}'
						'{S/ft:unix}'
						'{s/ft-ps: }'
						'{S/pc: 100%}'
						'{s/pc-ln: }'
						'{S/ln:  }'
						'{S/lN:  1}'
						'{S/cl::1  }',
						base_attrs
					),
				},
			),
			'env': updated(env, LANG='en_US.UTF-8'),
		},
	)

	ret = True

	for additional_test_args in testss:
		test_args = {
			'cmd': vim_exe,
			'dim': dim,
			'args': args,
			'env': env,
			'cwd': TEST_ROOT,
			'attempts': 1,
		}
		test_args.update(additional_test_args)
		test_args['tests'][0].setdefault('prep_cb', lambda p: sleep(1.5))
		for test in test_args['tests']:
			test.setdefault('row', dim.rows - 2)
		ret = ret and do_terminal_tests(**test_args)

	return ret


if __name__ == '__main__':
	if main():
		raise SystemExit(0)
	else:
		raise SystemExit(1)
