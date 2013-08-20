# vim:fileencoding=utf-8:noet

import vim
from powerline.bindings.vim import getbufvar


def ctrlp(pl, side):
	ctrlp_type = getbufvar('%', 'powerline_ctrlp_type')
	ctrlp_args = getbufvar('%', 'powerline_ctrlp_args')

	return globals()['ctrlp_stl_{0}_{1}'.format(side, ctrlp_type)](pl, *ctrlp_args)


def ctrlp_stl_left_main(pl, focus, byfname, regex, prev, item, next, marked):
	marked = marked[2:-1]
	segments = []

	if int(regex):
		segments.append({
			'contents': 'regex',
			'highlight_group': ['ctrlp.regex', 'background'],
			})

	segments += [
		{
			'contents': prev + ' ',
			'highlight_group': ['ctrlp.prev', 'background'],
			'draw_inner_divider': True,
			'priority': 40,
		},
		{
			'contents': item,
			'highlight_group': ['ctrlp.item', 'file_name'],
			'draw_inner_divider': True,
			'width': 10,
			'align': 'c',
		},
		{
			'contents': ' ' + next,
			'highlight_group': ['ctrlp.next', 'background'],
			'draw_inner_divider': True,
			'priority': 40,
		},
	]

	if marked != '-':
		segments.append({
			'contents': marked,
			'highlight_group': ['ctrlp.marked', 'background'],
			'draw_inner_divider': True,
			})

	return segments


def ctrlp_stl_right_main(pl, focus, byfname, regex, prev, item, next, marked):
	segments = [
		{
			'contents': focus,
			'highlight_group': ['ctrlp.focus', 'background'],
			'draw_inner_divider': True,
			'priority': 50,
		},
		{
			'contents': byfname,
			'highlight_group': ['ctrlp.byfname', 'background'],
			'priority': 50,
		},
	]

	return segments


def ctrlp_stl_left_prog(pl, progress):
	return [
		{
			'contents': 'Loading...',
			'highlight_group': ['ctrlp.progress', 'file_name'],
		},
	]


def ctrlp_stl_right_prog(pl, progress):
	return [
		{
			'contents': progress,
			'highlight_group': ['ctrlp.progress', 'file_name'],
		},
	]
