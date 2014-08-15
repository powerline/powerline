# vim:fileencoding=utf-8:noet

import os


def gundo(matcher_info):
	name = matcher_info['buffer'].name
	return name and os.path.basename(name) == '__Gundo__'


def gundo_preview(matcher_info):
	name = matcher_info['buffer'].name
	return name and os.path.basename(name) == '__Gundo_Preview__'
