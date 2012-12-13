" Powerline vim plugin
"
" If Powerline is installed in a Python search path, load the plugin by
" adding the following line to your .vimrc:
"
" python import plugin.vim.load_vim_plugin

python import sys, vim, os
python sys.path.append(vim.eval('expand("<sfile>:h:h:h")'))
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
	for w in range(1, winnr('$'))
		" getwinvar() returns empty string for undefined variables.
		" Use has_key(getwinvar(w, ''), 'powerline') if you care about variable
		" being really defined (currently with w:powerline=='' it will throw
		" E706: variable type mismatch).
		if getwinvar(w, 'powerline') is# ''
			call setwinvar(w, 'powerline', {})
		endif

		call setwinvar(w, '&statusline', '%!Powerline('. w .')')
	endfor
endfunction

augroup Powerline
	autocmd!
	autocmd BufEnter,BufWinEnter,WinEnter * let w:current = 1 | call s:UpdateAllWindows()
	autocmd BufLeave,BufWinLeave,WinLeave * let w:current = 0
augroup END
