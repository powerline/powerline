# vim:fileencoding=utf-8:noet

'''Tests for various logging features'''

from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import re
import codecs
import os

from io import StringIO
from shutil import rmtree

from powerline import finish_common_config, create_logger

from tests.modules import TestCase
from tests.modules.lib import replace_attr


TIMESTAMP_RE = r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}'


class TestRE(TestCase):
	def assertMatches(self, text, regexp):
		self.assertTrue(
			re.match(regexp, text),
			'{0!r} did not match {1!r}'.format(text, regexp),
		)


def close_handlers(logger):
	for handler in logger.handlers:
		handler.close()


class TestHandlers(TestRE):
	def test_stderr_handler_is_default(self):
		out = StringIO()
		err = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {})
			logger, pl, get_module_attr = create_logger(common_config)
			pl.error('Foo')
			close_handlers(logger)
			self.assertMatches(err.getvalue(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			self.assertEqual(out.getvalue(), '')

	def test_stream_override(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.error('Foo')
			close_handlers(logger)
			self.assertMatches(stream.getvalue(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_explicit_none(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [None]})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.error('Foo')
			close_handlers(logger)
			self.assertMatches(stream.getvalue(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_explicit_stream_handler(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [['logging.StreamHandler', [[]]]]})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.error('Foo')
			close_handlers(logger)
			self.assertEqual(stream.getvalue(), '')
			self.assertMatches(err.getvalue(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			self.assertEqual(out.getvalue(), '')

	def test_explicit_stream_handler_implicit_stream(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [['logging.StreamHandler', []]]})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.error('Foo')
			close_handlers(logger)
			self.assertMatches(stream.getvalue(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_file_handler(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		file_name = 'test_logging-test_file_handler'

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': file_name})
			try:
				logger, pl, get_module_attr = create_logger(common_config, stream=stream)
				pl.error('Foo')
				close_handlers(logger)
				with codecs.open(file_name, encoding='utf-8') as fp:
					self.assertMatches(fp.read(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			finally:
				os.unlink(file_name)
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_file_handler_create_dir(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		file_name = 'test_logging-test_file_handler_create_dir/file'

		self.assertFalse(os.path.isdir(os.path.dirname(file_name)))

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': file_name})
			try:
				logger, pl, get_module_attr = create_logger(common_config, stream=stream)
				pl.error('Foo')
				close_handlers(logger)
				self.assertTrue(os.path.isdir(os.path.dirname(file_name)))
				with codecs.open(file_name, encoding='utf-8') as fp:
					self.assertMatches(fp.read(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			finally:
				rmtree(os.path.dirname(file_name))
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_multiple_files(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		file_name_1 = 'test_logging-test_multiple_files-1'
		file_name_2 = file_name_1[:-1] + '2'

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [file_name_1, file_name_2]})
			try:
				try:
					logger, pl, get_module_attr = create_logger(common_config, stream=stream)
					pl.error('Foo')
					close_handlers(logger)
					for file_name in (file_name_1, file_name_2):
						with codecs.open(file_name, encoding='utf-8') as fp:
							self.assertMatches(fp.read(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
				finally:
					os.unlink(file_name_1)
			finally:
				os.unlink(file_name_2)
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_multiple_files_and_stream(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		file_name_1 = 'test_logging-test_multiple_files_and_stream-1'
		file_name_2 = file_name_1[:-1] + '2'

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [file_name_1, file_name_2, None]})
			try:
				try:
					logger, pl, get_module_attr = create_logger(common_config, stream=stream)
					pl.error('Foo')
					close_handlers(logger)
					for file_name in (file_name_1, file_name_2):
						with codecs.open(file_name, encoding='utf-8') as fp:
							self.assertMatches(fp.read(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
				finally:
					os.unlink(file_name_1)
			finally:
				os.unlink(file_name_2)
			self.assertMatches(stream.getvalue(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_handler_args(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		file_name = 'test_logging-test_handler_args'

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [
				['RotatingFileHandler', [[file_name]]]
			]})
			try:
				logger, pl, get_module_attr = create_logger(common_config, stream=stream)
				pl.error('Foo')
				close_handlers(logger)
				with codecs.open(file_name, encoding='utf-8') as fp:
					self.assertMatches(fp.read(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
			finally:
				os.unlink(file_name)
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_handler_args_kwargs(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		file_name = 'test_logging-test_handler_args_kwargs'

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [
				['RotatingFileHandler', [[file_name], {'maxBytes': 1, 'backupCount': 1}]]
			]})
			try:
				try:
					logger, pl, get_module_attr = create_logger(common_config, stream=stream)
					pl.error('Foo')
					pl.error('Bar')
					close_handlers(logger)
					with codecs.open(file_name, encoding='utf-8') as fp:
						self.assertMatches(fp.read(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Bar\n$')
					with codecs.open(file_name + '.1', encoding='utf-8') as fp:
						self.assertMatches(fp.read(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Foo\n$')
				finally:
					os.unlink(file_name + '.1')
			finally:
				os.unlink(file_name)
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_logger_level(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		stream1 = StringIO()
		stream2 = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [
				['logging.StreamHandler', [[stream1]], 'WARNING'],
				['logging.StreamHandler', [[stream2]], 'ERROR'],
			]})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.warn('Foo')
			pl.error('Bar')
			close_handlers(logger)
			self.assertMatches(stream1.getvalue(), (
				'^' + TIMESTAMP_RE + ':WARNING:__unknown__:Foo\n'
				+ TIMESTAMP_RE + ':ERROR:__unknown__:Bar\n$'
			))
			self.assertMatches(stream2.getvalue(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Bar\n$')
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_logger_level_not_overriding_default(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		stream1 = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [
				['logging.StreamHandler', [[stream1]], 'DEBUG'],
			]})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.debug('Foo')
			pl.error('Bar')
			close_handlers(logger)
			self.assertMatches(stream1.getvalue(), '^' + TIMESTAMP_RE + ':ERROR:__unknown__:Bar\n$')
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_top_log_level(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		stream1 = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [
				['logging.StreamHandler', [[stream1]], 'DEBUG'],
			], 'log_level': 'DEBUG'})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.debug('Foo')
			pl.error('Bar')
			close_handlers(logger)
			self.assertMatches(stream1.getvalue(), (
				'^' + TIMESTAMP_RE + ':DEBUG:__unknown__:Foo\n'
				+ TIMESTAMP_RE + ':ERROR:__unknown__:Bar\n$'
			))
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_logger_format(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		stream1 = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [
				['logging.StreamHandler', [[stream1]], 'WARNING', 'FOO'],
			]})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.warn('Foo')
			pl.error('Bar')
			close_handlers(logger)
			self.assertEqual(stream1.getvalue(), 'FOO\nFOO\n')
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')

	def test_top_log_format(self):
		out = StringIO()
		err = StringIO()
		stream = StringIO()
		stream1 = StringIO()
		stream2 = StringIO()

		with replace_attr(sys, 'stdout', out, 'stderr', err):
			common_config = finish_common_config('utf-8', {'log_file': [
				['logging.StreamHandler', [[stream1]], 'WARNING', 'FOO'],
				['logging.StreamHandler', [[stream2]], 'WARNING'],
			], 'log_format': 'BAR'})
			logger, pl, get_module_attr = create_logger(common_config, stream=stream)
			pl.warn('Foo')
			pl.error('Bar')
			close_handlers(logger)
			self.assertEqual(stream2.getvalue(), 'BAR\nBAR\n')
			self.assertEqual(stream1.getvalue(), 'FOO\nFOO\n')
			self.assertEqual(stream.getvalue(), '')
			self.assertEqual(err.getvalue(), '')
			self.assertEqual(out.getvalue(), '')


class TestPowerlineLogger(TestRE):
	def test_args_formatting(self):
		stream = StringIO()

		common_config = finish_common_config('utf-8', {})
		logger, pl, get_module_attr = create_logger(common_config, stream=stream)
		pl.warn('foo {0}', 'Test')
		pl.warn('bar {0!r}', 'Test')
		close_handlers(logger)
		self.assertMatches(stream.getvalue(), (
			'^' + TIMESTAMP_RE + ':WARNING:__unknown__:foo Test\n'
			+ TIMESTAMP_RE + ':WARNING:__unknown__:bar u?\'Test\'\n$'
		))

	def test_prefix_formatting(self):
		stream = StringIO()

		common_config = finish_common_config('utf-8', {})
		logger, pl, get_module_attr = create_logger(common_config, stream=stream)
		pl.prefix = '1'
		pl.warn('foo')
		pl.prefix = '2'
		pl.warn('bar')
		close_handlers(logger)
		self.assertMatches(stream.getvalue(), (
			'^' + TIMESTAMP_RE + ':WARNING:__unknown__:1:foo\n'
			+ TIMESTAMP_RE + ':WARNING:__unknown__:2:bar\n$'
		))

	def test_kwargs_formatting(self):
		stream = StringIO()

		common_config = finish_common_config('utf-8', {})
		logger, pl, get_module_attr = create_logger(common_config, stream=stream)
		pl.warn('foo {arg}', arg='Test')
		pl.warn('bar {arg!r}', arg='Test')
		close_handlers(logger)
		self.assertMatches(stream.getvalue(), (
			'^' + TIMESTAMP_RE + ':WARNING:__unknown__:foo Test\n'
			+ TIMESTAMP_RE + ':WARNING:__unknown__:bar u?\'Test\'\n$'
		))

	def test_args_kwargs_formatting(self):
		stream = StringIO()

		common_config = finish_common_config('utf-8', {})
		logger, pl, get_module_attr = create_logger(common_config, stream=stream)
		pl.warn('foo {0!r} {arg}', 'Test0', arg='Test')
		pl.warn('bar {0} {arg!r}', 'Test0', arg='Test')
		close_handlers(logger)
		self.assertMatches(stream.getvalue(), (
			'^' + TIMESTAMP_RE + ':WARNING:__unknown__:foo u?\'Test0\' Test\n'
			+ TIMESTAMP_RE + ':WARNING:__unknown__:bar Test0 u?\'Test\'\n$'
		))

	def test_exception_formatting(self):
		stream = StringIO()

		common_config = finish_common_config('utf-8', {})
		logger, pl, get_module_attr = create_logger(common_config, stream=stream)
		try:
			raise ValueError('foo')
		except ValueError:
			pl.exception('Message')
		close_handlers(logger)
		self.assertMatches(stream.getvalue(), (
			'^' + TIMESTAMP_RE + ':ERROR:__unknown__:Message\n'
			+ 'Traceback \\(most recent call last\\):\n'
			+ '(?:  File ".*?", line \\d+, in \\w+\n    [^\n]*\n)+'
			+ 'ValueError: foo\n$'
		))

	def test_levels(self):
		stream = StringIO()

		common_config = finish_common_config('utf-8', {'log_level': 'DEBUG'})
		logger, pl, get_module_attr = create_logger(common_config, stream=stream)
		pl.debug('1')
		pl.info('2')
		pl.warn('3')
		pl.error('4')
		pl.critical('5')
		close_handlers(logger)
		self.assertMatches(stream.getvalue(), (
			'^' + TIMESTAMP_RE + ':DEBUG:__unknown__:1\n'
			+ TIMESTAMP_RE + ':INFO:__unknown__:2\n'
			+ TIMESTAMP_RE + ':WARNING:__unknown__:3\n'
			+ TIMESTAMP_RE + ':ERROR:__unknown__:4\n'
			+ TIMESTAMP_RE + ':CRITICAL:__unknown__:5\n$'
		))


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
