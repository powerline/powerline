# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import json

from subprocess import check_call
from shutil import rmtree
from itertools import chain

from powerline import Powerline


CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')


class TestPowerline(Powerline):
	def __init__(self, _paths, *args, **kwargs):
		super(TestPowerline, self).__init__(*args, **kwargs)
		self._paths = _paths

	def get_config_paths(self):
		return self._paths


def mkdir_recursive(directory):
	if os.path.isdir(directory):
		return
	mkdir_recursive(os.path.dirname(directory))
	os.mkdir(directory)


class FSTree(object):
	__slots__ = ('tree', 'p', 'p_kwargs', 'create_p', 'get_config_paths', 'root')

	def __init__(
		self,
		tree,
		p_kwargs={'run_once': True},
		root=CONFIG_DIR,
		get_config_paths=lambda p: (p,),
		create_p=False
	):
		self.tree = tree
		self.root = root
		self.get_config_paths = get_config_paths
		self.create_p = create_p
		self.p = None
		self.p_kwargs = p_kwargs

	def __enter__(self, *args):
		os.mkdir(self.root)
		for k, v in self.tree.items():
			fname = os.path.join(self.root, k) + '.json'
			mkdir_recursive(os.path.dirname(fname))
			with open(fname, 'w') as F:
				json.dump(v, F)
		if self.create_p:
			self.p = TestPowerline(
				_paths=self.get_config_paths(self.root),
				ext='test',
				renderer_module='tests.lib.config_mock',
				**self.p_kwargs
			)
		if os.environ.get('POWERLINE_RUN_LINT_DURING_TESTS'):
			try:
				check_call(chain(['scripts/powerline-lint'], *[
					('-p', d) for d in (
						self.p.get_config_paths() if self.p
						else self.get_config_paths(self.root)
					)
				]))
			except:
				self.__exit__()
				raise
		return self.p and self.p.__enter__(*args)

	def __exit__(self, *args):
		try:
			rmtree(self.root)
		finally:
			if self.p:
				self.p.__exit__(*args)
