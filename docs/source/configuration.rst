*******************************
Configuration and customization
*******************************

.. note::
   **Forking the main GitHub repo is not needed to personalize Powerline 
   configuration!** Please read through the :ref:`quick-guide` for a quick 
   introduction to user configuration.

Powerline is configured with one main configuration file, and with separate 
configuration files for themes and colorschemes. All configuration files are 
written in JSON, with the exception of segment definitions, which are 
written in Python.

Powerline provides default configurations in the following locations:

:ref:`Main configuration <config-main>`
    :file:`powerline/config.json`
:ref:`Colorschemes <config-colorschemes>`
    :file:`powerline/colorschemes/{name}.json`, 
    :file:`powerline/colorscheme/{extension}/__main__.json`, 
    :file:`powerline/colorschemes/{extension}/{name}.json`
:ref:`Themes <config-themes>`
    :file:`powerline/themes/{top_theme}.json`, 
    :file:`powerline/themes/{extension}/__main__.json`, 
    :file:`powerline/themes/{extension}/default.json`

The default configuration files are stored in the main package. User 
configuration files are stored in :file:`$XDG_CONFIG_HOME/powerline` for 
Linux users, and in :file:`~/.config/powerline` for OS X users. This usually 
corresponds to :file:`~/.config/powerline` on both platforms.

If per-instance configuration is needed please refer to :ref:`Local 
configuration overrides <local-configuration-overrides>`.

.. _configuration-merging:

.. note::
   Existing multiple configuration files that have the same name, but are placed 
   in different directories, will be merged. Merging happens in the following 
   order:

   * :file:`{powerline_root}/powerline/config_files` is checked for 
     configuration first. Configuration from this source has least priority.
   * :file:`$XDG_CONFIG_DIRS/powerline` directories are the next ones to check. 
     Checking happens in the reversed order: directories mentioned last are 
     checked before directories mentioned first. Each new found file is merged 
     with the result of previous merge.
   * :file:`$XDG_CONFIG_HOME/powerline` directory is the last to check. 
     Configuration from there has top priority.

   When merging configuration only dictionaries are merged and they are merged 
   recursively: keys from next file overrule those from the previous unless 
   corresponding values are both dictionaries in which case these dictionaries 
   are merged and key is assigned the result of the merge.

.. note:: Some configuration files (i.e. themes and colorschemes) have two level
    of merging: first happens merging described above, second theme- or 
    colorscheme-specific merging happens.

.. _quick-guide:

Quick setup guide
=================

This guide will help you with the initial configuration of Powerline.

Look at configuration in :file:`{powerline_root}/powerline/config_files`. If you 
want to modify some file you can create :file:`~/.config/powerline` directory 
and put modifications there: all configuration files are :ref:`merged 
<configuration-merging>` with each other.

Each extension (vim, tmux, etc.) has its own theme, and they are located in 
:file:`{config directory}/themes/{extension}/default.json`. Best way to modify 
it is to copy this theme as a whole, remove ``segment_data`` key with 
corresponding value if present (unless you need to modify it, in which case only 
modifications must be left) and do necessary modifications in the list of 
segments (lists are not subject to merging: this is why you need a copy).

If you want to move, remove or customize any of the provided segments in the 
copy, you can do that by updating the segment dictionary in the theme you want 
to customize. A segment dictionary looks like this:

.. code-block:: javascript

   {
       "name": "segment_name"
       ...
   }

You can move the segment dictionaries around to change the segment 
positions, or remove the entire dictionary to remove the segment from the 
prompt or statusline.

.. note:: It’s essential that the contents of all your configuration files 
   is valid JSON! It’s strongly recommended that you run your configuration 
   files through ``jsonlint`` after changing them.

.. note::
   If your modifications appear not to work, run :ref:`powerline-lint script 
   <command-powerline-lint>`. This script should show you the location of the 
   error.

Some segments need a user configuration to work properly. Here’s a couple of 
segments that you may want to customize right away:

**E-mail alert segment**
    You have to set your username and password (and possibly server/port) 
    for the e-mail alert segment. If you’re using GMail it’s recommended 
    that you `generate an application-specific password 
    <https://accounts.google.com/IssuedAuthSubTokens>`_ for this purpose.

    Open a theme file, scroll down to the ``email_imap_alert`` segment and 
    set your ``username`` and ``password``.  The server defaults to GMail’s 
    IMAP server, but you can set the server/port by adding a ``server`` and 
    a ``port`` argument.
**Weather segment**
    The weather segment will try to find your location using a GeoIP lookup, 
    so unless you’re on a VPN you probably won’t have to change the location 
    query.

    If you want to change the location query or the temperature unit you’ll 
    have to update the segment arguments. Open a theme file, scroll down to 
    the weather segment and update it to include unit/location query 
    arguments:

    .. code-block:: javascript

       {
           "name": "weather",
           "priority": 50,
           "args": {
               "unit": "F",
               "location_query": "oslo, norway"
           }
       },

References
==========

.. toctree::
   :glob:

   configuration/reference
   configuration/segments
   configuration/listers
   configuration/selectors
   configuration/local
