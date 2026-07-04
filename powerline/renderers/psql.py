# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell.readline import ReadlineRenderer


class PsqlRenderer(ReadlineRenderer):
	'''PostgreSQL psql prompt renderer (readline non-printing markers).'''


renderer = PsqlRenderer