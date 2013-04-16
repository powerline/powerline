*************
Configuration
*************

.. note:: **You DO NOT have to fork the main GitHub repo to personalize your 
   Powerline configuration!** Please read through the :ref:`quick-guide` for 
   a quick introduction to user configuration.

Powerline is configured with one main configuration file, and with separate 
configuration files for themes and colorschemes. All configuration files are 
written in JSON, with the exception of segment definitions, which are 
written in Python.

Powerline provides default configurations in the following locations:

`Main configuration`_
    :file:`powerline/config.json`
`Colorschemes`_
    :file:`powerline/colorschemes/{extension}/default.json`
`Themes`_
    :file:`powerline/themes/{extension}/default.json`

The default configuration files are stored in the main package. User 
configuration files are stored in :file:`$XDG_CONFIG_HOME/powerline` for 
Linux users, and in :file:`~/.config/powerline` for OS X users. This usually 
corresponds to :file:`~/.config/powerline` on both platforms.

.. _quick-guide:

Quick setup guide
=================

This guide will help you with the initial configuration of Powerline.

Start by copying the entire set of default configuration files to the 
corresponding path in your user config directory:

.. code-block:: sh

   mkdir ~/.config/powerline
   cp -R /path/to/powerline/config_files/* ~/.config/powerline

Each extension (vim, tmux, etc.) has its own theme, and they are located in 
:file:`{config directory}/themes/{extension}/default.json`.

If you want to move, remove or customize any of the provided segments, you 
can do that by updating the segment dictionary in the theme you want to 
customize. A segment dictionary looks like this:

.. code-block:: javascript

   {
       "name": "segment_name"
       ...
   }

You can move the segment dictionaries around to change the segment 
positions, or remove the entire dictionary to remove the segment from the 
prompt or statusline.

.. note:: It's essential that the contents of all your configuration files 
   is valid JSON! It's strongly recommended that you run your configuration 
   files through ``jsonlint`` after changing them.

Some segments need a user configuration to work properly. Here's a couple of 
segments that you may want to customize right away:

**E-mail alert segment**
    You have to set your username and password (and possibly server/port) 
    for the e-mail alert segment. If you're using GMail it's recommended 
    that you `generate an application-specific password 
    <https://accounts.google.com/IssuedAuthSubTokens>`_ for this purpose.

    Open a theme file, scroll down to the ``email_imap_alert`` segment and 
    set your ``username`` and ``password``.  The server defaults to GMail's 
    IMAP server, but you can set the server/port by adding a ``server`` and 
    a ``port`` argument.
**Weather segment**
    The weather segment will try to find your location using a GeoIP lookup, 
    so unless you're on a VPN you probably won't have to change the location 
    query.
   
    If you want to change the location query or the temperature unit you'll 
    have to update the segment arguments. Open a theme file, scroll down to 
    the weather segment and update it to include unit/location query 
    arguments:

    .. code-block:: javascript

       {
           "name": "weather",
           "priority": 50,
           "args": {
               "unit": "f",
               "location_query": "oslo, norway"
           }
       },

.. _config-main:

Main configuration
==================

:Location: :file:`powerline/config.json`

The main configuration file defines some common options that applies to all 
extensions, as well as some extension-specific options like themes and 
colorschemes.

Common configuration
--------------------

Common configuration is a subdictionary that is a value of ``common`` key in 
:file:`powerline/config.json` file.

.. _config-common-term_truecolor:

``term_truecolor``
    Defines whether to output cterm indices (8-bit) or RGB colors (24-bit) 
    to the terminal emulator. See the :ref:`term-feature-support-matrix` for 
    information on whether your terminal emulator supports 24-bit colors.

.. _config-common-ambiwidth:

``ambiwidth``
    Tells powerline what to do with characters with East Asian Width Class 
    Ambigious (such as Euro, Registered Sign, Copyright Sign, Greek
    letters, Cyrillic letters). Valid values: any positive integer; it is 
    suggested that you only set it to 1 (default) or 2.

.. _config-common-additional_escapes:

``additional_escapes``
    Valid for shell extensions, makes sense only if :ref:`term_truecolor 
    <config-common-term_truecolor>` is enabled. Is to be set from command-line 
    (unless you are sure you always need it). Controls additional escaping that 
    is needed for tmux/screen to work with terminal true color escape codes: 
    normally tmux/screen prevent terminal emulator from receiving these control 
    codes thus rendering powerline prompt colorless. Valid values: ``"tmux"``, 
    ``"screen"``, ``null`` (default).

``dividers``
    Defines the dividers used in all Powerline extensions. This option 
    should usually only be changed if you don't have a patched font, or if 
    you use a font patched with the legacy font patcher.

    The ``hard`` dividers are used to divide segments with different 
    background colors, while the ``soft`` dividers are used to divide 
    segments with the same background color.

.. _config-common-paths:

``paths``
    Defines additional paths which will be searched for modules when using 
    :ref:`module segment option <config-themes-seg-module>`. Paths defined here 
    have priority when searching for modules.

``log_file``
    Defines path which will hold powerline logs. If not present, logging will be 
    done to stderr.

``log_level``
    String, determines logging level. Defaults to ``WARNING``.

``log_format``
    String, determines format of the log messages. Defaults to 
    ``'%(asctime)s:%(level)s:%(message)s'``.

``interval``
    Number, determines time (in seconds) between checks for changed 
    configuration. Checks are done in a seprate thread. Use ``null`` to check 
    for configuration changes on ``.render()`` call in main thread.
    Defaults to ``None``.

``reload_config``
    Boolean, determines whether configuration should be reloaded at all. 
    Defaults to ``True``.

Extension-specific configuration
--------------------------------

Common configuration is a subdictionary that is a value of ``ext`` key in 
:file:`powerline/config.json` file.

``colorscheme``
    Defines the colorscheme used for this extension.

``theme``
    .. _config-ext-theme:

    Defines the theme used for this extension.

``local_themes``
    .. _config-ext-local_themes:

    Defines themes used when certain conditions are met, e.g. for 
    buffer-specific statuslines in vim. Value depends on extension used. For vim 
    it is a dictionary ``{matcher_name : theme_name}``, where ``matcher_name`` 
    is either ``matcher_module.module_attribute`` or ``module_attribute`` 
    (``matcher_module`` defaults to ``powerline.matchers.vim``) and 
    ``module_attribute`` should point to a function that returns boolean value 
    indicating that current buffer has (not) matched conditions.

.. _config-colors:

Color definitions
=================

:Location: :file:`powerline/colors.json`

.. _config-colors-colors:

``colors``
    Color definitions, consisting of a dict where the key is the name of the 
    color, and the value is one of the following:

    * A cterm color index.
    * A list with a cterm color index and a hex color string (e.g. ``[123, 
      "aabbcc"]``). This is useful for colorschemes that use colors that 
      aren't available in color terminals.

``gradients``
    Gradient definitions, consisting of a dict where the key is the name of the 
    gradient, and the value is a list containing one or two items, second item 
    is optional:

    * A list of cterm color indicies.
    * A list of hex color strings.

.. _config-colorschemes:

Colorschemes
============

:Location: :file:`powerline/colorschemes/{extension}/{name}.json`

``name``
    Name of the colorscheme.

.. _config-colorschemes-groups:

``groups``
    Segment highlighting groups, consisting of a dict where the key is the 
    name of the highlighting group (usually the function name for function 
    segments), and the value is a dict that defines the foreground color, 
    background color and optional attributes:

    ``fg``
        Foreground color. Must be defined in :ref:`colors 
        <config-colors-colors>`.

    ``bg``
        Background color. Must be defined in :ref:`colors 
        <config-colors-colors>`.

    ``attr``
        Optional list of attributes. Valid values are one or more of 
        ``bold``, ``italic`` and ``underline``. Note that some attributes 
        may be unavailable in some applications or terminal emulators.

``mode_translations``
    Mode-specific highlighting for extensions that support it (e.g. the vim 
    extension). It's an easy way of changing a color in a specific mode.  
    Consists of a dict where the key is the mode and the value is a dict 
    with the following options:

    ``colors``
        A dict where the key is the color to be translated in this mode, and 
        the value is the new color. Both the key and the value must be defined 
        in :ref:`colors <config-colors-colors>`.

    ``groups``
        Segment highlighting groups for this mode. Same syntax as the main 
        :ref:`groups <config-colorschemes-groups>` option.

.. _config-themes:

Themes
======

:Location: :file:`powerline/themes/{extension}/{name}.json`

``name``
    Name of the theme.

.. _config-themes-default_module:

``default_module``
    Python module where segments will be looked by default.

.. _config-themes-segment_data:

``segment_data``
    A dict where keys are segment names or strings ``{module}.{name}``. Used to 
    specify default values for various keys:
    :ref:`after <config-theme-seg-after>`,
    :ref:`before <config-theme-seg-before>`,
    :ref:`contents <config-theme-seg-contents>` (only for string segments
    if :ref:`name <config-themes-seg-name>` is defined),
    :ref:`args <config-themes-seg-args>` (only for function segments). When 
    using :ref:`local themes <config-ext-local_themes>` values of these keys are 
    first searched in the segment description, then in ``segment_data`` key of 
    a local theme, then in ``segment_data`` key of a :ref:`default theme 
    <config-ext-theme>`. For the :ref:`default theme <config-ext-theme>` itself 
    step 2 is obviously avoided.

``segments``
    A dict with a ``left`` and a ``right`` list, consisting of segment 
    dicts. Each segment has the following options:

    ``type``
        The segment type. Can be one of ``function`` (default), ``string`` 
        or ``filler``:

        ``function``
            The segment contents is the return value of the function defined 
            in the :ref:`name option <config-themes-seg-name>`.

        ``string``
            A static string segment where the contents is defined in the 
            :ref:`contents option <config-themes-seg-contents>`, and the 
            highlighting group is defined in the :ref:`highlight_group 
            option <config-themes-seg-highlight_group>`.

    ``module``
        .. _config-themes-seg-module:

        Function module, only required for function segments. Defaults to 
        ``powerline.segments.{extension}``. Default is overriden by 
        :ref:`default_module theme option <config-themes-default_module>`.

    ``name``
        .. _config-themes-seg-name:

        Function name, only required for function segments.

    ``highlight_group``
        .. _config-themes-seg-highlight_group:

        Highlighting group for this segment. Consists of a prioritized list 
        of highlighting groups, where the first highlighting group that is 
        available in the colorscheme is used.

        Ignored for segments that have ``function`` type.

    ``before``
        .. _config-themes-seg-before:

        A string which will be prepended to the segment contents.

    ``after``
        .. _config-themes-seg-after:

        A string which will be appended to the segment contents.

    ``contents``
        .. _config-themes-seg-contents:

        Segment contents, only required for ``string`` segments.

    ``args``
        .. _config-themes-seg-args:

        A dict of arguments to be passed to a ``function`` segment.

    ``align``
        Aligns the segments contents to the left (``l``), center (``c``) or 
        right (``r``).

    ``width``
        Enforces a specific width for this segment.

        This segment will work as a spacer if the width is set to ``auto``.
        Several spacers may be used, and the space will be distributed 
        equally among all the spacer segments. Spacers may have contents, 
        either returned by a function or a static string, and the contents 
        can be aligned with the ``align`` property.

    ``priority``
        Optional segment priority. Segments with priority ``None`` (the default 
        priority, represented by ``null`` in json) will always be included, 
        regardless of the width of the prompt/statusline.

        If the priority is any number, the segment may be removed if the 
        prompt/statusline width is too small for all the segments to be 
        rendered. A lower number means that the segment has a higher priority.

        Segments are removed according to their priority, with low priority 
        segments being removed first.

    ``draw_hard_divider``, ``draw_soft_divider``
        Whether to draw a divider between this and the adjacent segment. The 
        adjacent segment is to the *right* for segments on the *left* side, and 
        vice versa. Hard dividers are used between segments with different 
        background colors, soft ones are used between segments with same 
        background. Both options default to ``True``.

    ``draw_inner_divider``
        Determines whether inner soft dividers are to be drawn for function 
        segments. Only applicable for functions returning multiple segments. 
        Defaults to ``False``.

    ``exclude_modes``
        A list of modes where this segment will be excluded: The segment is 
        included in all modes, *except* for the modes in this list.

    ``include_modes``
        A list of modes where this segment will be included: The segment is 
        *not* included in any modes, *except* for the modes in this list.

Segments
========

Segments are written in Python, and the default segments provided with 
Powerline are located in :file:`powerline/segments/{extension}.py`.  
User-defined segments can be defined in any module in ``sys.path`` or 
:ref:`paths common configuration option <config-common-paths>`, import is 
always absolute.

Segments are regular Python functions, and they may accept arguments. All 
arguments should have a default value which will be used for themes that 
don't provide an ``args`` dict.

A segment function must return one of the following values:

* ``None``, which will remove the segment from the prompt/statusline.
* A string, which will be the segment contents.
* A list of dicts consisting of a ``contents`` string, and 
  a ``highlight_group`` list. This is useful for providing a particular 
  highlighting group depending on the segment contents.

Local configuration
===================

Depending on the application used it is possible to override configuration. Here 
is the list:

Vim overrides
-------------

Vim configuration can be overridden using the following options:

``g:powerline_config_overrides``
    Dictionary, recursively merged with contents of 
    :file:`powerline/config.json`.

``g:powerline_theme_overrides__{theme_name}``
    Dictionary, recursively merged with contents of 
    :file:`powerline/themes/vim/{theme_name}.json`. Note that this way you can’t 
    redefine some value (e.g. segment) in list, only the whole list itself: only 
    dictionaries are merged recursively.

``g:powerline_config_path``
    Path (must be expanded, ``~`` shortcut is not supported). Points to the 
    directory which will be searched for configuration. When this option is 
    present, none of the other locations are searched.

Powerline script overrides
--------------------------

Powerline script has a number of options controlling powerline behavior. Here 
``VALUE`` always means “some JSON object”.

``-c KEY.NESTED_KEY=VALUE`` or ``--config=KEY.NESTED_KEY=VALUE``
    Overrides options from :file:`powerline/config.json`. 
    ``KEY.KEY2.KEY3=VALUE`` is a shortcut for ``KEY={"KEY2": {"KEY3": VALUE}}``. 
    Multiple options (i.e. ``-c K1=V1 -c K2=V2``) are allowed, result (in the 
    example: ``{"K1": V1, "K2": V2}``) is recursively merged with the contents 
    of the file.

``-t THEME_NAME.KEY.NESTED_KEY=VALUE`` or ``--theme_option=THEME_NAME.KEY.NESTED_KEY=VALUE``
    Overrides options from :file:`powerline/themes/{ext}/{THEME_NAME}.json`. 
    ``KEY.NESTED_KEY=VALUE`` is processed like described above, ``{ext}`` is the 
    first argument to powerline script. May be passed multiple times.

``-p PATH`` or ``--config_path=PATH``
    Sets directory where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed by powerline script itself, but ``-p ~/.powerline`` will likely be 
    expanded by the shell to something like ``-p /home/user/.powerline``.

Zsh/zpython overrides
---------------------

Here overrides are controlled by similarly to the powerline script, but values 
are taken from zsh variables.

``POWERLINE_CONFIG``
    Overrides options from :file:`powerline/config.json`. Should be a zsh 
    associative array with keys equal to ``KEY.NESTED_KEY`` and values being 
    JSON strings. Pair ``KEY.KEY1 VALUE`` is equivalent to ``{"KEY": {"KEY1": 
    VALUE}}``. All pairs are then recursively merged into one dictionary and 
    this dictionary is recursively merged with the contents of the file.

``POWERLINE_THEME_CONFIG``
    Overrides options from :file:`powerline/themes/shell/*.json`. Should be 
    a zsh associative array with keys equal to ``THEME_NAME.KEY.NESTED_KEY`` and 
    values being JSON strings. Is processed like the above ``POWERLINE_CONFIG``, 
    but only subdictionaries for ``THEME_NAME`` key are merged with theme 
    configuration when theme with given name is requested.

``POWERLINE_CONFIG_PATH``
    Sets directory where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed by powerline script itself, but zsh usually performs them on its 
    own if you set variable without quotes: ``POWERLINE_CONFIG_PATH=~/example``. 
    Expansion depends on zsh configuration.

Ipython overrides
-----------------

Ipython overrides depend on ipython version. Before ipython-0.11 you should pass 
additional keyword arguments to setup() function. After ipython-0.11 you should 
use ``c.Powerline.KEY``. Supported ``KEY`` strings or keyword argument names:

``config_overrides``
    Overrides options from :file:`powerline/config.json`. Should be a dictionary 
    that will be recursively merged with the contents of the file.

``theme_overrides``
    Overrides options from :file:`powerline/themes/ipython/*.json`. Should be 
    a dictionary where keys are theme names and values are dictionaries which 
    will be recursively merged with the contents of the given theme.

``path``
    Sets directory where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed thus you cannot use paths starting with ``~/``.
