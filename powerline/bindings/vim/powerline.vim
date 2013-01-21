exec g:powerline_pycmd 'import uuid'
exec g:powerline_pycmd 'from powerline.core import Powerline'
exec g:powerline_pycmd 'powerline = Powerline("vim")'

if exists('*'. g:powerline_pyeval)
	let s:pyeval = function(g:powerline_pyeval)
else
	exec g:powerline_pycmd 'import json, vim'
	function! s:pyeval(e)
		exec g:powerline_pycmd 'vim.command("return " + json.dumps(eval(vim.eval("a:e"))))'
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
