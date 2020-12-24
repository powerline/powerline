# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import os

if sys.version_info < (2, 7):
	from unittest2 import TestCase as TestCase  # NOQA
	from unittest2 import main as _main  # NOQA
	from unittest2.case import SkipTest  # NOQA
else:
	from unittest import TestCase as TestCase  # NOQA
	from unittest import main as _main  # NOQA
	from unittest.case import SkipTest  # NOQA

from tests.modules.lib import PowerlineSingleTest


class PowerlineDummyTest(object):
	def __enter__(self):
		return self

	def __exit__(self, *args):
		pass

	def fail(self, *args, **kwargs):
		pass

	def exception(self, *args, **kwargs):
		pass


class PowerlineTestSuite(object):
	def __init__(self, name):
		self.name = name

	def __enter__(self):
		self.saved_current_suite = os.environ['POWERLINE_CURRENT_SUITE']
		os.environ['POWERLINE_CURRENT_SUITE'] = (
			self.saved_current_suite + '/' + self.name)
		self.suite = self.saved_current_suite + '/' + self.name
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type is not None:
			self.exception(
				'suite_noexcept',
				'Exception while running test suite: {0!r}'.format(exc_value),
			)
		os.environ['POWERLINE_CURRENT_SUITE'] = self.saved_current_suite

	def record_test_failure(self, fail_char, test_name, message, allow_failure=False):
		try:
			suite_obj = self.suite
		except AttributeError:
			suite_obj = "unknown"
		if allow_failure:
			fail_char = 'A' + fail_char
		full_msg = '{fail_char} {suite}|{test_name} :: {message}'.format(
			fail_char=fail_char,
			suite=suite_obj,
			test_name=test_name,
			message=message,
		)
		try:
			with open(os.environ['FAILURES_FILE'], 'a') as ffd:
				ffd.write(full_msg + '\n')
		except KeyError:
			# Ignore writing to FAILURES_FILE if this is not defined in OS_ENVIRON
			pass
		return False

	def exception(self, test_name, message, allow_failure=False):
		return self.record_test_failure('E', test_name, message, allow_failure)

	def fail(self, test_name, message, allow_failure=False):
		return self.record_test_failure('F', test_name, message, allow_failure)

	def test(self, name, attempts_left=0):
		if not attempts_left:
			return PowerlineSingleTest(self, name)
		else:
			return PowerlineDummyTest()

	def subsuite(self, name):
		return PowerlineTestSuite(name)


suite = None


def main(*args, **kwargs):
	global suite
	suite = PowerlineTestSuite(sys.argv[0])
	_main(*args, **kwargs)
