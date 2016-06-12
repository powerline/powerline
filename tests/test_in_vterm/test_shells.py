#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import os
import re
import json
import logging
import codecs

from time import sleep
from difflib import ndiff

from tests.lib.terminal import ExpectProcess, coltext_to_shesc, coltext_join


logger = logging.getLogger('test_shells')


VTERM_TEST_DATA_DIR = os.path.abspath(os.path.dirname(__file__))
VTERM_DATA_DIR = os.path.join(VTERM_TEST_DATA_DIR, 'shell')

VTERM_TEST_BASE = 'vterm_shell'
VTERM_TEST_DIR = os.path.abspath('tests/' + VTERM_TEST_BASE)
VTERM_TEST_BASE = VTERM_TEST_BASE.encode('ascii')
POWERLINE_PROMPT_RE = re.compile(b'\x1B\\[0m')
TCSH_CONTINUATION_RE = re.compile(b'\\?')

PID_FILE = os.path.join(VTERM_TEST_DIR, '3rd', 'pid')


def test_expected_result():
	pass


ABOVE_LEFT = json.dumps([{
	'left': [
		{
			'function': 'powerline.segments.common.env.environment',
			'args': {'variable': 'DISPLAYED_ENV_VAR'},
		}
	],
}])

ABOVE_FULL = json.dumps([{
	'left': [
		{
			'type': 'string',
			'name': 'background',
			'draw_hard_divider': False,
			'width': 'auto',
		},
	],
	'right': [
		{
			'function': 'powerline.segments.common.env.environment',
			'args': {'variable': 'DISPLAYED_ENV_VAR'},
		},
	],
}])

CONT_RIGHT = json.dumps([{
	'type': 'string',
	'name': 'background',
	'contents': 'CONT',
}])

