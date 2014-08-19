# vim:fileencoding=utf-8:noet

'''Tests for shell.py parser'''


from powerline.shell import get_argparser, finish_args
from tests import TestCase
from tests.lib import replace_attr
import sys
if sys.version_info < (3,):
	from io import BytesIO as StrIO
else:
	from io import StringIO as StrIO  # NOQA


class TestParser(TestCase):
	def test_main_err(self):
		parser = get_argparser()
		out = StrIO()
		err = StrIO()

		def flush():
			out.truncate(0)
			err.truncate(0)

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			for raising_args, raising_reg in [
				([],                                     'too few arguments|the following arguments are required: ext'),
				(['-r'],                                 'expected one argument'),
				(['shell', '-r'],                        'expected one argument'),
				(['shell', '-w'],                        'expected one argument'),
				(['shell', '-c'],                        'expected one argument'),
				(['shell', '-t'],                        'expected one argument'),
				(['shell', '-p'],                        'expected one argument'),
				(['shell', '-R'],                        'expected one argument'),
				(['shell', '--renderer_module'],         'expected one argument'),
				(['shell', '--width'],                   'expected one argument'),
				(['shell', '--last_exit_code'],          'expected one argument'),
				(['shell', '--last_pipe_status'],        'expected one argument'),
				(['shell', '--config'],                  'expected one argument'),
				(['shell', '--theme_option'],            'expected one argument'),
				(['shell', '--config_path'],             'expected one argument'),
				(['shell', '--renderer_arg'],            'expected one argument'),
				(['shell', '--jobnum'],                  'expected one argument'),
				(['-r', '.zsh'],                         'too few arguments|the following arguments are required: ext'),
				(['shell', '--last_exit_code', 'i'],     'invalid int value'),
				(['shell', '--last_pipe_status', '1 i'], 'invalid <lambda> value'),
			]:
				self.assertRaises(SystemExit, parser.parse_args, raising_args)
				self.assertFalse(out.getvalue())
				self.assertRegexpMatches(err.getvalue(), raising_reg)
				flush()

	def test_main_normal(self):
		parser = get_argparser()
		out = StrIO()
		err = StrIO()
		with replace_attr(sys, 'stdout', out, 'stderr', err):
			for argv, expargs in [
				(['shell'],               {'ext': ['shell']}),
				(['shell', '-r', '.zsh'], {'ext': ['shell'], 'renderer_module': '.zsh'}),
				([
					'shell',
					'left',
					'-r', '.zsh',
					'--last_exit_code', '10',
					'--last_pipe_status', '10 20 30',
					'--jobnum=10',
					'-w', '100',
					'-c', 'common.term_truecolor=true',
					'-c', 'common.spaces=4',
					'-t', 'default.segment_data.hostname.before=H:',
					'-p', '.',
					'-p', '..',
					'-R', 'smth={"abc":"def"}',
				], {
					'ext': ['shell'],
					'side': 'left',
					'renderer_module': '.zsh',
					'last_exit_code': 10,
					'last_pipe_status': [10, 20, 30],
					'jobnum': 10,
					'width': 100,
					'config': {'common': {'term_truecolor': True, 'spaces': 4}},
					'theme_option': {
						'default': {
							'segment_data': {
								'hostname': {
									'before': 'H:'
								}
							}
						}
					},
					'config_path': ['.', '..'],
					'renderer_arg': {'smth': {'abc': 'def'}},
				}),
				(['shell', '-R', 'arg=true'], {'ext': ['shell'], 'renderer_arg': {'arg': True}}),
				(['shell', '-R', 'arg=true', '-R', 'arg='], {'ext': ['shell'], 'renderer_arg': {}}),
				(['shell', '-R', 'arg='], {'ext': ['shell'], 'renderer_arg': {}}),
				(['shell', '-t', 'default.segment_info={"hostname": {}}'], {
					'ext': ['shell'],
					'theme_option': {
						'default': {
							'segment_info': {
								'hostname': {}
							}
						}
					},
				}),
				(['shell', '-c', 'common={ }'], {'ext': ['shell'], 'config': {'common': {}}}),
			]:
				args = parser.parse_args(argv)
				finish_args(args)
				for key, val in expargs.items():
					self.assertEqual(getattr(args, key), val)
				for key, val in args.__dict__.items():
					if key not in expargs:
						self.assertFalse(val, msg='key {0} is {1} while it should be something false'.format(key, val))
				self.assertFalse(err.getvalue() + out.getvalue(), msg='unexpected output: {0!r} {1!r}'.format(
					err.getvalue(),
					out.getvalue(),
				))


if __name__ == '__main__':
	from tests import main
	main()
