# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import pdb
import os
import sys

from powerline.bindings.pdb import use_powerline_prompt


@use_powerline_prompt
class Pdb(pdb.Pdb):
	pass


p = Pdb()


script = os.path.join(os.path.dirname(__file__), 'pdb-script.py')
with open(script, 'r') as fd:
	code = compile(fd.read(), script, 'exec')


p.run('exec(code)', globals={'code': code})