SHELLS_INPUT_PIECES = {
	'functions': [
		'set_theme_option() {\n',
		'	export POWERLINE_THEME_OVERRIDES="$POWERLINE_THEME_OVERRIDES;$1=$2"\n',
		'	powerline-reload-config\n',
		'}\n',
		'unset_last_theme_option() {\n',
		'	export POWERLINE_THEME_OVERRIDES="${POWERLINE_THEME_OVERRIDES%;*}"\n',
		'	powerline-reload-config\n',
		'}\n',
		'set_theme() {\n',
		'	export POWERLINE_CONFIG_OVERRIDES="ext.shell.theme=$1"\n',
		'	powerline-reload-config\n',
		'}\n',
		'leftonly_theme() {\n',
		'	set_theme default_leftonly\n',
		'}\n',
		'default_theme() {\n',
		'	set_theme default\n',
		'}\n',
		'set_above_left() {\n',
		'	set_theme_option default_leftonly.segments.above "$ABOVE_LEFT"\n',
		'}\n',
		'set_above_full() {\n',
		'	set_theme_option default_leftonly.segments.above "$ABOVE_FULL"\n',
		'}\n',
		'set_dabc_div() {\n',
		'	set_theme_option default_leftonly.dividers.left.hard \\$ABC\n',
		'}\n',
		'set_virtual_env() {\n',
		'	export VIRTUAL_ENV="$HOME/.virtenvs/$1"\n',
		'}\n',
		'unset_virtual_env() {\n',
		'	export VIRTUAL_ENV=\n',
		'}\n',
		'bgrun() {\n',
		'	bgscript.sh & waitpid.sh\n',
		'}\n',
		'bgkill() {\n',
		'	kill `cat pid`\n',
		'	sleep 1.1\n',
		'}\n',
		'set_displayed_env_var() {\n',
		'	export DISPLAYED_ENV_VAR="$1"\n',
		'}\n',
		'unset_displayed_env_var() {\n',
		'	unset DISPLAYED_ENV_VAR\n',
		'}\n',
		'vi_bindings() {\n',
		'	bindkey -v\n',
		'}\n',
		'emacs_bindings() {\n',
		'	bindkey -e\n',
		'}\n',
		'ret() {\n',
		'	return $1\n',
		'}\n',
	],
	'fish_functions': [
		'function set_theme_option\n',
		'	set -g -x POWERLINE_THEME_OVERRIDES "$POWERLINE_THEME_OVERRIDES;$argv[1]=$argv[2]"\n',
		'end\n',
		'function unset_last_theme_option\n',
		'	set -g -x POWERLINE_THEME_OVERRIDES (echo -n "$POWERLINE_THEME_OVERRIDES" | sed -r -e \'s/^(.*);.*$/\\1/\')\n',
		'end\n',
		'function set_theme\n',
		'	set -g -x POWERLINE_CONFIG_OVERRIDES "ext.shell.theme=$argv"\n',
		'end\n',
		'function leftonly_theme\n',
		'	set_theme default_leftonly\n',
		'end\n',
		'function default_theme\n',
		'	set_theme default\n',
		'end\n',
		'function set_above_left\n',
		'	set_theme_option default_leftonly.segments.above "$ABOVE_LEFT"\n',
		'end\n',
		'function set_above_full\n',
		'	set_theme_option default_leftonly.segments.above "$ABOVE_FULL"\n',
		'end\n',
		'function set_dabc_div\n',
		'	set_theme_option default_leftonly.dividers.left.hard \\$ABC\n',
		'end\n',
		'function set_virtual_env\n',
		'	set -g -x VIRTUAL_ENV "$HOME/.virtenvs/$argv"\n',
		'end\n',
		'function unset_virtual_env\n',
		'	set -g -x -e VIRTUAL_ENV\n',
		'end\n',
		'function bgrun\n',
		'	bgscript.sh & waitpid.sh\n',
		'end\n',
		'function bgkill\n',
		'	kill (cat pid)\n',
		'	sleep 1.1\n',
		'end\n',
		'function set_displayed_env_var\n',
		'	set -g -x DISPLAYED_ENV_VAR "$argv"\n',
		'end\n',
		'function unset_displayed_env_var\n',
		'	set -g -x -e DISPLAYED_ENV_VAR\n',
		'end\n',
		'function vi_bindings\n',
		'	set -g fish_key_bindings fish_vi_key_bindings\n',
		'end\n',
		'function emacs_bindings\n',
		'	set -g fish_key_bindings fish_default_key_bindings\n',
		'end\n',
		'function ret\n',
		'	return $argv\n',
		'end\n',
	],
	'rc_functions': [
		'fn set_theme_option {\n',
		'	POWERLINE_THEME_OVERRIDES = $POWERLINE_THEME_OVERRIDES\';\'$1\'=\'$2\n',
		'}\n',
		'fn unset_last_theme_option {\n',
		'	POWERLINE_THEME_OVERRIDES = ``() {echo -n $POWERLINE_THEME_OVERRIDES | sed -r -e \'s/^(.*);.*$/\\1/\'}\n',
		'}\n',
		'fn set_theme {\n',
		'	POWERLINE_CONFIG_OVERRIDES = \'ext.shell.theme=\'$1\n',
		'}\n',
		'fn leftonly_theme {\n',
		'	set_theme default_leftonly\n',
		'}\n',
		'fn default_theme {\n',
		'	set_theme default\n',
		'}\n',
		'fn set_above_left {\n',
		'	set_theme_option default_leftonly.segments.above $ABOVE_LEFT\n',
		'}\n',
		'fn set_above_full {\n',
		'	set_theme_option default_leftonly.segments.above $ABOVE_FULL\n',
		'}\n',
		'fn set_dabc_div {\n',
		'	set_theme_option default_leftonly.dividers.left.hard \'$ABC\'\n',
		'}\n',
		'fn set_virtual_env {\n',
		'	VIRTUAL_ENV = $HOME\'.virtenvs/\'$1\n'
		'}\n',
		'fn unset_virtual_env {\n',
		'	VIRTUAL_ENV = ()\n'
		'}\n',
		'fn bgrun {\n',
		'	bgscript.sh & waitpid.sh\n',
		'}\n',
		'fn bgkill {\n',
		'	kill `{cat pid}\n',
		'	sleep 1.1\n',
		'}\n',
		'fn set_displayed_env_var {\n',
		'	DISPLAYED_ENV_VAR = $1\n',
		'}\n',
		'fn unset_displayed_env_var {\n',
		'	DISPLAYED_ENV_VAR = ()\n',
		'}\n',
		'fn ret {\n',
		'	return $1\n',
		'}\n',
	],
	'tcsh_functions': [
		'set D=\'$\'\n',
		'alias unset_last_theme_option \'setenv POWERLINE_THEME_OVERRIDES "`sh -c \'\\\'\'echo -n "${D}POWERLINE_THEME_OVERRIDES"\'\\\'\' | sed -r -e \'\\\'\'s/^(.*);.*$D/\\1/;s/[\\x22$D]/\\\\0/g\'\\\'\'`"\'\n',
		'alias leftonly_theme \'setenv POWERLINE_CONFIG_OVERRIDES "ext.shell.theme=default_leftonly"\'\n',
		'alias default_theme \'setenv POWERLINE_CONFIG_OVERRIDES "ext.shell.theme=default"\'\n',
		'alias set_above_left \'setenv POWERLINE_THEME_OVERRIDES $POWERLINE_THEME_OVERRIDES:q";default_leftonly.segments.above="$ABOVE_LEFT:q\'\n',
		'alias set_above_full \'setenv POWERLINE_THEME_OVERRIDES $POWERLINE_THEME_OVERRIDES:q";default_leftonly.segments.above="$ABOVE_FULL:q\'\n',
		'alias set_dabc_div \'setenv POWERLINE_THEME_OVERRIDES $POWERLINE_THEME_OVERRIDES:q\'\\\'\';default_leftonly.dividers.left.hard=$ABC\'\\\'\'\'\n',
		'alias set_virtual_env \'setenv VIRTUAL_ENV\'\n',
		'alias unset_virtual_env \'unsetenv VIRTUAL_ENV\'\n',
		'alias bgrun \'bgscript.sh & waitpid.sh\'\n',
		'alias bgkill \'kill `cat pid`; sleep 1.1s\'\n',
		'alias set_displayed_env_var \'setenv DISPLAYED_ENV_VAR\'\n',
		'alias unset_displayed_env_var \'unsetenv DISPLAYED_ENV_VAR\'\n',
		'alias ret "sh -c \'exit \\$1\' -"\n',
	],
	'dash_bgkill_function': [
		'bgkill() {\n',
		'	kill `cat pid`\n',
		'	sleep 1.1\n',
		# Needed to collect zombie process, otherwise it will be shown as 
		# a background job forever.
		'	jobs >/dev/null\n',
		'}\n'
	],
	'default_theme_options': [
		'set_theme_option default_leftonly.segment_data.hostname.display false\n',
		'set_theme_option default.segment_data.hostname.display false\n',
		'set_theme_option default_leftonly.segment_data.user.display false\n',
		'set_theme_option default.segment_data.user.display false\n',
	],
	'tcsh_default_theme_options': [
		'setenv POWERLINE_THEME_OVERRIDES $POWERLINE_THEME_OVERRIDES:q";default_leftonly.segment_data.hostname.display=false"\n',
		'setenv POWERLINE_THEME_OVERRIDES $POWERLINE_THEME_OVERRIDES:q";default.segment_data.hostname.display=false"\n',
		'setenv POWERLINE_THEME_OVERRIDES $POWERLINE_THEME_OVERRIDES:q";default_leftonly.segment_data.user.display=false"\n',
		'setenv POWERLINE_THEME_OVERRIDES $POWERLINE_THEME_OVERRIDES:q";default.segment_data.user.display=false"\n',
	],
	'fish_default_env': [
		'unset_virtual_env\n',
		'set -g -x POWERLINE\n',
		'set fish_function_path "$PWD/../../../powerline/bindings/fish" $fish_function_path\n'
	],
	'left_theme': ['leftonly_theme\n'],

	'default_input': [
		'cd .git\n',
		'cd ..\n',
		'set_virtual_env some-virtual-environment\n',
		'unset_virtual_env\n',
		'bgrun\n',
		'false\n',
		'bgkill\n',
		'echo \'\\\n',
		'abc\\\n',
		'def\\\n',
		'\'\n',
		'cd \'%%\'\n',
		'cd ../\'\\[\\]\'\n',
		'cd ../\'#[bold]\'\n',
		'cd ../\'(echo)\'\n',
		'cd ../\'$(echo)\'\n',
		'cd ../\'`echo`\'\n',
		'cd ../$DIR1\n',
		'cd ../$DIR2\n',
		'cd ../$DIR3\n',
		'cd ..\n',
		'set_above_left\n',
		'set_displayed_env_var foo\n',
		'unset_displayed_env_var\n',
		'unset_last_theme_option\n',
		'set_above_full\n',
		'set_displayed_env_var foo\n',
		'unset_displayed_env_var\n',
		'unset_last_theme_option\n',
		'set_dabc_div\n',
		'false\n',
		'unset_last_theme_option\n',
	],
	'vi_input': [
		'vi_bindings ; set_theme default\n',
		'\x1B',
		'a',
		'emacs_bindings ; set_theme default_leftonly\n',
	],
	'select_input': [
		'select abc in def ghi jkl\n',
		'do\n',
		'	echo $abc\n',
		'	break\n',
		'done\n',
		'1\n',
	],
	'rc_continuation_input': [
		'echo `{\n',
		'	echo Continuation!\n',
		'}\n',
	],
	'left_ps1_input': [
		'set_theme default\n',
		'false\n',
		'ret 1 | ret 0\n',
		'set_theme default_leftonly\n',
	],
	'left_ps2_input': [
		'set_theme_option continuation.segments.right "$CONT_RIGHT"\n',
		'echo \'\n',
		'abc\'\n',
		'unset_last_theme_option\n',
	],
}

