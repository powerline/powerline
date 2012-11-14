" Powerline vim example
" Run with :source %

let s:did_highlighting = 0
let s:segments = [
	\ { 'contents': 'mode()',                  'fg': 22,  'bg': 148, 'attr': 1 },
	\ { 'contents': '"⭠ develop"',             'fg': 247, 'bg': 240, 'priority': 10 },
	\ { 'contents': '" ".expand("%:p:h")."/"', 'fg': 250, 'bg': 240, 'padding': '', 'draw_divider': 0, 'priority': 5 },
	\ { 'contents': 'expand("%:p:t")." "',     'fg': 231, 'bg': 240, 'padding': '', 'attr': 1 },
	\ { 'filler': 1 },
	\ { 'contents': '&ff',                     'fg': 245, 'bg': 236, 'side': 'r', 'priority': 50 },
	\ { 'contents': '&fenc',                   'fg': 245, 'bg': 236, 'side': 'r', 'priority': 50 },
	\ { 'contents': '&ft',                     'fg': 245, 'bg': 236, 'side': 'r', 'priority': 50 },
	\ { 'contents': '(line(".") * 100 / line("$") * 100) / 100 . "%%"', 'fg': 247, 'bg': 240, 'side': 'r', 'priority': 30 },
	\ { 'contents': '"⭡"',                     'fg': 239, 'bg': 252, 'side': 'r' },
	\ { 'contents': 'line(".")',               'fg': 239, 'bg': 252, 'side': 'r', 'attr': 1, 'padding': '', 'draw_divider': 0 },
	\ { 'contents': '":". col(".")',           'fg': 244, 'bg': 252, 'side': 'r', 'padding': '', 'draw_divider': 0, 'priority': 30 },
\ ]

function! DynStl()
	python <<EOF
import vim
import sys
sys.path.append('.')

from lib.core import Segment
from lib.renderers import VimSegmentRenderer

winwidth = int(vim.eval('winwidth(0)'))
segments = [{
		'contents': vim.eval(s.get('contents', '""')),
		'fg': int(s.get('fg', 0)) or None,
		'bg': int(s.get('bg', 0)) or None,
		'attr': int(s.get('attr', 0)),
		'priority': int(s.get('priority', -1)),
		'padding': s.get('padding', ' '),
		'draw_divider': int(s.get('draw_divider', 1)),
		'filler': bool(s.get('filler', 0)),
		'side': s.get('side', 'l'),
	} for s in vim.eval('s:segments')]

powerline = Segment([Segment(**segment) for segment in segments], 236, 236)

renderer = VimSegmentRenderer()
stl = powerline.render(renderer, winwidth)

if int(vim.eval('s:did_highlighting')) == 0:
	vim.command(renderer.get_hl_statements())
	vim.command('let s:did_highlighting = 1')

vim.command('return "{0}"'.format(stl))
EOF
endfunction

let &stl = '%!DynStl()'
