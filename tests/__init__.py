# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

if sys.version_info < (2, 7):
	from unittest2 import TestCase, main  # NOQA
	from unittest2.case import SkipTest  # NOQA
else:
	from unittest import TestCase, main  # NOQA
	from unittest.case import SkipTest  # NOQA
