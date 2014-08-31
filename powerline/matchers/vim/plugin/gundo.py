# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os


def gundo(matcher_info):
	name = matcher_info['buffer'].name
	return name and os.path.basename(name) == '__Gundo__'


def gundo_preview(matcher_info):
	name = matcher_info['buffer'].name
	return name and os.path.basename(name) == '__Gundo_Preview__'
