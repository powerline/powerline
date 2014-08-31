# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import re


def nerdtree(matcher_info):
	name = matcher_info['buffer'].name
	return name and re.match(r'NERD_tree_\d+', os.path.basename(name))
