********************
Installation on OS X
********************

Python package
==============

1. Install a proper Python version (see `issue #39 
   <https://github.com/powerline/powerline/issues/39>`_ for a discussion 
   regarding the required Python version on OS X)::

       sudo port select python python27-apple

   Homebrew may be used here::

       brew install python

   .. note::
      There are three variants of the powerline client.  The fastest is
      written in C and will be compiled if the compiler and libraries are
      detected during installation.  The second fastest option is
      :file:`powerline.sh` which requires ``socat`` and ``coreutils``.
      ``coreutils`` may be installed using ``brew install 
      coreutils``.  If neither of these are viable, then Powerline will
      utilize a fallback client written in Python.

2. Install Powerline using one of the following commands:

   .. code-block:: sh

       pip install --user powerline-status

   will get current release version and

   .. code-block:: sh

       pip install --user git+https://github.com/powerline/powerline

   will get latest development version.

   .. warning::
      When using ``brew install`` to install Python one must not supply
      ``--user`` flag to ``pip``.

   .. note::
      Due to the naming conflict with an unrelated project powerline is named 
      ``powerline-status`` in PyPI.

   .. note::
      Powerline developers should be aware that ``pip install --editable`` does 
      not currently fully work. Installation performed this way are missing 
      ``powerline`` executable that needs to be symlinked. It will be located in 
      ``scripts/powerline``.

Vim installation
================

Any terminal vim version with Python 3.2+ or Python 2.6+ support should work, 
but MacVim users need to install it using the following command::

    brew install macvim --env-std --with-override-system-vim

Fonts installation
==================

To install patched font double-click the font file in Finder, then click 
:guilabel:`Install this font` in the preview window.

After installing the patched font MacVim or terminal emulator (whatever 
application powerline should work with) need to be configured to use the patched 
font. The correct font usually ends with *for Powerline*.
