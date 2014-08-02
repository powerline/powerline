*************
Shell prompts
*************

Bash prompt
===========

Add the following line to your :file:`bashrc`, where ``{repository_root}`` is 
the absolute path to your Powerline installation directory:

.. code-block:: bash

   . {repository_root}/powerline/bindings/bash/powerline.sh

Zsh prompt
==========

Add the following line to your :file:`zshrc`, where ``{repository_root}`` is the 
absolute path to your Powerline installation directory:

.. code-block:: bash

   . {repository_root}/powerline/bindings/zsh/powerline.zsh

Fish prompt
===========

Add the following line to your :file:`config.fish`, where ``{repository_root}`` 
is the absolute path to your Powerline installation directory:

.. code-block:: bash

   set fish_function_path $fish_function_path "{repository_root}/powerline/bindings/fish"
   powerline-setup

.. _tmux-statusline:

Busybox (ash), mksh and dash prompt
=====================================

After launching busybox run the following command:

.. code-block:: bash

   . {repository_root}/powerline/bindings/shell/powerline.sh

Mksh users may put this line into ``~/.mkshrc`` file. Dash users may use the 
following in ``~/.profile``:

.. code-block:: bash

    if test "x$0" != "x${0#dash}" ; then
        export ENV={repository_root}/powerline/bindings/shell/powerline.sh
    fi

.. note::
    Dash users that already have ``$ENV`` defined should either put the ``. 
    …/shell/powerline.sh`` line in the ``$ENV`` file or create a new file which 
    will source (using ``.`` command) both former ``$ENV`` file and 
    :file:`powerline.sh` files and set ``$ENV`` to the path of this new file.

.. warning::
    Job count is using some weird hack that uses signals and temporary files for 
    interprocess communication. It may be wrong sometimes. Not the case in mksh.

.. warning::
    Busybox has two shells: ``ash`` and ``hush``. Second is known to segfault in 
    busybox 1.22.1 when using :file:`powerline.sh` script.
