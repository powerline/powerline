*************
Shell prompts
*************

.. note::
    Powerline daemon is not run automatically by any of my bindings. It is 
    advised to add

    .. code-block:: bash

        powerline-daemon -q

    before any other powerline-related code in the shell configuration file.

Bash prompt
===========

Add the following line to the :file:`bashrc`, where ``{repository_root}`` is the 
absolute path to the Powerline installation directory:

.. code-block:: bash

   . {repository_root}/powerline/bindings/bash/powerline.sh

.. note::
    Since without powerline daemon bash bindings are very slow PS2 
    (continuation) and PS3 (select) prompts are not set up. Thus it is advised 
    to use

    .. code-block:: bash

       powerline-daemon -q
       POWERLINE_BASH_CONTINUATION=1
       POWERLINE_BASH_SELECT=1
       . {repository_root}/powerline/bindings/bash/powerline.sh

    in the bash configuration file. Without ``POWERLINE_BASH_*`` variables PS2 
    and PS3 prompts are computed exactly once at bash startup.

.. warning::
    At maximum bash continuation PS2 and select PS3 prompts are computed each 
    time main PS1 prompt is computed. Thus putting e.g. current time into PS2 or 
    PS3 prompt will not work as expected.

    At minimum they are computed once on startup.

Zsh prompt
==========

Add the following line to the :file:`zshrc`, where ``{repository_root}`` is the 
absolute path to the Powerline installation directory:

.. code-block:: bash

   . {repository_root}/powerline/bindings/zsh/powerline.zsh

Fish prompt
===========

Add the following line to :file:`config.fish`, where ``{repository_root}`` is 
the absolute path to the Powerline installation directory:

.. code-block:: bash

   set fish_function_path $fish_function_path "{repository_root}/powerline/bindings/fish"
   powerline-setup

Rcsh prompt
===========

Powerline supports Plan9 rc reimplementation *by Byron Rakitzis* packaged by 
many \*nix distributions. To use it add

.. code-block:: bash

   . {repository_root}/powerline/bindings/rc/powerline.rc

to :file:`rcrc` file (usually :file:`~/.rcrc`) and make sure ``rc`` is started 
as a login shell (with ``-l`` argument): otherwise this configuration file is 
not read.

.. warning::
   Original Plan9 shell and its \*nix port are not supported because they are 
   missing ``prompt`` special function (it is being called once before each 
   non-continuation prompt). Since powerline could not support shell without 
   this or equivalent feature some other not-so-critical features of that port 
   were used.

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
    Mksh users have to set ``$POWERLINE_SHELL_CONTINUATION`` and 
    ``$POWERLINE_SHELL_SELECT`` to 1 to get PS2 and PS3 (continuation and 
    select) prompts support respectively: as command substitution is not 
    performed in these shells for these prompts they are updated once each time 
    PS1 prompt is displayed which may be slow.

    It is also known that while PS2 and PS3 update is triggered at PS1 update it 
    is *actually performed* only *next* time PS1 is displayed which means that 
    PS2 and PS3 prompts will be outdated and may be incorrect for this reason.

    Without these variables PS2 and PS3 prompts will be set once at startup. 
    This only touches mksh users: busybox and dash both have no such problem.

.. warning::
    Job count is using some weird hack that uses signals and temporary files for 
    interprocess communication. It may be wrong sometimes. Not the case in mksh.

.. warning::
    Busybox has two shells: ``ash`` and ``hush``. Second is known to segfault in 
    busybox 1.22.1 when using :file:`powerline.sh` script.
