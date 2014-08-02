*********************
Installation on Linux
*********************

The following distribution-specific packages are officially supported, and they 
provide an easy way of installing and upgrading Powerline. The packages will 
automatically do most of the configuration for you.

* `Arch Linux (AUR), Python 2 version <https://aur.archlinux.org/packages/python2-powerline-git/>`_
* `Arch Linux (AUR), Python 3 version <https://aur.archlinux.org/packages/python-powerline-git/>`_
* Gentoo Live ebuild in `raiagent <https://github.com/leycec/raiagent>`_ overlay

If you're running a distribution without an official package you'll have to 
follow the installation guide below:

1. Install Python 3.2+ or Python 2.6+ with ``pip``. This step is 
   distribution-specific, so no commands provided.
2. Install Powerline using the following command::

       pip install --user git+git://github.com/Lokaltog/powerline

.. note:: You need to use the GitHub URI when installing Powerline! This 
   project is currently unavailable on the PyPI due to a naming conflict 
   with an unrelated project.

.. note:: If you are powerline developer you should be aware that ``pip install 
   --editable`` does not currently fully work. If you
   install powerline this way you will be missing ``powerline`` executable and 
   need to symlink it. It will be located in ``scripts/powerline``.
