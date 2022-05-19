# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import subprocess
from traceback import print_exc

__version__ = "2.8.2"

def get_version():
	try:
		return __version__ + 'b' + subprocess.check_output(['git', 'rev-list', '--count', __version__ + '..HEAD']).strip().decode()
	except Exception:
		print_exc()
		return __version__

