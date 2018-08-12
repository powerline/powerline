# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import os

from functools import partial
from collections import namedtuple
from time import sleep
from platform import python_implementation

from powerline.segments import shell, tmux, pdb, i3wm
from powerline.lib.vcs import get_fallback_create_watcher
from powerline.lib.unicode import out_u

import tests.modules.vim as vim_module

from tests.modules.lib import (Args, urllib_read, replace_attr, new_module,
                               replace_module_module, replace_env, Pl)
from tests.modules import TestCase, SkipTest


def get_dummy_guess(**kwargs):
	if 'directory' in kwargs:
		def guess(path, create_watcher):
			return Args(branch=lambda: out_u(os.path.basename(path)), **kwargs)
	else:
		def guess(path, create_watcher):
			return Args(branch=lambda: out_u(os.path.basename(path)), directory=path, **kwargs)
	return guess


class TestShell(TestCase):
	def test_last_status(self):
		pl = Pl()
		segment_info = {'args': Args(last_exit_code=10)}
		self.assertEqual(shell.last_status(pl=pl, segment_info=segment_info), [
			{'contents': '10', 'highlight_groups': ['exit_fail']}
		])
		segment_info['args'].last_exit_code = 0
		self.assertEqual(shell.last_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_exit_code = None
		self.assertEqual(shell.last_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_exit_code = 'sigsegv'
		self.assertEqual(shell.last_status(pl=pl, segment_info=segment_info), [
			{'contents': 'sigsegv', 'highlight_groups': ['exit_fail']}
		])
		segment_info['args'].last_exit_code = 'sigsegv+core'
		self.assertEqual(shell.last_status(pl=pl, segment_info=segment_info), [
			{'contents': 'sigsegv+core', 'highlight_groups': ['exit_fail']}
		])

	def test_last_pipe_status(self):
		pl = Pl()
		segment_info = {'args': Args(last_pipe_status=[], last_exit_code=0)}
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_pipe_status = [0, 0, 0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_pipe_status = [0, 0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_pipe_status = [0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), None)
		segment_info['args'].last_pipe_status = [0, 2, 0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
			{'contents': '2', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True},
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
		])
		segment_info['args'].last_pipe_status = [2, 0, 0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '2', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True},
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
		])
		segment_info['args'].last_pipe_status = [0, 0, 2]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
			{'contents': '2', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True},
		])
		segment_info['args'].last_pipe_status = [2]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '2', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True},
		])
		segment_info['args'].last_pipe_status = [0, 'sigsegv', 'sigsegv+core']
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
			{'contents': 'sigsegv', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True},
			{'contents': 'sigsegv+core', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True}
		])
		segment_info['args'].last_pipe_status = [0, 'sigsegv', 0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
			{'contents': 'sigsegv', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True},
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True}
		])
		segment_info['args'].last_pipe_status = [0, 'sigsegv+core', 0]
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True},
			{'contents': 'sigsegv+core', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True},
			{'contents': '0', 'highlight_groups': ['exit_success'], 'draw_inner_divider': True}
		])
		segment_info['args'].last_pipe_status = []
		segment_info['args'].last_exit_code = 5
		self.assertEqual(shell.last_pipe_status(pl=pl, segment_info=segment_info), [
			{'contents': '5', 'highlight_groups': ['exit_fail'], 'draw_inner_divider': True},
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
			'highlight_groups': ['continuation:current', 'continuation'],
		}])
		segment_info = {'parser_state': 'if cmdsubst'}
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'l',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, right_align=True), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'r',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=False), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation'],
			},
			{
				'contents': 'cmdsubst',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'l',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=False, right_align=True), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation'],
				'width': 'auto',
				'align': 'r',
			},
			{
				'contents': 'cmdsubst',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation:current', 'continuation'],
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=True, right_align=True), [
			{
				'contents': 'if',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'r',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=True, right_align=True, renames={'if': 'IF'}), [
			{
				'contents': 'IF',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'r',
			},
		])
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info, omit_cmdsubst=True, right_align=True, renames={'if': None}), [
			{
				'contents': '',
				'highlight_groups': ['continuation:current', 'continuation'],
				'width': 'auto',
				'align': 'r',
			},
		])
		segment_info = {'parser_state': 'then then then cmdsubst'}
		self.assertEqual(shell.continuation(pl=pl, segment_info=segment_info), [
			{
				'contents': 'then',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation'],
			},
			{
				'contents': 'then',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation'],
			},
			{
				'contents': 'then',
				'draw_inner_divider': True,
				'highlight_groups': ['continuation:current', 'continuation'],
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
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'abc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'def', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			segment_info['home'] = '/abc/def/ghi'
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			segment_info.update(shortened_path='~foo/ghi')
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '~foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_shortened_path=False), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			segment_info.pop('shortened_path')
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=3), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=3, shorten_home=False), [
				{'contents': '...', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1), [
				{'contents': '...', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, ellipsis='---'), [
				{'contents': '---', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, ellipsis=None), [
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True), [
				{'contents': '.../', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True, ellipsis='---'), [
				{'contents': '---/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True, ellipsis=None), [
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'fo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2, use_path_separator=True), [
				{'contents': '~/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'fo/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			cwd[0] = '/etc'
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_path_separator=False), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'etc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_path_separator=True), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'etc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			cwd[0] = '/'
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_path_separator=False), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, use_path_separator=True), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			ose = OSError()
			ose.errno = 2
			cwd[0] = ose
			self.assertEqual(shell.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2), [
				{'contents': '[not found]', 'divider_highlight_group': 'cwd:divider', 'highlight_groups': ['cwd:current_folder', 'cwd'], 'draw_inner_divider': True}
			])
			cwd[0] = OSError()
			self.assertRaises(OSError, shell.cwd, pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2)
			cwd[0] = ValueError()
			self.assertRaises(ValueError, shell.cwd, pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2)


class TestTmux(TestCase):
	def test_attached_clients(self):
		def get_tmux_output(pl, cmd, *args):
			if cmd == 'list-panes':
				return 'session_name\n'
			elif cmd == 'list-clients':
				return '/dev/pts/2: 0 [191x51 xterm-256color] (utf8)\n/dev/pts/3: 0 [191x51 xterm-256color] (utf8)'

		pl = Pl()
		with replace_attr(tmux, 'get_tmux_output', get_tmux_output):
			self.assertEqual(tmux.attached_clients(pl=pl), '2')
			self.assertEqual(tmux.attached_clients(pl=pl, minimum=3), None)


class TestCommon(TestCase):
	@classmethod
	def setUpClass(cls):
		module = __import__(str('powerline.segments.common.{0}'.format(cls.module_name)))
		cls.module = getattr(module.segments.common, str(cls.module_name))


class TestNet(TestCommon):
	module_name = 'net'

	def test_hostname(self):
		pl = Pl()
		with replace_env('SSH_CLIENT', '192.168.0.12 40921 22') as segment_info:
			with replace_module_module(self.module, 'socket', gethostname=lambda: 'abc'):
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info), 'abc')
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True), 'abc')
			with replace_module_module(self.module, 'socket', gethostname=lambda: 'abc.mydomain'):
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info), 'abc.mydomain')
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info, exclude_domain=True), 'abc')
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True), 'abc.mydomain')
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True, exclude_domain=True), 'abc')
			segment_info['environ'].pop('SSH_CLIENT')
			with replace_module_module(self.module, 'socket', gethostname=lambda: 'abc'):
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info), 'abc')
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True), None)
			with replace_module_module(self.module, 'socket', gethostname=lambda: 'abc.mydomain'):
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info), 'abc.mydomain')
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info, exclude_domain=True), 'abc')
				self.assertEqual(self.module.hostname(pl=pl, segment_info=segment_info, only_if_ssh=True, exclude_domain=True), None)

	def test_external_ip(self):
		pl = Pl()
		with replace_attr(self.module, 'urllib_read', urllib_read):
			self.assertEqual(self.module.external_ip(pl=pl), [{'contents': '127.0.0.1', 'divider_highlight_group': 'background:divider'}])

	def test_internal_ip(self):
		try:
			import netifaces
		except ImportError:
			raise SkipTest('netifaces module is not available')
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
			self.module, 'netifaces',
			interfaces=(lambda: interfaces),
			ifaddresses=(lambda interface: addr[interface]),
			AF_INET=netifaces.AF_INET,
			AF_INET6=netifaces.AF_INET6,
		):
			self.assertEqual(self.module.internal_ip(pl=pl), '192.168.100.200')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='auto'), '192.168.100.200')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='lo'), '127.0.0.1')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='teredo'), None)
			self.assertEqual(self.module.internal_ip(pl=pl, ipv=4), '192.168.100.200')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='auto', ipv=4), '192.168.100.200')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='lo', ipv=4), '127.0.0.1')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='teredo', ipv=4), None)
			self.assertEqual(self.module.internal_ip(pl=pl, ipv=6), 'feff::5446:5eff:fe5a:7777%enp2s0')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='auto', ipv=6), 'feff::5446:5eff:fe5a:7777%enp2s0')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='lo', ipv=6), '::1')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='teredo', ipv=6), 'feff::5446:5eff:fe5a:7777')
			interfaces[1:2] = ()
			self.assertEqual(self.module.internal_ip(pl=pl, ipv=6), 'feff::5446:5eff:fe5a:7777')
			interfaces[1:2] = ()
			self.assertEqual(self.module.internal_ip(pl=pl, ipv=6), '::1')
			interfaces[:] = ()
			self.assertEqual(self.module.internal_ip(pl=pl, ipv=6), None)

		gateways = {
			'default': {
				netifaces.AF_INET: ('192.168.100.1', 'enp2s0'),
				netifaces.AF_INET6: ('feff::5446:5eff:fe5a:0001', 'enp2s0')
			}
		}

		with replace_module_module(
			self.module, 'netifaces',
			interfaces=(lambda: interfaces),
			ifaddresses=(lambda interface: addr[interface]),
			gateways=(lambda: gateways),
			AF_INET=netifaces.AF_INET,
			AF_INET6=netifaces.AF_INET6,
		):
			# default gateway has specified address family
			self.assertEqual(self.module.internal_ip(pl=pl, interface='default_gateway', ipv=4), '192.168.100.200')
			self.assertEqual(self.module.internal_ip(pl=pl, interface='default_gateway', ipv=6), 'feff::5446:5eff:fe5a:7777%enp2s0')
			# default gateway doesn't have specified address family
			gateways['default'] = {}
			self.assertEqual(self.module.internal_ip(pl=pl, interface='default_gateway', ipv=4), None)
			self.assertEqual(self.module.internal_ip(pl=pl, interface='default_gateway', ipv=6), None)

	def test_network_load(self):
		def gb(interface):
			return None

		f = [gb]

		def _get_bytes(interface):
			return f[0](interface)

		pl = Pl()

		with replace_attr(self.module, '_get_bytes', _get_bytes):
			self.module.network_load.startup(pl=pl)
			try:
				self.assertEqual(self.module.network_load(pl=pl, interface='eth0'), None)
				sleep(self.module.network_load.interval)
				self.assertEqual(self.module.network_load(pl=pl, interface='eth0'), None)
				while 'prev' not in self.module.network_load.interfaces.get('eth0', {}):
					sleep(0.1)
				self.assertEqual(self.module.network_load(pl=pl, interface='eth0'), None)

				l = [0, 0]

				def gb2(interface):
					l[0] += 1200
					l[1] += 2400
					return tuple(l)
				f[0] = gb2

				while not self.module.network_load.interfaces.get('eth0', {}).get('prev', (None, None))[1]:
					sleep(0.1)
				self.assertEqual(self.module.network_load(pl=pl, interface='eth0'), [
					{'divider_highlight_group': 'network_load:divider', 'contents': 'DL  1 KiB/s', 'highlight_groups': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'network_load:divider', 'contents': 'UL  2 KiB/s', 'highlight_groups': ['network_load_sent', 'network_load']},
				])
				self.assertEqual(self.module.network_load(pl=pl, interface='eth0', recv_format='r {value}', sent_format='s {value}'), [
					{'divider_highlight_group': 'network_load:divider', 'contents': 'r 1 KiB/s', 'highlight_groups': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'network_load:divider', 'contents': 's 2 KiB/s', 'highlight_groups': ['network_load_sent', 'network_load']},
				])
				self.assertEqual(self.module.network_load(pl=pl, recv_format='r {value}', sent_format='s {value}', suffix='bps', interface='eth0'), [
					{'divider_highlight_group': 'network_load:divider', 'contents': 'r 1 Kibps', 'highlight_groups': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'network_load:divider', 'contents': 's 2 Kibps', 'highlight_groups': ['network_load_sent', 'network_load']},
				])
				self.assertEqual(self.module.network_load(pl=pl, recv_format='r {value}', sent_format='s {value}', si_prefix=True, interface='eth0'), [
					{'divider_highlight_group': 'network_load:divider', 'contents': 'r 1 kB/s', 'highlight_groups': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'network_load:divider', 'contents': 's 2 kB/s', 'highlight_groups': ['network_load_sent', 'network_load']},
				])
				self.assertEqual(self.module.network_load(pl=pl, recv_format='r {value}', sent_format='s {value}', recv_max=0, interface='eth0'), [
					{'divider_highlight_group': 'network_load:divider', 'contents': 'r 1 KiB/s', 'highlight_groups': ['network_load_recv_gradient', 'network_load_gradient', 'network_load_recv', 'network_load'], 'gradient_level': 100},
					{'divider_highlight_group': 'network_load:divider', 'contents': 's 2 KiB/s', 'highlight_groups': ['network_load_sent', 'network_load']},
				])

				class ApproxEqual(object):
					def __eq__(self, i):
						return abs(i - 50.0) < 1

				self.assertEqual(self.module.network_load(pl=pl, recv_format='r {value}', sent_format='s {value}', sent_max=4800, interface='eth0'), [
					{'divider_highlight_group': 'network_load:divider', 'contents': 'r 1 KiB/s', 'highlight_groups': ['network_load_recv', 'network_load']},
					{'divider_highlight_group': 'network_load:divider', 'contents': 's 2 KiB/s', 'highlight_groups': ['network_load_sent_gradient', 'network_load_gradient', 'network_load_sent', 'network_load'], 'gradient_level': ApproxEqual()},
				])
			finally:
				self.module.network_load.shutdown()


