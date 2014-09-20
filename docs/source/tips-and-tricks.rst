***************
Tips and tricks
***************

Vim
===

Useful settings
---------------

You may find the following vim settings useful when using the Powerline
statusline:

.. code-block:: vim

   set laststatus=2 " Always display the statusline in all windows
   set showtabline=2 " Always display the tabline, even if there is only one tab
   set noshowmode " Hide the default mode text (e.g. -- INSERT -- below the statusline)

.. _tips-and-tricks-urxvt:

Rxvt-unicode
============

Terminus font and urxvt
-----------------------

The Terminus fonts does not have the powerline glyphs and unless someone submits 
a patch to the font author, it is unlikely to happen.  However, Andre Klärner 
came up with this work around: In your ``~/.Xdefault`` file add the following::

  urxvt*font: xft:Terminus:pixelsize=12,xft:Inconsolata\ for\ Powerline:pixelsize=12

This will allow urxvt to fallback onto the Inconsolata fonts in case it does not 
find the right glyphs within the terminus font.

Source Code Pro font and urxvt
------------------------------

Much like the terminus font that was mentioned above, a similar fix can be 
applied to the Source Code Pro fonts.

In the ``~/.Xdefaults`` add the following::

    URxvt*font: xft:Source\ Code\ Pro\ Medium:pixelsize=13:antialias=true:hinting=true,xft:Source\ Code\ Pro\ Medium:pixelsize=13:antialias=true:hinting=true

I noticed that Source Code Pro has the glyphs there already, but the pixel size 
of the fonts play a role in whether or not the > or the < separators showing up 
or not. Using font size 12, glyphs on the right hand side of the powerline are 
present, but the ones on the left don’t. Pixel size 14, brings the reverse 
problem. Font size 13 seems to work just fine.

Reloading powerline after update
================================

Once you have updated powerline you generally have the following options:

#. Restart the application you are using it in. This is the safest one. Will not 
   work if the application uses ``powerline-daemon``.
#. For shell and tmux bindings (except for zsh with libzpython): do not do 
   anything if you do not use ``powerline-daemon``, run ``powerline-daemon 
   --replace`` if you do.
#. Use powerline reloading feature.

    .. warning::
      This feature is an unsafe one. It is not guaranteed to work always, it may 
      render your Python constantly error out in place of displaying powerline 
      and sometimes may render your application useless, forcing you to 
      restart.

      *Do not report any bugs occurred when using this feature unless you know 
      both what caused it and how this can be fixed.*

   * When using zsh with libzpython use

     .. code-block:: bash

        powerline-reload

     .. note:: This shell function is only defined when using libzpython.

   * When using IPython use

     ::

        %powerline reload

   * When using Vim use

     .. code-block:: Vim

        py powerline.reload()
        " or (depending on Python version you are using)
        py3 powerline.reload()
