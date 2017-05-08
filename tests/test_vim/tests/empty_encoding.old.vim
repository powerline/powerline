#!/usr/bin/vim -S
if has('multi_byte')
	if empty(&encoding)
		call writefile(['&encoding option value is empty, even though Vim has +multibyte'], 'message.fail')
		cquit
	endif
	qall
endif
if !empty(&encoding)
	call writefile(['&encoding option value is not empty, even though Vim does not have +multibyte'], 'message.fail')
	cquit
endif

let g:powerline_config_paths = [expand('<sfile>:p:h:h:h:h') . '/powerline/config_files']

try
	source <sfile>:p:h:h:h:h/powerline/bindings/vim/plugin/powerline.vim
catch
	call writefile(['Unexpected exception:', v:exception], 'message.fail')
	cquit
endtry
set ls=2
redrawstatus!
redir => g:messages
	messages
redir END
let mess=split(g:messages, "\n")
if len(mess)>1
	call writefile(['Unexpected message(s):']+mess, 'message.fail')
	cquit
endif
qall!
