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
	call s:CriticalError('You need vim compiled with Python 2.6+ or 3.2+ support
		\ for Powerline to work. Please consult the documentation for more details.')
	finish
endif

let s:powerline_pycmd = substitute(get(g:, 'powerline_pycmd', has('python') ? 'py' : 'py3'),
			\'\v^(py)%[thon](3?)$', '\1\2', '')
let s:powerline_pyeval = get(g:, 'powerline_pyeval', s:powerline_pycmd.'eval')

let s:import_cmd = 'from powerline.vim import VimPowerline'
try
	exec s:powerline_pycmd "try:\n"
				\         ."	".s:import_cmd."\n"
				\         ."except ImportError:\n"
				\         ."	import sys, vim\n"
				\         ."	sys.path.append(vim.eval('expand(\"<sfile>:h:h:h:h:h\")'))\n"
				\         ."	".s:import_cmd
	let s:launched = 1
finally
	if !exists('s:launched')
		call s:CriticalError('An error occurred while importing the Powerline package.
			\ This could be caused by an invalid sys.path setting, or by an incompatible
			\ Python version (Powerline requires Python 2.6+ or 3.2+ to work). Please consult
			\ the troubleshooting section in the documentation for possible solutions.')
		finish
	else
		unlet s:launched
	endif
endtry

if !get(g:, 'powerline_debugging_pyeval') && exists('*'. s:powerline_pyeval)
	let s:pyeval = function(s:powerline_pyeval)
else
	exec s:powerline_pycmd 'import json, vim'
	exec "function! s:pyeval(e)\n".
		\	s:powerline_pycmd." vim.command('return ' + json.dumps(eval(vim.eval('a:e'))))\n".
		\"endfunction"
endif

let s:last_window_id = 0
function! s:GetWinID(winnr)
	let r = getwinvar(a:winnr, 'window_id')
	if empty(r)
		let r = s:last_window_id
		let s:last_window_id += 1
		call setwinvar(a:winnr, 'window_id', r)
	endif
	" Without this condition it triggers unneeded statusline redraw
	if getwinvar(a:winnr, '&statusline') isnot# '%!Powerline('.r.')'
		call setwinvar(a:winnr, '&statusline', '%!Powerline('.r.')')
	endif
	return r
endfunction

function! Powerline(window_id)
	let winidx = index(map(range(1, winnr('$')), 's:GetWinID(v:val)'), a:window_id)
	let current = w:window_id is# a:window_id
	return s:pyeval('powerline.render('. a:window_id .', '. winidx .', '. current .')')
endfunction

function! PowerlineNew()
	call map(range(1, winnr('$')), 's:GetWinID(v:val)')
endfunction

function! PowerlineRegisterCachePurgerEvent(event)
	exec s:powerline_pycmd 'from powerline.segments.vim import launchevent as powerline_launchevent'
	augroup Powerline
		exec 'autocmd' a:event '*' s:powerline_pycmd.' powerline_launchevent("'.a:event.'")'
	augroup END
endfunction

augroup Powerline
	autocmd! ColorScheme * :exec s:powerline_pycmd 'powerline.reset_highlight()'
	autocmd! VimEnter    * :redrawstatus!
	autocmd! VimLeavePre * :exec s:powerline_pycmd 'powerline.shutdown()'
augroup END

exec s:powerline_pycmd 'powerline = VimPowerline()'
exec s:powerline_pycmd 'del VimPowerline'
" Is immediately changed when PowerlineNew() function is run. Good for global 
" value.
set statusline=%!PowerlineNew()
call PowerlineNew()
