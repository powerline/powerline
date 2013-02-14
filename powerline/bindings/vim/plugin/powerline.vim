if exists('g:powerline_loaded')
    finish
endif
let g:powerline_loaded = 1

function! s:CriticalError(message)
	echohl ErrorMsg
	echomsg a:message
	echohl None
endfunction

if ! has('python') && ! has('python3')
	call s:CriticalError('You need vim compiled with Python 2.7 or 3.3+ support
		\ for Powerline to work. Please consult the documentation for more details.')
	finish
endif

let s:powerline_pycmd = substitute(get(g:, 'powerline_pycmd', 'py'), '\v^(py)%[thon](3?)$', '\1\2', '')
let s:powerline_pyeval = get(g:, 'powerline_pyeval', s:powerline_pycmd.'eval')

exec s:powerline_pycmd 'import uuid'
try
	exec s:powerline_pycmd 'from powerline.core import Powerline'
catch
	" An error occured while importing the module, it could be installed
	" outside of Python's module search paths. Update sys.path and try again.
	exec s:powerline_pycmd 'import sys, vim'
	exec s:powerline_pycmd 'sys.path.append(vim.eval(''expand("<sfile>:h:h:h:h:h")''))'
	try
		exec s:powerline_pycmd 'from powerline.core import Powerline'
	catch
		call s:CriticalError('An error occured while importing the Powerline package.
			\ This could be caused by an invalid sys.path setting, or by an incompatible
			\ Python version (Powerline requires Python 2.7 or 3.3+ to work). Please consult
			\ the troubleshooting section in the documentation for possible solutions.')
		finish
	endtry
endtry
exec s:powerline_pycmd 'powerline = Powerline("vim", segment_info={})'

if !get(g:, 'powerline_debugging_pyeval') && exists('*'. s:powerline_pyeval)
	let s:pyeval = function(s:powerline_pyeval)
else
	exec s:powerline_pycmd 'import json, vim'
	exec "function! s:pyeval(e)\n".
		\	s:powerline_pycmd." vim.command('return ' + json.dumps(eval(vim.eval('a:e'))))\n".
		\"endfunction"
endif

function! Powerline(winnr, current)
	return s:pyeval('powerline.renderer.render('. a:winnr .', '. a:current .')')
endfunction

function! s:UpdateWindows(use_last_current_window_id)
	if ! exists('w:window_id')
		let w:window_id = s:pyeval('str(uuid.uuid4())')
	endif
	for winnr in range(1, winnr('$'))
		let current = 0
		if w:window_id == getwinvar(winnr, 'window_id') || (a:use_last_current_window_id && getwinvar(winnr, 'window_id') == s:last_current_window_id)
			let current = 1
			if bufname(winbufnr(winnr)) isnot# '[Command Line]'
				let s:last_current_window_id = getwinvar(winnr, 'window_id')
			endif
		endif
		call setwinvar(winnr, '&statusline', '%!Powerline('. winnr .', '. current .')')
	endfor
endfunction

function! PowerlineRegisterCachePurgerEvent(event)
	exec s:powerline_pycmd 'from powerline.segments.vim import launchevent as powerline_launchevent'
	augroup Powerline
		exec 'autocmd!' a:event '*' s:powerline_pycmd.' powerline_launchevent("'.a:event.'")'
	augroup END
endfunction

let s:last_current_window_id = ''
augroup Powerline
	autocmd!
	autocmd BufEnter,BufWinEnter,WinEnter,CmdwinEnter * call s:UpdateWindows(0) | redrawstatus
	autocmd CmdwinLeave * call s:UpdateWindows(1)
	autocmd ColorScheme * exec s:powerline_pycmd 'powerline.renderer.reset_highlight()'
augroup END
