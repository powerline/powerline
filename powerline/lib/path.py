# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals, absolute_import

import os


def realpath(path):
	return os.path.abspath(os.path.realpath(path))