shells = {
	'bash': {
		'args': ['--norc', '--noprofile', '-i'],
		'default_prompt': re.compile(b'^bash.*\\$', re.MULTILINE),
		'preinput': (
			SHELLS_INPUT_PIECES['functions']
			+ SHELLS_INPUT_PIECES['default_theme_options']
			+ SHELLS_INPUT_PIECES['left_theme']
			+ ['source ../../../powerline/bindings/bash/powerline.sh\n']
		),
		'input': (
			SHELLS_INPUT_PIECES['default_input']
			+ SHELLS_INPUT_PIECES['select_input']
		),
	},
	'zsh': {
		'args': ['-f', '-i'],
		'default_prompt': re.compile(b'^.*%', re.MULTILINE),
		'preinput': (
			[
				'unset HOME\n',
				'unsetopt promptsp transientrprompt\n',
				'setopt interactivecomments autonamedirs\n',
			]
			+ SHELLS_INPUT_PIECES['functions']
			+ SHELLS_INPUT_PIECES['default_theme_options']
			+ SHELLS_INPUT_PIECES['left_theme']
			+ ['source ../../../powerline/bindings/zsh/powerline.zsh\n']
		),
		'input': (
			SHELLS_INPUT_PIECES['default_input']
			+ SHELLS_INPUT_PIECES['vi_input']
			+ SHELLS_INPUT_PIECES['select_input']
			+ SHELLS_INPUT_PIECES['left_ps1_input']
			+ SHELLS_INPUT_PIECES['left_ps2_input']
		),
	},
	'fish': {
		'args': ['-i'],
		'default_prompt': re.compile(
			b'^.*@.* .*' + VTERM_TEST_BASE + b'>', re.MULTILINE),
		'preinput': (
			SHELLS_INPUT_PIECES['fish_functions']
			+ SHELLS_INPUT_PIECES['default_theme_options']
			+ SHELLS_INPUT_PIECES['fish_default_env']
			+ SHELLS_INPUT_PIECES['left_theme']
			+ [
				'while jobs | grep fish_update_completions\n',
				'	sleep 1\n',
				'end\n',
			]
			+ ['powerline-setup\n']
		),
		'input': (
			SHELLS_INPUT_PIECES['default_input']
			+ SHELLS_INPUT_PIECES['vi_input']
			+ SHELLS_INPUT_PIECES['left_ps1_input']
		),
	},
	'tcsh': {
		'args': ['-f', '-i'],
		'default_prompt': re.compile(b'^>', re.MULTILINE),
		'preinput': (
			SHELLS_INPUT_PIECES['tcsh_functions']
			+ SHELLS_INPUT_PIECES['left_theme']
			+ SHELLS_INPUT_PIECES['tcsh_default_theme_options']
			+ ['source ../../../powerline/bindings/tcsh/powerline.tcsh\n']
		),
		'input': (
			SHELLS_INPUT_PIECES['default_input']
		),
	},
	'busybox': {
		'args': ['ash', '-i'],
		'default_prompt': re.compile(
			b'^.*' + VTERM_TEST_BASE + b'\\$', re.MULTILINE),
		'preinput': (
			SHELLS_INPUT_PIECES['functions']
			+ SHELLS_INPUT_PIECES['default_theme_options']
			+ SHELLS_INPUT_PIECES['left_theme']
			+ ['source ../../../powerline/bindings/shell/powerline.sh\n']
		),
		'input': SHELLS_INPUT_PIECES['default_input'],
	},
	'mksh': {
		'args': ['-i'],
		'default_prompt': re.compile(b'^\\$', re.MULTILINE),
		'preinput': (
			SHELLS_INPUT_PIECES['functions']
			+ SHELLS_INPUT_PIECES['default_theme_options']
			+ SHELLS_INPUT_PIECES['left_theme']
			+ ['source ../../../powerline/bindings/shell/powerline.sh\n']
		),
		'input': SHELLS_INPUT_PIECES['default_input'],
	},
	'dash': {
		'args': ['-i'],
		'default_prompt': re.compile(b'^\\$', re.MULTILINE),
		'preinput': (
			SHELLS_INPUT_PIECES['functions']
			+ SHELLS_INPUT_PIECES['dash_bgkill_function']
			+ SHELLS_INPUT_PIECES['default_theme_options']
			+ SHELLS_INPUT_PIECES['left_theme']
			+ ['. ../../../powerline/bindings/shell/powerline.sh\n']
		),
		'input': SHELLS_INPUT_PIECES['default_input'],
	},
	'rc': {
		'args': ['-p', '-i'],
		'default_prompt': re.compile(b'^;', re.MULTILINE),
		'preinput': (
			SHELLS_INPUT_PIECES['rc_functions']
			+ SHELLS_INPUT_PIECES['default_theme_options']
			+ SHELLS_INPUT_PIECES['left_theme']
			+ ['. ../../../powerline/bindings/rc/powerline.rc\n']
		),
		'input': (
			SHELLS_INPUT_PIECES['default_input']
			+ SHELLS_INPUT_PIECES['rc_continuation_input']
		),
	},
	'ipython': {
		'args': ['-mIPython'],
		'default_prompt': POWERLINE_PROMPT_RE,
		'preinput': [],
		'input': [
			'print ("foo")\n',
			'bool 42\n',
			'bool 44\n',
			'class Test(object):\n',
			'pass\n',
			'\n',
		],
	},
	'pdb_module': {
		'args': [
			'-mpowerline.bindings.pdb' + (
				'' if sys.version_info > (2, 6) else '.__main__'
			),
			os.path.join(VTERM_TEST_DATA_DIR, 'pdb-script.py'),
		],
		'default_prompt': POWERLINE_PROMPT_RE,
		'preinput': [],
		'input': ['s\n'] + (['\n'] * 80),
	},
	'pdb_subclass': {
		'args': [
			os.path.join(VTERM_TEST_DATA_DIR, 'pdb-main.py'),
		],
		'default_prompt': POWERLINE_PROMPT_RE,
		'preinput': [],
		'input': ['s\n'] + (['\n'] * 80),
	},
}


