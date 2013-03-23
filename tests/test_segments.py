# vim:fileencoding=utf-8:noet

from powerline.segments import shell, common
import tests.vim as vim_module
import sys
import os
from tests.lib import Args, urllib_read, replace_module_attr, new_module, replace_module_module, replace_env
from tests import TestCase


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
		with replace_env('SSH_CLIENT', '192.168.0.12 40921 22'):
			with replace_module_module(common, 'socket', gethostname=lambda: 'abc'):
				self.assertEqual(common.hostname(), 'abc')
				self.assertEqual(common.hostname(only_if_ssh=True), 'abc')
				os.environ.pop('SSH_CLIENT')
				self.assertEqual(common.hostname(), 'abc')
				self.assertEqual(common.hostname(only_if_ssh=True), None)

	def test_user(self):
		new_os = new_module('os', environ={'USER': 'def'}, getpid=lambda: 1)
		new_psutil = new_module('psutil', Process=lambda pid: Args(username='def'))
		with replace_module_attr(common, 'os', new_os):
			with replace_module_attr(common, 'psutil', new_psutil):
				self.assertEqual(common.user(), [{'contents': 'def', 'highlight_group': 'user'}])
				new_os.geteuid = lambda: 1
				self.assertEqual(common.user(), [{'contents': 'def', 'highlight_group': 'user'}])
				new_os.geteuid = lambda: 0
				self.assertEqual(common.user(), [{'contents': 'def', 'highlight_group': ['superuser', 'user']}])

	def test_branch(self):
		with replace_module_attr(common, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda: None)):
			self.assertEqual(common.branch(status_colors=False), 'tests')
			self.assertEqual(common.branch(status_colors=True),
					[{'contents': 'tests', 'highlight_group': ['branch_clean', 'branch']}])
		with replace_module_attr(common, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda: 'D  ')):
			self.assertEqual(common.branch(status_colors=False), 'tests')
			self.assertEqual(common.branch(),
					[{'contents': 'tests', 'highlight_group': ['branch_dirty', 'branch']}])
		with replace_module_attr(common, 'guess', lambda path: None):
			self.assertEqual(common.branch(), None)

	def test_cwd(self):
		new_os = new_module('os', path=os.path, environ={}, sep='/')
		new_os.getcwd = lambda: '/abc/def/ghi/foo/bar'
		with replace_module_attr(common, 'os', new_os):
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
			self.assertRaises(OSError, common.cwd, tuple(), {'dir_limit_depth': 2, 'dir_shorten_len': 2})
			new_os.getcwdu = lambda: raises(ValueError())
			self.assertRaises(ValueError, common.cwd, tuple(), {'dir_limit_depth': 2, 'dir_shorten_len': 2})

	def test_date(self):
		with replace_module_attr(common, 'datetime', Args(now=lambda: Args(strftime=lambda fmt: fmt))):
			self.assertEqual(common.date(), [{'contents': '%Y-%m-%d', 'highlight_group': ['date'], 'divider_highlight_group': None}])
			self.assertEqual(common.date(format='%H:%M', istime=True), [{'contents': '%H:%M', 'highlight_group': ['time', 'date'], 'divider_highlight_group': 'time:divider'}])

	def test_fuzzy_time(self):
		time = Args(hour=0, minute=45)
		with replace_module_attr(common, 'datetime', Args(now=lambda: time)):
			self.assertEqual(common.fuzzy_time(), 'quarter to one')
			time.hour = 23
			time.minute = 59
			self.assertEqual(common.fuzzy_time(), 'round about midnight')
			time.minute = 33
			self.assertEqual(common.fuzzy_time(), 'twenty-five to twelve')
			time.minute = 60
			self.assertEqual(common.fuzzy_time(), 'twelve o\'clock')

	def test_external_ip(self):
		with replace_module_attr(common, 'urllib_read', urllib_read):
			self.assertEqual(common.external_ip(), [{'contents': '127.0.0.1', 'divider_highlight_group': 'background:divider'}])

	def test_uptime(self):
		with replace_module_attr(common, '_get_uptime', lambda: 65536):
			self.assertEqual(common.uptime(), [{'contents': '0d 18h 12m', 'divider_highlight_group': 'background:divider'}])

		def _get_uptime():
			raise NotImplementedError

		with replace_module_attr(common, '_get_uptime', _get_uptime):
			self.assertEqual(common.uptime(), None)

	def test_weather(self):
		with replace_module_attr(common, 'urllib_read', urllib_read):
			self.assertEqual(common.weather(), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': '☁ '},
				{'draw_divider': False, 'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 30.0}
				])
			self.assertEqual(common.weather(temp_coldest=0, temp_hottest=100), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': '☁ '},
				{'draw_divider': False, 'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 0}
				])
			self.assertEqual(common.weather(temp_coldest=-100, temp_hottest=-50), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': '☁ '},
				{'draw_divider': False, 'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 100}
				])
			self.assertEqual(common.weather(icons={'cloudy': 'o'}), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'o '},
				{'draw_divider': False, 'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 30.0}
				])
			self.assertEqual(common.weather(icons={'partly_cloudy_day': 'x'}), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': 'x '},
				{'draw_divider': False, 'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9°C', 'gradient_level': 30.0}
				])
			self.assertEqual(common.weather(unit='F'), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': '☁ '},
				{'draw_divider': False, 'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '16°F', 'gradient_level': 30.0}
				])
			self.assertEqual(common.weather(unit='K'), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': '☁ '},
				{'draw_divider': False, 'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '264K', 'gradient_level': 30.0}
				])
			self.assertEqual(common.weather(temp_format='{temp:.1e}C'), [
				{'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_condition_partly_cloudy_day', 'weather_condition_cloudy', 'weather_conditions', 'weather'], 'contents': '☁ '},
				{'draw_divider': False, 'divider_highlight_group': 'background:divider', 'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'], 'contents': '-9.0e+00C', 'gradient_level': 30.0}
				])

	def test_system_load(self):
		with replace_module_module(common, 'os', getloadavg=lambda: (7.5, 3.5, 1.5)):
			with replace_module_attr(common, 'cpu_count', lambda: 2):
				self.assertEqual(common.system_load(),
						[{'contents': '7.5 ', 'highlight_group': ['system_load_gradient', 'system_load'], 'draw_divider': True, 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
						{'contents': '3.5 ', 'highlight_group': ['system_load_gradient', 'system_load'], 'draw_divider': False, 'divider_highlight_group': 'background:divider', 'gradient_level': 75.0},
						{'contents': '1.5', 'highlight_group': ['system_load_gradient', 'system_load'], 'draw_divider': False, 'divider_highlight_group': 'background:divider', 'gradient_level': 0}])
				self.assertEqual(common.system_load(format='{avg:.0f}', threshold_good=0, threshold_bad=1),
						[{'contents': '8 ', 'highlight_group': ['system_load_gradient', 'system_load'], 'draw_divider': True, 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
						{'contents': '4 ', 'highlight_group': ['system_load_gradient', 'system_load'], 'draw_divider': False, 'divider_highlight_group': 'background:divider', 'gradient_level': 100},
						{'contents': '2', 'highlight_group': ['system_load_gradient', 'system_load'], 'draw_divider': False, 'divider_highlight_group': 'background:divider', 'gradient_level': 75.0}])

	def test_cpu_load_percent(self):
		with replace_module_module(common, 'psutil', cpu_percent=lambda **kwargs: 52.3):
			self.assertEqual(common.cpu_load_percent(), '52%')

	def test_network_load(self):
		def _get_bytes(interface):
			return None
		with replace_module_attr(common, '_get_bytes', _get_bytes):
			self.assertEqual(common.network_load(), None)
		l = [0, 0]

		def _get_bytes2(interface):
			l[0] += 1200
			l[1] += 2400
			return tuple(l)

		from imp import reload
		reload(common)
		with replace_module_attr(common, '_get_bytes', _get_bytes2):
			common.network_load.startup()
			common.network_load.sleep(0)
			common.network_load.sleep(0)
			self.assertEqual(common.network_load(), [
				{'divider_highlight_group': 'background:divider', 'contents': '⬇  1 KiB/s', 'highlight_group': ['network_load_recv', 'network_load']},
				{'divider_highlight_group': 'background:divider', 'contents': '⬆  2 KiB/s', 'highlight_group': ['network_load_sent', 'network_load']},
				])
			self.assertEqual(common.network_load(recv_format='r {value}', sent_format='s {value}'), [
				{'divider_highlight_group': 'background:divider', 'contents': 'r 1 KiB/s', 'highlight_group': ['network_load_recv', 'network_load']},
				{'divider_highlight_group': 'background:divider', 'contents': 's 2 KiB/s', 'highlight_group': ['network_load_sent', 'network_load']},
				])
			self.assertEqual(common.network_load(recv_format='r {value}', sent_format='s {value}', suffix='bps'), [
				{'divider_highlight_group': 'background:divider', 'contents': 'r 1 Kibps', 'highlight_group': ['network_load_recv', 'network_load']},
				{'divider_highlight_group': 'background:divider', 'contents': 's 2 Kibps', 'highlight_group': ['network_load_sent', 'network_load']},
				])
			self.assertEqual(common.network_load(recv_format='r {value}', sent_format='s {value}', si_prefix=True), [
				{'divider_highlight_group': 'background:divider', 'contents': 'r 1 kB/s', 'highlight_group': ['network_load_recv', 'network_load']},
				{'divider_highlight_group': 'background:divider', 'contents': 's 2 kB/s', 'highlight_group': ['network_load_sent', 'network_load']},
				])
			self.assertEqual(common.network_load(recv_format='r {value}', sent_format='s {value}', recv_max=0), [
				{'divider_highlight_group': 'background:divider', 'contents': 'r 1 KiB/s', 'highlight_group': ['network_load_recv_gradient', 'network_load_gradient', 'network_load_recv', 'network_load'], 'gradient_level': 100},
				{'divider_highlight_group': 'background:divider', 'contents': 's 2 KiB/s', 'highlight_group': ['network_load_sent', 'network_load']},
				])
			class ApproxEqual(object):
				def __eq__(self, i):
					return abs(i - 50.0) < 1
			self.assertEqual(common.network_load(recv_format='r {value}', sent_format='s {value}', sent_max=4800), [
				{'divider_highlight_group': 'background:divider', 'contents': 'r 1 KiB/s', 'highlight_group': ['network_load_recv', 'network_load']},
				{'divider_highlight_group': 'background:divider', 'contents': 's 2 KiB/s', 'highlight_group': ['network_load_sent_gradient', 'network_load_gradient', 'network_load_sent', 'network_load'], 'gradient_level': ApproxEqual()},
				])

	def test_virtualenv(self):
		with replace_env('VIRTUAL_ENV', '/abc/def/ghi'):
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
		with vim_module._with('mode', 'i') as segment_info:
			self.assertEqual(vim.mode(segment_info=segment_info), 'INSERT')
		with vim_module._with('mode', chr(ord('V') - 0x40)) as segment_info:
			self.assertEqual(vim.mode(segment_info=segment_info), 'V·BLCK')
			self.assertEqual(vim.mode(segment_info=segment_info, override={'^V': 'VBLK'}), 'VBLK')

	def test_modified_indicator(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.modified_indicator(segment_info=segment_info), None)
		segment_info['buffer'][0] = 'abc'
		try:
			self.assertEqual(vim.modified_indicator(segment_info=segment_info), '+')
			self.assertEqual(vim.modified_indicator(segment_info=segment_info, text='-'), '-')
		finally:
			vim_module._bw(segment_info['bufnr'])

	def test_paste_indicator(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.paste_indicator(segment_info=segment_info), None)
		with vim_module._with('options', paste=1):
			self.assertEqual(vim.paste_indicator(segment_info=segment_info), 'PASTE')
			self.assertEqual(vim.paste_indicator(segment_info=segment_info, text='P'), 'P')

	def test_readonly_indicator(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.readonly_indicator(segment_info=segment_info), None)
		with vim_module._with('bufoptions', readonly=1):
			self.assertEqual(vim.readonly_indicator(segment_info=segment_info), '')
			self.assertEqual(vim.readonly_indicator(segment_info=segment_info, text='L'), 'L')

	def test_file_directory(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.file_directory(segment_info=segment_info), None)
		with replace_env('HOME', '/home/foo'):
			with vim_module._with('buffer', '/tmp/abc') as segment_info:
				self.assertEqual(vim.file_directory(segment_info=segment_info), '/tmp/')
				os.environ['HOME'] = '/tmp'
				self.assertEqual(vim.file_directory(segment_info=segment_info), '~/')

	def test_file_name(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.file_name(segment_info=segment_info), None)
		self.assertEqual(vim.file_name(segment_info=segment_info, display_no_file=True),
				[{'contents': '[No file]', 'highlight_group': ['file_name_no_file', 'file_name']}])
		self.assertEqual(vim.file_name(segment_info=segment_info, display_no_file=True, no_file_text='X'),
				[{'contents': 'X', 'highlight_group': ['file_name_no_file', 'file_name']}])
		with vim_module._with('buffer', '/tmp/abc') as segment_info:
			self.assertEqual(vim.file_name(segment_info=segment_info), 'abc')
		with vim_module._with('buffer', '/tmp/’’') as segment_info:
			self.assertEqual(vim.file_name(segment_info=segment_info), '’’')

	def test_file_size(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.file_size(segment_info=segment_info), '0 B')
		with vim_module._with('buffer', os.path.join(os.path.dirname(__file__), 'empty')) as segment_info:
			self.assertEqual(vim.file_size(segment_info=segment_info), '0 B')

	def test_file_opts(self):
		segment_info = vim_module._get_segment_info()
		self.assertEqual(vim.file_format(segment_info=segment_info),
				[{'divider_highlight_group': 'background:divider', 'contents': 'unix'}])
		self.assertEqual(vim.file_encoding(segment_info=segment_info),
				[{'divider_highlight_group': 'background:divider', 'contents': 'utf-8'}])
		self.assertEqual(vim.file_type(segment_info=segment_info), None)
		with vim_module._with('bufoptions', filetype='python'):
			self.assertEqual(vim.file_type(segment_info=segment_info),
					[{'divider_highlight_group': 'background:divider', 'contents': 'python'}])

	def test_line_percent(self):
		segment_info = vim_module._get_segment_info()
		segment_info['buffer'][0:-1] = [str(i) for i in range(100)]
		try:
			self.assertEqual(vim.line_percent(segment_info=segment_info), '1')
			vim_module._set_cursor(50, 0)
			self.assertEqual(vim.line_percent(segment_info=segment_info), '50')
			self.assertEqual(vim.line_percent(segment_info=segment_info, gradient=True),
					[{'contents': '50', 'highlight_group': ['line_percent_gradient', 'line_percent'], 'gradient_level': 50 * 100.0 / 101}])
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
		with vim_module._with('buffer', '/foo') as segment_info:
			with replace_module_attr(vim, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda: None, directory=path)):
				self.assertEqual(vim.branch(segment_info=segment_info),
						[{'divider_highlight_group': 'branch:divider', 'highlight_group': ['branch'], 'contents': 'foo'}])
				self.assertEqual(vim.branch(segment_info=segment_info, status_colors=True),
						[{'divider_highlight_group': 'branch:divider', 'highlight_group': ['branch_clean', 'branch'], 'contents': 'foo'}])
			with replace_module_attr(vim, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda: 'DU', directory=path)):
				self.assertEqual(vim.branch(segment_info=segment_info),
						[{'divider_highlight_group': 'branch:divider', 'highlight_group': ['branch'], 'contents': 'foo'}])
				self.assertEqual(vim.branch(segment_info=segment_info, status_colors=True),
						[{'divider_highlight_group': 'branch:divider', 'highlight_group': ['branch_dirty', 'branch'], 'contents': 'foo'}])

	def test_file_vcs_status(self):
		with vim_module._with('buffer', '/foo') as segment_info:
			with replace_module_attr(vim, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda file: 'M', directory=path)):
				self.assertEqual(vim.file_vcs_status(segment_info=segment_info),
						[{'highlight_group': ['file_vcs_status_M', 'file_vcs_status'], 'contents': 'M'}])
			with replace_module_attr(vim, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda file: None, directory=path)):
				self.assertEqual(vim.file_vcs_status(segment_info=segment_info), None)
		with vim_module._with('buffer', '/bar') as segment_info:
			with vim_module._with('bufoptions', buftype='nofile'):
				with replace_module_attr(vim, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda file: 'M', directory=path)):
					self.assertEqual(vim.file_vcs_status(segment_info=segment_info), None)

	def test_repository_status(self):
		segment_info = vim_module._get_segment_info()
		with replace_module_attr(vim, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda: None, directory=path)):
			self.assertEqual(vim.repository_status(segment_info=segment_info), None)
		with replace_module_attr(vim, 'guess', lambda path: Args(branch=lambda: os.path.basename(path), status=lambda: 'DU', directory=path)):
			self.assertEqual(vim.repository_status(segment_info=segment_info), 'DU')


old_cwd = None


def setUpModule():
	global old_cwd
	global __file__
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'path')))
	old_cwd = os.getcwd()
	__file__ = os.path.abspath(__file__)
	os.chdir(os.path.dirname(__file__))
	from powerline.segments import vim
	globals()['vim'] = vim


def tearDownModule():
	global old_cwd
	os.chdir(old_cwd)
	sys.path.pop(0)


if __name__ == '__main__':
	from tests import main
	main()
