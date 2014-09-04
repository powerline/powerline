# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import os

from functools import partial

from powerline.segments import shell, tmux, common
from powerline.lib.vcs import get_fallback_create_watcher

import tests.vim as vim_module

from tests.lib import Args, urllib_read, replace_attr, new_module, replace_module_module, replace_env, Pl
from tests import TestCase, SkipTest


def get_dummy_guess(**kwargs):
	if 'directory' in kwargs:
		def guess(path, create_watcher):
			return Args(branch=lambda: os.path.basename(path), **kwargs)
	else:
		def guess(path, create_watcher):
			return Args(branch=lambda: os.path.basename(path), directory=path, **kwargs)
	return guess


class TestShell(TestCase):
	def test_last_status(self):
		pl = Pl()
		segment_info = {'args': Args(last_exit_code=10)}
		self.assertEqual(shell.last_status(pl=pl, segment_info=segment_info), [
			{'contents': '10', 'highlight_group': ['exit_fail']}
		])
		segment_info['args'].last_exit_code = 0
		self.assertEqual(shell.last_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_exit_code = None
		self.assertEqual(shell.last_status(pl=pl, segment_info=segment_info), None)

	def test_last_pipe_status(self):
		pl = Pl()
		segment_info = {'args': Args(last_pipe_status=[])}
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_pipe_status = [0, 0, 0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_pipe_status = [0, 2, 0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '0', 'highlight_group': ['exit_success'], 'draw_inner_divider': True},
			{'contents': '2', 'highlight_group': ['exit_fail'], 'draw_inner_divider': True},
			{'contents': '0', 'highlight_group': ['exit_success'], 'draw_inner_divider': True}
		])

	def test_jobnum(self):
		pl = Pl()
		segment_info = {'args': Args(jobnum=0)}
		self.assertEqual(shell.jobnum(pl=pl, segment_info=segment_info), None)
		self.assertEqual(shell.jobnum(pl=pl, segment_info=segment_info, show_zero=False), None)
		self.assertEqual(shell.jobnum(pl=pl, segment_info=segment_info, show_zero=True), '0')
		segment_info = {'args': Args(jobnum=1)}
		self.assertEqual(shell.jobnum(pl=pl, segment_info=segment_info), '1')
		self.assertEqual(shell.jobnum(pl=pl, segment_info=segment_info, show_zero=False), '1')
		self.assertEqual(shell.jobnum(pl=pl, segment_info=segment_info, show_zero=True), '1')

	def test_continuation(self):
		pl = Pl()
		self.assertEqual(shell.continuation(pl=pl, segment_info={}), [{
			'contents': '',
			'width': 'auto',
			'highlight_group': ['continuation:current', 'continuation'],
		}])
		segment_info = {'parser_state': 'if cmdsubst'}
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_group': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'l',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, right_align=True), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_group': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'r',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=False), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_group': ['continuation'],
			},
			{
				'contents': 'cmdsubst',
				'draw_inner_divider': True,
				'highlight_group': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'l',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=False, right_align=True), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_group': ['continuation'],
				'width': 'auto',
				'align': 'r',
			},
			{
				'contents': 'cmdsubst',
				'draw_inner_divider': True,
				'highlight_group': ['continuation:current', 'continuation'],
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=True, right_align=True), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_group': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'r',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=True, right_align=True, renames={'if': 'IF'}), [
			{
				'contents': 'IF',
				'draw_inner_divider': True,
				'highlight_group': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'r',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=True, right_align=True, renames={'if': None}), [
			{
				'contents': '',
				'highlight_group': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'r',
			},
		])
		segment_info = {'parser_state': 'then then then cmdsubst'}
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info), [
			{
				'contents': 'then',
				'draw_inner_divider': True,
				'highlight_group': ['continuation'],
			},
			{
				'contents': 'then',
				'draw_inner_divider': True,
				'highlight_group': ['continuation'],
			},
			{
				'contents': 'then',
				'draw_inner_divider': True,
				'highlight_group': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'l',
			},
		])

	def test_cwd(self):
		new_os = new_module('os', path=os.path, sep='/')
		pl = Pl()
		cwd = [None]

		def getcwd():
			wd = cwd[0]
			if isinstance(wd, Exception):
				raise wd
			else:
				return wd

		segment_info = {'getcwd': getcwd, 'home': None}
		with replace_attr(shell, 'os', new_os):
			cwd[0] = '/abc/def/ghi/foo/bar'
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'abc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'def', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			segment_info['home'] = '/abc/def/ghi'
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			segment_info.update(shortened_path='~foo/ghi')
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '~foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_shortened_path=False), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			segment_info.pop('shortened_path')
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=3), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=3, shorten_home=False), [
				{'contents': '...', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1), [
				{'contents': '...', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, ellipsis='---'), [
				{'contents': '---', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, ellipsis=None), [
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True), [
				{'contents': '.../', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True, ellipsis='---'), [
				{'contents': '---/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True, ellipsis=None), [
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'fo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2, use_path_separator=True), [
				{'contents': '~/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'fo/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			cwd[0] = '/etc'
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_path_separator=False), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'etc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_path_separator=True), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'etc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			cwd[0] = '/'
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_path_separator=False), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_path_separator=True), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			ose = OSError()
			ose.errno = 2
			cwd[0] = ose
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2), [
				{'contents': '[not found]', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd'], 'draw_inner_divider': True}
			])
			cwd[0] = OSError()
			self.assertRaises(OSError, shell.cwd, pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2)
			cwd[0] = ValueError()
			self.assertRaises(ValueError, shell.cwd, pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2)

	def test_date(self):
		pl = Pl()
		with replace_attr(common, 'datetime', Args(now=lambda: Args(strftime=lambda fmt: fmt))):
			self.assertEqual(common.date(pl=pl), [{'contents': '%Y-%m-%d', 'highlight_group': ['date'], 'divider_highlight_group': None}])
			self.assertEqual(common.date(pl=pl, format='%H:%M', istime=True), [{'contents': '%H:%M', 'highlight_group': ['time', 'date'], 'divider_highlight_group': 'time:divider'}])


class TestTmux(TestCase):
	def test_attached_clients(self):
		def get_tmux_output(cmd, *args):
			if cmd == 'list-panes':
				return 'session_name\n'
			elif cmd == 'list-clients':
				return '/dev/pts/2: 0 [191x51 xterm-256color] (utf8)\n/dev/pts/3: 0 [191x51 xterm-256color] (utf8)'

		pl = Pl()
		with replace_attr(tmux, 'get_tmux_output', get_tmux_output):
			self.assertEqual(tmux.attached_clients(pl=pl), '2')
			self.assertEqual(tmux.attached_clients(pl=pl, minimum=3), None)


class TestCommon(TestCase):
	def test_hostname(self):
		pl = Pl()
		with replace_env('SSH_CLIENT', '192.168.0.12 40921 22') as segment_info:
			with replace_module_module(common, 'socket', gethostname=lambda: 'abc'):
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info), 'abc')
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True), 'abc')
			with replace_module_module(common, 'socket', gethostname=lambda: 'abc.mydomain'):
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info), 'abc.mydomain')
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info, exclude_domain=True), 'abc')
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True), 'abc.mydomain')
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True, exclude_domain=True), 'abc')
			segment_info['environ'].pop('SSH_CLIENT')
			with replace_module_module(common, 'socket', gethostname=lambda: 'abc'):
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info), 'abc')
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True), None)
			with replace_module_module(common, 'socket', gethostname=lambda: 'abc.mydomain'):
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info), 'abc.mydomain')
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info, exclude_domain=True), 'abc')
				self.assertEqual(common.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True, exclude_domain=True), None)

	def test_user(self):
		new_os = new_module('os', getpid=lambda: 1)

		class Process(object):
			def __init__(self, pid):
				pass

			def username(self):
				return 'def'

			if hasattr(common, 'psutil') and not callable(common.psutil.Process.username):
				username = property(username)

		new_psutil = new_module('psutil', Process=Process)
		pl = Pl()
		with replace_env('USER', 'def') as segment_info:
			common.username = False
			with replace_attr(common, 'os', new_os):
				with replace_attr(common, 'psutil', new_psutil):
					with replace_attr(common, '_geteuid', lambda: 5):
						self.assertEqual(common.user(pl=pl, segment_info=segment_info), [
							{'contents': 'def', 'highlight_group': ['user']}
						])
						self.assertEqual(common.user(pl=pl, segment_info=segment_info, hide_user='abc'), [
							{'contents': 'def', 'highlight_group': ['user']}
						])
						self.assertEqual(common.user(pl=pl, segment_info=segment_info, hide_user='def'), None)
					with replace_attr(common, '_geteuid', lambda: 0):
						self.assertEqual(common.user(pl=pl, segment_info=segment_info), [
							{'contents': 'def', 'highlight_group': ['superuser', 'user']}
						])

	def test_branch(self):
		pl = Pl()
		create_watcher = get_fallback_create_watcher()
		segment_info = {'getcwd': os.getcwd}
		branch = partial(common.branch, pl=pl, create_watcher=create_watcher)
		with replace_attr(common, 'guess', get_dummy_guess(status=lambda: None, directory='/tmp/tests')):
			with replace_attr(common, 'tree_status', lambda repo, pl: None):
				self.assertEqual(branch(segment_info=segment_info, status_colors=False), [
					{'highlight_group': ['branch'], 'contents': 'tests'}
				])
				self.assertEqual(branch(segment_info=segment_info, status_colors=True), [
					{'contents': 'tests', 'highlight_group': ['branch_clean', 'branch']}
				])
		with replace_attr(common, 'guess', get_dummy_guess(status=lambda: 'D  ', directory='/tmp/tests')):
			with replace_attr(common, 'tree_status', lambda repo, pl: 'D '):
				self.assertEqual(branch(segment_info=segment_info, status_colors=False), [
					{'highlight_group': ['branch'], 'contents': 'tests'}
				])
				self.assertEqual(branch(segment_info=segment_info, status_colors=True), [
					{'contents': 'tests', 'highlight_group': ['branch_dirty', 'branch']}
				])
				self.assertEqual(branch(segment_info=segment_info, status_colors=False), [
					{'highlight_group': ['branch'], 'contents': 'tests'}
				])
		with replace_attr(common, 'guess', lambda path, create_watcher: None):
			self.assertEqual(branch(segment_info=segment_info, status_colors=False), None)

	def test_cwd(self):
		new_os = new_module('os', path=os.path, sep='/')
		pl = Pl()
		cwd = [None]

		def getcwd():
			wd = cwd[0]
			if isinstance(wd, Exception):
				raise wd
			else:
				return wd

		segment_info = {'getcwd': getcwd, 'home': None}
		with replace_attr(common, 'os', new_os):
			cwd[0] = '/abc/def/ghi/foo/bar'
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'abc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'def', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			segment_info['home'] = '/abc/def/ghi'
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=3), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=3, shorten_home=False), [
				{'contents': '...', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1), [
				{'contents': '...', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, ellipsis='---'), [
				{'contents': '---', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, ellipsis=None), [
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True), [
				{'contents': '.../', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True, ellipsis='---'), [
				{'contents': '---/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True, ellipsis=None), [
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'fo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2, use_path_separator=True), [
				{'contents': '~/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'fo/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']}
			])
			cwd[0] = '/etc'
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, use_path_separator=False), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'etc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, use_path_separator=True), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'etc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			cwd[0] = '/'
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, use_path_separator=False), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, use_path_separator=True), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_group': ['cwd:current_folder', 'cwd']},
			])
			ose = OSError()
			ose.errno = 2
			cwd[0] = ose
			self.assertEqual(common.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2), [
				{'contents': '[not found]', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd'], 'draw_inner_divider': True}
			])
			cwd[0] = OSError()
			self.assertRaises(OSError, common.cwd, pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2)
			cwd[0] = ValueError()
			self.assertRaises(ValueError, common.cwd, pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2)

	def test_date(self):
		pl = Pl()
		with replace_attr(common, 'datetime', Args(now=lambda: Args(strftime=lambda fmt: fmt))):
			self.assertEqual(common.date(pl=pl), [{'contents': '%Y-%m-%d', 'highlight_group': ['date'], 'divider_highlight_group': None}])
			self.assertEqual(common.date(pl=pl, format='%H:%M', istime=True), [{'contents': '%H:%M', 'highlight_group': ['time', 'date'], 'divider_highlight_group': 'time:divider'}])

	def test_fuzzy_time(self):
		time = Args(hour=0, minute=45)
		pl = Pl()
		with replace_attr(common, 'datetime', Args(now=lambda: time)):
			self.assertEqual(common.fuzzy_time(pl=pl), 'quarter to one')
			time.hour = 23
			time.minute = 59
			self.assertEqual(common.fuzzy_time(pl=pl), 'round about midnight')
			time.minute = 33
			self.assertEqual(common.fuzzy_time(pl=pl), 'twenty-five to twelve')
			time.minute = 60
			self.assertEqual(common.fuzzy_time(pl=pl), 'twelve o\'clock')
			time.minute = 33
			self.assertEqual(common.fuzzy_time(pl=pl, unicode_text=False), 'twenty-five to twelve')
			time.minute = 60
			self.assertEqual(common.fuzzy_time(pl=pl, unicode_text=False), 'twelve o\'clock')
			time.minute = 33
			self.assertEqual(common.fuzzy_time(pl=pl, unicode_text=True), 'twenty‐five to twelve')
			time.minute = 60
			self.assertEqual(common.fuzzy_time(pl=pl, unicode_text=True), 'twelve o’clock')

	def test_external_ip(self):
		pl = Pl()
		with replace_attr(common, 'urllib_read', urllib_read):
			self.assertEqual(common.external_ip(pl=pl), [{'contents': '127.0.0.1', 'divider_highlight_group': 'background:divider'}])

	def test_uptime(self):
		pl = Pl()
		with replace_attr(common, '_get_uptime', lambda: 259200):
			self.assertEqual(common.uptime(pl=pl), [{'contents': '3d', 'divider_highlight_group': 'background:divider'}])
		with replace_attr(common, '_get_uptime', lambda: 93784):
			self.assertEqual(common.uptime(pl=pl), [{'contents': '1d 2h 3m', 'divider_highlight_group': 'background:divider'}])
			self.assertEqual(common.uptime(pl=pl, shorten_len=4), [{'contents': '1d 2h 3m 4s', 'divider_highlight_group': 'background:divider'}])
		with replace_attr(common, '_get_uptime', lambda: 65536):
			self.assertEqual(common.uptime(pl=pl), [{'contents': '18h 12m 16s', 'divider_highlight_group': 'background:divider'}])
			self.assertEqual(common.uptime(pl=pl, shorten_len=2), [{'contents': '18h 12m', 'divider_highlight_group': 'background:divider'}])
			self.assertEqual(common.uptime(pl=pl, shorten_len=1), [{'contents': '18h', 'divider_highlight_group': 'background:divider'}])

		def _get_uptime():
			raise NotImplementedError

		with replace_attr(common, '_get_uptime', _get_uptime):
			self.assertEqual(common.uptime(pl=pl), None)

	def test_weather(self):
		pl = Pl()
		with replace_attr(common, 'urllib_read', urllib_read):
			self.assertEqual(common.weather(pl=pl), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'CLOUDS '},
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 30.0}
			])
			self.assertEqual(common.weather(pl=pl, temp_coldest=0, temp_hottest=100), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'CLOUDS '},
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 0}
			])
			self.assertEqual(common.weather(pl=pl, temp_coldest=-100, temp_hottest=-50), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'CLOUDS '},
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 100}
			])
			self.assertEqual(common.weather(pl=pl, icons={'cloudy': 'o'}), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'o '},
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 30.0}
			])
			self.assertEqual(common.weather(pl=pl, icons={'partly_cloudy_day': 'x'}), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'x '},
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 30.0}
			])
			self.assertEqual(common.weather(pl=pl, unit='F'), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'CLOUDS '},
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '16°F', 'gradient_level': 30.0}
			])
			self.assertEqual(common.weather(pl=pl, unit='K'), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'CLOUDS '},
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '264K', 'gradient_level': 30.0}
			])
			self.assertEqual(common.weather(pl=pl, temp_format='{temp:.1e}C'), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'CLOUDS '},
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9.0e+00C', 'gradient_level': 30.0}
			])

	def test_system_load(self):
		pl = Pl()
		with replace_module_module(common, 'os', getloadavg=lambda: (7.5, 3.5, 1.5)):
			with replace_attr(common, '_cpu_count', lambda: 2):
				self.assertEqual(common.system_load(pl=pl), [
					{'contents': '7.5 ', 'highlight_group': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
					{'contents': '3.5 ', 'highlight_group': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 75.0},
					{'contents': '1.5', 'highlight_group': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 0}
				])
				self.assertEqual(common.system_load(pl=pl, format='{avg:.0f}', threshold_good=0, threshold_bad=1), [
					{'contents': '8 ', 'highlight_group': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
					{'contents': '4 ', 'highlight_group': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
					{'contents': '2', 'highlight_group': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 75.0}
				])

	def test_cpu_load_percent(self):
		pl = Pl()
		with replace_module_module(common, 'psutil', cpu_percent=lambda **kwargs: 52.3):
			self.assertEqual(common.cpu_load_percent(pl=pl), [{
				'contents': '52%',
				'gradient_level': 52.3,
				'highlight_group': ['cpu_load_percent_gradient', 'cpu_load_percent'],
			}])
			self.assertEqual(common.cpu_load_percent(pl=pl, format='{0:.1f}%'), [{
				'contents': '52.3%',
				'gradient_level': 52.3,
				'highlight_group': ['cpu_load_percent_gradient', 'cpu_load_percent'],
			}])

	def test_network_load(self):
		from time import sleep

		def gb(interface):
			return None

		f = [gb]

		def _get_bytes(interface):
			return f[0](interface)

		pl = Pl()

		with replace_attr(common, '_get_bytes', _get_bytes):
			common.network_load.startup(pl=pl)
			try:
				self.assertEqual(common.network_load(pl=pl, interface='eth0'), None)
				sleep(common.network_load.interval)
				self.assertEqual(common.network_load(pl=pl, interface='eth0'), None)
				while 'prev' not in common.network_load.interfaces.get('eth0', {}):
					sleep(0.1)
				self.assertEqual(common.network_load(pl=pl, interface='eth0'), None)

				l = [0, 0]

				def gb2(interface):
					l[0] += 1200
					l[1] += 2400
					return tuple(l)
				f[0] = gb2

				while not common.network_load.interfaces.get('eth0', {}).get('prev', (None, None))[1]:
					sleep(0.1)
				self.assertEqual(common.network_load(pl=pl, interface='eth0'), [
					{'divider_highlight_group': 'background:divider', 'contents': 'DL  1 KiB/s', 'highlight_group': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'background:divider', 'contents': 'UL  2 KiB/s', 'highlight_group': ['network_load_sent', 'network_load']},
				])
				self.assertEqual(common.network_load(pl=pl, interface='eth0', recv_format='r {value}', sent_format='s {value}'), [
					{'divider_highlight_group': 'background:divider', 'contents': 'r 1 KiB/s', 'highlight_group': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'background:divider', 'contents': 's 2 KiB/s', 'highlight_group': ['network_load_sent', 'network_load']},
				])
				self.assertEqual(common.network_load(pl=pl, recv_format='r {value}', sent_format='s {value}', suffix='bps', interface='eth0'), [
					{'divider_highlight_group': 'background:divider', 'contents': 'r 1 Kibps', 'highlight_group': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'background:divider', 'contents': 's 2 Kibps', 'highlight_group': ['network_load_sent', 'network_load']},
				])
				self.assertEqual(common.network_load(pl=pl, recv_format='r {value}', sent_format='s {value}', si_prefix=True, interface='eth0'), [
					{'divider_highlight_group': 'background:divider', 'contents': 'r 1 kB/s', 'highlight_group': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'background:divider', 'contents': 's 2 kB/s', 'highlight_group': ['network_load_sent', 'network_load']},
				])
				self.assertEqual(common.network_load(pl=pl, recv_format='r {value}', sent_format='s {value}', recv_max=0, interface='eth0'), [
					{'divider_highlight_group': 'background:divider', 'contents': 'r 1 KiB/s', 'highlight_group': ['network_load_recv_gradient', 'network_load_gradient', 'network_load_recv', 'network_load'], 'gradient_level': 100},
					{'divider_highlight_group': 'background:divider', 'contents': 's 2 KiB/s', 'highlight_group': ['network_load_sent', 'network_load']},
				])

				class ApproxEqual(object):
					def __eq__(self, i):
						return abs(i - 50.0) < 1

				self.assertEqual(common.network_load(pl=pl, recv_format='r {value}', sent_format='s {value}', sent_max=4800, interface='eth0'), [
					{'divider_highlight_group': 'background:divider', 'contents': 'r 1 KiB/s', 'highlight_group': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'background:divider', 'contents': 's 2 KiB/s', 'highlight_group': ['network_load_sent_gradient', 'network_load_gradient', 'network_load_sent', 'network_load'], 'gradient_level': ApproxEqual()},
				])
			finally:
				common.network_load.shutdown()

	def test_virtualenv(self):
		pl = Pl()
		with replace_env('VIRTUAL_ENV', '/abc/def/ghi') as segment_info:
			self.assertEqual(common.virtualenv(pl=pl, segment_info=segment_info), 'ghi')
			segment_info['environ'].pop('VIRTUAL_ENV')
			self.assertEqual(common.virtualenv(pl=pl, segment_info=segment_info), None)

	def test_environment(self):
		pl = Pl()
		variable = 'FOO'
		value = 'bar'
		with replace_env(variable, value) as segment_info:
			self.assertEqual(common.environment(pl=pl, segment_info=segment_info, variable=variable), value)
			segment_info['environ'].pop(variable)
			self.assertEqual(common.environment(pl=pl, segment_info=segment_info, variable=variable), None)

	def test_email_imap_alert(self):
		# TODO
		pass

	def test_now_playing(self):
		# TODO
		pass

	def test_battery(self):
		pl = Pl()

		def _get_capacity(pl):
			return 86

		with replace_attr(common, '_get_capacity', _get_capacity):
			self.assertEqual(common.battery(pl=pl), [{
				'contents': '86%',
				'highlight_group': ['battery_gradient', 'battery'],
				'gradient_level': 14,
			}])
			self.assertEqual(common.battery(pl=pl, format='{capacity:.2f}'), [{
				'contents': '0.86',
				'highlight_group': ['battery_gradient', 'battery'],
				'gradient_level': 14,
			}])
			self.assertEqual(common.battery(pl=pl, steps=7), [{
				'contents': '86%',
				'highlight_group': ['battery_gradient', 'battery'],
				'gradient_level': 14,
			}])
			self.assertEqual(common.battery(pl=pl, gamify=True), [
				{
					'contents': 'OOOO',
					'draw_inner_divider': False,
					'highlight_group': ['battery_full', 'battery_gradient', 'battery'],
					'gradient_level': 0
				},
				{
					'contents': 'O',
					'draw_inner_divider': False,
					'highlight_group': ['battery_empty', 'battery_gradient', 'battery'],
					'gradient_level': 100
				}
			])
			self.assertEqual(common.battery(pl=pl, gamify=True, full_heart='+', empty_heart='-', steps='10'), [
				{
					'contents': '++++++++',
					'draw_inner_divider': False,
					'highlight_group': ['battery_full', 'battery_gradient', 'battery'],
					'gradient_level': 0
				},
				{
					'contents': '--',
					'draw_inner_divider': False,
					'highlight_group': ['battery_empty', 'battery_gradient', 'battery'],
					'gradient_level': 100
				}
			])

	def test_internal_ip(self):
		try:
			import netifaces
		except ImportError:
			raise SkipTest()
		pl = Pl()
		addr = {
			'enp2s0': {
				netifaces.AF_INET: [{'addr': '192.168.100.200'}],
				netifaces.AF_INET6: [{'addr': 'feff::5446:5eff:fe5a:7777%enp2s0'}]
			},
			'lo': {
				netifaces.AF_INET: [{'addr': '127.0.0.1'}],
				netifaces.AF_INET6: [{'addr': '::1'}]
			},
			'teredo': {
				netifaces.AF_INET6: [{'addr': 'feff::5446:5eff:fe5a:7777'}]
			},
		}
		interfaces = ['lo', 'enp2s0', 'teredo']
		with replace_module_module(
			common, 'netifaces',
			interfaces=(lambda: interfaces),
			ifaddresses=(lambda interface: addr[interface]),
			AF_INET=netifaces.AF_INET,
			AF_INET6=netifaces.AF_INET6,
		):
			self.assertEqual(common.internal_ip(pl=pl), '192.168.100.200')
			self.assertEqual(common.internal_ip(pl=pl, interface='detect'), '192.168.100.200')
			self.assertEqual(common.internal_ip(pl=pl, interface='lo'), '127.0.0.1')
			self.assertEqual(common.internal_ip(pl=pl, interface='teredo'), None)
			self.assertEqual(common.internal_ip(pl=pl, ipv=4), '192.168.100.200')
			self.assertEqual(common.internal_ip(pl=pl, interface='detect', ipv=4), '192.168.100.200')
			self.assertEqual(common.internal_ip(pl=pl, interface='lo', ipv=4), '127.0.0.1')
			self.assertEqual(common.internal_ip(pl=pl, interface='teredo', ipv=4), None)
			self.assertEqual(common.internal_ip(pl=pl, ipv=6), 'feff::5446:5eff:fe5a:7777%enp2s0')
			self.assertEqual(common.internal_ip(pl=pl, interface='detect', ipv=6), 'feff::5446:5eff:fe5a:7777%enp2s0')
			self.assertEqual(common.internal_ip(pl=pl, interface='lo', ipv=6), '::1')
			self.assertEqual(common.internal_ip(pl=pl, interface='teredo', ipv=6), 'feff::5446:5eff:fe5a:7777')
			interfaces[1:2] = ()
			self.assertEqual(common.internal_ip(pl=pl, ipv=6), 'feff::5446:5eff:fe5a:7777')
			interfaces[1:2] = ()
			self.assertEqual(common.internal_ip(pl=pl, ipv=6), '::1')
			interfaces[:] = ()
			self.assertEqual(common.internal_ip(pl=pl, ipv=6), None)


class TestVim(TestCase):
	def test_mode(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info), 'NORMAL')
		self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info, override={'i': 'INS'}), 'NORMAL')
		self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info, override={'n': 'NORM'}), 'NORM')
		with vim_module._with('mode', 'i') as segment_info:
			self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info), 'INSERT')
		with vim_module._with('mode', chr(ord('V') - 0x40)) as segment_info:
			self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info), 'V-BLCK')
			self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info, override={'^V': 'VBLK'}), 'VBLK')

	def test_visual_range(self):
		pl = Pl()
		vr = partial(self.vim.visual_range, pl=pl)
		vim_module.current.window.cursor = [0, 0]
		try:
			with vim_module._with('mode', 'i') as segment_info:
				self.assertEqual(vr(segment_info=segment_info), '')
			with vim_module._with('mode', '^V') as segment_info:
				self.assertEqual(vr(segment_info=segment_info), '1 x 1')
				with vim_module._with('vpos', line=5, col=5, off=0):
					self.assertEqual(vr(segment_info=segment_info), '5 x 5')
				with vim_module._with('vpos', line=5, col=4, off=0):
					self.assertEqual(vr(segment_info=segment_info), '5 x 4')
			with vim_module._with('mode', '^S') as segment_info:
				self.assertEqual(vr(segment_info=segment_info), '1 x 1')
				with vim_module._with('vpos', line=5, col=5, off=0):
					self.assertEqual(vr(segment_info=segment_info), '5 x 5')
				with vim_module._with('vpos', line=5, col=4, off=0):
					self.assertEqual(vr(segment_info=segment_info), '5 x 4')
			with vim_module._with('mode', 'V') as segment_info:
				self.assertEqual(vr(segment_info=segment_info), 'L:1')
				with vim_module._with('vpos', line=5, col=5, off=0):
					self.assertEqual(vr(segment_info=segment_info), 'L:5')
				with vim_module._with('vpos', line=5, col=4, off=0):
					self.assertEqual(vr(segment_info=segment_info), 'L:5')
			with vim_module._with('mode', 'S') as segment_info:
				self.assertEqual(vr(segment_info=segment_info), 'L:1')
				with vim_module._with('vpos', line=5, col=5, off=0):
					self.assertEqual(vr(segment_info=segment_info), 'L:5')
				with vim_module._with('vpos', line=5, col=4, off=0):
					self.assertEqual(vr(segment_info=segment_info), 'L:5')
			with vim_module._with('mode', 'v') as segment_info:
				self.assertEqual(vr(segment_info=segment_info), 'C:1')
				with vim_module._with('vpos', line=5, col=5, off=0):
					self.assertEqual(vr(segment_info=segment_info), 'L:5')
				with vim_module._with('vpos', line=5, col=4, off=0):
					self.assertEqual(vr(segment_info=segment_info), 'L:5')
			with vim_module._with('mode', 's') as segment_info:
				self.assertEqual(vr(segment_info=segment_info), 'C:1')
				with vim_module._with('vpos', line=5, col=5, off=0):
					self.assertEqual(vr(segment_info=segment_info), 'L:5')
				with vim_module._with('vpos', line=5, col=4, off=0):
					self.assertEqual(vr(segment_info=segment_info), 'L:5')
		finally:
			vim_module._close(1)

	def test_modified_indicator(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.modified_indicator(pl=pl, segment_info=segment_info), None)
		segment_info['buffer'][0] = 'abc'
		try:
			self.assertEqual(self.vim.modified_indicator(pl=pl, segment_info=segment_info), '+')
			self.assertEqual(self.vim.modified_indicator(pl=pl, segment_info=segment_info, text='-'), '-')
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_paste_indicator(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.paste_indicator(pl=pl, segment_info=segment_info), None)
		with vim_module._with('options', paste=1):
			self.assertEqual(self.vim.paste_indicator(pl=pl, segment_info=segment_info), 'PASTE')
			self.assertEqual(self.vim.paste_indicator(pl=pl, segment_info=segment_info, text='P'), 'P')

	def test_readonly_indicator(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.readonly_indicator(pl=pl, segment_info=segment_info), None)
		with vim_module._with('bufoptions', readonly=1):
			self.assertEqual(self.vim.readonly_indicator(pl=pl, segment_info=segment_info), 'RO')
			self.assertEqual(self.vim.readonly_indicator(pl=pl, segment_info=segment_info, text='L'), 'L')

	def test_file_scheme(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.file_scheme(pl=pl, segment_info=segment_info), None)
		with vim_module._with('buffer', '/tmp/’’/abc') as segment_info:
			self.assertEqual(self.vim.file_scheme(pl=pl, segment_info=segment_info), None)
		with vim_module._with('buffer', 'zipfile:/tmp/abc.zip::abc/abc.vim') as segment_info:
			self.assertEqual(self.vim.file_scheme(pl=pl, segment_info=segment_info), 'zipfile')

	def test_file_directory(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info), None)
		with replace_env('HOME', '/home/foo', os.environ):
			with vim_module._with('buffer', '/tmp/’’/abc') as segment_info:
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info), '/tmp/’’/')
			with vim_module._with('buffer', b'/tmp/\xFF\xFF/abc') as segment_info:
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info), '/tmp/<ff><ff>/')
			with vim_module._with('buffer', '/tmp/abc') as segment_info:
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info), '/tmp/')
				os.environ['HOME'] = '/tmp'
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info), '~/')
			with vim_module._with('buffer', 'zipfile:/tmp/abc.zip::abc/abc.vim') as segment_info:
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info, remove_scheme=False), 'zipfile:/tmp/abc.zip::abc/')
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info, remove_scheme=True), '/tmp/abc.zip::abc/')
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info), '/tmp/abc.zip::abc/')
				os.environ['HOME'] = '/tmp'
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info, remove_scheme=False), 'zipfile:/tmp/abc.zip::abc/')
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info, remove_scheme=True), '/tmp/abc.zip::abc/')
				self.assertEqual(self.vim.file_directory(pl=pl, segment_info=segment_info), '/tmp/abc.zip::abc/')

	def test_file_name(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.file_name(pl=pl, segment_info=segment_info), None)
		self.assertEqual(self.vim.file_name(pl=pl, segment_info=segment_info, display_no_file=True), [
			{'contents': '[No file]', 'highlight_group': ['file_name_no_file', 'file_name']}
		])
		self.assertEqual(self.vim.file_name(pl=pl, segment_info=segment_info, display_no_file=True, no_file_text='X'), [
			{'contents': 'X', 'highlight_group': ['file_name_no_file', 'file_name']}
		])
		with vim_module._with('buffer', '/tmp/abc') as segment_info:
			self.assertEqual(self.vim.file_name(pl=pl, segment_info=segment_info), 'abc')
		with vim_module._with('buffer', '/tmp/’’') as segment_info:
			self.assertEqual(self.vim.file_name(pl=pl, segment_info=segment_info), '’’')
		with vim_module._with('buffer', b'/tmp/\xFF\xFF') as segment_info:
			self.assertEqual(self.vim.file_name(pl=pl, segment_info=segment_info), '<ff><ff>')

	def test_file_size(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.file_size(pl=pl, segment_info=segment_info), '0 B')
		with vim_module._with('buffer', os.path.join(os.path.dirname(__file__), 'empty')) as segment_info:
			self.assertEqual(self.vim.file_size(pl=pl, segment_info=segment_info), '0 B')

	def test_file_opts(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.file_format(pl=pl, segment_info=segment_info), [
			{'divider_highlight_group': 'background:divider', 'contents': 'unix'}
		])
		self.assertEqual(self.vim.file_encoding(pl=pl, segment_info=segment_info), [
			{'divider_highlight_group': 'background:divider', 'contents': 'utf-8'}
		])
		self.assertEqual(self.vim.file_type(pl=pl, segment_info=segment_info), None)
		with vim_module._with('bufoptions', filetype='python'):
			self.assertEqual(self.vim.file_type(pl=pl, segment_info=segment_info), [
				{'divider_highlight_group': 'background:divider', 'contents': 'python'}
			])

	def test_window_title(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.window_title(pl=pl, segment_info=segment_info), None)
		with vim_module._with('wvars', quickfix_title='Abc'):
			self.assertEqual(self.vim.window_title(pl=pl, segment_info=segment_info), 'Abc')

	def test_line_percent(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		segment_info['buffer'][0:-1] = [str(i) for i in range(100)]
		try:
			self.assertEqual(self.vim.line_percent(pl=pl, segment_info=segment_info), '1')
			vim_module._set_cursor(50, 0)
			self.assertEqual(self.vim.line_percent(pl=pl, segment_info=segment_info), '50')
			self.assertEqual(self.vim.line_percent(pl=pl, segment_info=segment_info, gradient=True), [
				{'contents': '50', 'highlight_group': ['line_percent_gradient', 'line_percent'], 'gradient_level': 50 * 100.0 / 101}
			])
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_line_count(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		segment_info['buffer'][0:-1] = [str(i) for i in range(99)]
		try:
			self.assertEqual(self.vim.line_count(pl=pl, segment_info=segment_info), '100')
			vim_module._set_cursor(50, 0)
			self.assertEqual(self.vim.line_count(pl=pl, segment_info=segment_info), '100')
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_position(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		try:
			segment_info['buffer'][0:-1] = [str(i) for i in range(99)]
			vim_module._set_cursor(49, 0)
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info), '50%')
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info, gradient=True), [
				{'contents': '50%', 'highlight_group': ['position_gradient', 'position'], 'gradient_level': 50.0}
			])
			vim_module._set_cursor(0, 0)
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info), 'Top')
			vim_module._set_cursor(97, 0)
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info, position_strings={'top': 'Comienzo', 'bottom': 'Final', 'all': 'Todo'}), 'Final')
			segment_info['buffer'][0:-1] = [str(i) for i in range(2)]
			vim_module._set_cursor(0, 0)
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info, position_strings={'top': 'Comienzo', 'bottom': 'Final', 'all': 'Todo'}), 'Todo')
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info, gradient=True), [
				{'contents': 'All', 'highlight_group': ['position_gradient', 'position'], 'gradient_level': 0.0}
			])
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_cursor_current(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.line_current(pl=pl, segment_info=segment_info), '1')
		self.assertEqual(self.vim.col_current(pl=pl, segment_info=segment_info), '1')
		self.assertEqual(self.vim.virtcol_current(pl=pl, segment_info=segment_info), [{
			'highlight_group': ['virtcol_current_gradient', 'virtcol_current', 'col_current'], 'contents': '1', 'gradient_level': 100.0 / 80,
		}])
		self.assertEqual(self.vim.virtcol_current(pl=pl, segment_info=segment_info, gradient=False), [{
			'highlight_group': ['virtcol_current', 'col_current'], 'contents': '1',
		}])

	def test_modified_buffers(self):
		pl = Pl()
		self.assertEqual(self.vim.modified_buffers(pl=pl), None)

	def test_branch(self):
		pl = Pl()
		create_watcher = get_fallback_create_watcher()
		branch = partial(self.vim.branch, pl=pl, create_watcher=create_watcher)
		with vim_module._with('buffer', '/foo') as segment_info:
			with replace_attr(self.vim, 'guess', get_dummy_guess(status=lambda: None)):
				with replace_attr(self.vim, 'tree_status', lambda repo, pl: None):
					self.assertEqual(branch(segment_info=segment_info, status_colors=False), [
						{'divider_highlight_group': 'branch:divider', 'highlight_group': ['branch'], 'contents': 'foo'}
					])
					self.assertEqual(branch(segment_info=segment_info, status_colors=True), [
						{'divider_highlight_group': 'branch:divider', 'highlight_group': ['branch_clean', 'branch'], 'contents': 'foo'}
					])
			with replace_attr(self.vim, 'guess', get_dummy_guess(status=lambda: 'DU')):
				with replace_attr(self.vim, 'tree_status', lambda repo, pl: 'DU'):
					self.assertEqual(branch(segment_info=segment_info, status_colors=False), [
						{'divider_highlight_group': 'branch:divider', 'highlight_group': ['branch'], 'contents': 'foo'}
					])
					self.assertEqual(branch(segment_info=segment_info, status_colors=True), [
						{'divider_highlight_group': 'branch:divider', 'highlight_group': ['branch_dirty', 'branch'], 'contents': 'foo'}
					])

	def test_file_vcs_status(self):
		pl = Pl()
		create_watcher = get_fallback_create_watcher()
		file_vcs_status = partial(self.vim.file_vcs_status, pl=pl, create_watcher=create_watcher)
		with vim_module._with('buffer', '/foo') as segment_info:
			with replace_attr(self.vim, 'guess', get_dummy_guess(status=lambda file: 'M')):
				self.assertEqual(file_vcs_status(segment_info=segment_info), [
					{'highlight_group': ['file_vcs_status_M', 'file_vcs_status'], 'contents': 'M'}
				])
			with replace_attr(self.vim, 'guess', get_dummy_guess(status=lambda file: None)):
				self.assertEqual(file_vcs_status(segment_info=segment_info), None)
		with vim_module._with('buffer', '/bar') as segment_info:
			with vim_module._with('bufoptions', buftype='nofile'):
				with replace_attr(self.vim, 'guess', get_dummy_guess(status=lambda file: 'M')):
					self.assertEqual(file_vcs_status(segment_info=segment_info), None)

	def test_trailing_whitespace(self):
		pl = Pl()
		with vim_module._with('buffer', 'tws') as segment_info:
			trailing_whitespace = partial(self.vim.trailing_whitespace, pl=pl, segment_info=segment_info)
			self.assertEqual(trailing_whitespace(), None)
			self.assertEqual(trailing_whitespace(), None)
			vim_module.current.buffer[0] = ' '
			self.assertEqual(trailing_whitespace(), [{
				'highlight_group': ['trailing_whitespace', 'warning'],
				'contents': '1',
			}])
			self.assertEqual(trailing_whitespace(), [{
				'highlight_group': ['trailing_whitespace', 'warning'],
				'contents': '1',
			}])
			vim_module.current.buffer[0] = ''
			self.assertEqual(trailing_whitespace(), None)
			self.assertEqual(trailing_whitespace(), None)

	def test_tabnr(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.tabnr(pl=pl, segment_info=segment_info, show_current=True), '1')
		self.assertEqual(self.vim.tabnr(pl=pl, segment_info=segment_info, show_current=False), None)

	def test_bufnr(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.bufnr(pl=pl, segment_info=segment_info, show_current=True), str(segment_info['bufnr']))
		self.assertEqual(self.vim.bufnr(pl=pl, segment_info=segment_info, show_current=False), None)

	def test_winnr(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.winnr(pl=pl, segment_info=segment_info, show_current=True), str(segment_info['winnr']))
		self.assertEqual(self.vim.winnr(pl=pl, segment_info=segment_info, show_current=False), None)

	def test_segment_info(self):
		pl = Pl()
		with vim_module._with('tabpage'):
			with vim_module._with('buffer', '1') as segment_info:
				self.assertEqual(self.vim.tab_modified_indicator(pl=pl, segment_info=segment_info), None)
				vim_module.current.buffer[0] = ' '
				self.assertEqual(self.vim.tab_modified_indicator(pl=pl, segment_info=segment_info), [{
					'contents': '+',
					'highlight_group': ['tab_modified_indicator', 'modified_indicator'],
				}])
				vim_module._undo()
				self.assertEqual(self.vim.tab_modified_indicator(pl=pl, segment_info=segment_info), None)
				old_buffer = vim_module.current.buffer
				vim_module._new('2')
				segment_info = vim_module._get_segment_info()
				self.assertEqual(self.vim.tab_modified_indicator(pl=pl, segment_info=segment_info), None)
				old_buffer[0] = ' '
				self.assertEqual(self.vim.modified_indicator(pl=pl, segment_info=segment_info), None)
				self.assertEqual(self.vim.tab_modified_indicator(pl=pl, segment_info=segment_info), [{
					'contents': '+',
					'highlight_group': ['tab_modified_indicator', 'modified_indicator'],
				}])

	@classmethod
	def setUpClass(cls):
		sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'path')))
		from powerline.segments import vim
		cls.vim = vim

	@classmethod
	def tearDownClass(cls):
		sys.path.pop(0)


old_cwd = None


def setUpModule():
	global old_cwd
	global __file__
	old_cwd = os.getcwd()
	__file__ = os.path.abspath(__file__)
	os.chdir(os.path.dirname(__file__))


def tearDownModule():
	global old_cwd
	os.chdir(old_cwd)


if __name__ == '__main__':
	from tests import main
	main()
