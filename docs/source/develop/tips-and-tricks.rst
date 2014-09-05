****************************************
Tips and tricks for powerline developers
****************************************

Profiling powerline in Vim
==========================

Given that current directory is the root of the powerline repository the 
following command may be used:

.. code-block:: sh

    vim --cmd 'let g:powerline_pyeval="powerline#debug#profile_pyeval"' \
        --cmd 'set rtp=powerline/bindings/vim' \
        -c 'runtime! plugin/powerline.vim' \
        {other arguments if needed}

After some time run ``:WriteProfiling {filename}`` Vim command. Currently this 
only works with recent Vim and python-2*. It should be easy to modify 
:file:`powerline/bindings/vim/autoload/powerline/debug.vim` to suit other 
needs.
