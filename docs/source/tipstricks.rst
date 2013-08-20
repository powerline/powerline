*************
Tips & Tricks
*************

Vim
===

Fix terminal timeout when pressing escape
-----------------------------------------

When you're pressing :kbd:`Escape` to leave insert mode in the terminal, it 
will by default take a second or another keystroke to leave insert mode 
completely and update the statusline. If you find this annoying, you can add 
the following snippet to your :file:`vimrc` to escape insert mode 
immediately:

.. code-block:: vim

   if ! has('gui_running')
       set ttimeoutlen=10
       augroup FastEscape
           autocmd!
           au InsertEnter * set timeoutlen=0
           au InsertLeave * set timeoutlen=1000
       augroup END
   endif

Useful settings
---------------

You may find the following vim settings useful when using the Powerline 
statusline:

.. code-block:: vim
   
   set laststatus=2 " Always display the statusline in all windows
   set noshowmode " Hide the default mode text (e.g. -- INSERT -- below the statusline)
