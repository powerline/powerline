# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from powerline.bindings.vim import buffer_name


def commandt(matcher_info):
	name = buffer_name(matcher_info)
	return name and os.path.basename(name) == b'GoToFile'
