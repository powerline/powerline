" Powerline vim example
" Run with :source %

python import sys, vim, os
python sys.path.append(vim.eval('expand("<sfile>:h:h:h")'))
python from examples.vim.pl import statusline
python from powerline.core import Powerline
python pl = Powerline('vim')

if exists('*pyeval')
	let s:pyeval = function('pyeval')
else
	python import json
	function! s:pyeval(e)
		python vim.command('return ' + json.dumps(eval(vim.eval('a:e'))))
	endfunction
endif

function! Powerline(winnr)
	return s:pyeval('pl.renderer.render('. a:winnr .')')
endfunction

function! s:WinDoPowerline()
	if ! exists('w:powerline')
		let w:powerline = {}
	endif

	let &l:stl = '%!Powerline('. winnr() .')'
endfunction

augroup Powerline
	autocmd!
	autocmd BufEnter,BufWinEnter,WinEnter * let w:current = 1 | let currwin = winnr() | windo call s:WinDoPowerline() | exec currwin . 'wincmd w'
	autocmd BufLeave,BufWinLeave,WinLeave * let w:current = 0
augroup END
