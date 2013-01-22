if exists('g:powerline_loaded')
    finish
endif
let g:powerline_loaded = 1

let s:powerline_pycmd = substitute(get(g:, 'powerline_pycmd', 'py'), '\v^(py)%[thon](3?)$', '\1\2', '')
let s:powerline_pyeval = get(g:, 'powerline_pyeval', s:powerline_pycmd.'eval')

exec s:powerline_pycmd 'import uuid'
exec s:powerline_pycmd 'from powerline.core import Powerline'
exec s:powerline_pycmd 'powerline = Powerline("vim")'

if exists('*'. s:powerline_pyeval)
	let s:pyeval = function(s:powerline_pyeval)
else
	exec s:powerline_pycmd 'import json, vim'
	function! s:pyeval(e)
		exec s:powerline_pycmd 'vim.command("return " + json.dumps(eval(vim.eval("a:e"))))'
	endfunction
endif

function! Powerline(winnr, current)
	return s:pyeval('powerline.renderer.render('. a:winnr .', '. a:current .')')
endfunction

function! s:UpdateWindows()
	if ! exists('w:window_id')
		let w:window_id = s:pyeval('str(uuid.uuid4())')
	endif
	for winnr in range(1, winnr('$'))
		call setwinvar(winnr, '&statusline', '%!Powerline('. winnr .', '. (w:window_id == getwinvar(winnr, 'window_id')) .')')
	endfor
	redrawstatus
endfunction

augroup Powerline
	autocmd!
	autocmd BufEnter,BufWinEnter,WinEnter * call s:UpdateWindows()
augroup END
