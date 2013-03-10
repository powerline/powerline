:tocdepth: 2

.. _installation-osx:

********************
Installation on OS X
********************

Plugin installation
===================

Python package
--------------

1. Install a proper Python version (see `issue #39 
   <https://github.com/Lokaltog/powerline/issues/39>`_ for a discussion 
   regarding the required Python version on OS X)::

       sudo port select python python27-apple

2. Install Powerline using the following command::

       pip install --user git+git://github.com/Lokaltog/powerline

.. note:: You need to use the GitHub URI when installing Powerline! This 
   project is currently unavailable on the PyPI due to a naming conflict 
   with an unrelated project.

Vim installation
----------------

Any terminal vim version with Python 3.2+ or Python 2.6+ support should work, 
but if you're using MacVim you need to install it using the following command::

    brew install macvim --env-std --override-system-vim

Font installation
=================

You need a patched font for Powerline to work on OS X. Check out the 
`powerline-fonts`_ repository on GitHub for patched versions of some popular 
programming fonts.

1. Download the font of your choice and install it by double-clicking the 
   font file in Finder and then click :guilabel:`Install this font` in the 
   preview window.

   If you can't find your preferred font in the `powerline-fonts`_ repo, 
   you'll have to patch your own font instead. See :ref:`font-patching` for 
   instructions.
2. Configure MacVim or your terminal emulator to use the patched font (the 
   correct font usually ends with *for Powerline*).

.. _powerline-fonts: https://github.com/Lokaltog/powerline-fonts

Troubleshooting
===============

.. contents::
   :local:

I can't see any fancy symbols, what's wrong?
--------------------------------------------

* If you're using iTerm2, please update to `this revision 
  <https://github.com/gnachman/iTerm2/commit/8e3ad6dabf83c60b8cf4a3e3327c596401744af6>`_ 
  or newer.
* You need to set your ``LANG`` and ``LC_*`` environment variables to 
  a UTF-8 locale (e.g. ``LANG=en_US.utf8``). Consult your Linux distro's 
  documentation for information about setting these variables correctly.

The colors look weird in the default OS X Terminal app!
-------------------------------------------------------

* The arrows may have the wrong colors if you have changed the "minimum 
  contrast" slider in the color tab of  your OS X settings.
* The default OS X Terminal app is known to have some issues with the 
  Powerline colors. Please use another terminal emulator. iTerm2 should work 
  fine.

The colors look weird in iTerm2!
--------------------------------

* The arrows may have the wrong colors if you have changed the "minimum 
  contrast" slider in the color tab of  your OS X settings.
* Please disable background transparency to resolve this issue.

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

* See `issue #39 <https://github.com/Lokaltog/powerline/issues/39>`_ for 
  a discussion and other possible solutions for this issue.

.. include:: troubleshooting-common.rst
