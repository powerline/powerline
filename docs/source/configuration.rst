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
           "divider_highlight_group": "background:divider"
           "args": {
               "unit": "f",
               "location_query": "oslo, norway"
           }
       },

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

.. _config-term_24bit_colors:

``term_24bit_colors``
    Defines whether to output cterm indices (8-bit) or RGB colors (24-bit) 
    to the terminal emulator. See the :ref:`term-feature-support-matrix` for 
    information on whether your terminal emulator supports 24-bit colors.

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
    :ref:`module segment option <config-themes-seg-module>`. Paths defined 
    here have priority when searching for modules.

Extension-specific configuration
--------------------------------

Common configuration is a subdictionary that is a value of ``ext`` key in 
:file:`powerline/config.json` file.

``colorscheme``
    Defines the colorscheme used for this extension.

``theme``
    Defines the theme used for this extension.

``local_themes``
    Defines themes used when certain conditions are met, e.g. for 
    buffer-specific statuslines in vim. Requires a custom matcher and theme.

Colorschemes
============

:Location: :file:`powerline/colorschemes/{extension}/{name}.json`

``name``
    Name of the colorscheme.

.. _config-colorscheme-colors:

``colors``
    Color definitions, consisting of a dict where the key is the name of the 
    color, and the value is one of the following:

    * A cterm color index.
    * A list with a cterm color index and a hex color string (e.g. ``[123, 
      "aabbcc"]``). This is useful for colorschemes that use colors that 
      aren't available in color terminals.

.. _config-colorscheme-groups:

``groups``
    Segment highlighting groups, consisting of a dict where the key is the 
    name of the highlighting group (usually the function name for function 
    segments), and the value is a dict that defines the foreground color, 
    background color and optional attributes:

    ``fg``
        Foreground color. Must be defined in :ref:`colors 
        <config-colorscheme-colors>`.

    ``bg``
        Background color. Must be defined in :ref:`colors 
        <config-colorscheme-colors>`.

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
        the value is the new color. Both the key and the value must be 
        defined in :ref:`colors <config-colorscheme-colors>`.

    ``groups``
        Segment highlighting groups for this mode. Same syntax as the main 
        :ref:`groups <config-colorscheme-groups>` option.

Themes
======

:Location: :file:`powerline/themes/{extension}/{name}.json`

``name``
    Name of the theme.

.. _config-themes-default_module:

``default_module``
    Python module where segments will be looked by default.

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

    ``before``
        A string which will be prepended to the segment contents.

    ``after``
        A string which will be appended to the segment contents.

    ``contents``
        .. _config-themes-seg-contents:

        Segment contents, only required for ``string`` segments.

    ``args``
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
        Optional segment priority. Segments with priority ``-1`` (the 
        default priority) will always be included, regardless of the width 
        of the prompt/statusline.

        If the priority is ``0`` or more, the segment may be removed if the 
        prompt/statusline width is too small for all the segments to be 
        rendered. A lower number means that the segment has a higher 
        priority.

        Segments are removed according to their priority, with low priority 
        segments being removed first.

    ``draw_divider``
        Whether to draw a divider between this and the adjacent segment. The 
        adjacent segment is to the *right* for segments on the *left* side, 
        and vice versa.

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
