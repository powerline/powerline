# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from powerline.bindings.vim import buffer_name


def gundo(matcher_info):
	name = buffer_name(matcher_info)
	return name and os.path.basename(name) == b'__Gundo__'


def gundo_preview(matcher_info):
	name = buffer_name(matcher_info)
	return name and os.path.basename(name) == b'__Gundo_Preview__'
