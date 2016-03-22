# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from powerline.bindings.vim import vim_getbufoption, buffer_name


def help(matcher_info):
	return vim_getbufoption(matcher_info, 'buftype') == 'help'


def cmdwin(matcher_info):
	name = buffer_name(matcher_info)
	return name and os.path.basename(name) == b'[Command Line]'


def quickfix(matcher_info):
	return vim_getbufoption(matcher_info, 'buftype') == 'quickfix'