def find_last_nonempty_line(p, lastrow):
	for row in range(p.rows - 1, lastrow, -1):
		if p[row, 0].text:
			return row
	return lastrow


def print_screen(p):
	empty_lines_cnt = 0
	for line in p[Ellipsis, Ellipsis]:
		ctext = coltext_join(line)
		print(coltext_to_shesc(ctext))
		if ctext:
			empty_lines_cnt = 0
		else:
			empty_lines_cnt += 1
		if empty_lines_cnt > 3:
			break


def find_ok_file(sh, test_type, test_client):
	for fname in (
		'.'.join((sh, test_type, test_client, 'ok')),
		'.'.join((sh, test_type, 'ok')),
		'.'.join((sh, test_type == 'internal' and 'daemon' or test_type, 'ok')),
		'.'.join((sh, 'ok')),
		'.'.join(('shell', 'ok')),
	):
		full_fname = os.path.join(VTERM_DATA_DIR, fname)
		if os.path.exists(full_fname):
			return full_fname
	raise IOError('OK file not found')


MAX_ATTEMPTS = 3
ECHO_LINE_RE = re.compile('^\x1B\\[38;2;240;240;240;48;2;0;0;0m(.*?) *\x1B\\[m$')
PDB_SKIP_LINE_RE = re.compile('^\x1B\\[38;2;240;240;240;48;2;0;0;0m[^\x1B]*\x1B\\[m$')