class TestEnv(TestCommon):
	module_name = 'env'

	def test_user(self):
		new_os = new_module('os', getpid=lambda: 1)

		class Process(object):
			def __init__(self, pid):
				pass

			def username(self):
				return 'def@DOMAIN.COM'

			if hasattr(self.module, 'psutil') and not callable(self.module.psutil.Process.username):
				username = property(username)

		segment_info = {'environ': {}}

		def user(*args, **kwargs):
			return self.module.user(pl=pl, segment_info=segment_info, *args, **kwargs)

		struct_passwd = namedtuple('struct_passwd', ('pw_name',))
		new_psutil = new_module('psutil', Process=Process)
		new_pwd = new_module('pwd', getpwuid=lambda uid: struct_passwd(pw_name='def@DOMAIN.COM'))
		new_getpass = new_module('getpass', getuser=lambda: 'def@DOMAIN.COM')
		pl = Pl()
		with replace_attr(self.module, 'pwd', new_pwd):
			with replace_attr(self.module, 'getpass', new_getpass):
				with replace_attr(self.module, 'os', new_os):
					with replace_attr(self.module, 'psutil', new_psutil):
						with replace_attr(self.module, '_geteuid', lambda: 5):
							self.assertEqual(user(), [
								{'contents': 'def@DOMAIN.COM', 'highlight_groups': ['user']}
							])
							self.assertEqual(user(hide_user='abc'), [
								{'contents': 'def@DOMAIN.COM', 'highlight_groups': ['user']}
							])
							self.assertEqual(user(hide_domain=False), [
								{'contents': 'def@DOMAIN.COM', 'highlight_groups': ['user']}
							])
							self.assertEqual(user(hide_user='def@DOMAIN.COM'), None)
							self.assertEqual(user(hide_domain=True), [
								{'contents': 'def', 'highlight_groups': ['user']}
							])
						with replace_attr(self.module, '_geteuid', lambda: 0):
							self.assertEqual(user(), [
								{'contents': 'def', 'highlight_groups': ['superuser', 'user']}
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
		with replace_attr(self.module, 'os', new_os):
			cwd[0] = '/abc/def/ghi/foo/bar'
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'abc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'def', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			segment_info['home'] = '/abc/def/ghi'
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=3), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=3, shorten_home=False), [
				{'contents': '...', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'foo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1), [
				{'contents': '...', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, ellipsis='---'), [
				{'contents': '---', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, ellipsis=None), [
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True), [
				{'contents': '.../', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True, ellipsis='---'), [
				{'contents': '---/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=1, use_path_separator=True, ellipsis=None), [
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2), [
				{'contents': '~', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'fo', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2, use_path_separator=True), [
				{'contents': '~/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'fo/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']}
			])
			cwd[0] = '/etc'
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, use_path_separator=False), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True},
				{'contents': 'etc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, use_path_separator=True), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False},
				{'contents': 'etc', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			cwd[0] = '/'
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, use_path_separator=False), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': True, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, use_path_separator=True), [
				{'contents': '/', 'divider_highlight_group': 'cwd:divider', 'draw_inner_divider': False, 'highlight_groups': ['cwd:current_folder', 'cwd']},
			])
			ose = OSError()
			ose.errno = 2
			cwd[0] = ose
			self.assertEqual(self.module.cwd(pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2), [
				{'contents': '[not found]', 'divider_highlight_group': 'cwd:divider', 'highlight_groups': ['cwd:current_folder', 'cwd'], 'draw_inner_divider': True}
			])
			cwd[0] = OSError()
			self.assertRaises(OSError, self.module.cwd, pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2)
			cwd[0] = ValueError()
			self.assertRaises(ValueError, self.module.cwd, pl=pl, segment_info=segment_info, dir_limit_depth=2, dir_shorten_len=2)

	def test_virtualenv(self):
		pl = Pl()
		with replace_env('VIRTUAL_ENV', '/abc/def/ghi') as segment_info:
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info), 'ghi')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_conda=True), 'ghi')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True, ignore_conda=True), None)

			segment_info['environ'].pop('VIRTUAL_ENV')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_conda=True), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True, ignore_conda=True), None)

		with replace_env('CONDA_DEFAULT_ENV', 'foo') as segment_info:
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info), 'foo')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_conda=True), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True), 'foo')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True, ignore_conda=True), None)

			segment_info['environ'].pop('CONDA_DEFAULT_ENV')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_conda=True), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True, ignore_conda=True), None)

		with replace_env('CONDA_DEFAULT_ENV', 'foo', environ={'VIRTUAL_ENV': '/sbc/def/ghi'}) as segment_info:
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info), 'ghi')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_conda=True), 'ghi')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True), 'foo')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True, ignore_conda=True), None)

			segment_info['environ'].pop('CONDA_DEFAULT_ENV')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info), 'ghi')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_conda=True), 'ghi')
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True), None)
			self.assertEqual(self.module.virtualenv(pl=pl, segment_info=segment_info, ignore_venv=True, ignore_conda=True), None)

	def test_environment(self):
		pl = Pl()
		variable = 'FOO'
		value = 'bar'
		with replace_env(variable, value) as segment_info:
			self.assertEqual(self.module.environment(pl=pl, segment_info=segment_info, variable=variable), value)
			segment_info['environ'].pop(variable)
			self.assertEqual(self.module.environment(pl=pl, segment_info=segment_info, variable=variable), None)


