" Powerline vim plugin
"
" If Powerline is installed in a Python search path, load the plugin by
" adding the following line to your .vimrc:
"
" python import plugin.vim.load_vim_plugin

python import sys, vim, os
python sys.path.append(vim.eval('expand("<sfile>:h:h:h")'))
python import uuid
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

function! s:UpdateAllWindows()
	for winnr in range(1, winnr('$'))
		if getwinvar(winnr, 'window_id') is# ''
			call setwinvar(winnr, 'window_id', s:pyeval('str(uuid.uuid4())'))
		endif

		call setwinvar(winnr, '&statusline', '%!Powerline('. winnr .')')
	endfor
endfunction

augroup Powerline
	autocmd!
	autocmd BufEnter,BufWinEnter,WinEnter * let w:current = 1 | call s:UpdateAllWindows()
	autocmd BufLeave,BufWinLeave,WinLeave * let w:current = 0
augroup END
