# -*- coding: utf-8 -*-

from unittest import TestCase
from powerline.segments import shell, common
import tests.vim as vim_module
import sys
import os
import imp


class Args(object):
	theme_option = None
	config = None
	config_path = None
	ext = ['shell']
	renderer_module = None

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)


vim = None


class TestShell(TestCase):
	def test_last_status(self):
		self.assertEqual(shell.last_status(Args(last_exit_code=10)),
				[{'contents': '10', 'highlight_group': 'exit_fail'}])
		self.assertEqual(shell.last_status(Args(last_exit_code=None)), None)

	def test_last_pipe_status(self):
		self.assertEqual(shell.last_pipe_status(Args(last_pipe_status=[])), None)
		self.assertEqual(shell.last_pipe_status(Args(last_pipe_status=[0, 0, 0])), None)
		self.assertEqual(shell.last_pipe_status(Args(last_pipe_status=[0, 2, 0])),
				[{'contents': '0', 'highlight_group': 'exit_success'},
				{'contents': '2', 'highlight_group': 'exit_fail'},
				{'contents': '0', 'highlight_group': 'exit_success'}])


class TestCommon(TestCase):
	def test_hostname(self):
		os.environ['SSH_CLIENT'] = '192.168.0.12 40921 22'
		socket = imp.new_module('socket')
		socket.gethostname = lambda: 'abc'
		sys.modules['socket'] = socket
		try:
			self.assertEqual(common.hostname(), 'abc')
			self.assertEqual(common.hostname(only_if_ssh=True), 'abc')
			os.environ.pop('SSH_CLIENT')
			self.assertEqual(common.hostname(), 'abc')
			self.assertEqual(common.hostname(only_if_ssh=True), None)
		finally:
			sys.modules.pop('socket')

	def test_user(self):
		new_os = imp.new_module('os')
		new_os.environ = {'USER': 'def'}
		common.os = new_os
		try:
			self.assertEqual(common.user(), [{'contents': 'def', 'highlight_group': 'user'}])
			new_os.geteuid = lambda: 1
			self.assertEqual(common.user(), [{'contents': 'def', 'highlight_group': 'user'}])
			new_os.geteuid = lambda: 0
			self.assertEqual(common.user(), [{'contents': 'def', 'highlight_group': ['superuser', 'user']}])
		finally:
			common.os = os

	def test_branch(self):
		vcslib = imp.new_module('powerline.lib.vcs')
		vcslib.guess = lambda path: Args(branch=lambda: os.path.basename(path))
		sys.modules['powerline.lib.vcs'] = vcslib
		try:
			self.assertEqual(common.branch(), 'tests')
			vcslib.guess = lambda path: None
			self.assertEqual(common.branch(), None)
		finally:
			sys.modules.pop('powerline.lib.vcs')

	def test_cwd(self):
		new_os = imp.new_module('os')
		new_os.path = os.path
		new_os.environ = {}
		new_os.sep = '/'
		new_os.getcwd = lambda: '/abc/def/ghi/foo/bar'
		common.os = new_os
		try:
			self.assertEqual(common.cwd(),
					[{'contents': '/', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'abc', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'def', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'foo', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd']}])
			new_os.getcwdu = lambda: '/abc/def/ghi/foo/bar'
			self.assertEqual(common.cwd(),
					[{'contents': '/', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'abc', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'def', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'ghi', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'foo', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd']}])
			new_os.environ['HOME'] = '/abc/def/ghi'
			self.assertEqual(common.cwd(),
					[{'contents': '~', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'foo', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd']}])
			self.assertEqual(common.cwd(dir_limit_depth=3),
					[{'contents': '~', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'foo', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd']}])
			self.assertEqual(common.cwd(dir_limit_depth=1),
					[{'contents': '⋯', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd']}])
			self.assertEqual(common.cwd(dir_limit_depth=2, dir_shorten_len=2),
					[{'contents': '~', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'fo', 'divider_highlight_group': 'cwd:divider'},
					{'contents': 'bar', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd']}])
			ose = OSError()
			ose.errno = 2

			def raises(exc):
				raise exc

			new_os.getcwdu = lambda: raises(ose)
			self.assertEqual(common.cwd(dir_limit_depth=2, dir_shorten_len=2),
					[{'contents': '[not found]', 'divider_highlight_group': 'cwd:divider', 'highlight_group': ['cwd:current_folder', 'cwd']}])
			new_os.getcwdu = lambda: raises(OSError())
			with self.assertRaises(OSError):
				common.cwd(dir_limit_depth=2, dir_shorten_len=2),
			new_os.getcwdu = lambda: raises(ValueError())
			with self.assertRaises(ValueError):
				common.cwd(dir_limit_depth=2, dir_shorten_len=2),
		finally:
			common.os = os

	def test_date(self):
		datetime = imp.new_module('datetime')
		datetime.datetime = Args(now=lambda: Args(strftime=lambda fmt: fmt))
		sys.modules['datetime'] = datetime
		try:
			self.assertEqual(common.date(), [{'contents': '%Y-%m-%d', 'highlight_group': ['date'], 'divider_highlight_group': None}])
			self.assertEqual(common.date(format='%H:%M', istime=True), [{'contents': '%H:%M', 'highlight_group': ['time', 'date'], 'divider_highlight_group': 'time:divider'}])
		finally:
			sys.modules.pop('datetime')

	def test_fuzzy_time(self):
		datetime = imp.new_module('datetime')
		time = Args(hour=0, minute=45)
		datetime.datetime = Args(now=lambda: time)
		sys.modules['datetime'] = datetime
		try:
			self.assertEqual(common.fuzzy_time(), 'quarter to one')
			time.hour = 23
			time.minute = 59
			self.assertEqual(common.fuzzy_time(), 'round about midnight')
			time.minute = 33
			self.assertEqual(common.fuzzy_time(), 'twenty-five to twelve')
			time.minute = 60
			self.assertEqual(common.fuzzy_time(), 'twelve o\'clock')
		finally:
			sys.modules.pop('datetime')

	def test_external_ip(self):
		old_urllib_read = common.urllib_read
		common.urllib_read = lambda url: '127.0.0.1'
		try:
			self.assertEqual(common.external_ip(), [{'contents': '127.0.0.1', 'divider_highlight_group': 'background:divider'}])
		finally:
			common.urllib_read = old_urllib_read

	def test_uptime(self):
		# TODO
		pass

	def test_weather(self):
		# TODO
		pass

	def test_system_load(self):
		new_os = imp.new_module('os')
		new_os.getloadavg = lambda: (7.5, 3.5, 1.5)
		multiprocessing = imp.new_module('multiprocessing')
		multiprocessing.cpu_count = lambda: 2
		common.os = new_os
		sys.modules['multiprocessing'] = multiprocessing
		try:
			self.assertEqual(common.system_load(),
					[{'contents': '7.5 ', 'highlight_group': ['system_load_ugly', 'system_load'], 'draw_divider': True, 'divider_highlight_group': 'background:divider'},
					{'contents': '3.5 ', 'highlight_group': ['system_load_bad', 'system_load'], 'draw_divider': False, 'divider_highlight_group': 'background:divider'},
					{'contents': '1.5', 'highlight_group': ['system_load_good', 'system_load'], 'draw_divider': False, 'divider_highlight_group': 'background:divider'}])
			self.assertEqual(common.system_load(format='{avg:.0f}', threshold_good=0, threshold_bad=1),
					[{'contents': '8 ', 'highlight_group': ['system_load_ugly', 'system_load'], 'draw_divider': True, 'divider_highlight_group': 'background:divider'},
					{'contents': '4 ', 'highlight_group': ['system_load_ugly', 'system_load'], 'draw_divider': False, 'divider_highlight_group': 'background:divider'},
					{'contents': '2', 'highlight_group': ['system_load_bad', 'system_load'], 'draw_divider': False, 'divider_highlight_group': 'background:divider'}])
		finally:
			common.os = os
			sys.modules.pop('multiprocessing')

	def test_cpu_load_percent(self):
		psutil = imp.new_module('psutil')
		psutil.cpu_percent = lambda **kwargs: 52.3
		sys.modules['psutil'] = psutil
		try:
			self.assertEqual(common.cpu_load_percent(), '52%')
		finally:
			sys.modules.pop('psutil')

	def test_network_load(self):
		# TODO
		pass

	def test_virtualenv(self):
		os.environ['VIRTUAL_ENV'] = '/abc/def/ghi'
		self.assertEqual(common.virtualenv(), 'ghi')
		os.environ.pop('VIRTUAL_ENV')
		self.assertEqual(common.virtualenv(), None)

	def test_email_imap_alert(self):
		# TODO
		pass

	def test_now_playing(self):
		# TODO
		pass


class TestVim(TestCase):
	def test_mode(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.mode(segment_info=segment_info), 'NORMAL')
		self.assertEqual(vim.mode(segment_info=segment_info, override={'i': 'INS'}), 'NORMAL')
		self.assertEqual(vim.mode(segment_info=segment_info, override={'n': 'NORM'}), 'NORM')
		try:
			vim_module._start_mode('i')
			segment_info = vim_module._get_segment_info()
			self.assertEqual(vim.mode(segment_info=segment_info), 'INSERT')
			vim_module._start_mode(chr(ord('V') - 0x40))
			segment_info = vim_module._get_segment_info()
			self.assertEqual(vim.mode(segment_info=segment_info), 'V·BLCK')
			self.assertEqual(vim.mode(segment_info=segment_info, override={'^V': 'VBLK'}), 'VBLK')
		finally:
			vim_module._start_mode('n')

	def test_modified_indicator(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.modified_indicator(segment_info=segment_info), None)
		segment_info['buffer'][0] = 'abc'
		try:
			self.assertEqual(vim.modified_indicator(segment_info=segment_info), '+')
			self.assertEqual(vim.modified_indicator(segment_info=segment_info, text='-'), '-')
		finally:
			vim_module._undo()

	def test_paste_indicator(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.paste_indicator(segment_info=segment_info), None)
		vim_module._options['paste'] = 1
		try:
			self.assertEqual(vim.paste_indicator(segment_info=segment_info), 'PASTE')
			self.assertEqual(vim.paste_indicator(segment_info=segment_info, text='P'), 'P')
		finally:
			vim_module._options['paste'] = 0

	def test_readonly_indicator(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.readonly_indicator(segment_info=segment_info), None)
		vim_module._buf_options[vim_module._buffer()]['readonly'] = 1
		try:
			self.assertEqual(vim.readonly_indicator(segment_info=segment_info), '')
			self.assertEqual(vim.readonly_indicator(segment_info=segment_info, text='L'), 'L')
		finally:
			vim_module._buf_options[vim_module._buffer()]['readonly'] = 0

	def test_file_directory(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.file_directory(segment_info=segment_info), None)
		os.environ['HOME'] = '/home/foo'
		vim_module._edit('/tmp/abc')
		segment_info = vim_module._get_segment_info()
		try:
			self.assertEqual(vim.file_directory(segment_info=segment_info), '/tmp/')
			os.environ['HOME'] = '/tmp'
			self.assertEqual(vim.file_directory(segment_info=segment_info), '~/')
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_file_name(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.file_name(segment_info=segment_info), None)
		self.assertEqual(vim.file_name(segment_info=segment_info, display_no_file=True),
				[{'contents': '[No file]', 'highlight_group': ['file_name_no_file', 'file_name']}])
		self.assertEqual(vim.file_name(segment_info=segment_info, display_no_file=True, no_file_text='X'),
				[{'contents': 'X', 'highlight_group': ['file_name_no_file', 'file_name']}])
		vim_module._edit('/tmp/abc')
		segment_info = vim_module._get_segment_info()
		try:
			self.assertEqual(vim.file_name(segment_info=segment_info), 'abc')
		finally:
			vim_module._bw(segment_info['bufnr'])
		vim_module._edit('/tmp/’’')
		segment_info = vim_module._get_segment_info()
		try:
			self.assertEqual(vim.file_name(segment_info=segment_info), '’’')
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_file_size(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.file_size(segment_info=segment_info), None)
		vim_module._edit(os.path.join(os.path.dirname(__file__), 'empty'))
		segment_info = vim_module._get_segment_info()
		try:
			self.assertEqual(vim.file_size(segment_info=segment_info), '0 B')
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_file_opts(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.file_format(segment_info=segment_info),
				[{'divider_highlight_group': 'background:divider', 'contents': 'unix'}])
		self.assertEqual(vim.file_encoding(segment_info=segment_info),
				[{'divider_highlight_group': 'background:divider', 'contents': 'utf-8'}])
		self.assertEqual(vim.file_type(segment_info=segment_info), None)
		vim_module._set_filetype('python')
		try:
			self.assertEqual(vim.file_type(segment_info=segment_info),
					[{'divider_highlight_group': 'background:divider', 'contents': 'python'}])
		finally:
			vim_module._set_filetype('')

	def test_line_percent(self):
		segment_info = vim_module._get_segment_info()
		segment_info['buffer'][0:-1] = [str(i) for i in range(100)]
		try:
			self.assertEqual(vim.line_percent(segment_info=segment_info), '0')
			vim_module._set_cursor(50, 0)
			self.assertEqual(vim.line_percent(segment_info=segment_info), '49')
			self.assertEqual(vim.line_percent(segment_info=segment_info, gradient=True),
					[{'contents': '49', 'highlight_group': ['line_percent_gradient', 'line_percent'], 'gradient_level': 49}])
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_cursor_current(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.line_current(segment_info=segment_info), '1')
		self.assertEqual(vim.col_current(segment_info=segment_info), '1')
		self.assertEqual(vim.virtcol_current(segment_info=segment_info),
				[{'highlight_group': ['virtcol_current', 'col_current'], 'contents': '1'}])

	def test_modified_buffers(self):
		self.assertEqual(vim.modified_buffers(), None)

	def test_branch(self):
		# TODO
		pass

	def test_file_vcs_status(self):
		# TODO
		pass

	def test_repository_status(self):
		# TODO
		pass


old_cwd = None


def setUpModule():
	global old_cwd
	old_cwd = os.getcwd()
	os.chdir(os.path.dirname(__file__))
	sys.modules['vim'] = vim_module._get_module()
	from powerline.segments import vim
	globals()['vim'] = vim


def tearDownModule():
	global old_cwd
	sys.modules.pop('vim')
	os.chdir(old_cwd)
