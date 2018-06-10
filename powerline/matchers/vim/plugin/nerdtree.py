# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.editors import EditorBufferNameBase


nerdtree = EditorBufferNameBase().matches('NERD_tree_\\d+$')
'''Match nerdtree buffer
'''
