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

function! s:GetWinID(winnr)
	let r = getwinvar(a:winnr, 'window_id')
	if empty(r)
		let r = s:pyeval('str(uuid.uuid4())')
		call setwinvar(a:winnr, 'window_id', r)
		call setwinvar(a:winnr, '&statusline', '%!Powerline("'.r.'")')
	endif
	return r
endfunction

function! Powerline(window_id)
	let winidx = index(map(range(1, winnr('$')), 's:GetWinID(v:val)'), a:window_id)
	let current = w:window_id is# a:window_id
	return s:pyeval('powerline.renderer.render("'. a:window_id .'", '. winidx .', '. current .')')
endfunction

function! PowerlineNew()
	return Powerline(s:GetWinID(winnr()))
endfunction

set statusline=%!PowerlineNew()

function! PowerlineRegisterCachePurgerEvent(event)
	exec s:powerline_pycmd 'from powerline.segments.vim import launchevent as powerline_launchevent'
	augroup Powerline
		exec 'autocmd!' a:event '*' s:powerline_pycmd.' powerline_launchevent("'.a:event.'")'
	augroup END
endfunction

augroup Powerline
	autocmd!
	autocmd ColorScheme * exec s:powerline_pycmd 'powerline.renderer.reset_highlight()'
augroup END
