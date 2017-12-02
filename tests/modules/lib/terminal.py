# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import threading
import os

from time import sleep
from itertools import groupby
from signal import SIGKILL
from difflib import ndiff

import pexpect

from powerline.lib.unicode import u

from tests.modules.lib.vterm import VTerm, Dimensions


class MutableDimensions(object):
	def __init__(self, rows, cols):
		super(MutableDimensions, self).__init__()
		self._list = [rows, cols]

	def __getitem__(self, idx):
		return self._list[idx]

	def __setitem__(self, idx, val):
		self._list[idx] = val

	def __iter__(self):
		return iter(self._list)

	def __len__(self):
		return 2

	def __nonzero__(self):
		return True

	__bool__ = __nonzero__

	rows = property(
		fget = lambda self: self._list[0],
		fset = lambda self, val: self._list.__setitem__(0, val),
	)
	cols = property(
		fget = lambda self: self._list[1],
		fset = lambda self, val: self._list.__setitem__(1, val),
	)


class ExpectProcess(threading.Thread):
	def __init__(self, lib, dim, cmd, args, cwd=None, env=None):
		super(ExpectProcess, self).__init__()
		self.vterm = VTerm(lib, dim)
		self.lock = threading.Lock()
		self.dim = Dimensions(*dim)
		self.cmd = cmd
		self.args = args
		self.cwd = cwd
		self.env = env
		self.buffer = []
		self.child_lock = threading.Lock()
		self.shutdown_event = threading.Event()
		self.started_event = threading.Event()

	def run(self):
		with self.child_lock:
			child = pexpect.spawn(self.cmd, self.args, cwd=self.cwd,
			                      env=self.env)
			sleep(0.5)
			child.setwinsize(self.dim.rows, self.dim.cols)
			sleep(0.5)
			self.child = child
			self.started_event.set()
		status = None
		while status is None and not self.shutdown_event.is_set():
			try:
				with self.child_lock:
					s = child.read_nonblocking(size=1024, timeout=0)
					status = child.status
			except pexpect.TIMEOUT:
				pass
			except pexpect.EOF:
				break
			else:
				with self.lock:
					self.vterm.push(s)
					self.buffer.append(s)

		if status is None:
			child.kill(SIGKILL)

	def kill(self):
		self.shutdown_event.set()

	def resize(self, dim):
		with self.child_lock:
			self.dim = Dimensions(*dim)
			self.child.setwinsize(self.dim.rows, self.dim.cols)
			self.vterm.resize(self.dim)

	def __getitem__(self, position):
		with self.lock:
			return self.vterm.vtscreen[position]

	def read(self):
		with self.lock:
			ret = b''.join(self.buffer)
			del self.buffer[:]
			return ret

	def send(self, data):
		with self.child_lock:
			self.child.send(data)

	def get_highlighted_text(self, text, attrs, default_props=(),
	                         use_escapes=False):
		ret = []
		new_attrs = attrs.copy()
		for cell_properties, segment_text in text:
			if use_escapes:
				escapes = ('\033[38;2;{0};{1};{2};48;2;{3};{4};{5}'.format(
					*(cell_properties[0] + cell_properties[1]))) + (
						';1' if cell_properties[2] else ''
					) + (
						';3' if cell_properties[3] else ''
					) + (
						';4' if cell_properties[4] else ''
					) + 'm'
				ret.append(escapes + segment_text + '\033[0m')
			else:
				segment_text = segment_text.translate({'{': '{{', '}': '}}'})
				if cell_properties not in new_attrs:
					new_attrs[cell_properties] = len(new_attrs) + 1
				props_name = new_attrs[cell_properties]
				if props_name in default_props:
					ret.append(segment_text)
				else:
					ret.append('{' + str(props_name) + ':' + segment_text + '}')
		return ''.join(ret), new_attrs

	def get_row(self, row, attrs, default_props=(), use_escapes=False):
		with self.lock:
			return self.get_highlighted_text((
				(key, ''.join((cell.text for cell in subline)))
				for key, subline in groupby((
					self.vterm.vtscreen[row, col]
					for col in range(self.dim.cols)
				), lambda cell: cell.cell_properties_key)
			), attrs, default_props, use_escapes)

	def get_screen(self, attrs, default_props=(), use_escapes=False):
		lines = []
		for row in range(self.dim.rows):
			line, attrs = self.get_row(row, attrs, default_props, use_escapes)
			lines.append(line)
		return '\n'.join(lines), attrs


