" Project vimrc file. To be sourced each time you open any file in this 
" repository. You may use [vimscript #3393][1] [(homepage)][2] to do this 
" automatically.
"
" [1]: http://www.vim.org/scripts/script.php?script_id=3393
" [2]: https://github.com/thinca/vim-localrc
let g:syntastic_python_flake8_args = '--ignore=W191,E501,E128,W291,E126,E101'
let b:syntastic_checkers = ['flake8']
unlet! g:python_space_error_highlight
let g:pymode_syntax_indent_errors = 0
let g:pymode_syntax_space_errors = 0