def main(sh, test_type, test_client, attempts=MAX_ATTEMPTS):
	if attempts <= 0:
		return False
	print('Attempt %u' % (MAX_ATTEMPTS - attempts))
	vterm_path = os.path.join(VTERM_TEST_DIR, 'path')
	rows = 1024
	cols = 110

	shell_exe = sh

	if os.path.exists('tests/bot-ci/deps/libvterm/libvterm.so'):
		lib = 'tests/bot-ci/deps/libvterm/libvterm.so'
	else:
		lib = os.environ.get('POWERLINE_LIBVTERM', 'libvterm.so')

	p = ExpectProcess(
		lib=lib,
		rows=rows,
		cols=cols,
		cmd=shell_exe,
		args=shells[sh]['args'],
		cwd=os.path.join(VTERM_TEST_DIR, '3rd'),
		env={
			'LANG': 'en_US.UTF-8',
			'TERMINFO': os.path.join(VTERM_TEST_DIR, 'terminfo'),
			'TERM': 'st-256color',  # See test_tmux.py for explanations.
			'PATH': vterm_path,
			'SHELL': os.path.join(VTERM_TEST_DIR, 'path', 'bash'),
			'POWERLINE_CONFIG_PATHS': os.path.abspath('powerline/config_files'),
			'POWERLINE_COMMAND_ARGS': os.environ.get('POWERLINE_COMMAND_ARGS', ''),
			'POWERLINE_COMMAND': os.environ['POWERLINE_COMMAND'],
			'POWERLINE_THEME_OVERRIDES': os.environ.get('POWERLINE_THEME_OVERRIDES', ''),
			'POWERLINE_CONFIG_OVERRIDES': os.environ.get('POWERLINE_CONFIG_OVERRIDES', ''),
			'XDG_CONFIG_HOME': os.path.join(VTERM_TEST_DIR, 'empty_dir'),
			'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
			'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
			'ABOVE_LEFT': ABOVE_LEFT,
			'ABOVE_FULL': ABOVE_FULL,
			'CONT_RIGHT': CONT_RIGHT,
			'DIR1': os.environ['DIR1'],
			'DIR2': os.environ['DIR2'],
			'DIR3': os.environ['DIR3'],
			'POWERLINE_NO_ZSH_ZPYTHON': (
				'1'
				if sh == 'zsh' and test_client != 'internal'
				else ''
			),
			'POWERLINE_SHELL_SELECT': ('1' if test_client != 'render' else ''),
			'POWERLINE_SHELL_CONTINUATION': (
				'1' if test_client != 'render' else ''),
		},
		init_input=''.join(shells[sh]['preinput']),
		# Long timeout is needed for waiting for fish_update_completions.
		init_input_wait_timeout=(3 if sh == 'fish' else 1),
	)
	p.start()
	line = None
	stage = 'init'
	output1 = b''
	output2 = b''
	try:
		output1 = p.waitfor(POWERLINE_PROMPT_RE, timeout=10)
		while p.read():
			sleep(0.1)
		stage = 'init-nl'
		p.write('\n')
		output2 = p.waitfor(POWERLINE_PROMPT_RE)
		while p.read():
			sleep(0.1)
		stage = 'input'
		lastrow = 0
		screen = []
		old_cursor = p.cursor
		# Fish needs time to highlight input
		read_timeout = 0.5 if sh == 'fish' else 0.005
		for i, line in enumerate(shells[sh]['input']):
			p.write(line)
			if not line.endswith('\n') or i == 0:
				p.waitfor(POWERLINE_PROMPT_RE, timeout=2)
			else:
				is_bgkill = (line == 'bgkill\n')
				p.waitforcursor(
					(lambda cursor: (cursor.col >= 2
					                 and cursor.row > old_cursor.row)),
					timeout=(3 if is_bgkill else 2)
				)
			while p.read():
				sleep(read_timeout)
			old_cursor = p.cursor
			newlastrow = find_last_nonempty_line(p, lastrow)
			for row in range(lastrow, newlastrow + 1):
				screen_line = coltext_to_shesc(coltext_join(p[row, Ellipsis]))
				if sh.startswith('pdb'):
					if PDB_SKIP_LINE_RE.match(screen_line):
						continue
				else:
					# Echo lines sometimes leak in, sometimes not. Remove them.
					echo_match = ECHO_LINE_RE.match(screen_line)
					if echo_match and echo_match.group(1) == line.rstrip('\n'):
						continue
				screen.append(screen_line + '\n')
			lastrow = newlastrow
		if not screen[0]:
			screen.pop(0)
		try:
			with codecs.open(PID_FILE, 'r', encoding='ascii') as fd:
				pid = re.compile(fd.read().strip() + ' *')
				screen = [
					pid.subn('PID', i)[0] for i in screen
				]
		except IOError:
			pass
		else:
			os.unlink(PID_FILE)
		stage = 'check'
		try:
			ok_fname = find_ok_file(sh, test_type, test_client)
		except IOError:
			with codecs.open(os.path.join(VTERM_DATA_DIR, '.'.join((sh, test_type, test_client, 'ok'))), 'w', encoding='utf-8') as fd:
				fd.writelines(screen)
		else:
			with codecs.open(ok_fname, 'r', encoding='utf-8') as fd:
				ok_screen = list(fd)
			if ok_screen == screen:
				return True
			else:
				print('screens differ:')
				print(''.join(ndiff(ok_screen, screen)))
				print('Screen:')
				print_screen(p)
				print('Init output:')
				for line in output1.split(b'\n'):
					print(repr(line))
				print('NL output:')
				for line in output2.split(b'\n'):
					print(repr(line))
				print('Unread output:')
				for line in p.read().split(b'\n'):
					print(repr(line))
				out_fname = os.path.join(
					VTERM_TEST_DIR,
					'.'.join((sh, test_type, test_client, 'ok', str(attempts)))
				)
				with codecs.open(out_fname, 'w', encoding='utf-8') as fd:
					fd.writelines(screen)
	except Exception as e:
		logging.exception('Exception %r on line %r, stage %s', e, line, stage)
		print('Screen:')
		print_screen(p)
		print('Init output:')
		print(output1.decode('utf-8'))
		print('NL output:')
		print(output2.decode('utf-8'))
		print('Unread output:')
		print(p.read().decode('utf-8'))
	finally:
		p.close()
		p.join()
	return main(
		sh=sh, test_type=test_type, test_client=test_client,
		attempts=(attempts - 1)
	)


if __name__ == '__main__':
	if main(*sys.argv[1:]):
		raise SystemExit(0)
	else:
		raise SystemExit(1)
