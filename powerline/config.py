# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals, print_function
import os

BINDINGS_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bindings')
TMUX_CONFIG_DIRECTORY = os.path.join(BINDINGS_DIRECTORY, 'tmux')
DEFAULT_SYSTEM_CONFIG_DIR = None