class TestVcs(TestCommon):
	module_name = 'vcs'

	def test_branch(self):
		pl = Pl()
		create_watcher = get_fallback_create_watcher()
		segment_info = {'getcwd': os.getcwd}
		branch = partial(self.module.branch, pl=pl, create_watcher=create_watcher)
		with replace_attr(self.module, 'guess', get_dummy_guess(status=lambda: None, directory='/tmp/tests')):
			with replace_attr(self.module, 'tree_status', lambda repo, pl: None):
				self.assertEqual(branch(segment_info=segment_info, status_colors=False), [{
						'highlight_groups': ['branch'],
						'contents': 'tests',
						'divider_highlight_group': None
				}])
				self.assertEqual(branch(segment_info=segment_info, status_colors=True), [{
					'contents': 'tests',
					'highlight_groups': ['branch_clean', 'branch'],
					'divider_highlight_group': None
				}])
		with replace_attr(self.module, 'guess', get_dummy_guess(status=lambda: 'D  ', directory='/tmp/tests')):
			with replace_attr(self.module, 'tree_status', lambda repo, pl: 'D '):
				self.assertEqual(branch(segment_info=segment_info, status_colors=False), [{
					'highlight_groups': ['branch'],
					'contents': 'tests',
					'divider_highlight_group': None
				}])
				self.assertEqual(branch(segment_info=segment_info, status_colors=True), [{
					'contents': 'tests',
					'highlight_groups': ['branch_dirty', 'branch'],
					'divider_highlight_group': None
				}])
				self.assertEqual(branch(segment_info=segment_info, status_colors=False), [{
					'highlight_groups': ['branch'],
					'contents': 'tests',
					'divider_highlight_group': None
				}])
		with replace_attr(self.module, 'guess', lambda path, create_watcher: None):
			self.assertEqual(branch(segment_info=segment_info, status_colors=False), None)
		with replace_attr(self.module, 'guess', get_dummy_guess(status=lambda: 'U')):
			with replace_attr(self.module, 'tree_status', lambda repo, pl: 'U'):
				self.assertEqual(branch(segment_info=segment_info, status_colors=False, ignore_statuses=['U']), [{
					'highlight_groups': ['branch'],
					'contents': 'tests',
					'divider_highlight_group': None
				}])
				self.assertEqual(branch(segment_info=segment_info, status_colors=True, ignore_statuses=['DU']), [{
					'highlight_groups': ['branch_dirty', 'branch'],
					'contents': 'tests',
					'divider_highlight_group': None
				}])
				self.assertEqual(branch(segment_info=segment_info, status_colors=True), [{
					'highlight_groups': ['branch_dirty', 'branch'],
					'contents': 'tests',
					'divider_highlight_group': None
				}])
				self.assertEqual(branch(segment_info=segment_info, status_colors=True, ignore_statuses=['U']), [{
					'highlight_groups': ['branch_clean', 'branch'],
					'contents': 'tests',
					'divider_highlight_group': None
				}])

	def test_stash(self):
		pl = Pl()
		create_watcher = get_fallback_create_watcher()
		stash = partial(self.module.stash, pl=pl, create_watcher=create_watcher, segment_info={'getcwd': os.getcwd})

		def forge_stash(n):
		    return replace_attr(self.module, 'guess', get_dummy_guess(stash=lambda: n, directory='/tmp/tests'))

		with forge_stash(0):
			self.assertEqual(stash(), None)
		with forge_stash(1):
			self.assertEqual(stash(), [{
				'highlight_groups': ['stash'],
				'contents': '1',
				'divider_highlight_group': None
			}])
		with forge_stash(2):
			self.assertEqual(stash(), [{
				'highlight_groups': ['stash'],
				'contents': '2',
				'divider_highlight_group': None
			}])


