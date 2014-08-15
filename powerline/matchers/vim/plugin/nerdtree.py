# vim:fileencoding=utf-8:noet

import os
import re


def nerdtree(matcher_info):
	name = matcher_info['buffer'].name
	return name and re.match(r'NERD_tree_\d+', os.path.basename(name))
