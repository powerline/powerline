# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import re

from powerline.bindings.vim import buffer_name


NERD_TREE_RE = re.compile(b'NERD_tree_\\d+')


def nerdtree(matcher_info):
	name = buffer_name(matcher_info)
	return name and NERD_TREE_RE.match(os.path.basename(name))
