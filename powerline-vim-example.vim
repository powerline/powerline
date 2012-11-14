" Powerline vim example
" Run with :source %

let s:did_highlighting = 0

function! DynStl()
	python <<EOF
import vim
import sys
sys.path.append('.')

from lib.core import Segment
from lib.renderers import VimSegmentRenderer

winwidth = int(vim.eval('winwidth(0)'))

line_current = int(vim.eval('line(".")'))
line_end = int(vim.eval('line("$")'))
line_percent = int(float(line_current) / float(line_end) * 100)

powerline = Segment([
	Segment(vim.eval('mode()'), 22, 148, attr=Segment.ATTR_BOLD),
	Segment('⭠ develop', 247, 240, priority=10),
	Segment([
		Segment(vim.eval('expand("%:p:h")."/"'), draw_divider=False, priority=5),
		Segment(vim.eval('expand("%:p:t")'), 231, attr=Segment.ATTR_BOLD),
	], 250, 240),
	Segment(filler=True),
	Segment([
		Segment(vim.eval('&ff'), priority=50),
		Segment(vim.eval('&fenc'), priority=50),
		Segment(vim.eval('&ft'), priority=50),
		Segment(str(line_percent) + '%%', 247, 240, priority=30),
		Segment([
			Segment('⭡ ', 239),
			Segment(str(line_current), attr=Segment.ATTR_BOLD, draw_divider=False),
			Segment(vim.eval('":".col(".")'), 244, priority=30, draw_divider=False),
		], 235, 252),
	], 245, side='r'),
], fg=236, bg=236)

renderer = VimSegmentRenderer()
stl = powerline.render(renderer, winwidth)

if int(vim.eval('s:did_highlighting')) == 0:
	vim.command(renderer.get_hl_statements())
	vim.command('let s:did_highlighting = 1')

vim.command('return "{0}"'.format(stl))
EOF
endfunction

let &stl = '%!DynStl()'
