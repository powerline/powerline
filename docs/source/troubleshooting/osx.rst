***********************
Troubleshooting on OS X
***********************

I can’t see any fancy symbols, what’s wrong?
--------------------------------------------

* If you’re using iTerm2, please update to `this revision 
  <https://github.com/gnachman/iTerm2/commit/8e3ad6dabf83c60b8cf4a3e3327c596401744af6>`_ 
  or newer. Also make sure that Preferences>Profiles>Text>Non-ASCII Font is the same as
  your main Font.
* You need to set your ``LANG`` and ``LC_*`` environment variables to 
  a UTF-8 locale (e.g. ``LANG=en_US.utf8``). Consult your Linux distro’s 
  documentation for information about setting these variables correctly.

The colors look weird in the default OS X Terminal app!
-------------------------------------------------------

* The arrows may have the wrong colors if you have changed the “minimum 
  contrast” slider in the color tab of your OS X settings.
* The default OS X Terminal app is known to have some issues with the 
  Powerline colors. Please use another terminal emulator. iTerm2 should work 
  fine.

The colors look weird in iTerm2!
--------------------------------

* The arrows may have the wrong colors if you have changed the “minimum 
  contrast” slider in the color tab of your OS X settings.
* If you're using transparency, check “Keep background colors opaque”.

Statusline is getting wrapped to the next line in iTerm2
--------------------------------------------------------

* Turn off “Treat ambigious-width characters as double width” in `Preferences 
  --> Text`.
* Alternative: remove fancy dividers (they suck in this case), set 
  :ref:`ambiwidth <config-common-ambiwidth>` to 2.

I receive a ``NameError`` when trying to use Powerline with MacVim!
-------------------------------------------------------------------

* Please install MacVim using this command::

      brew install macvim --env-std --override-system-vim

  Then install Powerline locally with ``pip install --user``, or by 
  running these commands in the ``powerline`` directory::

      ./setup.py build
      ./setup.py install --user

I receive an ``ImportError`` when trying to use Powerline on OS X!
------------------------------------------------------------------

* This is caused by an invalid ``sys.path`` when using system vim and system 
  Python. Please try to select another Python distribution::

      sudo port select python python27-apple

* See `issue #39 <https://github.com/powerline/powerline/issues/39>`_ for 
  a discussion and other possible solutions for this issue.

I receive “FSEventStreamStart: register_with_server: ERROR” with status_colors
------------------------------------------------------------------------------

This is `a known <https://github.com/joyent/node/issues/5463>`_ libuv issue that 
happens if one is trying to watch too many files. It should be fixed in 
libuv-0.12. Until then it is suggested to either disable ``status_colors`` (from 
:py:func:`powerline.segments.common.vcs.branch`) or choose stat-based watcher 
(will have effectively the same effect as disabling ``status_colors``).