class TestTime(TestCommon):
	module_name = 'time'

	def test_date(self):
		pl = Pl()
		with replace_attr(self.module, 'datetime', Args(now=lambda: Args(strftime=lambda fmt: fmt))):
			self.assertEqual(self.module.date(pl=pl), [{'contents': '%Y-%m-%d', 'highlight_groups': ['date'], 'divider_highlight_group': None}])
			self.assertEqual(self.module.date(pl=pl, format='%H:%M', istime=True), [{'contents': '%H:%M', 'highlight_groups': ['time', 'date'], 'divider_highlight_group': 'time:divider'}])
		unicode_date = self.module.date(pl=pl, format='\u231a', istime=True)
		expected_unicode_date = [{'contents': '\u231a', 'highlight_groups': ['time', 'date'], 'divider_highlight_group': 'time:divider'}]
		if python_implementation() == 'PyPy' and sys.version_info >= (3,):
			if unicode_date != expected_unicode_date:
				raise SkipTest('Dates do not match, see https://bitbucket.org/pypy/pypy/issues/2161/pypy3-strftime-does-not-accept-unicode')
		self.assertEqual(unicode_date, expected_unicode_date)

	def test_fuzzy_time(self):
		time = Args(hour=0, minute=45)
		pl = Pl()
		with replace_attr(self.module, 'datetime', Args(now=lambda: time)):
			self.assertEqual(self.module.fuzzy_time(pl=pl), 'quarter to one')
			time.hour = 23
			time.minute = 59
			self.assertEqual(self.module.fuzzy_time(pl=pl), 'round about midnight')
			time.minute = 33
			self.assertEqual(self.module.fuzzy_time(pl=pl), 'twenty-five to twelve')
			time.minute = 60
			self.assertEqual(self.module.fuzzy_time(pl=pl), 'twelve o\'clock')
			time.minute = 33
			self.assertEqual(self.module.fuzzy_time(pl=pl, unicode_text=False), 'twenty-five to twelve')
			time.minute = 60
			self.assertEqual(self.module.fuzzy_time(pl=pl, unicode_text=False), 'twelve o\'clock')
			time.minute = 33
			self.assertEqual(self.module.fuzzy_time(pl=pl, unicode_text=True), 'twenty‐five to twelve')
			time.minute = 60
			self.assertEqual(self.module.fuzzy_time(pl=pl, unicode_text=True), 'twelve o’clock')


