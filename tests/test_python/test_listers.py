# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import powerline.listers.i3wm as i3wm

from tests.modules.lib import Args, replace_attr, Pl
from tests.modules import TestCase


class TestI3WM(TestCase):
	@staticmethod
	def get_workspaces():
		return iter([
			{'name': '1: w1', 'output': 'LVDS1', 'focused': False, 'urgent': False, 'visible': False},
			{'name': '2: w2', 'output': 'LVDS1', 'focused': False, 'urgent': False, 'visible': True},
			{'name': '3: w3', 'output': 'HDMI1', 'focused': False, 'urgent': True, 'visible': True},
			{'name': '4: w4', 'output': 'DVI01', 'focused': True, 'urgent': True, 'visible': True},
		])

	@staticmethod
	def get_outputs(pl):
		return iter([
			{'name': 'LVDS1'},
			{'name': 'HDMI1'},
			{'name': 'DVI01'},
		])

	def test_output_lister(self):
		pl = Pl()
		with replace_attr(i3wm, 'get_connected_xrandr_outputs', self.get_outputs):
			self.assertEqual(
				list(i3wm.output_lister(pl=pl, segment_info={'a': 1})),
				[
					({'a': 1, 'output': 'LVDS1'}, {'draw_inner_divider': None}),
					({'a': 1, 'output': 'HDMI1'}, {'draw_inner_divider': None}),
					({'a': 1, 'output': 'DVI01'}, {'draw_inner_divider': None}),
				]
			)

	def test_workspace_lister(self):
		pl = Pl()
		with replace_attr(i3wm, 'get_i3_connection', lambda: Args(get_workspaces=self.get_workspaces)):
			self.assertEqual(
				list(i3wm.workspace_lister(pl=pl, segment_info={'a': 1})),
				[
					({
						'a': 1,
						'output': 'LVDS1',
						'workspace': {
							'name': '1: w1',
							'focused': False,
							'urgent': False,
							'visible': False
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'LVDS1',
						'workspace': {
							'name': '2: w2',
							'focused': False,
							'urgent': False,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'HDMI1',
						'workspace': {
							'name': '3: w3',
							'focused': False,
							'urgent': True,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'DVI01',
						'workspace': {
							'name': '4: w4',
							'focused': True,
							'urgent': True,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
				]
			)

			self.assertEqual(
				list(i3wm.workspace_lister(pl=pl, segment_info={'a': 1}, output='LVDS1')),
				[
					({
						'a': 1,
						'output': 'LVDS1',
						'workspace': {
							'name': '1: w1',
							'focused': False,
							'urgent': False,
							'visible': False
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'LVDS1',
						'workspace': {
							'name': '2: w2',
							'focused': False,
							'urgent': False,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
				]
			)

			self.assertEqual(
				list(i3wm.workspace_lister(
					pl=pl,
					segment_info={'a': 1, 'output': 'LVDS1'}
				)),
				[
					({
						'a': 1,
						'output': 'LVDS1',
						'workspace': {
							'name': '1: w1',
							'focused': False,
							'urgent': False,
							'visible': False
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'LVDS1',
						'workspace': {
							'name': '2: w2',
							'focused': False,
							'urgent': False,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
				]
			)

			self.assertEqual(
				list(i3wm.workspace_lister(
					pl=pl,
					segment_info={'a': 1, 'output': 'LVDS1'},
					output=False
				)),
				[
					({
						'a': 1,
						'output': 'LVDS1',
						'workspace': {
							'name': '1: w1',
							'focused': False,
							'urgent': False,
							'visible': False
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'LVDS1',
						'workspace': {
							'name': '2: w2',
							'focused': False,
							'urgent': False,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'HDMI1',
						'workspace': {
							'name': '3: w3',
							'focused': False,
							'urgent': True,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'DVI01',
						'workspace': {
							'name': '4: w4',
							'focused': True,
							'urgent': True,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
				]
			)

			self.assertEqual(
				list(i3wm.workspace_lister(
					pl=pl,
					segment_info={'a': 1},
					only_show=['focused', 'urgent']
				)),
				[
					({
						'a': 1,
						'output': 'HDMI1',
						'workspace': {
							'name': '3: w3',
							'focused': False,
							'urgent': True,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
					({
						'a': 1,
						'output': 'DVI01',
						'workspace': {
							'name': '4: w4',
							'focused': True,
							'urgent': True,
							'visible': True
						}
					}, {'draw_inner_divider': None}),
				]
			)


if __name__ == '__main__':
	from tests.modules import main
	main()
