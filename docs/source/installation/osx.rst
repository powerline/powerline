********************
Installation on OS X
********************

Python package
==============

1. Install a proper Python version (see `issue #39 
   <https://github.com/powerline/powerline/issues/39>`_ for a discussion 
   regarding the required Python version on OS X)::

       sudo port select python python27-apple

   . Homebrew may be used here::

       brew install python

   .

   .. note::
      In case :file:`powerline.sh` as a client ``socat`` and ``coreutils`` need 
      to be installed. ``coreutils`` may be installed using ``brew install 
      coreutils``.

2. Install Powerline using one of the following commans:

   .. code-block:: sh

       pip install --user powerline-status

   will get current release version and

   .. code-block:: sh

       pip install --user git+git://github.com/powerline/powerline

   will get latest development version.

   .. warning::
      When using ``brew install`` to install Python one must not supply
      ``--user`` flag to ``pip``.

   .. note::
      Due to the naming conflict with an unrelated project powerline is named 
      ``powerline-status`` in PyPI.

   .. note::
      Powerline developers should be aware that``pip install --editable`` does 
      not currently fully work. Installation performed this way are missing 
      ``powerline`` executable that needs to be symlinked. It will be located in 
      ``scripts/powerline``.

Vim installation
================

Any terminal vim version with Python 3.2+ or Python 2.6+ support should work, 
but MacVim users need to install it using the following command::

    brew install macvim --env-std --override-system-vim

Fonts installation
==================

Install downloaded patched font by double-clicking the font file in Finder, then 
clicking :guilabel:`Install this font` in the preview window.

After installing the patched font MacVim or terminal emulator (whatever 
application powerline should work with) need to be configured to use the patched 
font. The correct font usually ends with *for Powerline*.
