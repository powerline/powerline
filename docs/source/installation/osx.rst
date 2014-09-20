********************
Installation on OS X
********************

Python package
==============

1. Install a proper Python version (see `issue #39 
   <https://github.com/Lokaltog/powerline/issues/39>`_ for a discussion 
   regarding the required Python version on OS X)::

       sudo port select python python27-apple

   . You may use homebrew for this::

       brew install python

   .

   .. note::
      In case you want or have to use ``powerline.sh`` socat-based client you 
      should also install GNU env named ``genv``. This may be achieved by 
      running ``brew install coreutils``.

2. Install Powerline using the following command::

       pip install --user git+git://github.com/Lokaltog/powerline

   .. warning::
      When using ``brew install`` to install Python one must not supply
      ``--user`` flag to ``pip``.

   .. note::
      You need to use the GitHub URI when installing Powerline! This project is 
      currently unavailable on the PyPI due to a naming conflict with an 
      unrelated project.

   .. note::
      If you are powerline developer you should be aware that ``pip install 
      --editable`` does not currently fully work. If you install powerline this 
      way you will be missing ``powerline`` executable and need to symlink it. It 
      will be located in ``scripts/powerline``.

Vim installation
================

Any terminal vim version with Python 3.2+ or Python 2.6+ support should work, 
but if you’re using MacVim you need to install it using the following command::

    brew install macvim --env-std --override-system-vim

Fonts installation
==================

Install downloaded patched font by double-clicking the font file in Finder, then 
clicking :guilabel:`Install this font` in the preview window.

After installing the patched font you need to update MacVim or your terminal 
emulator to use the patched font. The correct font usually ends with *for 
Powerline*.
