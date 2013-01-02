import importlib
import os
from powerline.lib.memoize import memoize

def generate_directories(path):
	yield path
	while True:
		old_path = path
		path = os.path.dirname(path)
		if path == old_path:
			break
		yield path

@memoize(100)
def guess(path):
	for directory in generate_directories(path):
		for vcs, vcs_dir in (('git', '.git'), ('mercurial', '.hg')):
			if os.path.isdir(os.path.join(directory, vcs_dir)):
				try:
					if vcs not in globals():
						globals()[vcs] = importlib.import_module('powerline.vcs.'+vcs)
					return globals()[vcs].Repository(directory)
				except:
					pass
	return None

# vim: noet ts=4 sts=4 sw=4
