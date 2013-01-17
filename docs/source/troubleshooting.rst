Troubleshooting
===============

I can't see any fancy symbols, what's wrong?
    Make sure that you've configured gvim or your terminal emulator to use 
    a patched font (see :ref:`font-patching`).

    Make sure that vim is compiled with the ``--with-features=big`` flag.

    If you're using rxvt-unicode, make sure that it's compiled with the 
    ``--enable-unicode3`` flag.

    If you're using iTerm2, please update to `this revision 
    <https://github.com/gnachman/iTerm2/commit/8e3ad6dabf83c60b8cf4a3e3327c596401744af6>`_ 
    or newer.

    You need to set your ``LANG`` and ``LC_*`` environment variables to 
    a UTF-8 locale (e.g. ``LANG=en_US.utf8``). Consult your Linux distro's 
    documentation for information about setting these variables correctly.

The fancy symbols look a bit blurry or "off"!
    Make sure that you have patched all variants of your font (i.e. both the 
    regular and the bold font files).

I'm unable to patch my font, what should I do?
    Font patching is only known to work on most Linux and OS X machines. If 
    you have followed the instructions on :ref:`font-patching` and still 
    have problems, please submit an issue on GitHub.

    You could also check out the `powerline-fonts 
    <https://github.com/Lokaltog/powerline-fonts>`_ repository on GitHub for 
    patched versions of some popular programming fonts.

The colors are weird in the default OS X Terminal app!
    The default OS X Terminal app is known to have some issues with the 
    Powerline colors. Please use another terminal emulator. iTerm2 should 
    work fine.

    The arrows may have the wrong colors if you have changed the "minimum 
    contrast" slider in the color tab of  your OS X settings.

I'm using tmux and Powerline looks like crap, what's wrong?
    You need to tell tmux that it has 256-color capabilities. Add this to 
    your :file:`.tmux.conf` to solve this issue::

        set -g default-terminal "screen-256color"

    If you use iTerm2, make sure that you have enabled the setting 'Set 
    locale variables automatically' in Profiles > Terminal > Environment.

Vim-specific issues
-------------------

The statusline has strange characters like ``^B`` in it!
    Please add ``set encoding=utf-8`` to your :file:`vimrc`.

The statusline has a lot of ``^`` or underline characters in it!
    You need to configure the ``fillchars`` setting to disable statusline 
    fillchars (see ``:h fillchars`` for details). Add this to your 
    :file:`vimrc` to solve this issue::

        set fillchars+=stl:\ ,stlnc:\ 

The statusline is hidden/only appears in split windows!
    Make sure that you have ``set laststatus=2`` in your :file:`vimrc`.

I'm using gVim for Windows, and ``cmd`` windows keep popping up when working in git repos!
    Either install ``libgit2`` and ``pygit2``, or disable the VCS segment in 
    your user configuration to resolve this issue.

I receive a ``NameError`` when trying to use Powerline with MacVim!
    Please install MacVim using this command::

        brew install macvim --env-std --override-system-vim

    Then install Powerline locally with ``pip install --user``, or by 
    running these commands in the ``powerline`` directory::

        ./setup.py build
        ./setup.py install --user

I receive an ``ImportError`` when trying to use Powerline on OS X!
    This is caused by an invalid ``sys.path`` when using system vim and 
    system Python. Please try to select another Python distribution::

        sudo port select python python27-apple
