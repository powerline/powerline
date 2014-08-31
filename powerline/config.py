# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os


POWERLINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINDINGS_DIRECTORY = os.path.join(POWERLINE_ROOT, 'powerline', 'bindings')
TMUX_CONFIG_DIRECTORY = os.path.join(BINDINGS_DIRECTORY, 'tmux')
DEFAULT_SYSTEM_CONFIG_DIR = None
