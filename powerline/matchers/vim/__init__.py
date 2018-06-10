# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.editors import EditorBufferNameBase
from powerline.editors.vim import VimBufferOption


help = VimBufferOption('buftype').equals('help')
'''Match help buffer
'''

quickfix = VimBufferOption('buftype').equals('quickfix')
'''Match quickfix buffer
'''

cmdwin = EditorBufferNameBase().equals('[Command Line]')
'''Match command buffer (i.e. what shows after ``q:``)
'''
