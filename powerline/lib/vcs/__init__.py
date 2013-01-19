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


vcs_props = (('git', '.git', os.path.exists),
			 ('mercurial', '.hg', os.path.isdir))

@memoize(100)
def guess(path):
	for directory in generate_directories(path):
		for vcs, vcs_dir, check in vcs_props:
			if check(os.path.join(directory, vcs_dir)):
				try:
					if vcs not in globals():
						globals()[vcs] = importlib.import_module('powerline.lib.vcs.' + vcs)
					return globals()[vcs].Repository(directory)
				except:
					pass
	return None
