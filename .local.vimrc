" Project vimrc file. To be sourced each time you open any file in this 
" repository. You may use [vimscript #3393][1] [(homepage)][2] to do this 
" automatically.
"
" [1]: http://www.vim.org/scripts/script.php?script_id=3393
" [2]: https://github.com/thinca/vim-localrc
setlocal noexpandtab
" Despite promise somewhere alignment is done only using tabs. Thus setting 
" &tabstop is a requirement.
setlocal tabstop=4
let g:syntastic_python_flake8_args = '--ignore=W191,E501,E121,E122,E123,E128,E225,W291,E126'
let b:syntastic_checkers = ['flake8']