class TestSys(TestCommon):
	module_name = 'sys'

	def test_uptime(self):
		pl = Pl()
		with replace_attr(self.module, '_get_uptime', lambda: 259200):
			self.assertEqual(self.module.uptime(pl=pl), [{'contents': '3d', 'divider_highlight_group': 'background:divider'}])
		with replace_attr(self.module, '_get_uptime', lambda: 93784):
			self.assertEqual(self.module.uptime(pl=pl), [{'contents': '1d 2h 3m', 'divider_highlight_group': 'background:divider'}])
			self.assertEqual(self.module.uptime(pl=pl, shorten_len=4), [{'contents': '1d 2h 3m 4s', 'divider_highlight_group': 'background:divider'}])
		with replace_attr(self.module, '_get_uptime', lambda: 65536):
			self.assertEqual(self.module.uptime(pl=pl), [{'contents': '18h 12m 16s', 'divider_highlight_group': 'background:divider'}])
			self.assertEqual(self.module.uptime(pl=pl, shorten_len=2), [{'contents': '18h 12m', 'divider_highlight_group': 'background:divider'}])
			self.assertEqual(self.module.uptime(pl=pl, shorten_len=1), [{'contents': '18h', 'divider_highlight_group': 'background:divider'}])

		def _get_uptime():
			raise NotImplementedError

		with replace_attr(self.module, '_get_uptime', _get_uptime):
			self.assertEqual(self.module.uptime(pl=pl), None)

	def test_system_load(self):
		pl = Pl()
		with replace_module_module(self.module, 'os', getloadavg=lambda: (7.5, 3.5, 1.5)):
			with replace_attr(self.module, '_cpu_count', lambda: 2):
				self.assertEqual(self.module.system_load(pl=pl), [
					{'contents': '7.5 ', 'highlight_groups': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
					{'contents': '3.5 ', 'highlight_groups': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 75.0},
					{'contents': '1.5', 'highlight_groups': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 0}
				])
				self.assertEqual(self.module.system_load(pl=pl, format='{avg:.0f}', threshold_good=0, threshold_bad=1), [
					{'contents': '8 ', 'highlight_groups': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
					{'contents': '4 ', 'highlight_groups': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
					{'contents': '2', 'highlight_groups': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 75.0}
				])
				self.assertEqual(self.module.system_load(pl=pl, short=True), [
					{'contents': '7.5', 'highlight_groups': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
				])
				self.assertEqual(self.module.system_load(pl=pl, format='{avg:.0f}', threshold_good=0, threshold_bad=1, short=True), [
					{'contents': '8', 'highlight_groups': ['system_load_gradient', 'system_load'], 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
				])

	def test_cpu_load_percent(self):
		try:
			__import__('psutil')
		except ImportError as e:
			raise SkipTest('Failed to import psutil: {0}'.format(e))
		pl = Pl()
		with replace_module_module(self.module, 'psutil', cpu_percent=lambda **kwargs: 52.3):
			self.assertEqual(self.module.cpu_load_percent(pl=pl), [{
				'contents': '52%',
				'gradient_level': 52.3,
				'highlight_groups': ['cpu_load_percent_gradient', 'cpu_load_percent'],
			}])
			self.assertEqual(self.module.cpu_load_percent(pl=pl, format='{0:.1f}%'), [{
				'contents': '52.3%',
				'gradient_level': 52.3,
				'highlight_groups': ['cpu_load_percent_gradient', 'cpu_load_percent'],
			}])


class TestWthr(TestCommon):
	module_name = 'wthr'

	def test_weather(self):
		pl = Pl()
		with replace_attr(self.module, 'urllib_read', urllib_read):
			self.assertEqual(self.module.weather(pl=pl), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'WINDY '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '14°C', 'gradient_level': 62.857142857142854}
			])
			self.assertEqual(self.module.weather(pl=pl, temp_coldest=0, temp_hottest=100), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'WINDY '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '14°C', 'gradient_level': 14.0}
			])
			self.assertEqual(self.module.weather(pl=pl, temp_coldest=-100, temp_hottest=-50), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'WINDY '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '14°C', 'gradient_level': 100}
			])
			self.assertEqual(self.module.weather(pl=pl, icons={'blustery': 'o'}), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'o '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '14°C', 'gradient_level': 62.857142857142854}
			])
			self.assertEqual(self.module.weather(pl=pl, icons={'windy': 'x'}), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'x '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '14°C', 'gradient_level': 62.857142857142854}
			])
			self.assertEqual(self.module.weather(pl=pl, unit='F'), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'WINDY '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '57°F', 'gradient_level': 62.857142857142854}
			])
			self.assertEqual(self.module.weather(pl=pl, unit='K'), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'WINDY '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '287K', 'gradient_level': 62.857142857142854}
			])
			self.assertEqual(self.module.weather(pl=pl, temp_format='{temp:.1e}C'), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'WINDY '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '1.4e+01C', 'gradient_level': 62.857142857142854}
			])
		with replace_attr(self.module, 'urllib_read', urllib_read):
			self.module.weather.startup(pl=pl, location_query='Meppen,06,DE')
			self.assertEqual(self.module.weather(pl=pl), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_blustery', 'weather_condition_windy', 'weather_conditions', 'weather'], 'contents': 'WINDY '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '14°C', 'gradient_level': 62.857142857142854}
			])
			self.assertEqual(self.module.weather(pl=pl, location_query='Moscow,RU'), [
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_condition_fair_night', 'weather_condition_night', 'weather_conditions', 'weather'], 'contents': 'NIGHT '},
				{'divider_highlight_group': 'background:divider', 'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '9°C', 'gradient_level': 55.714285714285715}
			])
			self.module.weather.shutdown()


class TestI3WM(TestCase):
	@staticmethod
	def get_workspaces():
		return iter([
			{'name': '1: w1', 'output': 'LVDS1', 'focused': False, 'urgent': False, 'visible': False},
			{'name': '2: w2', 'output': 'LVDS1', 'focused': False, 'urgent': False, 'visible': True},
			{'name': '3: w3', 'output': 'HDMI1', 'focused': False, 'urgent': True, 'visible': True},
			{'name': '4: w4', 'output': 'DVI01', 'focused': True, 'urgent': True, 'visible': True},
		])

	def test_workspaces(self):
		pl = Pl()
		with replace_attr(i3wm, 'get_i3_connection', lambda: Args(get_workspaces=self.get_workspaces)):
			segment_info = {}

			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info), [
				{'contents': '1: w1', 'highlight_groups': ['workspace']},
				{'contents': '2: w2', 'highlight_groups': ['w_visible', 'workspace']},
				{'contents': '3: w3', 'highlight_groups': ['w_urgent', 'w_visible', 'workspace']},
				{'contents': '4: w4', 'highlight_groups': ['w_focused', 'w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=None), [
				{'contents': '1: w1', 'highlight_groups': ['workspace']},
				{'contents': '2: w2', 'highlight_groups': ['w_visible', 'workspace']},
				{'contents': '3: w3', 'highlight_groups': ['w_urgent', 'w_visible', 'workspace']},
				{'contents': '4: w4', 'highlight_groups': ['w_focused', 'w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=['focused', 'urgent']), [
				{'contents': '3: w3', 'highlight_groups': ['w_urgent', 'w_visible', 'workspace']},
				{'contents': '4: w4', 'highlight_groups': ['w_focused', 'w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=['visible']), [
				{'contents': '2: w2', 'highlight_groups': ['w_visible', 'workspace']},
				{'contents': '3: w3', 'highlight_groups': ['w_urgent', 'w_visible', 'workspace']},
				{'contents': '4: w4', 'highlight_groups': ['w_focused', 'w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=['visible'], strip=3), [
				{'contents': 'w2', 'highlight_groups': ['w_visible', 'workspace']},
				{'contents': 'w3', 'highlight_groups': ['w_urgent', 'w_visible', 'workspace']},
				{'contents': 'w4', 'highlight_groups': ['w_focused', 'w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=['focused', 'urgent'], output='DVI01'), [
				{'contents': '4: w4', 'highlight_groups': ['w_focused', 'w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=['visible'], output='HDMI1'), [
				{'contents': '3: w3', 'highlight_groups': ['w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=['visible'], strip=3, output='LVDS1'), [
				{'contents': 'w2', 'highlight_groups': ['w_visible', 'workspace']},
			])
			segment_info['output'] = 'LVDS1'
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=['visible'], output='HDMI1'), [
				{'contents': '3: w3', 'highlight_groups': ['w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspaces(pl=pl, segment_info=segment_info, only_show=['visible'], strip=3), [
				{'contents': 'w2', 'highlight_groups': ['w_visible', 'workspace']},
			])

	def test_workspace(self):
		pl = Pl()
		with replace_attr(i3wm, 'get_i3_connection', lambda: Args(get_workspaces=self.get_workspaces)):
			segment_info = {}

			self.assertEqual(i3wm.workspace(pl=pl, segment_info=segment_info, workspace='1: w1'), [
				{'contents': '1: w1', 'highlight_groups': ['workspace']},
			])
			self.assertEqual(i3wm.workspace(pl=pl, segment_info=segment_info, workspace='3: w3', strip=True), [
				{'contents': 'w3', 'highlight_groups': ['w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspace(pl=pl, segment_info=segment_info, workspace='9: w9'), None)
			self.assertEqual(i3wm.workspace(pl=pl, segment_info=segment_info), [
				{'contents': '4: w4', 'highlight_groups': ['w_focused', 'w_urgent', 'w_visible', 'workspace']},
			])
			segment_info['workspace'] = next(self.get_workspaces())
			self.assertEqual(i3wm.workspace(pl=pl, segment_info=segment_info, workspace='4: w4'), [
				{'contents': '4: w4', 'highlight_groups': ['w_focused', 'w_urgent', 'w_visible', 'workspace']},
			])
			self.assertEqual(i3wm.workspace(pl=pl, segment_info=segment_info, strip=True), [
				{'contents': 'w1', 'highlight_groups': ['workspace']},
			])

	def test_mode(self):
		pl = Pl()
		self.assertEqual(i3wm.mode(pl=pl, segment_info={'mode': 'default'}), None)
		self.assertEqual(i3wm.mode(pl=pl, segment_info={'mode': 'test'}), 'test')
		self.assertEqual(i3wm.mode(pl=pl, segment_info={'mode': 'default'}, names={'default': 'test'}), 'test')
		self.assertEqual(i3wm.mode(pl=pl, segment_info={'mode': 'test'}, names={'default': 'test', 'test': 't'}), 't')

	def test_scratchpad(self):
		class Conn(object):
			def get_tree(self):
				return self

			def descendents(self):
				nodes_unfocused = [Args(focused = False)]
				nodes_focused = [Args(focused = True)]

				workspace_scratch = lambda: Args(name='__i3_scratch')
				workspace_noscratch = lambda: Args(name='2: www')
				return [
					Args(scratchpad_state='fresh', urgent=False, workspace=workspace_scratch, nodes=nodes_unfocused),
					Args(scratchpad_state='changed', urgent=True, workspace=workspace_noscratch, nodes=nodes_focused),
					Args(scratchpad_state='fresh', urgent=False, workspace=workspace_scratch, nodes=nodes_unfocused),
					Args(scratchpad_state=None, urgent=False, workspace=workspace_noscratch, nodes=nodes_unfocused),
					Args(scratchpad_state='fresh', urgent=False, workspace=workspace_scratch, nodes=nodes_focused),
					Args(scratchpad_state=None, urgent=True, workspace=workspace_noscratch, nodes=nodes_unfocused),
				]

		pl = Pl()
		with replace_attr(i3wm, 'get_i3_connection', lambda: Conn()):
			self.assertEqual(i3wm.scratchpad(pl=pl), [
				{'contents': 'O', 'highlight_groups': ['scratchpad']},
				{'contents': 'X', 'highlight_groups': ['scratchpad:urgent', 'scratchpad:focused', 'scratchpad:visible', 'scratchpad']},
				{'contents': 'O', 'highlight_groups': ['scratchpad']},
				{'contents': 'X', 'highlight_groups': ['scratchpad:visible', 'scratchpad']},
				{'contents': 'O', 'highlight_groups': ['scratchpad:focused', 'scratchpad']},
				{'contents': 'X', 'highlight_groups': ['scratchpad:urgent', 'scratchpad:visible', 'scratchpad']},
			])
			self.assertEqual(i3wm.scratchpad(pl=pl, icons={'changed': '-', 'fresh': 'o'}), [
				{'contents': 'o', 'highlight_groups': ['scratchpad']},
				{'contents': '-', 'highlight_groups': ['scratchpad:urgent', 'scratchpad:focused', 'scratchpad:visible', 'scratchpad']},
				{'contents': 'o', 'highlight_groups': ['scratchpad']},
				{'contents': '-', 'highlight_groups': ['scratchpad:visible', 'scratchpad']},
				{'contents': 'o', 'highlight_groups': ['scratchpad:focused', 'scratchpad']},
				{'contents': '-', 'highlight_groups': ['scratchpad:urgent', 'scratchpad:visible', 'scratchpad']},
			])


class TestMail(TestCommon):
	module_name = 'mail'

	def test_email_imap_alert(self):
		# TODO
		pass


class TestPlayers(TestCommon):
	module_name = 'players'

	def test_now_playing(self):
		# TODO
		pass


class TestBat(TestCommon):
	module_name = 'bat'

	def test_battery(self):
		pl = Pl()

		def _get_battery_status(pl):
			return 86, False

		with replace_attr(self.module, '_get_battery_status', _get_battery_status):
			self.assertEqual(self.module.battery(pl=pl), [{
				'contents': '  86%',
				'highlight_groups': ['battery_gradient', 'battery'],
				'gradient_level': 14,
			}])
			self.assertEqual(self.module.battery(pl=pl, format='{capacity:.2f}'), [{
				'contents': '0.86',
				'highlight_groups': ['battery_gradient', 'battery'],
				'gradient_level': 14,
			}])
			self.assertEqual(self.module.battery(pl=pl, steps=7), [{
				'contents': '  86%',
				'highlight_groups': ['battery_gradient', 'battery'],
				'gradient_level': 14,
			}])
			self.assertEqual(self.module.battery(pl=pl, gamify=True), [
				{
					'contents': ' ',
					'draw_inner_divider': False,
					'highlight_groups': ['battery_offline', 'battery_ac_state', 'battery_gradient', 'battery'],
					'gradient_level': 0
				},
				{
					'contents': 'OOOO',
					'draw_inner_divider': False,
					'highlight_groups': ['battery_full', 'battery_gradient', 'battery'],
					'gradient_level': 0
				},
				{
					'contents': 'O',
					'draw_inner_divider': False,
					'highlight_groups': ['battery_empty', 'battery_gradient', 'battery'],
					'gradient_level': 100
				}
			])
			self.assertEqual(self.module.battery(pl=pl, gamify=True, full_heart='+', empty_heart='-', steps='10'), [
				{
					'contents': ' ',
					'draw_inner_divider': False,
					'highlight_groups': ['battery_offline', 'battery_ac_state', 'battery_gradient', 'battery'],
					'gradient_level': 0
				},
				{
					'contents': '++++++++',
					'draw_inner_divider': False,
					'highlight_groups': ['battery_full', 'battery_gradient', 'battery'],
					'gradient_level': 0
				},
				{
					'contents': '--',
					'draw_inner_divider': False,
					'highlight_groups': ['battery_empty', 'battery_gradient', 'battery'],
					'gradient_level': 100
				}
			])

	def test_battery_with_ac_online(self):
		pl = Pl()

		def _get_battery_status(pl):
			return 86, True

		with replace_attr(self.module, '_get_battery_status', _get_battery_status):
			self.assertEqual(self.module.battery(pl=pl, online='C', offline=' '), [
				{
					'contents': 'C 86%',
					'highlight_groups': ['battery_gradient', 'battery'],
					'gradient_level': 14,
				}])

	def test_battery_with_ac_offline(self):
		pl = Pl()

		def _get_battery_status(pl):
			return 86, False

		with replace_attr(self.module, '_get_battery_status', _get_battery_status):
			self.assertEqual(self.module.battery(pl=pl, online='C', offline=' '), [
				{
					'contents': '  86%',
					'highlight_groups': ['battery_gradient', 'battery'],
					'gradient_level': 14,
				}])


class TestVim(TestCase):
	def test_mode(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info), 'NORMAL')
		self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info, override={'i': 'INS'}), 'NORMAL')
		self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info, override={'n': 'NORM'}), 'NORM')
		with vim_module._with('mode', 'i') as segment_info:
			self.assertEqual(self.vim.mode(pl=pl, segment_info=segment_info), 'INSERT')
		with vim_module._with('mode', 'i\0') as segment_info:
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
			{'contents': '[No file]', 'highlight_groups': ['file_name_no_file', 'file_name']}
		])
		self.assertEqual(self.vim.file_name(pl=pl, segment_info=segment_info, display_no_file=True, no_file_text='X'), [
			{'contents': 'X', 'highlight_groups': ['file_name_no_file', 'file_name']}
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
		with vim_module._with(
			'buffer',
			os.path.join(
				os.path.dirname(os.path.dirname(__file__)), 'empty')
		) as segment_info:
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
				{'contents': '50', 'highlight_groups': ['line_percent_gradient', 'line_percent'], 'gradient_level': 50 * 100.0 / 101}
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
				{'contents': '50%', 'highlight_groups': ['position_gradient', 'position'], 'gradient_level': 50.0}
			])
			vim_module._set_cursor(0, 0)
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info), 'Top')
			vim_module._set_cursor(97, 0)
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info, position_strings={'top': 'Comienzo', 'bottom': 'Final', 'all': 'Todo'}), 'Final')
			segment_info['buffer'][0:-1] = [str(i) for i in range(2)]
			vim_module._set_cursor(0, 0)
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info, position_strings={'top': 'Comienzo', 'bottom': 'Final', 'all': 'Todo'}), 'Todo')
			self.assertEqual(self.vim.position(pl=pl, segment_info=segment_info, gradient=True), [
				{'contents': 'All', 'highlight_groups': ['position_gradient', 'position'], 'gradient_level': 0.0}
			])
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_cursor_current(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.line_current(pl=pl, segment_info=segment_info), '1')
		self.assertEqual(self.vim.col_current(pl=pl, segment_info=segment_info), '1')
		self.assertEqual(self.vim.virtcol_current(pl=pl, segment_info=segment_info), [{
			'highlight_groups': ['virtcol_current_gradient', 'virtcol_current', 'col_current'], 'contents': '1', 'gradient_level': 100.0 / 80,
		}])
		self.assertEqual(self.vim.virtcol_current(pl=pl, segment_info=segment_info, gradient=False), [{
			'highlight_groups': ['virtcol_current', 'col_current'], 'contents': '1',
		}])

	def test_modified_buffers(self):
		pl = Pl()
		self.assertEqual(self.vim.modified_buffers(pl=pl), None)

	def test_branch(self):
		pl = Pl()
		create_watcher = get_fallback_create_watcher()
		branch = partial(self.vim.branch, pl=pl, create_watcher=create_watcher)
		with vim_module._with('buffer', '/foo') as segment_info:
			with replace_attr(self.vcs, 'guess', get_dummy_guess(status=lambda: None)):
				with replace_attr(self.vcs, 'tree_status', lambda repo, pl: None):
					self.assertEqual(branch(segment_info=segment_info, status_colors=False), [
						{'divider_highlight_group': 'branch:divider', 'highlight_groups': ['branch'], 'contents': 'foo'}
					])
					self.assertEqual(branch(segment_info=segment_info, status_colors=True), [
						{'divider_highlight_group': 'branch:divider', 'highlight_groups': ['branch_clean', 'branch'], 'contents': 'foo'}
					])
			with replace_attr(self.vcs, 'guess', get_dummy_guess(status=lambda: 'DU')):
				with replace_attr(self.vcs, 'tree_status', lambda repo, pl: 'DU'):
					self.assertEqual(branch(segment_info=segment_info, status_colors=False), [
						{'divider_highlight_group': 'branch:divider', 'highlight_groups': ['branch'], 'contents': 'foo'}
					])
					self.assertEqual(branch(segment_info=segment_info, status_colors=True), [
						{'divider_highlight_group': 'branch:divider', 'highlight_groups': ['branch_dirty', 'branch'], 'contents': 'foo'}
					])
			with replace_attr(self.vcs, 'guess', get_dummy_guess(status=lambda: 'U')):
				with replace_attr(self.vcs, 'tree_status', lambda repo, pl: 'U'):
					self.assertEqual(branch(segment_info=segment_info, status_colors=False, ignore_statuses=['U']), [
						{'divider_highlight_group': 'branch:divider', 'highlight_groups': ['branch'], 'contents': 'foo'}
					])
					self.assertEqual(branch(segment_info=segment_info, status_colors=True, ignore_statuses=['DU']), [
						{'divider_highlight_group': 'branch:divider', 'highlight_groups': ['branch_dirty', 'branch'], 'contents': 'foo'}
					])
					self.assertEqual(branch(segment_info=segment_info, status_colors=True), [
						{'divider_highlight_group': 'branch:divider', 'highlight_groups': ['branch_dirty', 'branch'], 'contents': 'foo'}
					])
					self.assertEqual(branch(segment_info=segment_info, status_colors=True, ignore_statuses=['U']), [
						{'divider_highlight_group': 'branch:divider', 'highlight_groups': ['branch_clean', 'branch'], 'contents': 'foo'}
					])

	def test_stash(self):
		pl = Pl()
		create_watcher = get_fallback_create_watcher()
		with vim_module._with('buffer', '/foo') as segment_info:
			stash = partial(self.vim.stash, pl=pl, create_watcher=create_watcher, segment_info=segment_info)

			def forge_stash(n):
				return replace_attr(self.vcs, 'guess', get_dummy_guess(stash=lambda: n))

			with forge_stash(0):
				self.assertEqual(stash(), None)
			with forge_stash(1):
				self.assertEqual(stash(), [{
					'divider_highlight_group': 'stash:divider',
					'highlight_groups': ['stash'],
					'contents': '1'
				}])
			with forge_stash(2):
				self.assertEqual(stash(), [{
					'divider_highlight_group': 'stash:divider',
					'highlight_groups': ['stash'],
					'contents': '2'
				}])

	def test_file_vcs_status(self):
		pl = Pl()
		create_watcher = get_fallback_create_watcher()
		file_vcs_status = partial(self.vim.file_vcs_status, pl=pl, create_watcher=create_watcher)
		with vim_module._with('buffer', '/foo') as segment_info:
			with replace_attr(self.vim, 'guess', get_dummy_guess(status=lambda file: 'M')):
				self.assertEqual(file_vcs_status(segment_info=segment_info), [
					{'highlight_groups': ['file_vcs_status_M', 'file_vcs_status'], 'contents': 'M'}
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
				'highlight_groups': ['trailing_whitespace', 'warning'],
				'contents': '1',
			}])
			self.assertEqual(trailing_whitespace(), [{
				'highlight_groups': ['trailing_whitespace', 'warning'],
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

	def test_tab(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()
		self.assertEqual(self.vim.tab(pl=pl, segment_info=segment_info), [{
			'contents': None,
			'literal_contents': (0, '%1T'),
		}])
		self.assertEqual(self.vim.tab(pl=pl, segment_info=segment_info, end=True), [{
			'contents': None,
			'literal_contents': (0, '%T'),
		}])

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
					'highlight_groups': ['tab_modified_indicator', 'modified_indicator'],
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
					'highlight_groups': ['tab_modified_indicator', 'modified_indicator'],
				}])

	def test_csv_col_current(self):
		pl = Pl()
		segment_info = vim_module._get_segment_info()

		def csv_col_current(**kwargs):
			self.vim.csv_cache and self.vim.csv_cache.clear()
			return self.vim.csv_col_current(pl=pl, segment_info=segment_info, **kwargs)

		buffer = segment_info['buffer']
		try:
			self.assertEqual(csv_col_current(), None)
			buffer.options['filetype'] = 'csv'
			self.assertEqual(csv_col_current(), None)
			buffer[:] = ['1;2;3', '4;5;6']
			vim_module._set_cursor(1, 1)
			self.assertEqual(csv_col_current(), [{
				'contents': '1', 'highlight_groups': ['csv:column_number', 'csv']
			}])
			vim_module._set_cursor(2, 3)
			self.assertEqual(csv_col_current(), [{
				'contents': '2', 'highlight_groups': ['csv:column_number', 'csv']
			}])
			vim_module._set_cursor(2, 3)
			self.assertEqual(csv_col_current(display_name=True), [{
				'contents': '2', 'highlight_groups': ['csv:column_number', 'csv']
			}, {
				'contents': ' (2)', 'highlight_groups': ['csv:column_name', 'csv']
			}])
			buffer[:0] = ['Foo;Bar;Baz']
			vim_module._set_cursor(2, 3)
			self.assertEqual(csv_col_current(), [{
				'contents': '2', 'highlight_groups': ['csv:column_number', 'csv']
			}, {
				'contents': ' (Bar)', 'highlight_groups': ['csv:column_name', 'csv']
			}])
			if sys.version_info < (2, 7):
				raise SkipTest('csv module in Python-2.6 does not handle multiline csv files well')
			buffer[len(buffer):] = ['1;"bc', 'def', 'ghi', 'jkl";3']
			vim_module._set_cursor(5, 1)
			self.assertEqual(csv_col_current(), [{
				'contents': '2', 'highlight_groups': ['csv:column_number', 'csv']
			}, {
				'contents': ' (Bar)', 'highlight_groups': ['csv:column_name', 'csv']
			}])
			vim_module._set_cursor(7, 6)
			self.assertEqual(csv_col_current(), [{
				'contents': '3', 'highlight_groups': ['csv:column_number', 'csv']
			}, {
				'contents': ' (Baz)', 'highlight_groups': ['csv:column_name', 'csv']
			}])
			self.assertEqual(csv_col_current(name_format=' ({column_name:.1})'), [{
				'contents': '3', 'highlight_groups': ['csv:column_number', 'csv']
			}, {
				'contents': ' (B)', 'highlight_groups': ['csv:column_name', 'csv']
			}])
			self.assertEqual(csv_col_current(display_name=True, name_format=' ({column_name:.1})'), [{
				'contents': '3', 'highlight_groups': ['csv:column_number', 'csv']
			}, {
				'contents': ' (B)', 'highlight_groups': ['csv:column_name', 'csv']
			}])
			self.assertEqual(csv_col_current(display_name=False, name_format=' ({column_name:.1})'), [{
				'contents': '3', 'highlight_groups': ['csv:column_number', 'csv']
			}])
			self.assertEqual(csv_col_current(display_name=False), [{
				'contents': '3', 'highlight_groups': ['csv:column_number', 'csv']
			}])
		finally:
			vim_module._bw(segment_info['bufnr'])

	@classmethod
	def setUpClass(cls):
		sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vim_sys_path')))
		from powerline.segments import vim
		cls.vim = vim
		from powerline.segments.common import vcs
		cls.vcs = vcs

	@classmethod
	def tearDownClass(cls):
		sys.path.pop(0)


class TestPDB(TestCase):
	def test_current_line(self):
		pl = Pl()
		self.assertEqual(pdb.current_line(pl=pl, segment_info={'curframe': Args(f_lineno=10)}), '10')

	def test_current_file(self):
		pl = Pl()
		cf = lambda **kwargs: pdb.current_file(
			pl=pl,
			segment_info={'curframe': Args(f_code=Args(co_filename='/tmp/abc.py'))},
			**kwargs
		)
		self.assertEqual(cf(), 'abc.py')
		self.assertEqual(cf(basename=True), 'abc.py')
		self.assertEqual(cf(basename=False), '/tmp/abc.py')

	def test_current_code_name(self):
		pl = Pl()
		ccn = lambda **kwargs: pdb.current_code_name(
			pl=pl,
			segment_info={'curframe': Args(f_code=Args(co_name='<module>'))},
			**kwargs
		)
		self.assertEqual(ccn(), '<module>')

	def test_current_context(self):
		pl = Pl()
		cc = lambda **kwargs: pdb.current_context(
			pl=pl,
			segment_info={'curframe': Args(f_code=Args(co_name='<module>', co_filename='/tmp/abc.py'))},
			**kwargs
		)
		self.assertEqual(cc(), 'abc.py')

	def test_stack_depth(self):
		pl = Pl()
		sd = lambda **kwargs: pdb.stack_depth(
			pl=pl,
			segment_info={'pdb': Args(stack=[1, 2, 3]), 'initial_stack_length': 1},
			**kwargs
		)
		self.assertEqual(sd(), '2')
		self.assertEqual(sd(full_stack=False), '2')
		self.assertEqual(sd(full_stack=True), '3')


old_cwd = None


def setUpModule():
	global old_cwd
	global __file__
	old_cwd = os.getcwd()
	__file__ = os.path.abspath(__file__)
	os.chdir(os.path.dirname(os.path.dirname(__file__)))


def tearDownModule():
	global old_cwd
	os.chdir(old_cwd)


if __name__ == '__main__':
	from tests.modules import main
	main()
