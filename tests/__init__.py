# vim:fileencoding=utf-8:noet
import sys
if sys.version_info < (2, 7):
	from unittest2 import TestCase, main  # NOQA
else:
	from unittest import TestCase, main  # NOQA
