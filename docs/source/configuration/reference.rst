***********************
Configuration reference
***********************

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

``watcher``
    Select filesystem watcher. Variants are

    =======  ===================================
    Variant  Description
    =======  ===================================
    auto     Selects most performant watcher.
    inotify  Select inotify watcher. Linux only.
    stat     Select stat-based polling watcher.
    =======  ===================================

    Default is ``auto``.

.. _config-common-additional_escapes:

``additional_escapes``
    Valid for shell extensions, makes sense only if :ref:`term_truecolor 
    <config-common-term_truecolor>` is enabled. Is to be set from command-line 
    (unless you are sure you always need it). Controls additional escaping that 
    is needed for tmux/screen to work with terminal true color escape codes: 
    normally tmux/screen prevent terminal emulator from receiving these control 
    codes thus rendering powerline prompt colorless. Valid values: ``"tmux"``, 
    ``"screen"``, ``null`` (default).

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

.. _config-common-default_top_theme:

``default_top_theme``
    String, determines which top-level theme will be used as the default. 
    Defaults to ``powerline``. See `Themes`_ section for more details.

Extension-specific configuration
--------------------------------

Common configuration is a subdictionary that is a value of ``ext`` key in 
:file:`powerline/config.json` file.

``colorscheme``
    Defines the colorscheme used for this extension.

``theme``
    .. _config-ext-theme:

    Defines the theme used for this extension.

``top_theme``
    .. _config-ext-top_theme:

    Defines the top-level theme used for this extension. See `Themes`_ section 
    for more details.

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

    It is expected that you define gradients from least alert color to most 
    alert or use non-alert colors.

.. _config-colorschemes:

Colorschemes
============

:Location: :file:`powerline/colorschemes/{name}.json`, 
           :file:`powerline/colorschemes/__main__.json`, 
           :file:`powerline/colorschemes/{extension}/{name}.json`

Colorscheme files are processed in order given: definitions from each next file 
override those from each previous file. It is required that either 
:file:`powerline/colorschemes/{name}.json`, or 
:file:`powerline/colorschemes/{extension}/{name}.json` exists.

``name``
    Name of the colorscheme.

.. _config-colorschemes-groups:

``groups``
    Segment highlighting groups, consisting of a dict where the key is the 
    name of the highlighting group (usually the function name for function 
    segments), and the value is either

    #) a dict that defines the foreground color, background color and 
       attributes:

       ``fg``
           Foreground color. Must be defined in :ref:`colors 
           <config-colors-colors>`.

       ``bg``
           Background color. Must be defined in :ref:`colors 
           <config-colors-colors>`.

       ``attr``
           List of attributes. Valid values are one or more of ``bold``, 
           ``italic`` and ``underline``. Note that some attributes may be 
           unavailable in some applications or terminal emulators. If you do not 
           need any attributes leave this empty.

    #) a string (an alias): a name of existing group. This group’s definition 
       will be used when this color is requested.

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

:Location: :file:`powerline/themes/{top_theme}.json`, 
           :file:`powerline/themes/__main__.json`, 
           :file:`powerline/themes/{extension}/{name}.json`

Theme files are processed in order given: definitions from each next file 
override those from each previous file. It is required that file 
:file:`powerline/themes/{extension}/{name}.json` exists.

`{top_theme}` component of the file name is obtained either from :ref:`top_theme 
extension-specific key <config-ext-top_theme>` or from :ref:`default_top_theme 
common configuration key <config-common-default_top_theme>`. Powerline ships 
with the following top themes:

==========================  ====================================================
Theme                       Description
==========================  ====================================================
powerline                   Default powerline theme with fancy powerline symbols
unicode                     Theme without any symbols from private use area
unicode_terminus            Theme containing only symbols from terminus PCF font
unicode_terminus_condensed  Like above, but occupies as less space as possible
ascii                       Theme without any unicode characters at all
==========================  ====================================================

``name``
    Name of the theme.

.. _config-themes-default_module:

``default_module``
    Python module where segments will be looked by default.

``spaces``
    Defines number of spaces just before the divider (on the right side) or just 
    after it (on the left side). These spaces will not be added if divider is 
    not drawn.

``dividers``
    Defines the dividers used in all Powerline extensions. This option 
    should usually only be changed if you don't have a patched font, or if 
    you use a font patched with the legacy font patcher.

    The ``hard`` dividers are used to divide segments with different 
    background colors, while the ``soft`` dividers are used to divide 
    segments with the same background color.

.. _config-themes-segment_data:

``segment_data``
    A dict where keys are segment names or strings ``{module}.{name}``. Used to 
    specify default values for various keys:
    :ref:`after <config-themes-seg-after>`,
    :ref:`before <config-themes-seg-before>`,
    :ref:`contents <config-themes-seg-contents>` (only for string segments
    if :ref:`name <config-themes-seg-name>` is defined),
    :ref:`display <config-themes-seg-display>`.

    Key :ref:`args <config-themes-seg-args>` (only for function and 
    segments_list segments) is handled specially: unlike other values it is 
    merged with all other values, except that a single ``{module}.{name}`` key 
    if found prevents merging all ``{name}`` values.

    When using :ref:`local themes <config-ext-local_themes>` values of these 
    keys are first searched in the segment description, then in ``segment_data`` 
    key of a local theme, then in ``segment_data`` key of a :ref:`default theme 
    <config-ext-theme>`. For the :ref:`default theme <config-ext-theme>` itself 
    step 2 is obviously avoided.

    .. note:: Top-level themes are out of equation here: they are merged
        before the above merging process happens.

``segments``
    A dict with a ``left`` and a ``right`` lists, consisting of segment 
    dictionaries. Shell themes may also contain ``above`` list of dictionaries. 
    Each item in ``above`` list may have ``left`` and ``right`` keys like this 
    dictionary, but no ``above`` key.

    .. _config-themes-above:

    ``above`` list is used for multiline shell configurations.

    ``left`` and ``right`` lists are used for segments that should be put on the 
    left or right side in the output. Actual mechanizm of putting segments on 
    the left or the right depends on used renderer, but most renderers require 
    one to specify segment with :ref:`width <config-themes-seg-width>` ``auto`` 
    on either side to make generated line fill all of the available width.

    Each segment dictionary has the following options:

    ``type``
        The segment type. Can be one of ``function`` (default), ``string``, 
        ``filler`` or ``segments_list``:

        ``function``
            The segment contents is the return value of the function defined 
            in the :ref:`name option <config-themes-seg-name>`.

        ``string``
            A static string segment where the contents is defined in the 
            :ref:`contents option <config-themes-seg-contents>`, and the 
            highlighting group is defined in the :ref:`highlight_group 
            option <config-themes-seg-highlight_group>`.

        ``segments_list``
            Sub-list of segments. This list only allows :ref:`name 
            <config-themes-seg-name>`, :ref:`segments 
            <config-themes-seg-segments>` and :ref:`args 
            <config-themes-seg-args>` options.

    ``module``
        .. _config-themes-seg-module:

        Function module, only required for function segments. Defaults to 
        ``powerline.segments.{extension}``. Default is overriden by 
        :ref:`default_module theme option <config-themes-default_module>`.

    ``name``
        .. _config-themes-seg-name:

        Function name, only required for function and list segments.

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
        .. _config-themes-seg-width:

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

    ``display``

        .. _config-themes-seg-display:

        Boolean. If false disables displaying of the segment.
        Defaults to ``True``.

    ``segments``
        A list of subsegments.
