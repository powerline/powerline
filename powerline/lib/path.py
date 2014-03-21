# vim:fileencoding=utf-8:noet

import os
import sys
import codecs

filesystem_encoding = sys.getfilesystemencoding()
if filesystem_encoding is None or codecs.lookup(filesystem_encoding).name == 'ascii':
	filesystem_encoding = 'utf-8'

def join(prefix, suffix):
	try:
		return os.path.join(prefix, suffix)
	except TypeError:
		if isinstance(suffix, bytes):
			suffix = suffix.decode(filesystem_encoding)
			return os.path.join(prefix, suffix)
		else:
			raise