def test_expected_result(p, test, last_attempt, last_attempt_cb, attempts):
	debugging_tests = not not os.environ.get('_POWERLINE_DEBUGGING_TESTS')
	expected_text, attrs = test['expected_result']
	result = None
	while attempts:
		if 'row' in test:
			row = test['row']
		else:
			row = p.dim.rows - 1
			while row >= 0 and not p[row, 0].text:
				row -= 1
			if row < 0:
				row = 0
		actual_text, all_attrs = p.get_row(row, attrs)
		if actual_text == expected_text:
			return True
		attempts -= 1
		print('Actual result does not match expected for row {0}. Attempts left: {1}.'.format(
			row, attempts))
		sleep(2)
	print('Result (row {0}):'.format(row))
	print(actual_text)
	print('Expected:')
	print(expected_text)
	print('Attributes:')
	for v, k in sorted(
		((v, k) for k, v in all_attrs.items()),
		key=(lambda t: '%02u'.format(t[0]) if isinstance(t[0], int) else t[0]),
	):
		print('{k!r}: {v!r},'.format(v=v, k=k))
	print('Screen:')
	screen, screen_attrs = p.get_screen(attrs, use_escapes=debugging_tests)
	print(screen)
	print(screen_attrs)
	print('_' * 80)
	print('Diff:')
	print('=' * 80)
	print(''.join((
		u(line) for line in ndiff([actual_text + '\n'], [expected_text + '\n']))
	))
	if last_attempt and last_attempt_cb:
		last_attempt_cb()
	return False


ENV_BASE = {
	# Reasoning:
	# 1. vt* TERMs (used to be vt100 here) make tmux-1.9 use different and
	#    identical colors for inactive windows. This is not like tmux-1.6: 
	#    foreground color is different from separator color and equal to (0, 
	#    102, 153) for some reason (separator has correct color). tmux-1.8 is 
	#    fine, so are older versions (though tmux-1.6 and tmux-1.7 do not have 
	#    highlighting for previously active window) and my system tmux-1.9a.
	# 2. screen, xterm and some other non-256color terminals both have the same
	#    issue and make libvterm emit complains like `Unhandled CSI SGR 3231`.
	# 3. screen-256color, xterm-256color and other -256color terminals make
	#    libvterm emit complains about unhandled escapes to stderr.
	# 4. `st-256color` does not have any of the above problems, but it may be
	#    not present on the target system because it is installed with 
	#    x11-terms/st and not with sys-libs/ncurses.
	#
	# For the given reasons decision was made: to fix tmux-1.9 tests and not 
	# make libvterm emit any data to stderr st-256color $TERM should be used, up 
	# until libvterm has its own terminfo database entry (if it ever will). To 
	# make sure that relevant terminfo entry is present on the target system it 
	# should be distributed with powerline test package. To make distribution 
	# not require modifying anything outside of powerline test directory 
	# TERMINFO variable is set.
	#
	# This fix propagates to non-tmux vterm tests just in case.
	'TERM': 'st-256color',
	# Also $TERMINFO definition in get_env

	'POWERLINE_CONFIG_PATHS': os.path.abspath('powerline/config_files'),
	'POWERLINE_COMMAND': 'powerline-render',
	'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
	'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
}


def get_env(vterm_path, test_dir, *args, **kwargs):
	env = ENV_BASE.copy()
	env.update({
		'TERMINFO': os.path.join(test_dir, 'terminfo'),
		'PATH': vterm_path,
		'SHELL': os.path.join(vterm_path, 'bash'),
	})
	env.update(*args, **kwargs)
	return env


def do_terminal_tests(tests, cmd, dim, args, env, suite, cwd=None, fin_cb=None,
                      last_attempt_cb=None, attempts=None):
	debugging_tests = not not os.environ.get('_POWERLINE_DEBUGGING_TESTS')
	default_attempts = 2 if debugging_tests else 3
	if attempts is None:
		attempts = default_attempts
	lib = os.environ.get('POWERLINE_LIBVTERM')
	if not lib:
		if os.path.exists('tests/bot-ci/deps/libvterm/libvterm.so'):
			lib = 'tests/bot-ci/deps/libvterm/libvterm.so'
		else:
			lib = 'libvterm.so'

	while attempts:
		try:
			p = ExpectProcess(
				lib=lib,
				dim=dim,
				cmd=cmd,
				args=args,
				cwd=cwd,
				env=env,
			)
			p.start()
			p.started_event.wait()

			ret = True

			for i, test in enumerate(tests):
				with suite.test(test.get('name', 'test_{0}'.format(i)),
				                attempts - 1) as ptest:
					try:
						test_prep = test['prep_cb']
					except KeyError:
						pass
					else:
						test_prep(p)
					test_result = test_expected_result(
						p, test, attempts == 0, last_attempt_cb,
						test.get('attempts', default_attempts)
					)
					if not test_result:
						ptest.fail('Result does not match expected')
				ret = ret and test_result

			if ret:
				return ret
		finally:
			if fin_cb:
				fin_cb(p=p, cmd=cmd, env=env)
			p.kill()
			p.join(10)
			assert(not p.isAlive())

		attempts -= 1

	return False
